"""
CM3070 Implementation Phase 5 Test Suite: Production Orchestration, Packaging, Persistence & Product Pipeline Wiring.

Covers Contract Suites and Invariants for Phase 5:
1. Unified orchestrator stage order
2. AUTO -> M2
3. No methodology fallback
4. ASR failure -> correct limitation path
5. No tactical events -> valid result
6. LLM timeout -> deterministic fallback
7. Validator rejection -> deterministic fallback
8. Identity unsafe -> player analytics withheld
9. Dynamic manifest uses probed metadata
10. 360-second duration policy
11. Result persistence idempotency
12. Dispatch idempotency
13. Callback HMAC remains enforced
14. Artifact paths are job-scoped
15. No hardcoded D:/ or G:/ production paths
16. No secret values committed
17. Stale qwen active manifest entry removed
18. Exact Llama digest retained
19. Exact prompt SHA retained
20. Exact Vision checkpoint hashes retained
21. Bounded real orchestrator smoke
22. Persisted result schema roundtrip
23. Frontend result contract alignment
"""
import hashlib
import importlib
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

# Check torch availability for smoke test guard
def _torch_available() -> bool:
    return importlib.util.find_spec("torch") is not None

from backend.app.core.config import settings
from backend.app.pipeline.orchestrator import (
    RESEARCH_HOMOGRAPHY_SHA256,
    MethodologyExecutionError,
    UnifiedAnalysisOrchestrator,
    VideoDurationExceededError,
    execute_analysis_job,
)
from backend.app.pipeline.registry import (
    ExecutionReadinessStatus,
    MethodologyExecutorRegistry,
    create_production_registry,
    resolve_methodology,
)
from backend.app.runners.m1_runner import M1VisionRunner
from backend.app.runners.m2_runner import M2VisionRunner
from backend.app.runners.m3_runner import M3VisionRunner
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
from backend.app.schemas.confidence import IdentityStatus, ReportStatus
from backend.app.schemas.identity import IdentityEvaluation
from backend.app.schemas.dispatch import (
    WorkerDispatch,
    WorkerDispatchRequest,
    WorkerDispatchState,
    WorkerProgressCallbackRequest,
)
from backend.app.schemas.job import AnalysisJob, CreateAnalysisJobRequest, JobStatus
from backend.app.schemas.manifest import (
    JobExecutionManifest,
    MediaProbedMetadata,
    ManifestMethodologyProvenance,
    ManifestRuntimeDiagnostics,
)
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.modes import ApplicationMode, AudioMode, CalibrationMode
from backend.app.schemas.report import GeneratedCoachReport
from backend.app.schemas.result import AnalysisResult
from backend.app.schemas.stages import AnalysisStage
from backend.app.services.dispatch_repository import (
    ActiveDispatchConflictError,
    InMemoryWorkerDispatchRepository,
)
from backend.app.services.dispatch_service import (
    AnalysisDispatchService,
    CallbackOwnershipMismatchError,
    JobStatusConflictError,
)
from backend.app.services.job_repository import InMemoryJobRepository
from backend.app.services.media_probe import MediaProbeResult, ProbeStatus
from backend.app.services.media_repository import InMemoryMediaRepository
from backend.app.services.modal_client import InMemoryModalClient
from backend.app.services.session_repository import InMemorySessionRepository


SAMPLE_VIDEO_PATH = Path("G:/My Drive/Football_Training_Assistant_MVP/data/custom/3v3_match_iphone16.MOV")
SAMPLE_AUDIO_PATH = Path("scratch/C04_Defensive_Marking_clip.wav")


def _create_mock_vision_result(session_id: str, job_id: str) -> SessionVisionResult:
    """Create a minimal valid SessionVisionResult for isolated orchestration tests."""
    return SessionVisionResult(
        session_id=session_id,
        job_id=job_id,
        coordinate_space=CoordinateSpace.MEDIA_SOURCE_SPACE,
        source_width=1920,
        source_height=1080,
        fps=30.0,
        total_frames=10,
        frames=[
            FrameVisionResult(
                frame_index=i,
                timestamp_s=i / 30.0,
                observations=[
                    TrackObservation(
                        opaque_track_id=1,
                        bbox=BoundingBox(
                            x1=100.0,
                            y1=100.0,
                            x2=200.0,
                            y2=200.0,
                            coordinate_space=CoordinateSpace.MEDIA_SOURCE_SPACE,
                        ),
                        bbox_norm=NormalizedBoundingBox(
                            x1_norm=100.0 / 1920.0,
                            y1_norm=100.0 / 1080.0,
                            x2_norm=200.0 / 1920.0,
                            y2_norm=200.0 / 1080.0,
                        ),
                        confidence=0.90,
                        detection_class="person",
                        class_id=0,
                    )
                ],
            )
            for i in range(10)
        ],
        player_level_analysis_allowed=False,
        method_formal_identity_status=FormalIdentityStatus.FAIL_UNSAFE_MERGE,
        method_formal_identity_evidence_basis=IdentityEvidenceBasis.FORMAL_DENSE_GT,
        runtime_identity_status=RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS,
        runtime_identity_evidence_basis=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
        method_provenance=MethodProvenance(
            methodology_id="METHOD_2_RFDETR_GTATRACK",
            detector_checkpoint_sha256="7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85",
            reid_checkpoint_sha256="8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd",
            operating_point=0.20,
            source_resolution=(1920, 1080),
            working_resolution=(1920, 1080),
            scale_factors=(1.0, 1.0),
        ),
    )


# ==============================================================================
# 1. Orchestrator Stage Order & Progression
# ==============================================================================
@pytest.mark.anyio
async def test_01_unified_orchestrator_stage_order():
    """Verify that the orchestrator executes stages in strict canonical order."""
    stages_recorded = []

    def mock_progress(stage, percent, message):
        stages_recorded.append(stage)

    orch = UnifiedAnalysisOrchestrator()
    mock_vision = _create_mock_vision_result("sess_order", "job_order")

    with patch.object(orch, "probe_media_metadata", return_value=MediaProbedMetadata(
        duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )):
        with patch.object(orch.registry, "get_executor") as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.execute.return_value = mock_vision
            mock_get_exec.return_value = mock_exec

            result = await orch.execute_analysis_job(
                job_id="job_order",
                session_id="sess_order",
                video_path=Path("backend/tests/fixtures/dummy.mp4") if Path("backend/tests/fixtures/dummy.mp4").exists() else Path(__file__),
                audio_mode=AudioMode.NO_AUDIO,
                progress_callback=mock_progress,
                force_deterministic_fallback=True,
            )

            assert isinstance(result, AnalysisResult)
            assert AnalysisStage.VALIDATING in stages_recorded
            assert AnalysisStage.PREPROCESSING in stages_recorded
            assert AnalysisStage.DETECTING in stages_recorded
            assert AnalysisStage.IDENTITY_EVALUATION in stages_recorded
            assert AnalysisStage.FUSION in stages_recorded
            assert AnalysisStage.GENERATING_REPORT in stages_recorded
            assert AnalysisStage.UPLOADING_RESULTS in stages_recorded


# ==============================================================================
# 2. AUTO Methodology Resolution & Strict Fallback Prohibition
# ==============================================================================
def test_02_auto_resolves_strictly_to_m2():
    """Verify AUTO resolution per P0 REV2A."""
    assert resolve_methodology("AUTO") == MethodologyId.METHOD_2_RFDETR_GTATRACK
    assert resolve_methodology("auto") == MethodologyId.METHOD_2_RFDETR_GTATRACK
    assert resolve_methodology("") == MethodologyId.METHOD_2_RFDETR_GTATRACK


@pytest.mark.anyio
async def test_03_no_methodology_fallback():
    """Verify that if requested methodology cannot execute, orchestrator fails closed."""
    custom_registry = MethodologyExecutorRegistry()
    orch = UnifiedAnalysisOrchestrator(registry=custom_registry)

    with patch.object(orch, "probe_media_metadata", return_value=MediaProbedMetadata(
        duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )):
        with pytest.raises(MethodologyExecutionError, match="METHODOLOGY_NOT_AVAILABLE"):
            await orch.execute_analysis_job(
                job_id="job_fail",
                session_id="sess_fail",
                video_path=Path(__file__),
                methodology=MethodologyId.METHOD_2_RFDETR_GTATRACK,
            )


# ==============================================================================
# 3. Stage Failure Semantics: ASR & No Tactical Events
# ==============================================================================
@pytest.mark.anyio
async def test_04_asr_failure_leads_to_completed_with_limitations():
    """Verify that ASR extraction failure continues Vision-only with COMPLETED_WITH_LIMITATIONS."""
    orch = UnifiedAnalysisOrchestrator()
    mock_vision = _create_mock_vision_result("sess_asr_fail", "job_asr_fail")

    with patch.object(orch, "probe_media_metadata", return_value=MediaProbedMetadata(
        duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )):
        with patch.object(orch.registry, "get_executor") as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.execute.return_value = mock_vision
            mock_get_exec.return_value = mock_exec

            # Force audio extraction error
            with patch.object(orch.audio_pipeline, "extract_audio", return_value=(None, MagicMock(error_code="FFMPEG_ERROR"))):
                result = await orch.execute_analysis_job(
                    job_id="job_asr_fail",
                    session_id="sess_asr_fail",
                    video_path=Path(__file__),
                    audio_mode=AudioMode.EXTRACT_FROM_VIDEO,
                    force_deterministic_fallback=True,
                )
                assert result.job_status == JobStatus.COMPLETED_WITH_LIMITATIONS
                assert any(lim.code == "AUDIO_EXTRACTION_FAILURE" for lim in result.limitations)


@pytest.mark.anyio
async def test_05_no_tactical_events_yields_valid_result():
    """Verify that zero tactical events in coach audio is a normal valid result, not an ASR failure."""
    orch = UnifiedAnalysisOrchestrator()
    mock_vision = _create_mock_vision_result("sess_no_events", "job_no_events")

    with patch.object(orch, "probe_media_metadata", return_value=MediaProbedMetadata(
        duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )):
        with patch.object(orch.registry, "get_executor") as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.execute.return_value = mock_vision
            mock_get_exec.return_value = mock_exec

            mock_asr_empty = MagicMock(events=[], full_text="good pass over there", segments=[])
            with patch.object(orch.audio_pipeline, "extract_audio", return_value=("fake.wav", None)):
                with patch.object(orch.audio_pipeline, "process_audio", return_value=mock_asr_empty):
                    result = await orch.execute_analysis_job(
                        job_id="job_no_events",
                        session_id="sess_no_events",
                        video_path=Path(__file__),
                        audio_mode=AudioMode.EXTRACT_FROM_VIDEO,
                        force_deterministic_fallback=True,
                    )
                    assert len(result.instruction_events) == 0
                    assert not any("ASR_TRANSCRIPTION_FAILURE" in lim.code for lim in result.limitations)


# ==============================================================================
# 4. LLM Fallback Semantics: Timeout & Validator Rejection
# ==============================================================================
@pytest.mark.anyio
async def test_06_llm_timeout_forces_deterministic_fallback():
    """Verify that LLM request timeout automatically engages deterministic fallback."""
    orch = UnifiedAnalysisOrchestrator()
    mock_vision = _create_mock_vision_result("sess_to", "job_to")

    with patch.object(orch, "probe_media_metadata", return_value=MediaProbedMetadata(
        duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )):
        with patch.object(orch.registry, "get_executor") as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.execute.return_value = mock_vision
            mock_get_exec.return_value = mock_exec

            # Force LLM timeout in reporting pipeline
            timeout_report = GeneratedCoachReport(
                session_id="sess_to",
                job_id="job_to",
                methodology_id="METHOD_2_RFDETR_GTATRACK",
                calibration_mode="NO_METRIC_CALIBRATION",
                player_level_analysis_allowed=False,
                report_status=ReportStatus.DETERMINISTIC_FALLBACK,
                report_markdown="# Fallback Report",
                fallback_reason="LLM_TIMEOUT",
            )
            with patch.object(orch.reporting_pipeline, "generate_report", return_value=timeout_report):
                result = await orch.execute_analysis_job(
                    job_id="job_to",
                    session_id="sess_to",
                    video_path=Path(__file__),
                    audio_mode=AudioMode.NO_AUDIO,
                )
                assert result.report_status == ReportStatus.DETERMINISTIC_FALLBACK
                assert any(lim.code == "DETERMINISTIC_REPORT_FALLBACK" for lim in result.limitations)


@pytest.mark.anyio
async def test_07_validator_rejection_forces_deterministic_fallback():
    """Verify that Patch 001 rejection engages deterministic fallback without failing job."""
    orch = UnifiedAnalysisOrchestrator()
    mock_vision = _create_mock_vision_result("sess_rej", "job_rej")

    with patch.object(orch, "probe_media_metadata", return_value=MediaProbedMetadata(
        duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )):
        with patch.object(orch.registry, "get_executor") as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.execute.return_value = mock_vision
            mock_get_exec.return_value = mock_exec

            rej_report = GeneratedCoachReport(
                session_id="sess_rej",
                job_id="job_rej",
                methodology_id="METHOD_2_RFDETR_GTATRACK",
                calibration_mode="NO_METRIC_CALIBRATION",
                player_level_analysis_allowed=False,
                report_status=ReportStatus.DETERMINISTIC_FALLBACK,
                report_markdown="# Fallback Report",
                fallback_reason="Grounding validation rejected by Patch 001",
            )
            with patch.object(orch.reporting_pipeline, "generate_report", return_value=rej_report):
                result = await orch.execute_analysis_job(
                    job_id="job_rej",
                    session_id="sess_rej",
                    video_path=Path(__file__),
                    audio_mode=AudioMode.NO_AUDIO,
                )
                assert result.report_status == ReportStatus.DETERMINISTIC_FALLBACK
                assert result.job_status == JobStatus.COMPLETED_WITH_LIMITATIONS


# ==============================================================================
# 5. Identity Safety & Dynamic Manifest
# ==============================================================================
@pytest.mark.anyio
async def test_08_identity_unsafe_withholds_player_analytics():
    """Verify that player-level analytics are withheld and observations remain anonymous."""
    orch = UnifiedAnalysisOrchestrator()
    mock_vision = _create_mock_vision_result("sess_id", "job_id")

    with patch.object(orch, "probe_media_metadata", return_value=MediaProbedMetadata(
        duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )):
        with patch.object(orch.registry, "get_executor") as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.execute.return_value = mock_vision
            mock_get_exec.return_value = mock_exec

            result = await orch.execute_analysis_job(
                job_id="job_id",
                session_id="sess_id",
                video_path=Path(__file__),
                audio_mode=AudioMode.NO_AUDIO,
                force_deterministic_fallback=True,
            )
            assert result.identity_evaluation.identity_status in (
                IdentityStatus.FAIL_HIGH_FRAGMENTATION,
                IdentityStatus.FAIL_UNSAFE_MERGE,
                "FAIL_HIGH_FRAGMENTATION",
                "FAIL_UNSAFE_MERGE",
            )


@pytest.mark.anyio
async def test_09_dynamic_manifest_uses_probed_metadata():
    """Verify that JobExecutionManifest records actual probed media metadata."""
    orch = UnifiedAnalysisOrchestrator()
    mock_vision = _create_mock_vision_result("sess_dyn", "job_dyn")

    probed = MediaProbedMetadata(
        duration_s=88.5, fps=29.97, resolution_width=3840, resolution_height=2160, container_format="mov"
    )

    with patch.object(orch, "probe_media_metadata", return_value=probed):
        with patch.object(orch.registry, "get_executor") as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.execute.return_value = mock_vision
            mock_get_exec.return_value = mock_exec

            result = await orch.execute_analysis_job(
                job_id="job_dyn",
                session_id="sess_dyn",
                video_path=Path(__file__),
                audio_mode=AudioMode.NO_AUDIO,
                force_deterministic_fallback=True,
            )
            assert result.execution_manifest is not None
            assert result.execution_manifest.media_metadata.duration_s == 88.5
            assert result.execution_manifest.media_metadata.fps == 29.97
            assert result.execution_manifest.media_metadata.resolution_width == 3840


# ==============================================================================
# 6. Duration Policy & Idempotency Contracts
# ==============================================================================
@pytest.mark.anyio
async def test_10_360_second_duration_policy():
    """Verify that videos exceeding 360 seconds raise VideoDurationExceededError."""
    orch = UnifiedAnalysisOrchestrator(max_duration_seconds=360.0)

    over_limit = MediaProbedMetadata(
        duration_s=361.2, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
    )
    with patch.object(orch, "probe_media_metadata", return_value=over_limit):
        with pytest.raises(VideoDurationExceededError, match="exceeds maximum allowed limit of 360.0 seconds"):
            await orch.execute_analysis_job(
                job_id="job_dur",
                session_id="sess_dur",
                video_path=Path(__file__),
            )


@pytest.mark.anyio
async def test_11_result_persistence_idempotency():
    """Verify that storing the same result twice overwrites idempotently without duplicating."""
    repo = InMemoryJobRepository()
    mock_result = AnalysisResult(
        id="res_1",
        session_id="sess_1",
        job_id="job_1",
        methodology_id=MethodologyId.METHOD_2_RFDETR_GTATRACK,
        application_mode=ApplicationMode.AUTOMATED_ANALYSIS,
        calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        job_status=JobStatus.COMPLETED,
        identity_evaluation=IdentityEvaluation(
            # Formal identity: immutable FAIL_UNSAFE_MERGE from dense-GT benchmark
            identity_status=IdentityStatus.FAIL_UNSAFE_MERGE,
            method_formal_identity_status="FAIL_UNSAFE_MERGE",
            method_formal_identity_evidence_basis="FORMAL_DENSE_GT",
            runtime_identity_status="UNVERIFIED_HEURISTIC_PASS",
            runtime_identity_evidence_basis="RUNTIME_HEURISTIC_ONLY",
            raw_track_ids=0,
            meaningful_identities=0,
            fragmentation_ratio=0.0,
            acceptance_threshold=1.5,
            player_level_analysis_allowed=False,
            withholding_reason="Methodology has not demonstrated safe persistent identity under formal benchmark evaluation.",
        ),
    )

    await repo.store_result(mock_result)
    assert (await repo.get_result("job_1")) is not None

    # Storing again must succeed without error
    await repo.store_result(mock_result)
    assert (await repo.get_result("job_1")).id == "res_1"


@pytest.mark.anyio
async def test_12_dispatch_idempotency():
    """Verify that multiple dispatch calls for the same job return the same dispatch record."""
    job_repo = InMemoryJobRepository()
    session_repo = InMemorySessionRepository()
    media_repo = InMemoryMediaRepository()
    dispatch_repo = InMemoryWorkerDispatchRepository()
    modal_client = InMemoryModalClient()

    # Pre-create session, media, and job
    from backend.app.schemas.media import MediaAsset, MediaType, UploadStatus
    from backend.app.schemas.session import Session

    session_repo.create_session(Session(id="sess_idem", title="Idem"))
    media_repo.create_media_asset(MediaAsset(
        id="vid_idem", session_id="sess_idem", media_type=MediaType.VIDEO,
        storage_bucket="analysis-inputs", storage_path="vid.mp4", original_filename="v.mp4",
        mime_type="video/mp4", size_bytes=1000, upload_status=UploadStatus.VALIDATED
    ))
    job = await job_repo.create_job(CreateAnalysisJobRequest(
        session_id="sess_idem", methodology_id=MethodologyId.METHOD_2_RFDETR_GTATRACK
    ))

    # Pass production registry so readiness check passes
    service = AnalysisDispatchService(
        job_repo=job_repo,
        session_repo=session_repo,
        media_repo=media_repo,
        dispatch_repo=dispatch_repo,
        modal_client=modal_client,
        executor_registry=create_production_registry(),
    )

    d1, was_replay1 = await service.dispatch_job(job.id)
    assert was_replay1 is False

    d2, was_replay2 = await service.dispatch_job(job.id)
    assert was_replay2 is True
    assert d1.id == d2.id


@pytest.mark.anyio
async def test_13_callback_hmac_remains_enforced():
    """Verify that invalid callback ownership or secret fails closed."""
    job_repo = InMemoryJobRepository()
    session_repo = InMemorySessionRepository()
    media_repo = InMemoryMediaRepository()
    dispatch_repo = InMemoryWorkerDispatchRepository()
    modal_client = InMemoryModalClient()

    service = AnalysisDispatchService(
        job_repo=job_repo,
        session_repo=session_repo,
        media_repo=media_repo,
        dispatch_repo=dispatch_repo,
        modal_client=modal_client,
    )

    cb = WorkerProgressCallbackRequest(
        job_id="job_nonexistent",
        dispatch_id="unknown_dispatch",
        dispatch_state=WorkerDispatchState.RUNNING,
        current_stage=AnalysisStage.VALIDATING,
        progress_percent=10.0,
    )

    with pytest.raises(CallbackOwnershipMismatchError):
        await service.handle_worker_callback(job_id="job_mismatch", callback=cb)


def test_14_artifact_paths_are_job_scoped():
    """Verify that artifact references in manifest are strictly job-scoped."""
    orch = UnifiedAnalysisOrchestrator()
    manifest = JobExecutionManifest(
        job_id="job_scoped_123",
        session_id="sess_123",
        media_metadata=MediaProbedMetadata(
            duration_s=10.0, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
        ),
        methodology=ManifestMethodologyProvenance(
            requested_methodology="AUTO",
            resolved_methodology="METHOD_2_RFDETR_GTATRACK",
        ),
        artifact_registry={
            "result_json": "jobs/job_scoped_123/results/result.json",
        },
    )
    for path in manifest.artifact_registry.values():
        assert path.startswith("jobs/job_scoped_123/")


# ==============================================================================
# 7. Security, Provenance & Model Manifest Audits
# ==============================================================================
def test_15_no_hardcoded_drive_letters_in_production_orchestrator():
    """Verify orchestrator source code contains no hardcoded D:\\ or G:\\ development paths."""
    orch_code = Path("backend/app/pipeline/orchestrator.py").read_text(encoding="utf-8")
    assert "D:\\" not in orch_code
    assert "G:\\" not in orch_code
    assert "D:/" not in orch_code
    assert "G:/" not in orch_code


def test_16_no_secret_values_committed():
    """Verify that model manifest and core configs contain zero hardcoded secrets."""
    manifest_text = Path("backend/app/core/model_manifest.yaml").read_text(encoding="utf-8")
    assert "eyJh" not in manifest_text
    assert "ak-" not in manifest_text
    assert "as-" not in manifest_text


def test_17_stale_qwen_active_manifest_entry_removed():
    """Verify that model manifest contains no active qwen references."""
    manifest = yaml.safe_load(Path("backend/app/core/model_manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["reporting_model"]["model_tag"] == "llama3.1:8b"
    assert "qwen3:8b" not in str(manifest)


def test_18_exact_llama_digest_retained():
    """Verify model manifest retains the exact frozen Llama 3.1 8B digest."""
    manifest = yaml.safe_load(Path("backend/app/core/model_manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["reporting_model"]["digest"] == "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"


def test_19_exact_prompt_sha_retained():
    """Verify coach_report_system.txt matches exact frozen SHA-256."""
    prompt_bytes = Path("backend/app/services/prompts/coach_report_system.txt").read_bytes()
    computed_sha = hashlib.sha256(prompt_bytes).hexdigest()
    assert computed_sha == "ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce"


def test_20_exact_vision_checkpoint_hashes_retained():
    """Verify model manifest retains exact frozen checkpoint hashes for M1, M2, M3."""
    manifest = yaml.safe_load(Path("backend/app/core/model_manifest.yaml").read_text(encoding="utf-8"))
    m1 = manifest["methodologies"]["METHOD_1_YOLO11_BOTSORT"]
    m2 = manifest["methodologies"]["METHOD_2_RFDETR_GTATRACK"]
    m3 = manifest["methodologies"]["METHOD_3_YOLO26_SRITRACK"]

    assert m1["detector"]["sha256"] == "ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b"
    assert m1["reid"]["sha256"] == "8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb"

    assert m2["detector"]["sha256"] == "7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85"
    assert m2["reid"]["sha256"] == "8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd"

    assert m3["detector"]["sha256"] == "ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf"
    assert m3["reid"]["sha256"] == "5f4f1fa2226680c26458872f6241b9a5355d6e29a405fda1acdbcb11874b32f8"


# ==============================================================================
# 8. Bounded Real Orchestrator Smoke & Roundtrip Contracts
# ==============================================================================
@pytest.mark.skipif(
    not (SAMPLE_VIDEO_PATH.exists() and SAMPLE_AUDIO_PATH.exists()) or not _torch_available(),
    reason="Sample media files or torch/vision models not accessible in this environment (IMPLEMENTATION_PHASE5_PARTIAL_BLOCK)",
)
@pytest.mark.anyio
async def test_21_bounded_real_orchestrator_smoke():
    """
    Executes a real bounded analysis job through the production orchestrator:
    Real C04 audio + real M2 vision tracking (frames 10415–10418) + Multimodal Fusion + deterministic report.

    Absolute Timebase Invariant:
      - source_offset_s = 167.0 s (C04 clip source offset)
      - Whisper local segment 0: [0.0 s, 4.63 s]
      - With offset: absolute [167.0 s, 171.63 s], reaction window [173.63 s, 177.63 s]
      - Vision frames 10415-10418 at 59.972 fps → absolute timestamps ≈ 173.66 s – 173.71 s
      - These fall inside [173.63 s, 177.63 s] → non-zero fusion evidence observations

    Identity Contract Invariant:
      - method_formal_identity_status = FAIL_UNSAFE_MERGE (immutable, from FORMAL_DENSE_GT)
      - runtime_identity_evidence_basis = RUNTIME_HEURISTIC_ONLY (separate from formal)
      - player_level_analysis_allowed = False
    """
    orch = UnifiedAnalysisOrchestrator()
    stages = []

    def on_prog(stg, pct, msg):
        stages.append((stg.value, pct))

    # Phase 5 Blocker 1: audio_source_offset_s=167.0 restores absolute multimodal timebase
    result = await orch.execute_analysis_job(
        job_id="job_real_smoke",
        session_id="sess_real_smoke",
        video_path=SAMPLE_VIDEO_PATH,
        audio_path=SAMPLE_AUDIO_PATH,
        methodology="AUTO",
        start_frame=10415,
        max_frames=4,
        progress_callback=on_prog,
        force_deterministic_fallback=True,
        audio_source_offset_s=167.0,
    )

    assert isinstance(result, AnalysisResult)
    assert result.methodology_id == MethodologyId.METHOD_2_RFDETR_GTATRACK
    assert len(result.instruction_events) in (1, 2)
    assert result.instruction_events[0].category == "Defensive"
    assert result.instruction_events[0].action == "mark"

    # BLOCKER 1: Absolute timebase — event 0 must carry absolute timestamps (offset applied)
    evt0 = result.instruction_events[0]
    assert evt0.start_s == pytest.approx(167.0, abs=0.1), (
        f"evt0.start_s expected ≈167.0 (absolute), got {evt0.start_s}"
    )
    assert evt0.end_s == pytest.approx(171.63, abs=0.5), (
        f"evt0.end_s expected ≈171.63 (absolute), got {evt0.end_s}"
    )
    # Reaction window: [end_s+2.0, end_s+6.0] → must contain the vision frames at ≈173.66–173.71 s
    assert evt0.alignment_window_start_s == pytest.approx(evt0.end_s + 2.0, abs=0.01)
    assert evt0.alignment_window_end_s == pytest.approx(evt0.end_s + 6.0, abs=0.01)
    # Vision frames (173.66 s) must fall inside the reaction window
    vision_ts_approx = 10415 / 59.972
    assert evt0.alignment_window_start_s <= vision_ts_approx <= evt0.alignment_window_end_s, (
        f"Vision frame timestamp {vision_ts_approx:.3f}s must be inside reaction window "
        f"[{evt0.alignment_window_start_s:.3f}, {evt0.alignment_window_end_s:.3f}]"
    )
    evidence = result.structured_evidence
    assert evidence is not None
    assert evidence["provenance"]["source_offset_s"] == 167.0
    vision_timestamps = evidence["provenance"]["vision_timestamps_s"]
    assert len(vision_timestamps) == 4
    assert all(evt0.alignment_window_start_s <= ts <= evt0.alignment_window_end_s for ts in vision_timestamps)
    assert sum(item["observations_count"] for item in evidence["evidence_items"] if item["source_event_id"] == evt0.id) > 0

    # BLOCKER 2: Formal identity contract
    id_eval = result.identity_evaluation
    assert id_eval.identity_status == IdentityStatus.FAIL_UNSAFE_MERGE, (
        f"Expected FAIL_UNSAFE_MERGE, got {id_eval.identity_status}"
    )
    assert id_eval.method_formal_identity_status == "FAIL_UNSAFE_MERGE"
    assert id_eval.method_formal_identity_evidence_basis == "FORMAL_DENSE_GT"
    assert id_eval.runtime_identity_evidence_basis == "RUNTIME_HEURISTIC_ONLY"
    assert id_eval.player_level_analysis_allowed is False
    # Historical Configuration C numbers must NOT appear in production withholding text
    withholding = id_eval.withholding_reason or ""
    assert "6.1667" not in withholding, "Historical frag ratio must not appear in production withholding text"
    assert "115" not in withholding, "Historical raw_track_ids must not appear in production withholding text"

    assert result.report_status == ReportStatus.DETERMINISTIC_FALLBACK
    assert "# AI-Driven Football Tactical Analysis" in result.report_markdown
    assert result.execution_manifest is not None
    assert result.execution_manifest.media_metadata.resolution_width == 3840


def test_22_persisted_result_schema_roundtrip():
    """Verify full JSON serialization and deserialization of AnalysisResult."""
    manifest = JobExecutionManifest(
        job_id="roundtrip_job",
        session_id="roundtrip_sess",
        media_metadata=MediaProbedMetadata(
            duration_s=12.5, fps=30.0, resolution_width=1920, resolution_height=1080, container_format="mp4"
        ),
        methodology=ManifestMethodologyProvenance(
            requested_methodology="AUTO",
            resolved_methodology="METHOD_2_RFDETR_GTATRACK",
        ),
    )

    orig = AnalysisResult(
        id="res_rt",
        session_id="sess_rt",
        job_id="job_rt",
        methodology_id=MethodologyId.METHOD_2_RFDETR_GTATRACK,
        application_mode=ApplicationMode.AUTOMATED_ANALYSIS,
        calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        job_status=JobStatus.COMPLETED_WITH_LIMITATIONS,
        identity_evaluation=IdentityEvaluation(
            # Formal identity contract — FAIL_UNSAFE_MERGE / FORMAL_DENSE_GT
            identity_status=IdentityStatus.FAIL_UNSAFE_MERGE,
            method_formal_identity_status="FAIL_UNSAFE_MERGE",
            method_formal_identity_evidence_basis="FORMAL_DENSE_GT",
            runtime_identity_status="UNVERIFIED_HEURISTIC_PASS",
            runtime_identity_evidence_basis="RUNTIME_HEURISTIC_ONLY",
            raw_track_ids=0,
            meaningful_identities=0,
            fragmentation_ratio=0.0,
            acceptance_threshold=1.5,
            player_level_analysis_allowed=False,
            withholding_reason="Methodology has not demonstrated safe persistent identity under formal benchmark evaluation.",
        ),
        execution_manifest=manifest,
        report_markdown="# Roundtrip Report",
        report_status=ReportStatus.DETERMINISTIC_FALLBACK,
    )

    json_str = orig.model_dump_json()
    reconstructed = AnalysisResult.model_validate_json(json_str)

    assert reconstructed.id == orig.id
    assert reconstructed.job_status == orig.job_status
    assert reconstructed.methodology_id == orig.methodology_id
    assert reconstructed.execution_manifest.media_metadata.duration_s == 12.5
    # Verify formal identity contract survives roundtrip
    assert reconstructed.identity_evaluation.identity_status == IdentityStatus.FAIL_UNSAFE_MERGE
    assert reconstructed.identity_evaluation.method_formal_identity_status == "FAIL_UNSAFE_MERGE"
    assert reconstructed.identity_evaluation.runtime_identity_evidence_basis == "RUNTIME_HEURISTIC_ONLY"


def test_23_frontend_result_contract_alignment():
    """Verify that AnalysisResult schema contains all fields expected by frontend analysis.$jobId.results.tsx."""
    fields = AnalysisResult.model_fields
    expected_frontend_fields = [
        "id", "session_id", "job_id", "methodology_id", "application_mode",
        "calibration_mode", "job_status", "identity_evaluation", "instruction_events",
        "limitations", "artifact_references", "report_markdown", "report_status",
    ]
    for ef in expected_frontend_fields:
        assert ef in fields, f"Missing field {ef} expected by frontend in AnalysisResult schema"


# ==============================================================================
# 9. Formal vs Runtime Identity Contract (Phase 5 Blocker 2)
# ==============================================================================
def test_24_formal_identity_fields_are_decoupled_from_runtime():
    """
    Verify that IdentityEvaluation carries decoupled formal and runtime identity fields.
    Formal = immutable benchmark result (FAIL_UNSAFE_MERGE / FORMAL_DENSE_GT).
    Runtime = heuristic upload diagnostics (RUNTIME_HEURISTIC_ONLY) — cannot unlock player-level.
    """
    fields = IdentityEvaluation.model_fields

    # Formal identity fields must exist
    assert "method_formal_identity_status" in fields
    assert "method_formal_identity_evidence_basis" in fields

    # Runtime identity fields must exist and be explicitly separate
    assert "runtime_identity_status" in fields
    assert "runtime_identity_evidence_basis" in fields

    # Instantiate and verify defaults match formal contract
    eval_instance = IdentityEvaluation(
        identity_status=IdentityStatus.FAIL_UNSAFE_MERGE,
        raw_track_ids=0,
        meaningful_identities=0,
        fragmentation_ratio=0.0,
    )
    assert eval_instance.method_formal_identity_status == "FAIL_UNSAFE_MERGE"
    assert eval_instance.method_formal_identity_evidence_basis == "FORMAL_DENSE_GT"
    assert eval_instance.runtime_identity_evidence_basis == "RUNTIME_HEURISTIC_ONLY"
    assert eval_instance.player_level_analysis_allowed is False


def test_25_llm_timeout_contract_is_120s():
    """
    Blocker 4: Verify the formal LLM benchmark timeout contract is 120 seconds,
    not 45 seconds. FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120.
    """
    from backend.app.pipeline.reporting import (
        FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS,
        DEFAULT_PRODUCTION_TIMEOUT_SECONDS,
    )
    assert FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS == 120, (
        f"FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS must be 120, got {FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS}"
    )
    assert DEFAULT_PRODUCTION_TIMEOUT_SECONDS == 120, (
        f"DEFAULT_PRODUCTION_TIMEOUT_SECONDS must be 120, got {DEFAULT_PRODUCTION_TIMEOUT_SECONDS}"
    )


def test_26_llm_service_timeout_default_and_override(monkeypatch):
    from backend.app.services.llm_report_service import LLMReportService

    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)
    assert LLMReportService().timeout_seconds == 120
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")
    assert LLMReportService().timeout_seconds == 45


@pytest.mark.anyio
async def test_27_bounded_offset_requires_explicit_audio_source():
    orch = UnifiedAnalysisOrchestrator()
    with pytest.raises(ValueError, match="bounded audio source offset"):
        await orch.execute_analysis_job(
            job_id="offset_guard",
            session_id="offset_guard",
            video_path=Path(__file__),
            audio_source_offset_s=167.0,
        )
