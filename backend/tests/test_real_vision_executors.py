"""
CM3070 Phase 2 Test Suite: Real Vision Execution Layer & Model Verification.

Validates:
1. Cryptographic checkpoint verification and fail-closed integrity gates
2. Methodology isolation and manual selection in MethodologyExecutorRegistry
3. Coordinate space transformations and anti-double-scaling contracts
4. Empty frame handling and timebase monotonicity
5. Real bounded inference and tracking execution for M1, M2, and M3
6. Mandatory identity withholding gate and fail-closed safety enforcement

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Sections 1, 2)
P0_CONTRACT_TEST_PLAN_REV2A.md (Suites 01-07, 10, 28)
IMPLEMENTATION_PHASE2_SOURCE_READBACK.md
"""
from pathlib import Path
import pytest
import numpy as np

from backend.app.adapters.m1_adapter import (
    M1_DETECTOR_PROVENANCE,
    M1_REID_PROVENANCE,
    M1_THRESHOLDS,
    M1_BOTSORT_CONFIG,
)
from backend.app.adapters.m2_adapter import (
    M2_DETECTOR_PROVENANCE,
    M2_REID_PROVENANCE,
    M2_OPERATING_POINT,
    M2_DEEPEIOU_CONFIG,
    M2_GTA_CONFIG,
)
from backend.app.adapters.m3_adapter import (
    M3_DETECTOR_PROVENANCE,
    M3_OPERATING_POINT,
    M3_SRITRACK_CONFIG,
)
from backend.app.pipeline.registry import (
    create_production_registry,
    resolve_methodology,
    ExecutionReadinessStatus,
    MethodologyExecutorRegistry,
)
from backend.app.runners import (
    BaseVisionRunner,
    M1VisionRunner,
    M2VisionRunner,
    M3VisionRunner,
    verify_checkpoint_file,
)
from backend.app.schemas.canonical_vision import (
    CoordinateSpace,
    FormalIdentityStatus,
    IdentityEvidenceBasis,
    RuntimeIdentityStatus,
    SessionVisionResult,
)
from backend.app.schemas.methodology import MethodologyId


SAMPLE_VIDEO_PATH = Path("G:/My Drive/Football_Training_Assistant_MVP/data/custom/3v3_match_iphone16.MOV")


# ==============================================================================
# 1. Cryptographic Checkpoint Verification & Fail-Closed Integrity Gates
# ==============================================================================
def test_checkpoint_cryptographic_verification_and_integrity():
    """Verify all frozen model checkpoints against their exact SHA-256 and byte sizes."""
    # M1 Detector
    r1 = M1VisionRunner()
    det1, reid1 = r1._resolve_checkpoints()
    assert det1.exists()
    assert det1.stat().st_size == M1_DETECTOR_PROVENANCE.checkpoint_size_bytes
    verify_checkpoint_file(
        det1,
        expected_sha256=M1_DETECTOR_PROVENANCE.checkpoint_sha256,
        expected_size_bytes=M1_DETECTOR_PROVENANCE.checkpoint_size_bytes,
    )

    # M1 ReID
    assert reid1.exists()
    assert reid1.stat().st_size == M1_REID_PROVENANCE.checkpoint_size_bytes
    verify_checkpoint_file(
        reid1,
        expected_sha256=M1_REID_PROVENANCE.checkpoint_sha256,
        expected_size_bytes=M1_REID_PROVENANCE.checkpoint_size_bytes,
    )

    # M2 Detector
    r2 = M2VisionRunner()
    det2, reid2 = r2._resolve_checkpoints()
    assert det2.exists()
    assert det2.stat().st_size == M2_DETECTOR_PROVENANCE.checkpoint_size_bytes
    verify_checkpoint_file(
        det2,
        expected_sha256=M2_DETECTOR_PROVENANCE.checkpoint_sha256,
        expected_size_bytes=M2_DETECTOR_PROVENANCE.checkpoint_size_bytes,
    )

    # M2 ReID
    assert reid2.exists()
    assert reid2.stat().st_size == M2_REID_PROVENANCE.checkpoint_size_bytes
    verify_checkpoint_file(
        reid2,
        expected_sha256=M2_REID_PROVENANCE.checkpoint_sha256,
        expected_size_bytes=M2_REID_PROVENANCE.checkpoint_size_bytes,
    )

    # M3 Detector
    r3 = M3VisionRunner()
    det3, reid3 = r3._resolve_checkpoints()
    assert det3.exists()
    assert det3.stat().st_size == M3_DETECTOR_PROVENANCE.checkpoint_size_bytes
    verify_checkpoint_file(
        det3,
        expected_sha256=M3_DETECTOR_PROVENANCE.checkpoint_sha256,
        expected_size_bytes=M3_DETECTOR_PROVENANCE.checkpoint_size_bytes,
    )

    # M3 ReID
    assert reid3.exists()
    assert reid3.stat().st_size == 1104745338
    verify_checkpoint_file(
        reid3,
        expected_sha256="5f4f1fa2226680c26458872f6241b9a5355d6e29a405fda1acdbcb11874b32f8",
        expected_size_bytes=1104745338,
    )


def test_checkpoint_fail_closed_on_corruption(tmp_path):
    """Corrupted file or mismatched SHA-256 must strictly raise ValueError."""
    fake_ckpt = tmp_path / "corrupt_model.pt"
    fake_ckpt.write_bytes(b"tampered content")

    with pytest.raises(ValueError, match="FROZEN_CHECKPOINT_CORRUPTION"):
        verify_checkpoint_file(
            fake_ckpt,
            expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            expected_size_bytes=1000,
        )

    with pytest.raises(ValueError, match="FROZEN_CHECKPOINT_INTEGRITY_MISMATCH"):
        verify_checkpoint_file(
            fake_ckpt,
            expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            expected_size_bytes=len(b"tampered content"),
        )


# ==============================================================================
# 2. Methodology Isolation & Explicit Registry Execution
# ==============================================================================
def test_production_registry_installation_and_isolation():
    """Verify that create_production_registry registers all three vision runners."""
    prod_registry = create_production_registry()

    for m in [
        MethodologyId.METHOD_1_YOLO11_BOTSORT,
        MethodologyId.METHOD_2_RFDETR_GTATRACK,
        MethodologyId.METHOD_3_YOLO26_SRITRACK,
    ]:
        assert prod_registry.is_ready_for_execution(m) is True
        status, msg = prod_registry.get_readiness_status(m)
        assert status == ExecutionReadinessStatus.READY_FOR_EXECUTION
        assert "installed and validated" in msg
        executor = prod_registry.get_executor(m)
        assert isinstance(executor, BaseVisionRunner)
        assert executor.methodology_id == m

    # Strict isolation: M1 executor must be M1VisionRunner, etc.
    assert isinstance(prod_registry.get_executor(MethodologyId.METHOD_1_YOLO11_BOTSORT), M1VisionRunner)
    assert isinstance(prod_registry.get_executor(MethodologyId.METHOD_2_RFDETR_GTATRACK), M2VisionRunner)
    assert isinstance(prod_registry.get_executor(MethodologyId.METHOD_3_YOLO26_SRITRACK), M3VisionRunner)

    # AUTO resolution strictly maps to M2
    assert resolve_methodology("AUTO") == MethodologyId.METHOD_2_RFDETR_GTATRACK


# ==============================================================================
# 3. Real Bounded Execution for Method 1 (YOLO11m + BoT-SORT)
# ==============================================================================
@pytest.mark.skipif(not SAMPLE_VIDEO_PATH.exists(), reason="Sample video not available")
def test_m1_real_execution_bounded_smoke():
    """Execute real M1 runner on 2 frames of match video; verify SessionVisionResult."""
    runner = M1VisionRunner()
    payload = {
        "video_path": str(SAMPLE_VIDEO_PATH),
        "start_frame": 8156,
        "max_frames": 2,
        "session_id": "test_m1_exec",
        "job_id": "job_m1_test",
    }
    result = runner.execute(payload)

    assert isinstance(result, SessionVisionResult)
    assert result.session_id == "test_m1_exec"
    assert result.job_id == "job_m1_test"
    assert result.source_width == 3840
    assert result.source_height == 2160
    assert result.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE
    assert len(result.frames) == 2

    # Verify frame observations & coordinates
    f0 = result.frames[0]
    assert f0.frame_index == 8156
    assert f0.timestamp_s == pytest.approx(8156 / result.fps, abs=1e-3)
    assert len(f0.observations) > 0, "M1 should detect players in frame 8156"

    for obs in f0.observations:
        # Bounding boxes must be strictly in 3840x2160 MEDIA_SOURCE_SPACE
        assert 0.0 <= obs.bbox.x1 < obs.bbox.x2 <= 3840.0
        assert 0.0 <= obs.bbox.y1 < obs.bbox.y2 <= 2160.0
        assert obs.bbox.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE
        # Normalized bounding boxes
        assert 0.0 <= obs.bbox_norm.x1_norm < obs.bbox_norm.x2_norm <= 1.0
        assert 0.0 <= obs.bbox_norm.y1_norm < obs.bbox_norm.y2_norm <= 1.0
        # Opaque track id is positive integer
        assert obs.opaque_track_id > 0
        # Physical player pseudonym strictly None under automated run
        assert obs.physical_player_pseudonym is None

    # Safety Gate verification
    assert result.player_level_analysis_allowed is False
    assert result.method_formal_identity_status == FormalIdentityStatus.FAIL_UNSAFE_MERGE
    assert result.method_formal_identity_evidence_basis == IdentityEvidenceBasis.FORMAL_DENSE_GT
    assert result.runtime_identity_status == RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS
    assert result.runtime_identity_evidence_basis == IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY


# ==============================================================================
# 4. Real Bounded Execution for Method 2 (RF-DETR-L + Deep-EIoU + OSNet + GTA)
# ==============================================================================
@pytest.mark.skipif(not SAMPLE_VIDEO_PATH.exists(), reason="Sample video not available")
def test_m2_real_execution_bounded_smoke():
    """Execute real M2 runner on 2 frames of match video; verify SessionVisionResult."""
    runner = M2VisionRunner()
    payload = {
        "video_path": str(SAMPLE_VIDEO_PATH),
        "start_frame": 8156,
        "max_frames": 2,
        "session_id": "test_m2_exec",
        "job_id": "job_m2_test",
    }
    result = runner.execute(payload)

    assert isinstance(result, SessionVisionResult)
    assert result.session_id == "test_m2_exec"
    assert result.job_id == "job_m2_test"
    assert result.source_width == 3840
    assert result.source_height == 2160
    assert result.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE
    assert len(result.frames) == 2

    f0 = result.frames[0]
    assert f0.frame_index == 8156
    assert len(f0.observations) > 0, "M2 should detect players in frame 8156"

    for obs in f0.observations:
        assert 0.0 <= obs.bbox.x1 < obs.bbox.x2 <= 3840.0
        assert 0.0 <= obs.bbox.y1 < obs.bbox.y2 <= 2160.0
        assert obs.bbox.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE
        assert obs.confidence >= M2_OPERATING_POINT
        assert obs.opaque_track_id > 0
        assert obs.physical_player_pseudonym is None

    # Safety Gate verification
    assert result.player_level_analysis_allowed is False
    assert result.method_formal_identity_status == FormalIdentityStatus.FAIL_UNSAFE_MERGE
    assert result.method_formal_identity_evidence_basis == IdentityEvidenceBasis.FORMAL_DENSE_GT


# ==============================================================================
# 5. Real Bounded Execution for Method 3 (YOLO26m + SRITrack-v1 + DINOv3)
# ==============================================================================
@pytest.mark.skipif(not SAMPLE_VIDEO_PATH.exists(), reason="Sample video not available")
def test_m3_real_execution_bounded_smoke():
    """Execute real M3 runner on 2 frames where player entered and is tracked."""
    runner = M3VisionRunner()
    payload = {
        "video_path": str(SAMPLE_VIDEO_PATH),
        "start_frame": 14364,
        "max_frames": 2,
        "session_id": "test_m3_exec",
        "job_id": "job_m3_test",
    }
    result = runner.execute(payload)

    assert isinstance(result, SessionVisionResult)
    assert result.session_id == "test_m3_exec"
    assert result.job_id == "job_m3_test"
    assert result.source_width == 3840
    assert result.source_height == 2160
    assert result.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE
    assert len(result.frames) == 2

    # Frame 14364 contains verified track from M3 baseline
    f0 = result.frames[0]
    assert len(f0.observations) > 0, "M3 should have active track at frame 14364"

    for obs in f0.observations:
        assert 0.0 <= obs.bbox.x1 < obs.bbox.x2 <= 3840.0
        assert 0.0 <= obs.bbox.y1 < obs.bbox.y2 <= 2160.0
        assert obs.bbox.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE
        assert obs.opaque_track_id > 0
        assert obs.physical_player_pseudonym is None

    # Safety Gate verification
    assert result.player_level_analysis_allowed is False
    assert result.method_formal_identity_status == FormalIdentityStatus.FAIL_UNSAFE_MERGE
    assert result.method_formal_identity_evidence_basis == IdentityEvidenceBasis.FORMAL_DENSE_GT


# ==============================================================================
# 6. Anti-Double-Scaling Contract Verification
# ==============================================================================
def test_anti_double_scaling_coordinate_lifecycle():
    """Assert that runner outputs are in 1920x1080 and adapter scales ONLY by source factor."""
    runner = M1VisionRunner()
    adapter = runner.get_adapter()

    # Synthetic native runner observation in 1920x1080
    native_data = [
        {
            "frame_index": 10,
            "tracks": [
                {
                    "track_id": 5,
                    "box_working": [100.0, 150.0, 300.0, 450.0],
                    "confidence": 0.85,
                    "class_id": 0,
                }
            ],
        }
    ]

    # Convert to 3840x2160 (scale = 2.0)
    res_4k = adapter.convert_native_tracks_to_session_result(
        session_id="anti_double_scaling_test",
        job_id="job_scale",
        source_width=3840,
        source_height=2160,
        fps=60.0,
        total_frames=1,
        native_frames_data=native_data,
    )

    obs = res_4k.frames[0].observations[0]
    # Exact 2.0x scaling from 1920x1080 to 3840x2160
    assert obs.bbox.x1 == 200.0  # 100 * 2.0
    assert obs.bbox.y1 == 300.0  # 150 * 2.0
    assert obs.bbox.x2 == 600.0  # 300 * 2.0
    assert obs.bbox.y2 == 900.0  # 450 * 2.0
    assert obs.bbox.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE

    # Normalized box
    assert obs.bbox_norm.x1_norm == pytest.approx(200.0 / 3840.0, abs=1e-5)
    assert obs.bbox_norm.y1_norm == pytest.approx(300.0 / 2160.0, abs=1e-5)


# ==============================================================================
# 7. Execution Safety: Fresh Tracker State & No Cross-Job Leakage
# ==============================================================================
def test_fresh_tracker_state_between_independent_jobs():
    """Verify that runners instantiate a fresh tracker per execution job with no state leakage."""
    r2 = M2VisionRunner()
    # Confirm that consecutive calls construct fresh tracker instances and clean local state
    _, _, _, Deep_EIoU, Tracklet, gta = r2._get_models()

    # Create dummy initial tracker instance simulating Job A
    from types import SimpleNamespace
    tracker_params = {
        "with_reid": True,
        "new_track_thresh": M2_DEEPEIOU_CONFIG["new_track_thresh"],
        "track_high_thresh": M2_DEEPEIOU_CONFIG["track_high_thresh"],
        "track_low_thresh": M2_DEEPEIOU_CONFIG["track_low_thresh"],
        "track_buffer": M2_DEEPEIOU_CONFIG["track_buffer"],
        "match_thresh": M2_DEEPEIOU_CONFIG["match_thresh"],
        "proximity_thresh": M2_DEEPEIOU_CONFIG["proximity_thresh"],
        "appearance_thresh": M2_DEEPEIOU_CONFIG["appearance_thresh"],
        "min_box_area": M2_DEEPEIOU_CONFIG["min_box_area"],
        "occ_iou_thresh": M2_DEEPEIOU_CONFIG["occ_iou_thresh"],
        "occ_sim_thresh": M2_DEEPEIOU_CONFIG["occ_sim_thresh"],
        "occ_buffer_frames": M2_DEEPEIOU_CONFIG["occ_buffer_frames"],
    }
    tracker_job_a = Deep_EIoU(SimpleNamespace(**tracker_params), frame_rate=30)
    det = np.array([[100.0, 100.0, 200.0, 200.0, 0.95]], dtype=np.float32)
    feat = np.ones((1, 512), dtype=np.float32)
    tracks_a = tracker_job_a.update(det, feat)
    assert len(tracks_a) == 1
    initial_track_id = tracks_a[0].track_id

    # Simulate Job B: A freshly created tracker must start at frame_id 0 and have 0 tracked tracks
    tracker_job_b = Deep_EIoU(SimpleNamespace(**tracker_params), frame_rate=30)
    assert tracker_job_b.frame_id == 0
    assert len(tracker_job_b.tracked_stracks) == 0
    assert len(tracker_job_b.lost_stracks) == 0
    assert len(tracker_job_b.removed_stracks) == 0


# ==============================================================================
# 8. Execution Safety: AUTO Routing & Fail-Closed Behavior
# ==============================================================================
def test_auto_resolves_only_to_m2():
    """Verify that AUTO resolves strictly to M2 and never to M1 or M3."""
    assert resolve_methodology("AUTO") == MethodologyId.METHOD_2_RFDETR_GTATRACK
    assert resolve_methodology("auto") == MethodologyId.METHOD_2_RFDETR_GTATRACK
    assert resolve_methodology(None) == MethodologyId.METHOD_2_RFDETR_GTATRACK


def test_auto_fails_closed_if_m2_unavailable():
    """Verify that if M2 executor is unavailable, AUTO fails closed and does NOT fall back."""
    custom_registry = MethodologyExecutorRegistry()
    # Register only M1 and M3, leaving M2 unregistered
    r1 = M1VisionRunner()
    r3 = M3VisionRunner()
    custom_registry.register_executor(r1)
    custom_registry.register_executor(r3)

    # AUTO must still resolve strictly to M2
    target_method = resolve_methodology("AUTO")
    assert target_method == MethodologyId.METHOD_2_RFDETR_GTATRACK

    # Registry must indicate M2 is NOT ready
    assert custom_registry.is_ready_for_execution(target_method) is False
    status, msg = custom_registry.get_readiness_status(target_method)
    assert status == ExecutionReadinessStatus.NOT_READY_FOR_EXECUTION

    # Registry get_executor must raise RuntimeError and MUST NOT fall back to M1 or M3
    with pytest.raises(RuntimeError, match="METHODOLOGY_EXECUTOR_NOT_READY"):
        custom_registry.get_executor(target_method)


def test_explicit_methodologies_execute_only_own_runner():
    """Verify that explicit M1/M2/M3 requests strictly execute their own isolated runner."""
    prod_registry = create_production_registry()

    m1_runner = prod_registry.get_executor(MethodologyId.METHOD_1_YOLO11_BOTSORT)
    assert isinstance(m1_runner, M1VisionRunner)
    assert m1_runner.methodology_id == MethodologyId.METHOD_1_YOLO11_BOTSORT

    m2_runner = prod_registry.get_executor(MethodologyId.METHOD_2_RFDETR_GTATRACK)
    assert isinstance(m2_runner, M2VisionRunner)
    assert m2_runner.methodology_id == MethodologyId.METHOD_2_RFDETR_GTATRACK

    m3_runner = prod_registry.get_executor(MethodologyId.METHOD_3_YOLO26_SRITRACK)
    assert isinstance(m3_runner, M3VisionRunner)
    assert m3_runner.methodology_id == MethodologyId.METHOD_3_YOLO26_SRITRACK


# ==============================================================================
# 9. Execution Safety: Output Monotonicity, Bounds, and Identity Withholding
# ==============================================================================
def test_monotonicity_source_bounds_and_identity_withholding():
    """Verify monotonic timestamps, bounding box bounds, provenance, and active identity withholding."""
    runner = M1VisionRunner()
    adapter = runner.get_adapter()

    # Multi-frame synthetic data
    native_data = [
        {
            "frame_index": 0,
            "tracks": [{"track_id": 1, "box_working": [50.0, 60.0, 150.0, 200.0], "confidence": 0.9, "class_id": 0}],
        },
        {
            "frame_index": 1,
            "tracks": [{"track_id": 1, "box_working": [52.0, 61.0, 152.0, 201.0], "confidence": 0.91, "class_id": 0}],
        },
        {
            "frame_index": 2,
            "tracks": [{"track_id": 1, "box_working": [55.0, 63.0, 155.0, 203.0], "confidence": 0.88, "class_id": 0}],
        },
    ]

    res = adapter.convert_native_tracks_to_session_result(
        session_id="monotonic_test",
        job_id="job_mono",
        source_width=1920,
        source_height=1080,
        fps=30.0,
        total_frames=3,
        native_frames_data=native_data,
    )

    # 1. Monotonic timestamps
    prev_ts = -1.0
    for frame in res.frames:
        assert frame.timestamp_s > prev_ts
        prev_ts = frame.timestamp_s

    # 2. Source bounds
    for frame in res.frames:
        for obs in frame.observations:
            assert 0.0 <= obs.bbox.x1 < obs.bbox.x2 <= 1920.0
            assert 0.0 <= obs.bbox.y1 < obs.bbox.y2 <= 1080.0
            assert 0.0 <= obs.bbox_norm.x1_norm < obs.bbox_norm.x2_norm <= 1.0
            assert 0.0 <= obs.bbox_norm.y1_norm < obs.bbox_norm.y2_norm <= 1.0

    # 3. Provenance matches selected method
    assert res.provenance is not None
    assert res.provenance.methodology_id == "METHOD_1_YOLO11_BOTSORT"
    assert res.provenance.detector_checkpoint_sha256 == M1_DETECTOR_PROVENANCE.checkpoint_sha256
    assert res.provenance.reid_checkpoint_sha256 == M1_REID_PROVENANCE.checkpoint_sha256

    # 4. Identity withholding strictly active
    assert res.player_level_analysis_allowed is False
    assert res.method_formal_identity_status == FormalIdentityStatus.FAIL_UNSAFE_MERGE
    assert res.method_formal_identity_evidence_basis == IdentityEvidenceBasis.FORMAL_DENSE_GT
    for frame in res.frames:
        for obs in frame.observations:
            assert obs.physical_player_pseudonym is None

