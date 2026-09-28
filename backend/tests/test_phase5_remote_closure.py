"""Regression checks for the Phase 5 remote product path."""
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.app.schemas.dispatch import WorkerDispatchRequest, WorkerProgressCallbackRequest
from backend.app.schemas.job import CreateAnalysisJobRequest, JobStatus
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.modes import ApplicationMode
from backend.app.schemas.result import AnalysisResult
from backend.app.schemas.identity import IdentityEvaluation
from backend.app.schemas.manifest import JobExecutionManifest, MediaProbedMetadata, ManifestMethodologyProvenance
from backend.app.services.job_repository import InMemoryJobRepository, SupabaseAnalysisJobRepository
from backend.app.services.modal_client import ProductionModalClient


def test_production_dispatch_selects_real_worker(monkeypatch):
    import modal

    selected = []
    submitted = []

    class FakeFunction:
        def spawn(self, payload):
            submitted.append(payload)
            return SimpleNamespace(object_id="fc-real-call")

    def from_name(app_name, function_name):
        selected.append((app_name, function_name))
        return FakeFunction()

    monkeypatch.setenv("MODAL_TOKEN_ID", "test-token-id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "test-token-secret")
    monkeypatch.setattr(modal.Function, "from_name", from_name)
    request = WorkerDispatchRequest(
        job_id="job", session_id="session", methodology_id=MethodologyId.METHOD_2_RFDETR_GTATRACK,
        dispatch_id="dispatch", video_storage_bucket="analysis-inputs",
        video_storage_path="sessions/session/video.mp4",
        callback_url="https://callback.example/api/v1/internal/jobs/job/progress",
        audio_source_offset_s=167.0, video_source_offset_s=167.0,
        start_frame=400, max_frames=4,
    )
    assert ProductionModalClient().submit_job(request) == "fc-real-call"
    assert selected == [("football-tactical-analysis", "execute_analysis_worker")]
    assert submitted[0]["video_source_offset_s"] == 167.0
    assert submitted[0]["audio_source_offset_s"] == 167.0
    assert "dispatch_placeholder" not in str(selected)


def test_worker_callback_contract_is_exact():
    payload = WorkerProgressCallbackRequest(
        job_id="job", dispatch_id="dispatch", dispatch_state="SUCCEEDED",
        current_stage="UPLOADING_RESULTS", progress_percent=100.0,
        job_status="COMPLETED_WITH_LIMITATIONS",
    ).model_dump(mode="json")
    assert payload["dispatch_state"] == "SUCCEEDED"
    assert payload["job_status"] == "COMPLETED_WITH_LIMITATIONS"
    assert set(payload) == set(WorkerProgressCallbackRequest.model_fields)


def test_auto_is_resolved_before_job_persistence():
    repo = InMemoryJobRepository()
    job = asyncio.run(repo.create_job(CreateAnalysisJobRequest(session_id="session", methodology_id="AUTO")))
    assert job.methodology_id == MethodologyId.METHOD_2_RFDETR_GTATRACK


def test_m2_runner_has_no_research_runtime_drive_dependency():
    root = Path(__file__).resolve().parents[1] / "app/runners/m2_runner.py"
    source = root.read_text(encoding="utf-8")
    assert "G:\\" not in source and "D:\\" not in source
    assert "M2_MODEL_ROOT" in source and '"models/m2"' in source
    assert 'vendored = Path(__file__).resolve().parent / "vendor" / "m2"' in source


def test_checkpoint_verifier_fails_closed(tmp_path, monkeypatch):
    from modal_app import worker

    monkeypatch.setattr(worker, "CHECKPOINTS", {"model.bin": (3, "wrong-hash")})
    (tmp_path / "model.bin").write_bytes(b"abc")
    with pytest.raises(RuntimeError, match="M2_CHECKPOINT_HASH_MISMATCH"):
        worker.verify_m2_checkpoints(tmp_path)


class FakeBucket:
    def __init__(self):
        self.files = {}

    def upload(self, path, file, file_options):
        if path in self.files:
            raise RuntimeError("already exists")
        self.files[path] = file

    def download(self, path):
        return self.files[path]

    def list(self, folder, options):
        prefix = folder + "/"
        return [{"name": key[len(prefix):]} for key in self.files if key.startswith(prefix)]


def test_supabase_storage_result_roundtrip_and_immutable_retry():
    bucket = FakeBucket()
    client = SimpleNamespace(storage=SimpleNamespace(from_=lambda name: bucket))
    repo = SupabaseAnalysisJobRepository(client)
    result = AnalysisResult(
        id="result", session_id="session", job_id="job",
        methodology_id=MethodologyId.METHOD_2_RFDETR_GTATRACK,
        application_mode=ApplicationMode.ANALYSIS_WITHOUT_METRICS,
        job_status=JobStatus.COMPLETED_WITH_LIMITATIONS,
        identity_evaluation=IdentityEvaluation(raw_track_ids=4, meaningful_identities=4, fragmentation_ratio=1.0),
        report_markdown="Withheld player level analysis.", structured_evidence={"evidence_items": []},
        execution_manifest=JobExecutionManifest(
            job_id="job", session_id="session",
            media_metadata=MediaProbedMetadata(duration_s=12.0, fps=60.0, resolution_width=1920,
                                               resolution_height=1080, container_format="mp4"),
            methodology=ManifestMethodologyProvenance(requested_methodology="AUTO",
                                                      resolved_methodology="METHOD_2_RFDETR_GTATRACK"),
        ),
    )
    asyncio.run(repo.store_result(result))
    assert asyncio.run(SupabaseAnalysisJobRepository(client).get_result("job")) == result
    asyncio.run(repo.store_result(result))
    altered = result.model_copy(update={"report_markdown": "Different report"})
    with pytest.raises(Exception):
        asyncio.run(repo.store_result(altered))
