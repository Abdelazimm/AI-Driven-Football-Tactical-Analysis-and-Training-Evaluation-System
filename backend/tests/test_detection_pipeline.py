"""
Unit tests for the production player detection pipeline.
Tests run completely headless on CPU with mock engines; NO real model inference,
NO CUDA, and NO loading of best.pt weights.
"""

import os
import json
import numpy as np
import pytest

from backend.app.pipeline.detection import (
    DetectionConfig,
    DetectionPipeline,
    MockDetectorEngine,
    generate_horizontal_tiles,
    remap_tile_bbox_to_full_frame,
    apply_global_nms,
    compute_box_iou,
    RawCandidateDetection,
    InvalidFrameError,
    DetectionError,
    ModelNotLoadedError,
)
from backend.app.schemas.detection import Detection


@pytest.fixture
def synthetic_fixture():
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        "detection",
        "synthetic_overlap_detections.json",
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_a_three_tile_generation():
    """A. Verify exactly 3 horizontal tiles are generated for standard 1920x1080 and 3840x2160."""
    tiles_1080p = generate_horizontal_tiles(width=1920, height=1080, tile_count=3, overlap_fraction=0.15)
    assert len(tiles_1080p) == 3
    for i, t in enumerate(tiles_1080p):
        assert t.tile_index == i
        assert t.y1 == 0
        assert t.y2 == 1080

    tiles_4k = generate_horizontal_tiles(width=3840, height=2160, tile_count=3, overlap_fraction=0.15)
    assert len(tiles_4k) == 3


def test_b_15_percent_overlap_behavior():
    """B. Verify that adjacent horizontal tiles overlap by at least 15% of tile width."""
    width = 1920
    height = 1080
    overlap_target = 0.15
    tiles = generate_horizontal_tiles(width=width, height=height, tile_count=3, overlap_fraction=overlap_target)

    # Check overlap between tile 0 and tile 1
    overlap_0_1 = tiles[0].x2 - tiles[1].x1
    ratio_0_1 = overlap_0_1 / tiles[0].width
    assert ratio_0_1 >= overlap_target, f"Overlap between tile 0 and 1 is {ratio_0_1:.3f} < {overlap_target}"

    # Check overlap between tile 1 and tile 2
    overlap_1_2 = tiles[1].x2 - tiles[2].x1
    ratio_1_2 = overlap_1_2 / tiles[1].width
    assert ratio_1_2 >= overlap_target, f"Overlap between tile 1 and 2 is {ratio_1_2:.3f} < {overlap_target}"


def test_c_full_frame_coverage():
    """C. Verify continuous full-frame coverage with no gaps from x=0 to x=width."""
    for width in [640, 1280, 1920, 3840, 4096]:
        tiles = generate_horizontal_tiles(width=width, height=1000, tile_count=3, overlap_fraction=0.15)
        assert tiles[0].x1 == 0
        assert tiles[-1].x2 == width

        # Ensure every adjacent boundary has x_next_start < x_current_end (no gaps)
        for i in range(len(tiles) - 1):
            assert tiles[i + 1].x1 < tiles[i].x2, f"Gap detected at width {width} between tile {i} and {i+1}"


def test_d_arbitrary_frame_resolution():
    """D. Verify tiling succeeds and produces valid bounded boxes on non-standard resolutions."""
    for w, h in [(720, 480), (1280, 720), (2560, 1440), (800, 600), (333, 444)]:
        tiles = generate_horizontal_tiles(width=w, height=h, tile_count=3, overlap_fraction=0.15)
        assert len(tiles) == 3
        for t in tiles:
            assert 0 <= t.x1 < t.x2 <= w
            assert 0 == t.y1 < t.y2 == h


def test_e_tile_to_full_frame_bbox_remapping():
    """E. Verify tile-local coordinates are correctly mapped to full-frame coordinates."""
    tile_x_offset = 605
    tile_y_offset = 0
    frame_w = 1920
    frame_h = 1080

    # Local box in tile 1: [15.0, 100.0, 50.0, 200.0]
    remapped = remap_tile_bbox_to_full_frame(
        x1=15.0, y1=100.0, x2=50.0, y2=200.0,
        tile_x_offset=tile_x_offset, tile_y_offset=tile_y_offset,
        frame_width=frame_w, frame_height=frame_h,
    )
    assert remapped == (620.0, 100.0, 655.0, 200.0)


def test_f_clipping_to_image_bounds():
    """F. Verify that bounding boxes extending beyond tile or frame bounds are clipped."""
    frame_w = 1000
    frame_h = 800

    # Box exceeding right and bottom
    remapped = remap_tile_bbox_to_full_frame(
        x1=950.0, y1=750.0, x2=1050.0, y2=850.0,
        tile_x_offset=0, tile_y_offset=0,
        frame_width=frame_w, frame_height=frame_h,
    )
    assert remapped == (950.0, 750.0, 1000.0, 800.0)

    # Completely outside box returns None
    degenerate = remap_tile_bbox_to_full_frame(
        x1=-100.0, y1=-100.0, x2=-50.0, y2=-50.0,
        tile_x_offset=0, tile_y_offset=0,
        frame_width=frame_w, frame_height=frame_h,
    )
    assert degenerate is None


def test_g_person_class_filtering():
    """G. Verify that non-person class IDs are filtered out."""
    config = DetectionConfig(person_class_id=0, confidence_threshold=0.20)
    mock_predictions = {
        0: [
            (10.0, 10.0, 50.0, 100.0, 0.90, 0),   # Person -> Keep
            (60.0, 10.0, 80.0, 40.0, 0.95, 32),   # Sports ball -> Drop
            (100.0, 10.0, 150.0, 80.0, 0.85, 1),  # Bicycle -> Drop
        ],
        1: [],
        2: [],
    }
    pipeline = DetectionPipeline(config=config, detector_engine=MockDetectorEngine(mock_predictions))
    pipeline.load_model("dummy_path")

    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    detections = pipeline.detect_frame(frame, frame_index=0, timestamp_s=0.0)

    assert len(detections) == 1
    assert detections[0].class_id == 0


def test_h_confidence_preservation():
    """H. Verify that confidence values are preserved and low-confidence boxes (<0.20) are excluded."""
    config = DetectionConfig(confidence_threshold=0.20)
    mock_predictions = {
        0: [
            (10.0, 10.0, 50.0, 100.0, 0.8845, 0),  # Valid high confidence
            (60.0, 10.0, 100.0, 100.0, 0.199, 0),  # Just below 0.20 threshold -> drop
        ],
        1: [],
        2: [],
    }
    pipeline = DetectionPipeline(config=config, detector_engine=MockDetectorEngine(mock_predictions))
    pipeline.load_model("dummy_path")

    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    detections = pipeline.detect_frame(frame, frame_index=0, timestamp_s=0.0)

    assert len(detections) == 1
    assert detections[0].confidence == 0.8845


def test_i_duplicate_removal_through_global_nms():
    """I. Verify global NMS merges duplicate detections in overlapping seam with IoU >= 0.70."""
    candidates = [
        # Seam detection from tile 0
        RawCandidateDetection(x1=620.0, y1=400.0, x2=680.0, y2=560.0, confidence=0.75, class_id=0, tile_index=0),
        # Seam detection from tile 1 (almost identical box, higher confidence)
        RawCandidateDetection(x1=620.0, y1=402.0, x2=679.0, y2=558.0, confidence=0.89, class_id=0, tile_index=1),
        # Distinct detection elsewhere
        RawCandidateDetection(x1=100.0, y1=100.0, x2=150.0, y2=200.0, confidence=0.85, class_id=0, tile_index=0),
    ]

    kept = apply_global_nms(candidates, iou_threshold=0.70)
    assert len(kept) == 2
    # Highest confidence for the seam box should be kept
    confidences = [c.confidence for c in kept]
    assert 0.89 in confidences
    assert 0.75 not in confidences
    assert 0.85 in confidences


def test_j_overlapping_tile_synthetic_fixture(synthetic_fixture):
    """J. Test end-to-end detection pipeline using the synthetic overlap fixture without YOLO."""
    w = synthetic_fixture["frame_dimensions"]["width"]
    h = synthetic_fixture["frame_dimensions"]["height"]

    mock_preds = {}
    tiles_data = synthetic_fixture["simulated_tile_detections"]
    for tile_key, items in tiles_data.items():
        idx = int(tile_key.split("_")[1])
        mock_preds[idx] = [
            (it["box"][0], it["box"][1], it["box"][2], it["box"][3], it["confidence"], it["class_id"])
            for it in items
        ]

    config = DetectionConfig(confidence_threshold=0.20, nms_iou_threshold=0.70)
    pipeline = DetectionPipeline(config=config, detector_engine=MockDetectorEngine(mock_preds))
    pipeline.load_model("dummy_path")

    frame = np.zeros((h, w, 3), dtype=np.uint8)
    detections = pipeline.detect_frame(frame, frame_index=42, fps=30.0)

    assert len(detections) == synthetic_fixture["expected_final_detections_count"]
    for det in detections:
        assert isinstance(det, Detection)
        assert det.class_id == 0
        assert det.confidence >= 0.20
        assert 0.0 <= det.x1 < det.x2 <= w
        assert 0.0 <= det.y1 < det.y2 <= h


def test_k_zero_detection_frame_behavior():
    """K. Verify that a frame with no player detections cleanly returns an empty list (not an error)."""
    mock_preds = {0: [], 1: [], 2: []}
    pipeline = DetectionPipeline(detector_engine=MockDetectorEngine(mock_preds))
    pipeline.load_model("dummy_path")

    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    detections = pipeline.detect_frame(frame, frame_index=10, timestamp_s=0.3333)

    assert detections == []
    assert isinstance(detections, list)


def test_l_invalid_frame_error_behavior():
    """L. Verify that invalid frame inputs raise InvalidFrameError."""
    pipeline = DetectionPipeline(detector_engine=MockDetectorEngine({}))
    pipeline.load_model("dummy_path")

    # Non-numpy input
    with pytest.raises(InvalidFrameError):
        pipeline.detect_frame("not_an_image", frame_index=0, timestamp_s=0.0)

    # Wrong shape (2D instead of 3D)
    with pytest.raises(InvalidFrameError):
        pipeline.detect_frame(np.zeros((100, 100)), frame_index=0, timestamp_s=0.0)

    # Empty array
    with pytest.raises(InvalidFrameError):
        pipeline.detect_frame(np.zeros((0, 0, 3)), frame_index=0, timestamp_s=0.0)

    # Missing timing
    with pytest.raises(InvalidFrameError):
        pipeline.detect_frame(np.zeros((100, 100, 3), dtype=np.uint8), frame_index=0, timestamp_s=None, fps=None)


def test_m_timestamp_and_fps_independence():
    """M. Verify that frame timestamp is derived dynamically and never hardcoded to research FPS."""
    pipeline = DetectionPipeline(detector_engine=MockDetectorEngine({0: [], 1: [], 2: []}))
    pipeline.load_model("dummy_path")

    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    # Case 1: Custom explicit timestamp_s
    mock_engine = MockDetectorEngine({0: [(10.0, 10.0, 20.0, 20.0, 0.9, 0)], 1: [], 2: []})
    pipeline.engine = mock_engine
    pipeline.load_model("dummy_path")
    d1 = pipeline.detect_frame(frame, frame_index=60, timestamp_s=1.2345)
    assert d1[0].timestamp_s == 1.2345

    # Case 2: Dynamic 25.0 FPS video
    mock_engine.is_loaded = True
    mock_engine.current_tile_call_count = 0
    d2 = pipeline.detect_frame(frame, frame_index=50, fps=25.0)
    assert d2[0].timestamp_s == 2.0

    # Case 3: Dynamic 30.0 FPS video
    mock_engine.is_loaded = True
    mock_engine.current_tile_call_count = 0
    d3 = pipeline.detect_frame(frame, frame_index=45, fps=30.0)
    assert d3[0].timestamp_s == 1.5


def test_n_output_parses_into_application_detection_schema():
    """N. Verify detection results cleanly instantiate and validate the application Detection schema."""
    mock_engine = MockDetectorEngine({
        0: [(10.0, 20.0, 80.0, 150.0, 0.9321, 0)],
        1: [],
        2: [],
    })
    pipeline = DetectionPipeline(detector_engine=mock_engine)
    pipeline.load_model("dummy_path")

    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    detections = pipeline.detect_frame(frame, frame_index=5, fps=60.0)

    assert len(detections) == 1
    det = detections[0]
    assert isinstance(det, Detection)

    # Test Pydantic dictionary serialization and re-validation
    serialized = det.model_dump()
    reloaded = Detection(**serialized)
    assert reloaded == det
    assert reloaded.detector_manifest_id == "stage4b_fine_tuned_tiled_yolo11m"
    assert reloaded.source_width == 1920
    assert reloaded.source_height == 1080
