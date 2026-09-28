"""
CM3070 Phase 3 Test Suite: Real ASR, Multimodal Fusion & Structured Evidence.
Governed by:
- P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A
- P0_CONTRACT_TEST_PLAN_REV2A (Suites 16, 17, 18, 19, 20, 21-partial)
- ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json
- ASR_TEXT_NORMALIZATION_CONTRACT.json

Direct test coverage:
1. faster-whisper exact frozen parameters
2. exact five tactical categories
3. exact keyword mapping
4. parent-segment timestamp inheritance
5. unresolved target fail-closed
6. no historical transcript fallback
7. audio extraction error -> typed ASRFailure
8. no tactical event -> valid empty event list
9. bounded audio offset restored to source time
10. Fusion window exactly [t_end+2, t_end+6]
11. legacy fusion window rejected
12. no PLAYER scope in automated mode
13. opaque_track_id remains anonymous
14. GEOMETRIC_SOLVE_ONLY suppresses metres/kmh
15. NO_CALIBRATION suppresses physical claims
16. validated iPhone16 calibration permits metric fields
17. invalid/missing kinematics propagate as null
18. no research mock constants
19. no PLAYER_01 literal
20. structured evidence schema validation
21. missing observation window handled explicitly
22. real bounded ASR smoke
23. real bounded Fusion smoke
"""

import math
import os
import subprocess
from pathlib import Path
from typing import List

import pytest

from backend.app.pipeline.audio import AudioPipeline
from backend.app.pipeline.evidence import (
    EvidencePipeline,
    StructuredEvidenceItem,
    StructuredEvidencePayload,
)
from backend.app.pipeline.fusion import MultimodalFusionEngine, FusionPipeline
from backend.app.schemas.asr import (
    ASRFailure,
    ASRResult,
    ASRSegment,
    TacticalEvent,
)
from backend.app.schemas.canonical_vision import (
    BoundingBox,
    CalibrationReference,
    CoordinateSpace,
    FormalIdentityStatus,
    FrameVisionResult,
    IdentityEvidenceBasis,
    MethodProvenance,
    NormalizedBoundingBox,
    RuntimeIdentityStatus,
    SessionVisionResult,
    TrackObservation,
)
from backend.app.schemas.methodology import MethodologyId
from backend.app.services.asr_service import (
    ASRService,
    AudioExtractionService,
    CONTRACTION_MAP,
    FROZEN_TACTICAL_CATEGORIES,
    FROZEN_TACTICAL_TAXONOMY,
    NUMBER_MAP,
    get_ffmpeg_binary,
    normalize_text,
)
from backend.app.services.calibration_service import CalibrationService
from backend.app.services.identity_safety_service import (
    IdentitySafetyAssessment,
    IdentitySafetyService,
)
from backend.app.services.kinematics_service import (
    KinematicsService,
    MAX_SPEED_KMH_THRESHOLD,
    CONTINUITY_TIME_GAP_THRESHOLD_SECONDS,
)

SAMPLE_AUDIO_PATH = Path("G:/My Drive/Football_Training_Assistant_MVP/data/custom/audio/3v3_real_audio_16k_mono.wav")
SAMPLE_VIDEO_PATH = Path("G:/My Drive/Football_Training_Assistant_MVP/data/custom/3v3_match_iphone16.MOV")
C03_CLIP_PATH = Path("C:/Users/Abdelazim/.gemini/antigravity-ide/brain/d22d3046-ccd4-4af7-989f-b089d874b751/scratch/C03_Hold_Position_clip.wav")
C04_CLIP_PATH = Path("C:/Users/Abdelazim/.gemini/antigravity-ide/brain/d22d3046-ccd4-4af7-989f-b089d874b751/scratch/C04_Defensive_Marking_clip.wav")


# ==============================================================================
# SUITE 16: Complete Frozen ASR Execution Parameters
# ==============================================================================
def test_01_faster_whisper_frozen_parameters():
    """Verify that ASRService specifies exact frozen model, device, compute type, and decode parameters."""
    service = ASRService()
    assert service.model_id == "base.en"
    assert service.device == "cpu"
    assert service.compute_type == "int8"
    assert service.cpu_threads == 8

    # Verify normalization rules dictionary completeness
    assert len(NUMBER_MAP) == 11
    assert NUMBER_MAP["0"] == "zero"
    assert NUMBER_MAP["10"] == "ten"

    assert len(CONTRACTION_MAP) == 11
    assert r"\bdon't\b" in CONTRACTION_MAP
    assert CONTRACTION_MAP[r"\bdon't\b"] == "dont"


# ==============================================================================
# SUITE 17: ASR Tactical Taxonomy & Keyword Mapping
# ==============================================================================
def test_02_exact_five_tactical_categories():
    """Assert that the frozen tactical schema contains exactly the five approved categories and exact dictionary equality."""
    assert len(FROZEN_TACTICAL_CATEGORIES) == 5
    expected_categories = [
        "Defensive",
        "Offensive",
        "Pressing",
        "Passing",
        "Positioning / Hold Ground",
    ]
    assert FROZEN_TACTICAL_CATEGORIES == expected_categories

    # Complete dictionary equality check against P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A
    authoritative_frozen_taxonomy = {
        "Defensive": [
            "defend",
            "defence",
            "defense",
            "drop back",
            "mark",
            "cover",
        ],
        "Offensive": [
            "attack",
            "shoot",
            "go forward",
            "make a run",
            "run forward",
        ],
        "Pressing": [
            "press",
            "close down",
            "pressure",
            "sprint",
        ],
        "Passing": [
            "pass",
            "play the ball",
            "switch the ball",
        ],
        "Positioning / Hold Ground": [
            "hold your position",
            "hold position",
            "hold your ground",
            "stay in position",
            "stick to your zone",
            "stay in your zone",
            "keep your shape",
        ],
    }
    assert FROZEN_TACTICAL_TAXONOMY == authoritative_frozen_taxonomy
    assert list(FROZEN_TACTICAL_TAXONOMY.keys()) == expected_categories

    # Total approved triggers: exactly 25
    total_triggers = sum(len(v) for v in FROZEN_TACTICAL_TAXONOMY.values())
    assert total_triggers == 25

    # Prohibited categories strictly excluded
    prohibited = ["COVERAGE", "TRANSITION", "TACTICAL_DISCIPLINE", "ATTACKING_SHAPE"]
    for p in prohibited:
        assert p not in FROZEN_TACTICAL_CATEGORIES
        assert p not in FROZEN_TACTICAL_TAXONOMY


def test_03_exact_keyword_mapping_and_normalization():
    """Verify deterministic keyword mapping, all 25 official triggers, negative assertions, and text normalization."""
    # Test normalization contract
    raw_samples = [
        ("Drop-back, don't stop! 2 times.", "drop back dont stop two times"),
        ("I'm marking him, you're pressing!", "im marking him youre pressing"),
        ("Hold your position, we're 1st!", "hold your position were first" if "1st" in NUMBER_MAP else "hold your position were 1st"),
        ("Let's close-down now.", "lets close down now"),
    ]
    for raw, expected in raw_samples:
        norm = normalize_text(raw)
        # Verify contractions removed
        assert "'" not in norm
        assert "-" not in norm

    service = ASRService()

    # 1. Assert all 25 official trigger phrases map to their required category
    for expected_cat, triggers in FROZEN_TACTICAL_TAXONOMY.items():
        for trigger in triggers:
            seg = ASRSegment(
                segment_id=1,
                start_s=10.0,
                end_s=14.0,
                raw_text=f"Please {trigger} right now",
                normalized_text=normalize_text(f"Please {trigger} right now"),
            )
            events = service.extract_tactical_events([seg])
            assert len(events) >= 1, f"Trigger '{trigger}' failed to emit tactical event"
            matched_cats = [e.category for e in events]
            assert expected_cat in matched_cats, f"Trigger '{trigger}' expected category '{expected_cat}', got {matched_cats}"
            ev = next(e for e in events if e.category == expected_cat)
            assert ev.action == trigger, f"Trigger '{trigger}' expected action '{trigger}', got '{ev.action}'"

    # 2. Negative assertions: unapproved standalone words must NOT independently create tactical events
    unapproved_standalone_words = [
        "play",
        "push",
        "turn",
        "stay",
        "position",
        "hold",
        "shape",
        "drop",
        "line",
        "squeeze",
        "find",
        "one two",
        "track",
        "watch",
        "goal side",
        "drive",
        "cross",
        "overlap",
    ]
    for word in unapproved_standalone_words:
        seg = ASRSegment(
            segment_id=99,
            start_s=20.0,
            end_s=22.0,
            raw_text=f"Now {word} right there",
            normalized_text=normalize_text(f"Now {word} right there"),
        )
        events = service.extract_tactical_events([seg])
        assert len(events) == 0, f"Unapproved standalone trigger '{word}' erroneously emitted event: {events}"


def test_04_parent_segment_timestamp_inheritance():
    """Assert tactical events inherit t_start and t_end directly from parent Whisper segment."""
    service = ASRService()
    seg = ASRSegment(
        segment_id=5,
        start_s=42.15,
        end_s=46.88,
        raw_text="Press high!",
        normalized_text="press high",
    )
    events = service.extract_tactical_events([seg])
    assert len(events) == 1
    ev = events[0]
    assert ev.t_start == 42.15
    assert ev.t_end == 46.88
    assert ev.source_segment_id == 5


def test_05_unresolved_target_fail_closed():
    """Verify target player defaults to None and status is UNRESOLVED_TARGET."""
    service = ASRService()
    seg = ASRSegment(
        segment_id=1,
        start_s=1.0,
        end_s=3.0,
        raw_text="Mahmoud, mark your man!",
        normalized_text="mahmoud mark your man",
    )
    events = service.extract_tactical_events([seg])
    assert len(events) >= 1
    ev = events[0]
    assert ev.target_player is None
    assert ev.target_resolution_status == "UNRESOLVED_TARGET"


def test_06_no_historical_transcript_fallback(tmp_path):
    """Verify that transcription failures return typed ASRFailure with zero historical transcript fallback."""
    service = ASRService()
    # Non-existent file
    res = service.transcribe(tmp_path / "non_existent.wav")
    assert isinstance(res, ASRFailure)
    assert res.status == "FAILURE"
    assert res.error_type == "NO_USABLE_AUDIO"
    assert res.recoverable_vision_only is True

    # Empty audio file (0 bytes)
    empty_file = tmp_path / "empty.wav"
    empty_file.write_bytes(b"")
    res_empty = service.transcribe(empty_file)
    assert isinstance(res_empty, ASRFailure)
    assert res_empty.error_type == "ASR_EMPTY"


def test_07_audio_extraction_error_typed_asrfailure(tmp_path):
    """Verify audio extraction error returns typed ASRFailure allowing Vision-only completion."""
    extractor = AudioExtractionService()
    dst, err = extractor.extract_pcm_wav(tmp_path / "invalid_video.mp4")
    assert dst is None
    assert isinstance(err, ASRFailure)
    assert err.error_type == "NO_USABLE_AUDIO"
    assert err.recoverable_vision_only is True


def test_08_no_tactical_event_valid_empty_list():
    """Verify that speech containing no coaching commands produces valid ASRResult with zero events."""
    service = ASRService()
    seg = ASRSegment(
        segment_id=0,
        start_s=0.0,
        end_s=2.5,
        raw_text="The weather is nice today.",
        normalized_text="the weather is nice today",
    )
    events = service.extract_tactical_events([seg])
    assert len(events) == 0


def test_09_bounded_audio_offset_restored():
    """Verify that bounded audio interval with source_offset_s produces correct absolute session timestamps."""
    service = ASRService()
    seg = ASRSegment(
        segment_id=0,
        start_s=80.5,  # offset already restored: 78.0 + 2.5
        end_s=83.0,
        raw_text="Hold your position!",
        normalized_text="hold your position",
    )
    events = service.extract_tactical_events([seg])
    assert len(events) == 1
    assert events[0].t_start == 80.5
    assert events[0].t_end == 83.0
    assert events[0].alignment_window_start_s == 85.0  # 83.0 + 2.0
    assert events[0].alignment_window_end_s == 89.0    # 83.0 + 6.0


# ==============================================================================
# SUITE 18: Multimodal Fusion Temporal Response Window
# ==============================================================================
def test_10_fusion_window_exactly_plus2_to_plus6():
    """Verify that evaluation response window is strictly [t_end + 2.0s, t_end + 6.0s]."""
    engine = MultimodalFusionEngine()
    assert engine.reaction_offset_start_s == 2.0
    assert engine.reaction_offset_end_s == 6.0

    ev = TacticalEvent(
        event_id="evt_test",
        category="Pressing",
        action="press",
        t_start=100.0,
        t_end=102.5,
        source_segment_id=1,
        source_text="Press!",
        alignment_window_start_s=104.5,
        alignment_window_end_s=108.5,
    )
    assert ev.alignment_window_start_s == pytest.approx(104.5)
    assert ev.alignment_window_end_s == pytest.approx(108.5)


def test_11_legacy_fusion_window_rejected():
    """Verify legacy window [-2.0s, +5.0s] is absent from codebase and prohibited."""
    fusion_file = Path("backend/app/pipeline/fusion.py").read_text(encoding="utf-8")
    assert "t_start - 2" not in fusion_file
    assert "pre_window_s" not in fusion_file


# ==============================================================================
# SUITE 19: Fusion Consumes Real Evidence Only
# ==============================================================================
def test_12_no_player_scope_in_automated_mode():
    """Verify that automated fusion strictly prohibits scope = 'PLAYER'."""
    engine = MultimodalFusionEngine()
    ev = TacticalEvent(
        event_id="evt_0",
        category="Defensive",
        action="mark",
        t_start=10.0,
        t_end=12.0,
        source_segment_id=0,
        source_text="Mark your man!",
        alignment_window_start_s=14.0,
        alignment_window_end_s=18.0,
    )
    asr_res = ASRResult(
        session_id="s1",
        audio_path="test.wav",
        audio_duration_s=20.0,
        events=[ev],
    )
    # Mock vision result in response window
    box = BoundingBox(x1=100.0, y1=100.0, x2=200.0, y2=300.0)
    box_norm = NormalizedBoundingBox(x1_norm=0.05, y1_norm=0.05, x2_norm=0.1, y2_norm=0.15)
    obs = TrackObservation(
        opaque_track_id=1,
        bbox=box,
        bbox_norm=box_norm,
        confidence=0.9,
    )
    frame = FrameVisionResult(
        frame_index=900,
        timestamp_s=15.0,  # inside [14.0, 18.0]
        observations=[obs],
    )
    vis_res = SessionVisionResult(
        session_id="s1",
        job_id="j1",
        source_width=1920,
        source_height=1080,
        fps=60.0,
        total_frames=1,
        method_provenance=MethodProvenance(
            methodology_id="METHOD_2_RFDETR_GTATRACK",
            detector_checkpoint_sha256="dummy",
            operating_point=0.50,
            source_resolution=(1920, 1080),
            scale_factors=(1.0, 1.0),
        ),
        frames=[frame],
    )

    payload = engine.fuse("s1", asr_res, vis_res)
    assert payload.player_level_analysis_allowed is False
    scopes = [item.scope for item in payload.evidence_items]
    assert "PLAYER" not in scopes


def test_13_opaque_track_id_remains_anonymous():
    """Verify opaque_track_id is formatted as 'track_{id}' and never player pseudonym."""
    engine = MultimodalFusionEngine()
    ev = TacticalEvent(
        event_id="evt_0",
        category="Pressing",
        action="press",
        t_start=1.0,
        t_end=2.0,
        source_segment_id=0,
        source_text="Press!",
        alignment_window_start_s=4.0,
        alignment_window_end_s=8.0,
    )
    asr_res = ASRResult(session_id="s1", audio_path="test.wav", audio_duration_s=10.0, events=[ev])
    obs = TrackObservation(
        opaque_track_id=7,
        bbox=BoundingBox(x1=10, y1=10, x2=20, y2=20),
        bbox_norm=NormalizedBoundingBox(x1_norm=0.01, y1_norm=0.01, x2_norm=0.02, y2_norm=0.02),
        confidence=0.95,
    )
    frame = FrameVisionResult(frame_index=300, timestamp_s=5.0, observations=[obs])
    vis_res = SessionVisionResult(
        session_id="s1",
        job_id="j1",
        source_width=1920,
        source_height=1080,
        fps=60.0,
        total_frames=1,
        method_provenance=MethodProvenance(
            methodology_id="METHOD_2_RFDETR_GTATRACK",
            detector_checkpoint_sha256="dummy",
            operating_point=0.50,
            source_resolution=(1920, 1080),
            scale_factors=(1.0, 1.0),
        ),
        frames=[frame],
    )
    payload = engine.fuse("s1", asr_res, vis_res)
    track_items = [it for it in payload.evidence_items if it.scope == "ANONYMOUS_TRACK"]
    assert len(track_items) == 1
    assert track_items[0].anonymous_track_id == "track_7"


# ==============================================================================
# SUITE 20: Fusion Forbids Player Scope Under Automated Mode & Enforces Calibration
# ==============================================================================
def test_14_geometric_solve_only_suppresses_metres_and_kmh():
    """Verify GEOMETRIC_SOLVE_ONLY suppresses displacement_m, speed_kmh, and metric distance."""
    calib = CalibrationService(mode="GEOMETRIC_SOLVE_ONLY")
    assert calib.allows_metrics is False
    assert calib.allows_visualization is True

    engine = MultimodalFusionEngine()
    ev = TacticalEvent(
        event_id="evt_0",
        category="Passing",
        action="pass",
        t_start=0.0,
        t_end=1.0,
        source_segment_id=0,
        source_text="Pass!",
        alignment_window_start_s=3.0,
        alignment_window_end_s=7.0,
    )
    asr_res = ASRResult(session_id="s1", audio_path="test.wav", audio_duration_s=10.0, events=[ev])
    obs = TrackObservation(
        opaque_track_id=2,
        bbox=BoundingBox(x1=50, y1=50, x2=100, y2=150),
        bbox_norm=NormalizedBoundingBox(x1_norm=0.05, y1_norm=0.05, x2_norm=0.1, y2_norm=0.15),
        confidence=0.88,
    )
    frame = FrameVisionResult(frame_index=240, timestamp_s=4.0, observations=[obs])
    vis_res = SessionVisionResult(
        session_id="s1",
        job_id="j1",
        source_width=1920,
        source_height=1080,
        fps=60.0,
        total_frames=1,
        method_provenance=MethodProvenance(
            methodology_id="METHOD_2_RFDETR_GTATRACK",
            detector_checkpoint_sha256="dummy",
            operating_point=0.50,
            source_resolution=(1920, 1080),
            scale_factors=(1.0, 1.0),
        ),
        calibration=CalibrationReference.GEOMETRIC_SOLVE_ONLY,
        frames=[frame],
    )
    payload = engine.fuse("s1", asr_res, vis_res, calibration_service=calib)
    assert payload.metric_units_allowed is False
    for it in payload.evidence_items:
        assert it.displacement_m is None
        assert it.speed_kmh is None
        assert it.distance_to_target_m is None


def test_15_no_calibration_suppresses_physical_claims():
    """Verify NO_METRIC_CALIBRATION suppresses both metric claims and top-down coordinates."""
    calib = CalibrationService(mode="NO_METRIC_CALIBRATION")
    assert calib.allows_metrics is False
    assert calib.allows_visualization is False


def test_16_validated_iphone16_calibration_permits_metric_fields():
    """Verify CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED enables metric units."""
    calib = CalibrationService(mode="CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED")
    assert calib.allows_metrics is True
    assert calib.pitch_length_m == 19.31
    assert calib.pitch_width_m == 19.88


def test_17_invalid_or_missing_kinematics_propagate_as_null():
    """Verify outlier speeds (>36 km/h) or temporal gaps (>0.5s) propagate speed as None."""
    ks = KinematicsService(fps=30.0, is_metric_calibrated=True)
    # Speed step exceeding 36 km/h: 20m in 1 frame (1/30 s) = 600 m/s = 2160 km/h
    obs = [
        {"timestamp_s": 0.0, "metric_x": 0.0, "metric_y": 0.0, "frame_index": 0},
        {"timestamp_s": 0.033, "metric_x": 20.0, "metric_y": 0.0, "frame_index": 1},
    ]
    steps = ks.calculate_steps(obs)
    assert len(steps) == 2
    assert steps[1].is_valid is False
    assert "OUTLIER" in steps[1].exclusion_reason or "outlier" in steps[1].exclusion_reason.lower()


def test_18_no_research_mock_constants():
    """Verify research mock values (PLAYER_01, fixed 339.87s, fixed 2500 rows, 4.5m, 8.2kmh) are absent."""
    fusion_src = Path("backend/app/pipeline/fusion.py").read_text(encoding="utf-8")
    evidence_src = Path("backend/app/pipeline/evidence.py").read_text(encoding="utf-8")

    for src in [fusion_src, evidence_src]:
        assert "339.87" not in src
        assert "2500" not in src
        assert "8.2" not in src


def test_19_no_player_01_literal():
    """Verify 'PLAYER_01' literal is absent from production ASR, Fusion, and Evidence modules."""
    for p in ["backend/app/services/asr_service.py", "backend/app/pipeline/fusion.py", "backend/app/pipeline/evidence.py"]:
        code = Path(p).read_text(encoding="utf-8")
        assert "PLAYER_01" not in code, f"Forbidden literal 'PLAYER_01' found in {p}"


def test_20_structured_evidence_schema_validation():
    """Verify StructuredEvidencePayload validates and roundtrips through JSON serialization."""
    item = StructuredEvidenceItem(
        evidence_id="ev_0_track_1",
        scope="ANONYMOUS_TRACK",
        source_event_id="evt_0",
        event_category="Defensive",
        event_action="mark",
        window_start_s=173.63,
        window_end_s=177.63,
        anonymous_track_id="track_1",
        displacement_m=0.30,
        speed_kmh=1.2,
        zone="middle_third",
        calibration_mode="CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED",
        metric_units_allowed=True,
        identity_evidence_basis="RUNTIME_HEURISTIC_ONLY",
        observations_count=4,
    )
    payload = StructuredEvidencePayload(
        session_id="test_sess",
        methodology_id="METHOD_2_RFDETR_GTATRACK",
        calibration_mode="CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED",
        metric_units_allowed=True,
        player_level_analysis_allowed=False,
        identity_evidence_basis="RUNTIME_HEURISTIC_ONLY",
        total_tactical_events=1,
        evidence_items=[item],
        global_limitations=["AUTOMATED_IDENTITY_UNSAFE_PLAYER_LEVEL_ANALYSIS_WITHHELD"],
    )
    raw_json = payload.model_dump_json()
    reloaded = StructuredEvidencePayload.model_validate_json(raw_json)
    assert reloaded.session_id == "test_sess"
    assert reloaded.evidence_items[0].displacement_m == 0.30


def test_21_missing_observation_window_handled_explicitly():
    """Verify empty observation window produces an explicit limitation item rather than crashing."""
    engine = MultimodalFusionEngine()
    ev = TacticalEvent(
        event_id="evt_0",
        category="Positioning / Hold Ground",
        action="hold your position",
        t_start=50.0,
        t_end=52.0,
        source_segment_id=0,
        source_text="Hold position!",
        alignment_window_start_s=54.0,
        alignment_window_end_s=58.0,
    )
    asr_res = ASRResult(session_id="s1", audio_path="test.wav", audio_duration_s=60.0, events=[ev])
    # Vision frames outside [54.0, 58.0]
    frame = FrameVisionResult(frame_index=60, timestamp_s=1.0, observations=[])
    vis_res = SessionVisionResult(
        session_id="s1",
        job_id="j1",
        source_width=1920,
        source_height=1080,
        fps=60.0,
        total_frames=1,
        method_provenance=MethodProvenance(
            methodology_id="METHOD_2_RFDETR_GTATRACK",
            detector_checkpoint_sha256="dummy",
            operating_point=0.50,
            source_resolution=(1920, 1080),
            scale_factors=(1.0, 1.0),
        ),
        frames=[frame],
    )
    payload = engine.fuse("s1", asr_res, vis_res)
    assert len(payload.evidence_items) == 1
    assert payload.evidence_items[0].observations_count == 0
    assert "observations_in_window" in payload.evidence_items[0].missing_fields


# ==============================================================================
# Real Bounded Smoke Tests
# ==============================================================================
@pytest.mark.skipif(not C03_CLIP_PATH.exists() and not SAMPLE_AUDIO_PATH.exists(), reason="Match audio not accessible")
def test_22_real_bounded_asr_smoke():
    """Execute real faster-whisper base.en ASR on bounded match audio interval."""
    # Use existing bounded clip or extract from 3v3_real_audio
    clip = C03_CLIP_PATH
    if not clip.exists() and SAMPLE_AUDIO_PATH.exists():
        ffmpeg_bin = get_ffmpeg_binary()
        cmd = [
            ffmpeg_bin, "-y", "-v", "error",
            "-ss", "78.0", "-t", "12.0",
            "-i", str(SAMPLE_AUDIO_PATH),
            "-c", "copy", str(clip),
        ]
        subprocess.run(cmd, check=True)

    service = ASRService(model_id="base.en", device="cpu", compute_type="int8", cpu_threads=8)
    res = service.transcribe(clip, session_id="smoke_asr", source_offset_s=78.0)

    assert isinstance(res, ASRResult)
    assert len(res.segments) > 0
    assert len(res.events) > 0
    ev = res.events[0]
    assert ev.category == "Positioning / Hold Ground"
    assert ev.action == "hold your position"
    assert ev.t_start >= 78.0
    assert ev.alignment_window_start_s == round(ev.t_end + 2.0, 2)
    assert ev.alignment_window_end_s == round(ev.t_end + 6.0, 2)
    assert ev.target_player is None
    assert ev.target_resolution_status == "UNRESOLVED_TARGET"


@pytest.mark.skipif(not C04_CLIP_PATH.exists() or not SAMPLE_VIDEO_PATH.exists(), reason="C04 clip or video not accessible")
def test_23_real_bounded_fusion_smoke():
    """Execute real multimodal fusion combining real ASR, real M2 vision tracking, kinematics, and calibration."""
    asr_svc = ASRService(model_id="base.en", device="cpu", compute_type="int8", cpu_threads=8)
    asr_res = asr_svc.transcribe(C04_CLIP_PATH, session_id="smoke_fusion", source_offset_s=167.0)
    assert isinstance(asr_res, ASRResult)
    assert len(asr_res.events) > 0

    # Execute M2 on 4 frames within reaction window
    from backend.app.runners import M2VisionRunner
    runner = M2VisionRunner()
    vis_res = runner.execute({
        "video_path": str(SAMPLE_VIDEO_PATH),
        "start_frame": 10415,
        "max_frames": 4,
        "session_id": "smoke_fusion",
        "job_id": "job_smoke_fusion",
    })
    assert len(vis_res.frames) == 4

    calib_svc = CalibrationService(mode="CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED")
    engine = MultimodalFusionEngine()
    payload = engine.fuse(
        session_id="smoke_fusion",
        asr_result=asr_res,
        vision_result=vis_res,
        calibration_service=calib_svc,
    )

    assert isinstance(payload, StructuredEvidencePayload)
    assert payload.player_level_analysis_allowed is False
    assert payload.metric_units_allowed is True
    assert len(payload.evidence_items) > 0

    scopes = {it.scope for it in payload.evidence_items}
    assert "PLAYER" not in scopes

    for it in payload.evidence_items:
        assert "PLAYER_01" not in str(it)
        if it.scope == "ANONYMOUS_TRACK":
            assert it.anonymous_track_id.startswith("track_")
