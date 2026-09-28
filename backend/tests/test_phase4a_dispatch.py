"""
Phase 4A Tests: Worker Dispatch Backbone, Idempotency & Methodology Readiness Gates.
CRITICAL: Uses in-memory fakes; strictly NO external Modal network calls.
"""
import uuid
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.job import JobStatus, AnalysisJob, CreateAnalysisJobRequest
from backend.app.schemas.stages import AnalysisStage
from backend.app.schemas.confidence import IdentityStatus
from backend.app.schemas.modes import ApplicationMode, CalibrationMode, AudioMode
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.session import Session
from backend.app.schemas.media import MediaAsset, MediaType, UploadStatus
from backend.app.schemas.dispatch import (
    WorkerDispatchState,
    WorkerDispatchRequest,
    WorkerDispatch,
    WorkerDispatchResponse,
)
from backend.app.services.dispatch_repository import (
    InMemoryWorkerDispatchRepository,
    ACTIVE_DISPATCH_STATES,
)
from backend.app.services.modal_client import (
    InMemoryModalClient,
    ModalAuthenticationError,
    ModalSubmissionError,
)
from backend.app.pipeline.registry import (
    MethodologyExecutorRegistry,
    MethodologyExecutor,
    ExecutionReadinessStatus,
)
from backend.app.services.dispatch_service import (
    AnalysisDispatchService,
    JobNotFoundError,
    JobStatusConflictError,
    RequiredMediaMissingError,
    MethodologyNotReadyError,
    DispatchSubmissionFailedError,
)
from backend.app.api.deps import (
    get_dispatch_service,
    _in_memory_jobs,
    _in_memory_sessions,
    _in_memory_media,
    _in_memory_storage,
    _in_memory_dispatch,
    _in_memory_modal,
)

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_dispatch_contracts():
    """Verify dispatch contract models and state enums."""
    states = [s.value for s in WorkerDispatchState]
    assert states == ["CREATED", "SUBMITTED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"]

    req = WorkerDispatchRequest(
        job_id="test_job_1",
        session_id="test_sess_1",
        methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
    )
    assert req.job_id == "test_job_1"

    res = WorkerDispatchResponse(
        dispatch_id="disp_1",
        job_id="test_job_1",
        provider="MODAL",
        provider_execution_id="exec_123",
        state=WorkerDispatchState.SUBMITTED,
        created_at=datetime.utcnow(),
    )
    assert res.state == WorkerDispatchState.SUBMITTED


def test_dispatch_repository_crud():
    """Verify WorkerDispatchRepository in-memory CRUD operations."""
    repo = InMemoryWorkerDispatchRepository()
    dispatch = WorkerDispatch(
        id="disp_100",
        job_id="job_100",
        provider="MODAL",
        state=WorkerDispatchState.CREATED,
        created_at=datetime.utcnow(),
    )
    created = repo.create_dispatch(dispatch)
    assert created.id == "disp_100"

    fetched = repo.get_dispatch("disp_100")
    assert fetched is not None
    assert fetched.state == WorkerDispatchState.CREATED

    # Active lookup
    active = repo.get_active_dispatch_for_job("job_100")
    assert active is not None
    assert active.id == "disp_100"

    # Update to terminal state
    dispatch.state = WorkerDispatchState.SUCCEEDED
    repo.update_dispatch(dispatch)

    active_after = repo.get_active_dispatch_for_job("job_100")
    assert active_after is None

    history = repo.list_dispatches_for_job("job_100")
    assert len(history) == 1


@pytest.mark.anyio
async def test_dispatch_unknown_job():
    """Dispatching a non-existent job must raise JobNotFoundError (404)."""
    service = AnalysisDispatchService(
        job_repo=_in_memory_jobs,
        session_repo=_in_memory_sessions,
        media_repo=_in_memory_media,
        dispatch_repo=_in_memory_dispatch,
        modal_client=_in_memory_modal,
    )
    with pytest.raises(JobNotFoundError):
        await service.dispatch_job("non_existent_job_id")


@pytest.mark.anyio
async def test_dispatch_non_queued_job():
    """Dispatching a job not in QUEUED status must raise JobStatusConflictError (409)."""
    job = await _in_memory_jobs.create_job(
        CreateAnalysisJobRequest(
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            session_id="sess_1",
        )
    )
    job.status = JobStatus.PROCESSING
    _in_memory_jobs._jobs[job.id] = job

    service = AnalysisDispatchService(
        job_repo=_in_memory_jobs,
        session_repo=_in_memory_sessions,
        media_repo=_in_memory_media,
        dispatch_repo=_in_memory_dispatch,
        modal_client=_in_memory_modal,
    )
    with pytest.raises(JobStatusConflictError):
        await service.dispatch_job(job.id)


@pytest.mark.anyio
async def test_dispatch_missing_media():
    """Dispatching a job without confirmed video must raise RequiredMediaMissingError (422)."""
    sess = _in_memory_sessions.create_session(
        Session(id="sess_no_media", title="Test Session")
    )
    job = await _in_memory_jobs.create_job(
        CreateAnalysisJobRequest(
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            session_id=sess.id,
        )
    )
    service = AnalysisDispatchService(
        job_repo=_in_memory_jobs,
        session_repo=_in_memory_sessions,
        media_repo=_in_memory_media,
        dispatch_repo=_in_memory_dispatch,
        modal_client=_in_memory_modal,
    )
    with pytest.raises(RequiredMediaMissingError):
        await service.dispatch_job(job.id)


@pytest.mark.anyio
async def test_dispatch_methodology_not_ready():
    """
    CRITICAL SCIENTIFIC GATE:
    All 3 methodologies must raise MethodologyNotReadyError (409)
    because production executors are not yet installed.
    """
    service = AnalysisDispatchService(
        job_repo=_in_memory_jobs,
        session_repo=_in_memory_sessions,
        media_repo=_in_memory_media,
        dispatch_repo=_in_memory_dispatch,
        modal_client=_in_memory_modal,
        executor_registry=MethodologyExecutorRegistry(),
    )

    for method in [
        MethodologyId.METHOD_1_YOLO11_BOTSORT,
        MethodologyId.METHOD_2_RFDETR_GTATRACK,
        MethodologyId.METHOD_3_YOLO26_SRITRACK,
    ]:
        sess = _in_memory_sessions.create_session(Session(id=f"sess_{method.value}", title="Test"))
        # Add confirmed media
        _in_memory_media.create_media_asset(
            MediaAsset(
                id=f"vid_{method.value}",
                session_id=sess.id,
                media_type=MediaType.VIDEO,
                storage_bucket="analysis-inputs",
                storage_path="path/vid.mp4",
                original_filename="vid.mp4",
                mime_type="video/mp4",
                size_bytes=1000,
                upload_status=UploadStatus.VALIDATED,
            )
        )
        job = await _in_memory_jobs.create_job(
            CreateAnalysisJobRequest(
                methodology_id=method,
                session_id=sess.id,
            )
        )
        with pytest.raises(MethodologyNotReadyError) as exc_info:
            await service.dispatch_job(job.id)
        assert exc_info.value.code == "METHODOLOGY_EXECUTOR_NOT_READY"


@pytest.mark.anyio
async def test_dispatch_idempotency():
    """
    If an active dispatch already exists for a QUEUED job,
    dispatch_job must return the existing dispatch without creating another worker.
    """
    sess = _in_memory_sessions.create_session(Session(id="sess_idem", title="Test"))
    _in_memory_media.create_media_asset(
        MediaAsset(
            id="vid_idem",
            session_id=sess.id,
            media_type=MediaType.VIDEO,
            storage_bucket="analysis-inputs",
            storage_path="path/vid.mp4",
            original_filename="vid.mp4",
            mime_type="video/mp4",
            size_bytes=1000,
            upload_status=UploadStatus.VALIDATED,
        )
    )
    job = await _in_memory_jobs.create_job(
        CreateAnalysisJobRequest(
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            session_id=sess.id,
        )
    )

    # Pre-seed an active dispatch
    existing_dispatch = WorkerDispatch(
        id="disp_existing_123",
        job_id=job.id,
        provider="MODAL",
        provider_execution_id="call_mock_active",
        state=WorkerDispatchState.SUBMITTED,
        created_at=datetime.utcnow(),
    )
    _in_memory_dispatch.create_dispatch(existing_dispatch)

    service = AnalysisDispatchService(
        job_repo=_in_memory_jobs,
        session_repo=_in_memory_sessions,
        media_repo=_in_memory_media,
        dispatch_repo=_in_memory_dispatch,
        modal_client=_in_memory_modal,
    )

    dispatch, was_idempotent = await service.dispatch_job(job.id)
    assert was_idempotent is True
    assert dispatch.id == "disp_existing_123"
    assert dispatch.state == WorkerDispatchState.SUBMITTED


@pytest.mark.anyio
async def test_dispatch_provider_failure_normalization():
    """
    When modal client fails during submission,
    the dispatch record transitions to FAILED and DispatchSubmissionFailedError is raised.
    """
    custom_registry = MethodologyExecutorRegistry()

    class FakeReadyExecutor(MethodologyExecutor):
        @property
        def methodology_id(self):
            return MethodologyId.METHOD_1_YOLO11_BOTSORT
        def execute(self, payload):
            return {}

    custom_registry.register_executor(FakeReadyExecutor())

    sess = _in_memory_sessions.create_session(Session(id="sess_fail", title="Test"))
    _in_memory_media.create_media_asset(
        MediaAsset(
            id="vid_fail",
            session_id=sess.id,
            media_type=MediaType.VIDEO,
            storage_bucket="analysis-inputs",
            storage_path="path/vid.mp4",
            original_filename="vid.mp4",
            mime_type="video/mp4",
            size_bytes=1000,
            upload_status=UploadStatus.VALIDATED,
        )
    )
    job = await _in_memory_jobs.create_job(
        CreateAnalysisJobRequest(
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            session_id=sess.id,
        )
    )

    failing_modal = InMemoryModalClient(configured=True, force_failure=True)
    service = AnalysisDispatchService(
        job_repo=_in_memory_jobs,
        session_repo=_in_memory_sessions,
        media_repo=_in_memory_media,
        dispatch_repo=_in_memory_dispatch,
        modal_client=failing_modal,
        executor_registry=custom_registry,
    )

    with pytest.raises(DispatchSubmissionFailedError):
        await service.dispatch_job(job.id)

    # Check that dispatch was marked FAILED
    dispatches = _in_memory_dispatch.list_dispatches_for_job(job.id)
    assert len(dispatches) == 1
    assert dispatches[0].state == WorkerDispatchState.FAILED
    assert dispatches[0].error_code == "MODAL_SUBMISSION_FAILED"


def test_job_status_five_values():
    """Strictly assert the 5 canonical JobStatus values."""
    expected = {"QUEUED", "PROCESSING", "COMPLETED", "COMPLETED_WITH_LIMITATIONS", "FAILED"}
    actual = {s.value for s in JobStatus}
    assert actual == expected


def test_analysis_stage_sixteen_values():
    """Strictly assert the 16 canonical AnalysisStage values."""
    expected = {
        "UPLOADED", "VALIDATING", "PREPROCESSING", "DETECTING", "TRACKING",
        "IDENTITY_EVALUATION", "CALIBRATING", "KINEMATICS", "AUDIO_EXTRACTION",
        "TRANSCRIBING", "INSTRUCTION_PARSING", "FUSION", "GENERATING_EVIDENCE",
        "GENERATING_REPORT", "RENDERING", "UPLOADING_RESULTS"
    }
    actual = {s.value for s in AnalysisStage}
    assert actual == expected


def test_identity_status_seven_values():
    """Strictly assert the 7 canonical IdentityStatus values."""
    expected = {
        "NOT_EVALUATED",
        "EVALUATING",
        "PASS_RELIABLE",
        "FAIL_HIGH_FRAGMENTATION",
        "FAIL_IDENTITY_CONFLICT",
        "FAIL_UNSAFE_MERGE",
        "FAIL_INVALID_OUTPUT",
    }
    actual = {s.value for s in IdentityStatus}
    assert actual == expected


def test_api_dispatch_endpoint_unknown_job():
    """API endpoint returns 404 for unknown job."""
    res = client.post("/api/v1/analysis/jobs/non_existent_123/dispatch")
    assert res.status_code == 404
    body = res.json()
    assert body["code"] == "JOB_NOT_FOUND"


def test_api_dispatch_endpoint_methodology_not_ready():
    """API endpoint returns 409 METHODOLOGY_EXECUTOR_NOT_READY for unvalidated methods."""
    app.dependency_overrides[get_dispatch_service] = lambda: AnalysisDispatchService(
        job_repo=_in_memory_jobs, session_repo=_in_memory_sessions,
        media_repo=_in_memory_media, dispatch_repo=_in_memory_dispatch,
        modal_client=_in_memory_modal, executor_registry=MethodologyExecutorRegistry(),
    )
    sess_res = client.post("/api/v1/sessions", json={"title": "Test Session"})
    sess_id = sess_res.json()["id"]

    # Register media intent
    upload_res = client.post(
        f"/api/v1/sessions/{sess_id}/media/upload-intent",
        json={"media_type": "VIDEO", "filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 1000},
    )
    assert upload_res.status_code == 201
    media_id = upload_res.json()["media_id"]
    storage_path = upload_res.json()["storage_path"]
    bucket = upload_res.json()["storage_bucket"]

    # Simulate storage upload and complete
    _in_memory_storage.simulate_upload(bucket, storage_path, 1000)
    complete_res = client.post(
        f"/api/v1/sessions/{sess_id}/media/{media_id}/complete",
        json={"size_bytes": 1000},
    )
    assert complete_res.status_code == 200

    # Create job
    job_res = client.post(
        "/api/v1/analysis/jobs",
        json={
            "methodology_id": "METHOD_1_YOLO11_BOTSORT",
            "session_id": sess_id,
        },
    )
    job_id = job_res.json()["id"]

    # Dispatch
    disp_res = client.post(f"/api/v1/analysis/jobs/{job_id}/dispatch")
    app.dependency_overrides.pop(get_dispatch_service, None)
    assert disp_res.status_code == 409
    body = disp_res.json()
    assert body["code"] == "METHODOLOGY_EXECUTOR_NOT_READY"


def test_api_dispatch_endpoint_idempotency():
    """API endpoint returns 200 with existing dispatch when active dispatch exists."""
    sess_res = client.post("/api/v1/sessions", json={"title": "Idempotency Session"})
    sess_id = sess_res.json()["id"]

    upload_res = client.post(
        f"/api/v1/sessions/{sess_id}/media/upload-intent",
        json={"media_type": "VIDEO", "filename": "test.mp4", "mime_type": "video/mp4", "size_bytes": 1000},
    )
    assert upload_res.status_code == 201
    media_id = upload_res.json()["media_id"]
    storage_path = upload_res.json()["storage_path"]
    bucket = upload_res.json()["storage_bucket"]

    _in_memory_storage.simulate_upload(bucket, storage_path, 1000)
    complete_res = client.post(
        f"/api/v1/sessions/{sess_id}/media/{media_id}/complete",
        json={"size_bytes": 1000},
    )
    assert complete_res.status_code == 200

    job_res = client.post(
        "/api/v1/analysis/jobs",
        json={
            "methodology_id": "METHOD_1_YOLO11_BOTSORT",
            "session_id": sess_id,
        },
    )
    job_id = job_res.json()["id"]

    # Pre-seed active dispatch
    _in_memory_dispatch.create_dispatch(
        WorkerDispatch(
            id="disp_preseeded_999",
            job_id=job_id,
            provider="MODAL",
            provider_execution_id="call_mock_123",
            state=WorkerDispatchState.SUBMITTED,
            created_at=datetime.utcnow(),
        )
    )

    # Calling dispatch should hit idempotency branch
    disp_res = client.post(f"/api/v1/analysis/jobs/{job_id}/dispatch")
    assert disp_res.status_code == 200
    body = disp_res.json()
    assert body["dispatch_id"] == "disp_preseeded_999"
    assert body["state"] == "SUBMITTED"
    assert "already exists" in body["message"]
