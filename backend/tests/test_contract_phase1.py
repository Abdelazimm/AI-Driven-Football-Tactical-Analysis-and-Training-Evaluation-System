"""CM3070 Phase 1 Contract Test Suite.

Governs Phase 1 implementation according to:
- P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md
- P0_CONTRACT_TEST_PLAN_REV2A.md
- P0_REV2A_VISION_PROVENANCE_CORRECTION.md

Covers:
- Suites 01 through 15
- Suite 26 (Dynamic JobExecutionManifest)
- Suite 27 (Nullable Manifest Calibration/RMSE)
- Suite 28 (Checkpoint Provenance Completeness)
- Suite 29 (Media Duration Ceiling Alignment)
"""
import math
from pathlib import Path
import pytest
from typing import List

from backend.app.adapters.common_adapter import (
    compute_normalized_box,
    create_empty_frame,
    project_box_working_to_source,
    validate_source_metadata,
)
from backend.app.adapters.m1_adapter import (
    M1Adapter,
    M1_DETECTOR_PROVENANCE,
    M1_REID_PROVENANCE,
    M1_DETECTION_CONFIG,
    M1_BOTSORT_CONFIG,
)
from backend.app.adapters.m2_adapter import (
    M2Adapter,
    M2_DETECTOR_PROVENANCE,
    M2_REID_PROVENANCE,
    M2_RFDETR_CONFIG,
    M2_GTATRACK_CONFIG,
)
from backend.app.adapters.m3_adapter import (
    M3Adapter,
    M3_DETECTOR_PROVENANCE,
    M3_SRITRACK_CONFIG,
)
from backend.app.core.config import settings
from backend.app.pipeline.registry import resolve_methodology, MethodologyRegistry
from backend.app.schemas.canonical_vision import (
    BoundingBox,
    CalibrationReference,
    CoordinateSpace,
    FormalIdentityStatus,
    IdentityEvidenceBasis,
    MethodProvenance,
    NormalizedBoundingBox,
    RuntimeIdentityStatus,
    TrackObservation,
)
from backend.app.schemas.manifest import (
    JobExecutionManifest,
    ManifestCalibrationMetadata,
    ManifestMethodologyProvenance,
    ManifestRuntimeDiagnostics,
    MediaProbedMetadata,
)
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.video import VideoMetadata
from backend.app.services.calibration_service import (
    CalibrationService,
    CalibrationValidationError,
    RESEARCH_HOMOGRAPHY_SHA256,
    RESEARCH_VIDEO_SHA256,
    RESEARCH_PITCH_LENGTH_M,
    RESEARCH_PITCH_WIDTH_M,
    RESEARCH_INDEPENDENT_RMSE_M,
)
from backend.app.services.identity_safety_service import (
    IdentitySafetyService,
    RuntimeIdentityDiagnostics,
)
from backend.app.services.kinematics_service import (
    KinematicsService,
    MAX_SPEED_KMH_THRESHOLD,
    CONTINUITY_TIME_GAP_THRESHOLD_SECONDS,
)


# ==============================================================================
# SUITE 01: M1 Adapter Baseline & Coordinates
# ==============================================================================
def test_01_m1_adapter_baseline_and_coordinates():
    """Suite 01: Asserts exact frozen M1 baseline detector, ReID, thresholds, and coordinate scaling."""
    # Detector provenance
    assert M1_DETECTOR_PROVENANCE.checkpoint_path == "runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt"
    assert M1_DETECTOR_PROVENANCE.checkpoint_filename == "epoch28.pt"
    assert M1_DETECTOR_PROVENANCE.checkpoint_sha256 == "ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b"
    assert M1_DETECTOR_PROVENANCE.checkpoint_size_bytes == 104950959

    # ReID provenance
    assert M1_REID_PROVENANCE.checkpoint_path == "runs/method_1/M1_FINAL_EVALUATION_BASELINE/checkpoints/yolo26n-reid.onnx"
    assert M1_REID_PROVENANCE.checkpoint_sha256 == "8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb"
    assert M1_REID_PROVENANCE.checkpoint_size_bytes == 9873245

    # Thresholds: candidate floor 0.05, qualification 0.25, tile NMS 0.70, global NMS 0.50
    assert M1_DETECTION_CONFIG["tracker_input_candidate_confidence_floor"] == 0.05
    assert M1_DETECTION_CONFIG["standalone_qualification_confidence"] == 0.25
    assert M1_DETECTION_CONFIG["tile_nms_iou"] == 0.70
    assert M1_DETECTION_CONFIG["global_nms_iou"] == 0.50

    # Purge historical Stage 4B values (40.5MB, 0.20 confidence)
    assert M1_DETECTOR_PROVENANCE.checkpoint_size_bytes != 40539756
    assert M1_DETECTION_CONFIG["tracker_input_candidate_confidence_floor"] != 0.20

    # BoT-SORT parameters
    assert M1_BOTSORT_CONFIG["track_high_thresh"] == 0.35
    assert M1_BOTSORT_CONFIG["track_low_thresh"] == 0.10
    assert M1_BOTSORT_CONFIG["new_track_thresh"] == 0.35
    assert M1_BOTSORT_CONFIG["track_buffer"] == 120
    assert M1_BOTSORT_CONFIG["match_thresh"] == 0.85
    assert M1_BOTSORT_CONFIG["gmc_method"] == "none"
    assert M1_BOTSORT_CONFIG["proximity_thresh"] == 0.15
    assert M1_BOTSORT_CONFIG["appearance_thresh"] == 0.88
    assert M1_BOTSORT_CONFIG["with_reid"] is True
    assert M1_BOTSORT_CONFIG["fuse_score"] is True

    # Coordinates: 1920x1080 -> 3840x2160 applies exact scale = 2.0 without double scaling
    adapter = M1Adapter()
    native_tracks = [
        {
            "frame_index": 0,
            "tracks": [
                {"track_id": 1, "box": [100.0, 200.0, 300.0, 400.0], "confidence": 0.85}
            ]
        }
    ]
    result = adapter.adapt_tracking_results(
        native_tracks,
        source_width=3840,
        source_height=2160,
        source_fps=59.972,
    )
    obs = result.frames[0].observations[0]
    # 100 * 2 = 200, 200 * 2 = 400, 300 * 2 = 600, 400 * 2 = 800
    assert obs.box.x1 == 200.0
    assert obs.box.y1 == 400.0
    assert obs.box.x2 == 600.0
    assert obs.box.y2 == 800.0
    assert obs.opaque_track_id == 1
    assert obs.physical_player_pseudonym is None


# ==============================================================================
# SUITE 02: M2 Adapter Anti-Double-Scaling
# ==============================================================================
def test_02_m2_adapter_anti_double_scaling():
    """Suite 02: Asserts M2 baseline checkpoint, operating point >= 0.50, and anti-double-scaling guarantee."""
    # Detector provenance
    assert M2_DETECTOR_PROVENANCE.checkpoint_path == "runs/method_2/M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth"
    assert M2_DETECTOR_PROVENANCE.checkpoint_filename == "checkpoint_best_total.pth"
    assert M2_DETECTOR_PROVENANCE.checkpoint_sha256 == "7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85"
    assert M2_DETECTOR_PROVENANCE.checkpoint_size_bytes == 134747227

    # ReID provenance
    assert M2_REID_PROVENANCE.checkpoint_path == "runs/method_2/M2_P0_preflight/checkpoints/sports_model.pth.tar-60"
    assert M2_REID_PROVENANCE.checkpoint_filename == "sports_model.pth.tar-60"
    assert M2_REID_PROVENANCE.checkpoint_sha256 == "8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd"
    assert M2_REID_PROVENANCE.checkpoint_size_bytes == 30393613

    # Operating parameters
    assert M2_RFDETR_CONFIG["score_threshold"] == 0.50
    assert M2_RFDETR_CONFIG["external_nms"] is False

    # Anti-double-scaling guarantee:
    # Native runner outputs 1920x1080 working space boxes.
    # Adapter does NOT apply 704 -> 1920 scaling. It applies ONLY source scaling.
    adapter = M2Adapter()
    native_m2_output = [
        {
            "frame_index": 10,
            "tracks": [
                {"track_id": 42, "box": [500.0, 300.0, 700.0, 600.0], "score": 0.88},
                {"track_id": 99, "box": [100.0, 100.0, 200.0, 200.0], "score": 0.40},  # Discarded (< 0.50)
            ]
        }
    ]
    result = adapter.adapt_tracking_results(
        native_m2_output,
        source_width=3840,
        source_height=2160,
        source_fps=30.0,
    )
    frame = result.frames[0]
    assert len(frame.observations) == 1  # 0.40 detection discarded
    obs = frame.observations[0]
    assert obs.opaque_track_id == 42
    # Scaled by 3840/1920 = 2.0
    assert obs.box.x1 == 1000.0
    assert obs.box.y1 == 600.0
    assert obs.box.x2 == 1400.0
    assert obs.box.y2 == 1200.0


# ==============================================================================
# SUITE 03: M3 Adapter P5A Provenance
# ==============================================================================
def test_03_m3_adapter_p5a_provenance():
    """Suite 03: Asserts M3 baseline, P5A amended track_new_th=0.30, and source coordinate projection."""
    assert M3_DETECTOR_PROVENANCE.checkpoint_path == "methodology_comparison/runs/method_3/M3_FORMAL_001_DOMAIN_ADAPTED/checkpoints/M3_ADAPTED_YOLO26M.pt"
    assert M3_DETECTOR_PROVENANCE.checkpoint_sha256 == "ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf"
    assert M3_DETECTOR_PROVENANCE.checkpoint_size_bytes == 44081689
    assert M3_SRITRACK_CONFIG["detector_operating_point"] == 0.30

    # P5A Amendment verification:
    # track_new_th amended from source default 0.70 to 0.30
    assert M3_SRITRACK_CONFIG["track_new_th"] == 0.30
    assert M3_SRITRACK_CONFIG["track_new_th_amendment"] == "P5A_SCORE_COMPATIBILITY_AMENDMENT"
    assert M3_SRITRACK_CONFIG["track_high_th"] == 0.60
    assert M3_SRITRACK_CONFIG["track_buffer"] == 1000

    adapter = M3Adapter()
    native_m3_output = [
        {
            "frame_index": 5,
            "tracks": [
                {"track_id": 7, "box": [400.0, 200.0, 600.0, 500.0], "confidence": 0.75}
            ]
        }
    ]
    result = adapter.adapt_tracking_results(
        native_m3_output,
        source_width=1920,
        source_height=1080,
        source_fps=25.0,
    )
    obs = result.frames[0].observations[0]
    # For 1080p source, scale is 1.0
    assert obs.box.x1 == 400.0
    assert obs.box.y1 == 200.0
    assert obs.box.x2 == 600.0
    assert obs.box.y2 == 500.0


# ==============================================================================
# SUITE 04: Methodology Isolation & Fail-Closed Registry
# ==============================================================================
def test_04_methodology_isolation():
    """Suite 04: Asserts strict isolation between M1, M2, and M3; AUTO -> M2; rejection of unknown; registry fail-closed."""
    # 1. AUTO -> METHOD_2_RFDETR_GTATRACK
    assert resolve_methodology("AUTO") == MethodologyId.METHOD_2_RFDETR_GTATRACK

    # 2. METHOD_1_YOLO11_BOTSORT -> METHOD_1_YOLO11_BOTSORT (enum & string)
    assert resolve_methodology(MethodologyId.METHOD_1_YOLO11_BOTSORT) == MethodologyId.METHOD_1_YOLO11_BOTSORT
    assert resolve_methodology("METHOD_1_YOLO11_BOTSORT") == MethodologyId.METHOD_1_YOLO11_BOTSORT

    # 3. METHOD_2_RFDETR_GTATRACK -> METHOD_2_RFDETR_GTATRACK (enum & string)
    assert resolve_methodology(MethodologyId.METHOD_2_RFDETR_GTATRACK) == MethodologyId.METHOD_2_RFDETR_GTATRACK
    assert resolve_methodology("METHOD_2_RFDETR_GTATRACK") == MethodologyId.METHOD_2_RFDETR_GTATRACK

    # 4. METHOD_3_YOLO26_SRITRACK -> METHOD_3_YOLO26_SRITRACK (enum & string)
    assert resolve_methodology(MethodologyId.METHOD_3_YOLO26_SRITRACK) == MethodologyId.METHOD_3_YOLO26_SRITRACK
    assert resolve_methodology("METHOD_3_YOLO26_SRITRACK") == MethodologyId.METHOD_3_YOLO26_SRITRACK

    # 5. Unknown methodology -> rejected / typed validation failure
    with pytest.raises(ValueError):
        resolve_methodology("UNKNOWN_METHOD")
    with pytest.raises(ValueError):
        resolve_methodology("INVALID_METHODOLOGY_XYZ")
    with pytest.raises(ValueError):
        resolve_methodology("METHOD_4_NONEXISTENT")

    # 6. Production registry remains strictly fail-closed:
    # get_executor(M1), get_executor(M2), get_executor(M3) must fail closed with METHODOLOGY_EXECUTOR_NOT_READY
    registry = MethodologyRegistry()
    for m in [
        MethodologyId.METHOD_1_YOLO11_BOTSORT,
        MethodologyId.METHOD_2_RFDETR_GTATRACK,
        MethodologyId.METHOD_3_YOLO26_SRITRACK,
    ]:
        assert registry.is_ready_for_execution(m) is False
        with pytest.raises(RuntimeError, match="METHODOLOGY_EXECUTOR_NOT_READY"):
            registry.get_executor(m)


# ==============================================================================
# SUITE 05: Canonical Bounding Box Spaces & Validation
# ==============================================================================
def test_05_canonical_bounding_box_spaces():
    """Suite 05: Asserts coordinate spaces and BoundingBox validation in MEDIA_SOURCE_SPACE."""
    assert CoordinateSpace.MEDIA_SOURCE_SPACE == "MEDIA_SOURCE_SPACE"
    assert CoordinateSpace.VISION_WORKING_SPACE == "VISION_WORKING_SPACE"
    assert CoordinateSpace.MODEL_INFERENCE_SPACE == "MODEL_INFERENCE_SPACE"

    # Valid bounding box in 3840x2160
    box = BoundingBox(x1=100.0, y1=200.0, x2=300.0, y2=500.0, source_width=3840, source_height=2160)
    assert box.x1 == 100.0
    assert box.y2 == 500.0

    # Inverted coordinates rejected
    with pytest.raises(ValueError, match=r"must be strictly > x1"):
        BoundingBox(x1=300.0, y1=200.0, x2=100.0, y2=500.0)

    # Exceeding source bounds rejected
    with pytest.raises(ValueError, match=r"exceeds source_width"):
        BoundingBox(x1=100.0, y1=200.0, x2=4000.0, y2=500.0, source_width=3840, source_height=2160)


# ==============================================================================
# SUITE 06: Bounding Box & Timebase Normalization
# ==============================================================================
def test_06_bbox_and_timebase_normalization():
    """Suite 06: Asserts normalized coordinates in [0, 1] and dynamic timestamp derivation."""
    norm = compute_normalized_box(x1=960.0, y1=540.0, x2=1920.0, y2=1080.0, source_width=1920, source_height=1080)
    assert norm.x1_norm == pytest.approx(0.5, abs=1e-5)
    assert norm.y1_norm == pytest.approx(0.5, abs=1e-5)
    assert norm.x2_norm == pytest.approx(1.0, abs=1e-5)
    assert norm.y2_norm == pytest.approx(1.0, abs=1e-5)

    # Probed FPS timebase derivation
    fps = 59.972
    frame_idx = 120
    timestamp_s = frame_idx / fps
    assert timestamp_s == pytest.approx(2.00093, abs=1e-4)


# ==============================================================================
# SUITE 07: Empty Frame Handling
# ==============================================================================
def test_07_empty_frame_handling():
    """Suite 07: Asserts empty frames emit is_empty_frame=True with empty observations."""
    empty_frame = create_empty_frame(frame_index=15, timestamp_s=0.5)
    assert empty_frame.frame_index == 15
    assert empty_frame.is_empty_frame is True
    assert empty_frame.observations == []


# ==============================================================================
# SUITE 08: Formal vs Runtime Identity Separation
# ==============================================================================
def test_08_formal_vs_runtime_identity_separation():
    """Suite 08: Asserts decoupling of method_formal_identity_status from runtime heuristics."""
    service = IdentitySafetyService()
    eval_result = service.evaluate_identity_safety(
        methodology=MethodologyId.METHOD_2_RFDETR_GTATRACK,
        runtime_diagnostics=RuntimeIdentityDiagnostics(
            raw_track_ids_count=50,
            meaningful_ids_count=20,
            fragmentation_ratio=2.5,
        ),
    )
    # Formal status remains permanently FAIL_UNSAFE_MERGE under FORMAL_DENSE_GT
    assert eval_result.method_formal_identity_status == FormalIdentityStatus.FAIL_UNSAFE_MERGE
    assert eval_result.method_formal_identity_evidence_basis == IdentityEvidenceBasis.FORMAL_DENSE_GT

    # Runtime heuristics cannot claim formal unsafe merge
    assert eval_result.runtime_identity_evidence_basis == IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY
    assert eval_result.runtime_identity_status == RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_FAIL


# ==============================================================================
# SUITE 09: Automated Identity Gate Withholding
# ==============================================================================
def test_09_automated_identity_gate_withholding():
    """Suite 09: Asserts player_level_analysis_allowed is False and withholding reason is explicit."""
    service = IdentitySafetyService()
    eval_result = service.evaluate_identity_safety(
        methodology=MethodologyId.METHOD_1_YOLO11_BOTSORT,
    )
    assert eval_result.player_level_analysis_allowed is False
    assert "not demonstrated sufficiently safe persistent physical-player identity" in eval_result.withholding_reason


# ==============================================================================
# SUITE 10: Opaque Track ID Cannot Be Player Pseudonym
# ==============================================================================
def test_10_opaque_track_id_cannot_be_player_pseudonym():
    """Suite 10: Asserts opaque_track_id cannot populate physical_player_pseudonym without Oracle."""
    box = BoundingBox(x1=10.0, y1=10.0, x2=50.0, y2=80.0)
    norm = NormalizedBoundingBox(x1_norm=0.01, y1_norm=0.01, x2_norm=0.05, y2_norm=0.08)

    # Automated run: physical_player_pseudonym must remain None
    obs = TrackObservation(
        frame_index=1,
        timestamp_s=0.033,
        opaque_track_id=14,
        confidence=0.92,
        box=box,
        box_normalized=norm,
        footpoint_x=30.0,
        footpoint_y=80.0,
        physical_player_pseudonym=None,
    )
    assert obs.opaque_track_id == 14
    assert obs.physical_player_pseudonym is None

    # Automated run attempting to assign physical_player_pseudonym raises ValueError
    with pytest.raises(ValueError, match="physical_player_pseudonym must remain null for automated runs"):
        TrackObservation(
            frame_index=1,
            timestamp_s=0.033,
            opaque_track_id=14,
            confidence=0.92,
            box=box,
            box_normalized=norm,
            footpoint_x=30.0,
            footpoint_y=80.0,
            physical_player_pseudonym="PLAYER_01",
            identity_evidence_basis=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
        )


# ==============================================================================
# SUITE 11: Limitation Wording Reflects Evidence Basis
# ==============================================================================
def test_11_frontend_limitation_wording():
    """Suite 11: Asserts limitation copy accurately attributes reason to benchmark evaluation
    and verifies the frontend production results route contract."""
    # 1. Backend Service assertion
    service = IdentitySafetyService()
    eval_result = service.evaluate_identity_safety(MethodologyId.METHOD_2_RFDETR_GTATRACK)
    reason = eval_result.withholding_reason
    assert "formal benchmark evaluation" in reason
    assert "dense-GT benchmark" in reason
    assert "accumulated player-level analytics are withheld" in reason
    assert "runtime diagnostics on the current upload are heuristic only" in reason
    # Must NOT claim the uploaded video itself was proven to contain an unsafe merge
    assert "this video was proven to have unsafe merges" not in reason
    assert "uploaded video itself was proven" not in reason

    # 2. Frontend production results route direct contract assertion
    frontend_results_path = (
        Path(__file__).resolve().parent.parent.parent
        / "frontend"
        / "tactical-ai-insights-main"
        / "src"
        / "routes"
        / "analysis.$jobId.results.tsx"
    )
    assert frontend_results_path.exists(), f"Frontend route not found: {frontend_results_path}"
    results_route_src = frontend_results_path.read_text(encoding="utf-8")

    # Target UI component where LimitationPanel is defined
    frontend_ui_path = (
        Path(__file__).resolve().parent.parent.parent
        / "frontend"
        / "tactical-ai-insights-main"
        / "src"
        / "components"
        / "tactical-ui.tsx"
    )
    assert frontend_ui_path.exists(), f"Frontend UI component not found: {frontend_ui_path}"
    tactical_ui_src = frontend_ui_path.read_text(encoding="utf-8")

    # Route must wire LimitationPanel with result.identity_evaluation.withholding_reason
    assert "LimitationPanel" in results_route_src
    assert "withholding_reason" in results_route_src

    # Evidence basis checks on the results route & component:
    combined_src = results_route_src + "\n" + tactical_ui_src

    # Rule 1: formal dense-GT benchmark failure basis
    assert "dense-GT benchmark" in combined_src or "formal dense-GT" in combined_src

    # Rule 2: accumulated player-level analytics are withheld
    assert "accumulated player-level analytics are withheld" in combined_src

    # Rule 3: runtime diagnostics on the current upload are heuristic only
    assert "runtime diagnostics on the current upload are heuristic only" in combined_src

    # Rule 4: Real UI must NOT claim the uploaded video itself was proven to contain FAIL_UNSAFE_MERGE
    assert "uploaded video itself was proven" not in combined_src.lower()
    assert "upload was proven to contain fail_unsafe_merge" not in combined_src.lower()


# ==============================================================================
# SUITE 12: Calibration Permission Matrix — Geometric Solve Only
# ==============================================================================
def test_12_calibration_geometric_solve_only_suppression():
    """Suite 12: Asserts GEOMETRIC_SOLVE_ONLY suppresses metres, km/h, and RMSE."""
    # Arbitrary 4-point homography matrix
    h_matrix = [
        [0.01, 0.0, 10.0],
        [0.0, 0.01, 5.0],
        [0.0, 0.0, 1.0],
    ]
    service = CalibrationService(
        mode=CalibrationReference.GEOMETRIC_SOLVE_ONLY,
        homography_matrix=h_matrix,
    )
    assert service.allows_visualization is True
    assert service.allows_metrics is False
    assert service.independent_rmse_m is None

    # Point projects for 2D visualization
    pt = service.project_point(100.0, 200.0)
    assert pt is not None
    assert pt[0] == pytest.approx(11.0)
    assert pt[1] == pytest.approx(7.0)


# ==============================================================================
# SUITE 13: Calibration Permission Matrix — No Calibration / Invalid
# ==============================================================================
def test_13_calibration_no_metric_mode():
    """Suite 13: Asserts NO_METRIC_CALIBRATION suppresses metrics and visualization."""
    service = CalibrationService(mode=CalibrationReference.NO_METRIC_CALIBRATION)
    assert service.allows_metrics is False
    assert service.allows_visualization is False
    assert service.project_point(100.0, 100.0) is None
    assert service.independent_rmse_m is None


# ==============================================================================
# SUITE 14: Calibration Permission Matrix — Camera-Specific Validated
# ==============================================================================
def test_14_calibration_camera_specific_validated():
    """Suite 14: Asserts CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED permits metrics and enforces geometry."""
    service = CalibrationService(
        mode=CalibrationReference.CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED,
        source_video_sha256=RESEARCH_VIDEO_SHA256,
    )
    assert service.allows_metrics is True
    assert service.allows_visualization is True
    assert service.pitch_length_m == RESEARCH_PITCH_LENGTH_M
    assert service.pitch_width_m == RESEARCH_PITCH_WIDTH_M
    assert service.independent_rmse_m == pytest.approx(RESEARCH_INDEPENDENT_RMSE_M, abs=1e-3)
    assert service.homography_sha256 == RESEARCH_HOMOGRAPHY_SHA256

    # Compatible video passes
    service.validate_compatibility(RESEARCH_VIDEO_SHA256)

    # Incompatible arbitrary video raises CalibrationValidationError
    with pytest.raises(CalibrationValidationError, match="Incompatible video source SHA"):
        service.validate_compatibility("arbitrary_unknown_video_sha256")


# ==============================================================================
# SUITE 15: Kinematics Time-Based Continuity & Outlier Rejection
# ==============================================================================
def test_15_kinematics_time_gap_and_outlier_rejection():
    """Suite 15: Asserts delta_t > 0.50s continuity reset, >36 km/h rejection, and 7-point median filtering."""
    fps = 30.0
    service = KinematicsService(fps=fps, is_metric_calibrated=True)

    # 1. 7-point median filter verification
    noisy_series = [10.0, 10.0, 10.0, 99.0, 10.0, 10.0, 10.0]
    smoothed = service.apply_7point_median_filter(noisy_series)
    assert smoothed[3] == 10.0  # Spike eliminated

    # 2. Velocity continuity & temporal gap reset
    # Frame 0 to 10 (delta_t = 10/30 = 0.333s <= 0.50s) -> Continuous
    # Frame 10 to 40 (delta_t = 30/30 = 1.000s > 0.50s) -> Gap Reset
    observations = [
        {"frame_index": 0, "metric_x": 0.0, "metric_y": 0.0},
        {"frame_index": 10, "metric_x": 1.0, "metric_y": 0.0},   # disp = 1.0m, dt = 0.333s => 3.0 m/s = 10.8 km/h
        {"frame_index": 40, "metric_x": 10.0, "metric_y": 0.0},  # dt = 1.0s > 0.50s => Continuity Gap!
        {"frame_index": 50, "metric_x": 100.0, "metric_y": 0.0}, # disp = 90.0m, dt = 0.333s => 270 m/s = 972 km/h => Outlier!
    ]
    steps = service.calculate_steps(observations)

    # Step 1: Valid continuous step
    assert steps[1].is_valid is True
    assert steps[1].speed_kmh == pytest.approx(10.8, abs=0.1)

    # Step 2: Continuity gap (> 0.50s)
    assert steps[2].is_valid is False
    assert steps[2].is_continuity_gap is True
    assert "Continuity reset" in steps[2].exclusion_reason

    # Step 3: Outlier speed (> 36.0 km/h)
    assert steps[3].is_valid is False
    assert steps[3].is_continuity_gap is False
    assert steps[3].speed_kmh > MAX_SPEED_KMH_THRESHOLD
    assert "REJECT_AND_EXCLUDE_OUTLIER" in steps[3].exclusion_reason

    # 3. Aggregated metrics: outlier and gap excluded from total distance
    metrics = service.calculate_track_kinematics(observations)
    # Only step 1 (1.0m) should be counted
    assert metrics["total_distance"].value == pytest.approx(1.0, abs=0.1)
    assert metrics["average_speed"].value == pytest.approx(10.8, abs=0.1)
    assert metrics["max_speed"].value == pytest.approx(10.8, abs=0.1)


# ==============================================================================
# SUITE 26: Dynamic Job Execution Manifest
# ==============================================================================
def test_26_dynamic_job_execution_manifest():
    """Suite 26: Asserts JobExecutionManifest records actual probed container values."""
    manifest = JobExecutionManifest(
        job_id="job_dynamic_123",
        session_id="sess_456",
        media_metadata=MediaProbedMetadata(
            duration_s=142.5,
            fps=29.97,
            width=1920,
            height=1080,
            container="mp4",
            video_codec="h264",
        ),
        methodology=ManifestMethodologyProvenance(
            requested="AUTO",
            resolved=MethodologyId.METHOD_2_RFDETR_GTATRACK,
            method_formal_identity_status=FormalIdentityStatus.FAIL_UNSAFE_MERGE,
            method_formal_identity_evidence_basis=IdentityEvidenceBasis.FORMAL_DENSE_GT,
        ),
        runtime_diagnostics=ManifestRuntimeDiagnostics(
            runtime_identity_status=RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS,
            runtime_identity_evidence_basis=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
            player_level_analysis_allowed=False,
            withholding_reason="Automated tracking methodology did not demonstrate safe persistent identity under formal benchmark.",
        ),
    )
    assert manifest.media_metadata.duration_s == 142.5
    assert manifest.media_metadata.fps == 29.97
    assert manifest.media_metadata.width == 1920
    assert manifest.calibration_metadata.mode == CalibrationReference.NO_METRIC_CALIBRATION
    assert manifest.calibration_metadata.homography_sha256 is None


# ==============================================================================
# SUITE 27: Nullable Manifest Calibration & RMSE Fields
# ==============================================================================
def test_27_manifest_calibration_nullable_fields():
    """Suite 27: Asserts homography_sha256 and rmse_m are null unless validated calibration exists."""
    uncalibrated_manifest = ManifestCalibrationMetadata()
    assert uncalibrated_manifest.mode == CalibrationReference.NO_METRIC_CALIBRATION
    assert uncalibrated_manifest.homography_sha256 is None
    assert uncalibrated_manifest.rmse_m is None

    geometric_manifest = ManifestCalibrationMetadata(
        mode=CalibrationReference.GEOMETRIC_SOLVE_ONLY,
        homography_sha256="abc123sha",
        rmse_m=None,  # Strictly None for unvalidated geometric solve
    )
    assert geometric_manifest.rmse_m is None


# ==============================================================================
# SUITE 28: Checkpoint Provenance Completeness
# ==============================================================================
def test_28_checkpoint_provenance_completeness():
    """Suite 28: Asserts cryptographic hashes and byte sizes across all three methods."""
    # M1
    assert len(M1_DETECTOR_PROVENANCE.checkpoint_sha256) == 64
    assert len(M1_REID_PROVENANCE.checkpoint_sha256) == 64
    assert M1_DETECTOR_PROVENANCE.checkpoint_size_bytes == 104950959
    assert M1_REID_PROVENANCE.checkpoint_size_bytes == 9873245

    # M2
    assert len(M2_DETECTOR_PROVENANCE.checkpoint_sha256) == 64
    assert len(M2_REID_PROVENANCE.checkpoint_sha256) == 64
    assert M2_DETECTOR_PROVENANCE.checkpoint_size_bytes == 134747227
    assert M2_REID_PROVENANCE.checkpoint_size_bytes == 30393613

    # M3
    assert len(M3_DETECTOR_PROVENANCE.checkpoint_sha256) == 64
    assert M3_DETECTOR_PROVENANCE.checkpoint_size_bytes == 44081689

    # Research Homography
    assert len(RESEARCH_HOMOGRAPHY_SHA256) == 64


# ==============================================================================
# SUITE 29 (Duration Portion): 360-Second Media Duration Ceiling
# ==============================================================================
def test_29_duration_ceiling_accepts_340s():
    """Suite 29: Asserts 360.0s media duration ceiling accepts the 339.99s research session."""
    assert settings.MAX_VIDEO_DURATION_SECONDS == 360.0

    # 339.99s research session is accepted
    meta_research = VideoMetadata(
        duration_seconds=339.99,
        width=3840,
        height=2160,
        fps=59.972,
        total_frames=20389,
        codec="h264",
        format="mp4",
        file_size_bytes=500000000,
        has_audio=True,
    )
    assert meta_research.duration_seconds <= settings.MAX_VIDEO_DURATION_SECONDS

    # 360.0s boundary accepted
    meta_boundary = VideoMetadata(
        duration_seconds=360.0,
        width=1920,
        height=1080,
        fps=30.0,
        total_frames=10800,
        codec="h264",
        format="mp4",
        file_size_bytes=1000000,
        has_audio=False,
    )
    assert meta_boundary.duration_seconds == 360.0

    # > 360.0s rejected by Pydantic schema validation
    with pytest.raises(ValueError, match="Input should be less than or equal to 360"):
        VideoMetadata(
            duration_seconds=360.1,
            width=1920,
            height=1080,
            fps=30.0,
            total_frames=10803,
            codec="h264",
            format="mp4",
            file_size_bytes=1000000,
            has_audio=False,
        )
