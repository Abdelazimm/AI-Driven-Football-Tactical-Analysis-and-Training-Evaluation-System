"""
Pre-Phase-4B Hardening Pack 1 Tests:
Job Lifecycle + Worker Callback + Atomic Dispatch Idempotency

Tests covering:
- C1: AnalysisJob lifecycle persistence, transitions, terminal immutability
- C2: Atomic dispatch idempotency under genuine concurrency (simulated concurrent requests)
- D2: Authenticated worker callback, ownership validation, terminal safety, and replay safety
- Methodology readiness gates verification (M1, M2, M3 remain closed)
"""
import asyncio
import uuid
from types import SimpleNamespace
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.job import JobStatus, AnalysisJob, CreateAnalysisJobRequest
from backend.app.schemas.stages import AnalysisStage
from backend.app.schemas.modes import ApplicationMode, CalibrationMode, AudioMode
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.session import Session
from backend.app.schemas.media import MediaAsset, MediaType, UploadStatus
from backend.app.schemas.dispatch import (
    WorkerDispatchState,
    WorkerDispatchRequest,
    WorkerDispatch,
    WorkerProgressCallbackRequest,
)
from backend.app.services.job_repository import (
    InMemoryJobRepository,
    InMemoryAnalysisJobRepository,
    InvalidJobTransitionError,
    TERMINAL_JOB_STATUSES,
)
from backend.app.services.dispatch_repository import (
    InMemoryWorkerDispatchRepository,
    ActiveDispatchConflictError,
    ACTIVE_DISPATCH_STATES,
)
from backend.app.services.modal_client import (
    InMemoryModalClient,
    ModalSubmissionError,
)
from backend.app.pipeline.registry import (
    MethodologyExecutorRegistry,
    MethodologyExecutor,
    ExecutionReadinessStatus,
    default_executor_registry,
)
from backend.app.services.dispatch_service import (
    AnalysisDispatchService,
    JobNotFoundError,
    JobStatusConflictError,
    RequiredMediaMissingError,
    MethodologyNotReadyError,
    DispatchSubmissionFailedError,
    CallbackOwnershipMismatchError,
    DispatchNotFoundError,
)
from backend.app.api.deps import (
    get_job_repository,
    get_session_repository,
    get_media_repository,
    get_dispatch_repository,
    get_dispatch_service,
    set_override_job_repository,
    set_override_session_repository,
    set_override_media_repository,
    set_override_dispatch_repository,
    set_override_modal_client,
    set_override_worker_secret,
)

client = TestClient(app)

TEST_WORKER_SECRET = "test-hardening-pack-1-secret-secure-token"


@pytest.fixture
def anyio_backend():
    return "asyncio"


class CountingModalClient(InMemoryModalClient):
    """Modal client spy that tracks invocation counts and optionally introduces latency."""

    def __init__(self, delay_seconds: float = 0.0):
        super().__init__()
        self.call_count = 0
        self.delay_seconds = delay_seconds

    def submit_job(self, request: WorkerDispatchRequest) -> str:
        self.call_count += 1
        return super().submit_job(request)


class MockMethodologyExecutor(MethodologyExecutor):
    def __init__(self, methodology_id: MethodologyId = MethodologyId.METHOD_1_YOLO11_BOTSORT):
        self._methodology_id = methodology_id

    @property
    def methodology_id(self) -> MethodologyId:
        return self._methodology_id

    def execute(self, payload: dict) -> dict:
        return {"status": "ok"}


# ==============================================================================
# 1. ATOMIC DISPATCH CONCURRENCY TESTS (C2)
# ==============================================================================

@pytest.mark.anyio
async def test_genuine_concurrent_dispatch_atomic_invariant():
    """
    Simulate two concurrent dispatch requests for the exact same job.
    Verifies:
    1. Exactly one provider submission occurs
    2. Exactly one active dispatch record exists
    3. Both concurrent callers resolve safely without 500 error
    4. One caller is the primary dispatcher, the other receives the idempotent replay
    5. No duplicate dispatch record survives
    """
    job_repo = InMemoryJobRepository()
    dispatch_repo = InMemoryWorkerDispatchRepository()
    session_repo = get_session_repository()
    media_repo = get_media_repository()

    # Pre-seed session & confirmed media
    sess_id = f"sess_concurrent_{uuid.uuid4().hex[:8]}"
    session = Session(
        id=sess_id,
        title="Concurrent Dispatch Test Session",
        user_id="coach_1",
        created_at=datetime.utcnow(),
    )
    session_repo.create_session(session)

    media = MediaAsset(
        id=f"med_vid_{uuid.uuid4().hex[:8]}",
        session_id=sess_id,
        media_type=MediaType.VIDEO,
        storage_bucket="analysis-inputs",
        storage_path="analysis-inputs/test.mp4",
        original_filename="test.mp4",
        mime_type="video/mp4",
        size_bytes=1000,
        upload_status=UploadStatus.VALIDATED,
        created_at=datetime.utcnow(),
    )
    media_repo.create_media_asset(media)

    # Pre-seed queued job
    job = await job_repo.create_job(
        CreateAnalysisJobRequest(
            session_id=sess_id,
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )

    # Temporary test registry allowing execution for this test only
    test_registry = MethodologyExecutorRegistry()
    test_registry.register_executor(MockMethodologyExecutor(MethodologyId.METHOD_1_YOLO11_BOTSORT))


    counting_modal = CountingModalClient()

    service = AnalysisDispatchService(
        job_repo=job_repo,
        session_repo=session_repo,
        media_repo=media_repo,
        dispatch_repo=dispatch_repo,
        modal_client=counting_modal,
        executor_registry=test_registry,
    )

    # Launch two concurrent dispatch calls
    result_a, result_b = await asyncio.gather(
        service.dispatch_job(job.id),
        service.dispatch_job(job.id),
    )

    dispatch_a, was_replay_a = result_a
    dispatch_b, was_replay_b = result_b

    # Both callers must receive a valid dispatch pointing to the same dispatch ID
    assert dispatch_a.id == dispatch_b.id
    assert dispatch_a.job_id == job.id

    # Exactly one was primary, exactly one was replay
    assert (was_replay_a, was_replay_b) in [(False, True), (True, False)]

    # Exactly one Modal submission was performed
    assert counting_modal.call_count == 1

    # Exactly one dispatch record exists in repository
    all_dispatches = dispatch_repo.list_dispatches_for_job(job.id)
    assert len(all_dispatches) == 1
    assert all_dispatches[0].state == WorkerDispatchState.SUBMITTED

    # Analysis job transitioned from QUEUED to PROCESSING / VALIDATING
    updated_job = await job_repo.get_job(job.id)
    assert updated_job.status == JobStatus.PROCESSING
    assert updated_job.current_stage == AnalysisStage.VALIDATING
    assert updated_job.progress_percent == 5.0


def test_repository_active_dispatch_uniqueness_conflict():
    """
    Directly verify that InMemoryWorkerDispatchRepository raises
    ActiveDispatchConflictError if a second active dispatch is inserted.
    """
    repo = InMemoryWorkerDispatchRepository()
    d1 = WorkerDispatch(
        id="d1",
        job_id="job_uniq_1",
        state=WorkerDispatchState.CREATED,
        created_at=datetime.utcnow(),
    )
    repo.create_dispatch(d1)

    # Attempting to insert another active dispatch for the same job must raise
    d2 = WorkerDispatch(
        id="d2",
        job_id="job_uniq_1",
        state=WorkerDispatchState.SUBMITTED,
        created_at=datetime.utcnow(),
    )
    with pytest.raises(ActiveDispatchConflictError):
        repo.create_dispatch(d2)

    # Updating d1 to SUCCEEDED frees the active slot
    d1.state = WorkerDispatchState.SUCCEEDED
    repo.update_dispatch(d1)

    # Now a second dispatch can be created since no active dispatch remains
    d3 = WorkerDispatch(
        id="d3",
        job_id="job_uniq_1",
        state=WorkerDispatchState.CREATED,
        created_at=datetime.utcnow(),
    )
    created_d3 = repo.create_dispatch(d3)
    assert created_d3.id == "d3"


# ==============================================================================
# 2. JOB LIFECYCLE REPOSITORY & STATE TRANSITION TESTS (C1)
# ==============================================================================

@pytest.mark.anyio
async def test_job_lifecycle_transitions():
    """
    Verify complete happy-path lifecycle progression:
    QUEUED -> PROCESSING -> stage progress updates -> COMPLETED
    """
    repo = InMemoryJobRepository()
    job = await repo.create_job(
        CreateAnalysisJobRequest(
            session_id="sess_life_1",
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )
    assert job.status == JobStatus.QUEUED
    assert job.current_stage == AnalysisStage.UPLOADED
    assert job.progress_percent == 0.0

    # 1. QUEUED -> PROCESSING / VALIDATING
    job_proc = await repo.update_job_lifecycle(
        job.id,
        status=JobStatus.PROCESSING,
        current_stage=AnalysisStage.VALIDATING,
        progress_percent=5.0,
        stage_message="Validating input video",
        modal_call_id="call_modal_123",
    )
    assert job_proc.status == JobStatus.PROCESSING
    assert job_proc.current_stage == AnalysisStage.VALIDATING
    assert job_proc.progress_percent == 5.0
    assert job_proc.modal_call_id == "call_modal_123"

    # 2. Stage progress updates within PROCESSING
    job_track = await repo.update_job_lifecycle(
        job.id,
        current_stage=AnalysisStage.TRACKING,
        progress_percent=45.0,
        stage_message="Tracking player trajectories",
    )
    assert job_track.status == JobStatus.PROCESSING
    assert job_track.current_stage == AnalysisStage.TRACKING
    assert job_track.progress_percent == 45.0

    # 3. PROCESSING -> COMPLETED
    job_done = await repo.update_job_lifecycle(
        job.id,
        status=JobStatus.COMPLETED,
        current_stage=AnalysisStage.UPLOADING_RESULTS,
        progress_percent=100.0,
        stage_message="Analysis completed",
    )
    assert job_done.status == JobStatus.COMPLETED
    assert job_done.current_stage == AnalysisStage.UPLOADING_RESULTS
    assert job_done.progress_percent == 100.0
    assert job_done.completed_at is not None


@pytest.mark.anyio
async def test_completed_with_limitations_contract_support():
    """
    Verify contract support for COMPLETED_WITH_LIMITATIONS
    WITHOUT implementing scientific decision logic.
    """
    repo = InMemoryJobRepository()
    job = await repo.create_job(
        CreateAnalysisJobRequest(
            session_id="sess_lim_1",
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )
    await repo.update_job_lifecycle(job.id, status=JobStatus.PROCESSING)

    job_lim = await repo.update_job_lifecycle(
        job.id,
        status=JobStatus.COMPLETED_WITH_LIMITATIONS,
        current_stage=AnalysisStage.GENERATING_REPORT,
        progress_percent=95.0,
        stage_message="Completed with limitations: player-level metrics withheld",
    )
    assert job_lim.status == JobStatus.COMPLETED_WITH_LIMITATIONS
    assert job_lim.completed_at is not None


@pytest.mark.anyio
async def test_terminal_state_cannot_be_reopened():
    """
    Verify terminal JobStatus values (COMPLETED, COMPLETED_WITH_LIMITATIONS, FAILED)
    cannot transition back to PROCESSING or QUEUED.
    """
    repo = InMemoryJobRepository()

    for terminal_status in [JobStatus.COMPLETED, JobStatus.COMPLETED_WITH_LIMITATIONS, JobStatus.FAILED]:
        job = await repo.create_job(
            CreateAnalysisJobRequest(
                session_id=f"sess_term_{terminal_status.value}",
                methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
                calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
            )
        )
        await repo.update_job_lifecycle(job.id, status=JobStatus.PROCESSING)
        await repo.update_job_lifecycle(job.id, status=terminal_status)

        # Illegal attempt to reopen terminal status
        with pytest.raises(InvalidJobTransitionError):
            await repo.update_job_lifecycle(job.id, status=JobStatus.PROCESSING)

        with pytest.raises(InvalidJobTransitionError):
            await repo.update_job_lifecycle(job.id, status=JobStatus.QUEUED)

        # Illegal attempt to overwrite progress of terminal job
        with pytest.raises(InvalidJobTransitionError):
            await repo.update_job_lifecycle(job.id, progress_percent=50.0)


@pytest.mark.anyio
async def test_failed_stage_preserves_last_reached_stage():
    """
    Verify that early failure in pipeline preserves:
    status = FAILED
    current_stage = last reached processing stage
    """
    repo = InMemoryJobRepository()
    job = await repo.create_job(
        CreateAnalysisJobRequest(
            session_id="sess_fail_1",
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )
    await repo.update_job_lifecycle(
        job.id,
        status=JobStatus.PROCESSING,
        current_stage=AnalysisStage.TRACKING,
        progress_percent=40.0,
    )

    # Fail during tracking
    failed_job = await repo.update_job_lifecycle(
        job.id,
        status=JobStatus.FAILED,
        current_stage=AnalysisStage.TRACKING,
        progress_percent=40.0,
        error_code="TRACKING_LOST",
        error_details="Target occlusion exceeded recovery window",
    )
    assert failed_job.status == JobStatus.FAILED
    assert failed_job.current_stage == AnalysisStage.TRACKING
    assert failed_job.error_code == "TRACKING_LOST"
    assert failed_job.error_details == "Target occlusion exceeded recovery window"
    assert failed_job.completed_at is not None


@pytest.mark.anyio
async def test_submission_failure_clears_active_dispatch():
    """
    Verify that Modal submission failure marks dispatch as FAILED (not active)
    and transitions AnalysisJob to FAILED without leaving a stuck CREATED/SUBMITTED dispatch.
    """
    job_repo = InMemoryJobRepository()
    dispatch_repo = InMemoryWorkerDispatchRepository()
    session_repo = get_session_repository()
    media_repo = get_media_repository()

    sess_id = f"sess_sub_fail_{uuid.uuid4().hex[:8]}"
    session_repo.create_session(
        Session(id=sess_id, title="Sub Fail Test", user_id="coach_1", created_at=datetime.utcnow())
    )
    media_repo.create_media_asset(
        MediaAsset(
            id=f"med_{uuid.uuid4().hex[:8]}",
            session_id=sess_id,
            media_type=MediaType.VIDEO,
            storage_bucket="analysis-inputs",
            storage_path="analysis-inputs/test.mp4",
            original_filename="test.mp4",
            mime_type="video/mp4",
            size_bytes=1000,
            upload_status=UploadStatus.VALIDATED,
            created_at=datetime.utcnow(),
        )
    )

    job = await job_repo.create_job(
        CreateAnalysisJobRequest(
            session_id=sess_id,
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )

    # Mock Modal client that throws ModalSubmissionError
    class FailingModalClient(InMemoryModalClient):
        def submit_job(self, request: WorkerDispatchRequest) -> str:
            raise ModalSubmissionError("Provider capacity exceeded", code="MODAL_RATE_LIMIT")

    test_registry = MethodologyExecutorRegistry()
    test_registry.register_executor(MockMethodologyExecutor(MethodologyId.METHOD_1_YOLO11_BOTSORT))

    service = AnalysisDispatchService(
        job_repo=job_repo,
        session_repo=session_repo,
        media_repo=media_repo,
        dispatch_repo=dispatch_repo,
        modal_client=FailingModalClient(),
        executor_registry=test_registry,
    )

    with pytest.raises(DispatchSubmissionFailedError) as exc_info:
        await service.dispatch_job(job.id)
    assert exc_info.value.code == "MODAL_RATE_LIMIT"

    # Verify no active dispatch remains
    active = dispatch_repo.get_active_dispatch_for_job(job.id)
    assert active is None

    # Verify dispatch record is FAILED
    all_dispatches = dispatch_repo.list_dispatches_for_job(job.id)
    assert len(all_dispatches) == 1
    assert all_dispatches[0].state == WorkerDispatchState.FAILED
    assert all_dispatches[0].error_code == "MODAL_RATE_LIMIT"

    # Verify job is FAILED with diagnostics
    failed_job = await job_repo.get_job(job.id)
    assert failed_job.status == JobStatus.FAILED
    assert failed_job.error_code == "MODAL_RATE_LIMIT"
    assert "Provider capacity exceeded" in failed_job.error_details


# ==============================================================================
# 3. WORKER CALLBACK CONTRACT & SECURITY TESTS (D2)
# ==============================================================================

@pytest.fixture(autouse=True)
def setup_test_overrides():
    """Setup test isolated repositories and secret."""
    test_jobs = InMemoryJobRepository()
    test_dispatches = InMemoryWorkerDispatchRepository()
    set_override_job_repository(test_jobs)
    set_override_dispatch_repository(test_dispatches)
    set_override_worker_secret(TEST_WORKER_SECRET)
    yield
    set_override_job_repository(None)
    set_override_dispatch_repository(None)
    set_override_worker_secret(None)


def test_callback_endpoint_auth_rejection():
    """Verify callback requires correct secret (constant-time verification)."""
    # 1. Missing secret
    res_no_auth = client.post("/api/v1/internal/jobs/job_123/progress", json={})
    assert res_no_auth.status_code == 401

    # 2. Wrong secret
    res_wrong = client.post(
        "/api/v1/internal/jobs/job_123/progress",
        headers={"X-Worker-Secret": "wrong-secret"},
        json={},
    )
    assert res_wrong.status_code == 401


@pytest.mark.anyio
async def test_callback_ownership_validation():
    """Verify callback rejects mismatched job/dispatch combinations."""
    job_repo = get_job_repository()
    dispatch_repo = get_dispatch_repository()

    job1 = await job_repo.create_job(
        CreateAnalysisJobRequest(
            session_id="sess_cb_1",
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )
    job2 = await job_repo.create_job(
        CreateAnalysisJobRequest(
            session_id="sess_cb_2",
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )

    # Dispatch belonging to job1
    d1 = WorkerDispatch(
        id="disp_for_job1",
        job_id=job1.id,
        state=WorkerDispatchState.RUNNING,
        created_at=datetime.utcnow(),
    )
    dispatch_repo.create_dispatch(d1)

    # Callback targeting job2 with disp_for_job1 must be rejected
    payload = {
        "job_id": job2.id,
        "dispatch_id": d1.id,
        "dispatch_state": "RUNNING",
        "current_stage": "TRACKING",
        "progress_percent": 30.0,
        "stage_message": "Tracking",
    }
    res = client.post(
        f"/api/v1/internal/jobs/{job2.id}/progress",
        headers={"X-Worker-Secret": TEST_WORKER_SECRET},
        json=payload,
    )
    assert res.status_code == 400
    assert res.json()["code"] == "CALLBACK_OWNERSHIP_MISMATCH"


@pytest.mark.anyio
async def test_callback_progress_and_completion_flow():
    """Verify valid callback updates progress and terminates job cleanly."""
    job_repo = get_job_repository()
    dispatch_repo = get_dispatch_repository()

    job = await job_repo.create_job(
        CreateAnalysisJobRequest(
            session_id="sess_cb_flow",
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )
    await job_repo.update_job_lifecycle(job.id, status=JobStatus.PROCESSING)

    dispatch = WorkerDispatch(
        id="disp_flow_1",
        job_id=job.id,
        state=WorkerDispatchState.SUBMITTED,
        created_at=datetime.utcnow(),
    )
    dispatch_repo.create_dispatch(dispatch)

    # 1. Worker reports RUNNING at DETECTING stage
    payload_running = {
        "job_id": job.id,
        "dispatch_id": dispatch.id,
        "dispatch_state": "RUNNING",
        "current_stage": "DETECTING",
        "progress_percent": 25.0,
        "stage_message": "Running YOLO detector",
    }
    res_run = client.post(
        f"/api/v1/internal/jobs/{job.id}/progress",
        headers={"X-Worker-Secret": TEST_WORKER_SECRET},
        json=payload_running,
    )
    assert res_run.status_code == 200
    data_run = res_run.json()
    assert data_run["dispatch_state"] == "RUNNING"
    assert data_run["job_status"] == "PROCESSING"
    assert data_run["current_stage"] == "DETECTING"
    assert data_run["progress_percent"] == 25.0

    # 2. Worker reports SUCCEEDED at UPLOADING_RESULTS
    payload_success = {
        "job_id": job.id,
        "dispatch_id": dispatch.id,
        "dispatch_state": "SUCCEEDED",
        "job_status": "COMPLETED",
        "current_stage": "UPLOADING_RESULTS",
        "progress_percent": 100.0,
        "stage_message": "Worker execution finished cleanly",
    }
    # A completion callback must be rejected until the canonical result is stored.
    premature = client.post(
        f"/api/v1/internal/jobs/{job.id}/progress",
        headers={"Authorization": f"Bearer {TEST_WORKER_SECRET}"},
        json=payload_success,
    )
    assert premature.status_code == 409
    assert premature.json()["code"] == "RESULT_NOT_PERSISTED"
    job_repo.store_result_for_testing(
        job.id, SimpleNamespace(job_id=job.id, job_status=JobStatus.COMPLETED)
    )
    res_succ = client.post(
        f"/api/v1/internal/jobs/{job.id}/progress",
        headers={"Authorization": f"Bearer {TEST_WORKER_SECRET}"},
        json=payload_success,
    )
    assert res_succ.status_code == 200
    data_succ = res_succ.json()
    assert data_succ["dispatch_state"] == "SUCCEEDED"
    assert data_succ["job_status"] == "COMPLETED"
    assert data_succ["progress_percent"] == 100.0

    # Check durable state
    persisted_job = await job_repo.get_job(job.id)
    assert persisted_job.status == JobStatus.COMPLETED
    assert persisted_job.completed_at is not None


@pytest.mark.anyio
async def test_callback_replay_and_stale_callback_safety():
    """
    Verify replay/idempotency safety:
    1. Duplicate identical callback does not corrupt state.
    2. Stale RUNNING callback arriving after job is COMPLETED cannot reopen the job.
    """
    job_repo = get_job_repository()
    dispatch_repo = get_dispatch_repository()

    job = await job_repo.create_job(
        CreateAnalysisJobRequest(
            session_id="sess_replay",
            methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
            calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
        )
    )
    await job_repo.update_job_lifecycle(
        job.id,
        status=JobStatus.COMPLETED,
        current_stage=AnalysisStage.UPLOADING_RESULTS,
        progress_percent=100.0,
        stage_message="Job completed",
    )

    dispatch = WorkerDispatch(
        id="disp_replay_1",
        job_id=job.id,
        state=WorkerDispatchState.SUCCEEDED,
        created_at=datetime.utcnow(),
    )
    dispatch_repo.create_dispatch(dispatch)

    # Late/stale callback attempting to report RUNNING
    stale_payload = {
        "job_id": job.id,
        "dispatch_id": dispatch.id,
        "dispatch_state": "RUNNING",
        "current_stage": "DETECTING",
        "progress_percent": 30.0,
        "stage_message": "Late packet from network retry",
    }
    res = client.post(
        f"/api/v1/internal/jobs/{job.id}/progress",
        headers={"X-Worker-Secret": TEST_WORKER_SECRET},
        json=stale_payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["job_status"] == "COMPLETED"
    assert "terminal state" in data["message"]

    # Verify persisted job remains COMPLETED with 100% progress
    persisted_job = await job_repo.get_job(job.id)
    assert persisted_job.status == JobStatus.COMPLETED
    assert persisted_job.current_stage == AnalysisStage.UPLOADING_RESULTS
    assert persisted_job.progress_percent == 100.0


# ==============================================================================
# 4. METHODOLOGY GATE CLOSED INVARIANT
# ==============================================================================

def test_production_methodology_gates_remain_closed():
    """
    Verify all three production methodologies remain strictly NOT_READY_FOR_EXECUTION.
    No executors registered; public dispatch returns 409 METHODOLOGY_EXECUTOR_NOT_READY.
    """
    for method_id in [
        MethodologyId.METHOD_1_YOLO11_BOTSORT,
        MethodologyId.METHOD_2_RFDETR_GTATRACK,
        MethodologyId.METHOD_3_YOLO26_SRITRACK,
    ]:
        status, explanation = default_executor_registry.get_readiness_status(method_id)
        assert status == ExecutionReadinessStatus.NOT_READY_FOR_EXECUTION
        assert "experimental" in explanation.lower() or "not ready" in explanation.lower()
