"""
Analysis dispatch application service.
Coordinates validation, idempotency, dispatch record creation, worker invocation,
and authenticated progress/completion callbacks.
"""
import uuid
import os
from typing import Optional, Tuple
from datetime import datetime

from backend.app.schemas.job import AnalysisJob, JobStatus
from backend.app.schemas.stages import AnalysisStage
from backend.app.schemas.media import MediaType, UploadStatus
from backend.app.schemas.dispatch import (
    WorkerDispatch,
    WorkerDispatchState,
    WorkerDispatchRequest,
    WorkerDispatchResponse,
    WorkerProgressCallbackRequest,
)
from backend.app.services.job_repository import AnalysisJobRepository, TERMINAL_JOB_STATUSES
from backend.app.services.session_repository import SessionRepository
from backend.app.services.media_repository import MediaRepository
from backend.app.services.dispatch_repository import (
    WorkerDispatchRepository,
    ActiveDispatchConflictError,
)
from backend.app.services.modal_client import (
    ModalDispatchClient,
    ModalError,
    ModalAuthenticationError,
    ModalSubmissionError,
)
from backend.app.pipeline.registry import (
    MethodologyExecutorRegistry,
    create_production_registry,
    ExecutionReadinessStatus,
)


class DispatchServiceError(Exception):
    """Base exception for dispatch service failures."""
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class JobNotFoundError(DispatchServiceError):
    def __init__(self, job_id: str):
        super().__init__(
            code="JOB_NOT_FOUND",
            message=f"Analysis job '{job_id}' does not exist.",
            status_code=404,
            details={"job_id": job_id},
        )


class DispatchNotFoundError(DispatchServiceError):
    def __init__(self, dispatch_id: str):
        super().__init__(
            code="DISPATCH_NOT_FOUND",
            message=f"Worker dispatch '{dispatch_id}' does not exist.",
            status_code=404,
            details={"dispatch_id": dispatch_id},
        )


class CallbackOwnershipMismatchError(DispatchServiceError):
    def __init__(self, job_id: str, dispatch_id: str, reason: str):
        super().__init__(
            code="CALLBACK_OWNERSHIP_MISMATCH",
            message=f"Ownership validation failed for job '{job_id}' and dispatch '{dispatch_id}': {reason}",
            status_code=400,
            details={"job_id": job_id, "dispatch_id": dispatch_id, "reason": reason},
        )


class JobStatusConflictError(DispatchServiceError):
    def __init__(self, job_id: str, status: JobStatus):
        super().__init__(
            code="INVALID_JOB_STATE",
            message=f"Only jobs in QUEUED status can be dispatched. Current status: '{status.value}'.",
            status_code=409,
            details={"job_id": job_id, "current_status": status.value},
        )


class RequiredMediaMissingError(DispatchServiceError):
    def __init__(self, job_id: str, message: str):
        super().__init__(
            code="REQUIRED_MEDIA_MISSING",
            message=message,
            status_code=422,
            details={"job_id": job_id},
        )


class MethodologyNotReadyError(DispatchServiceError):
    def __init__(self, methodology_id: str, explanation: str):
        super().__init__(
            code="METHODOLOGY_EXECUTOR_NOT_READY",
            message=explanation,
            status_code=409,
            details={"methodology_id": methodology_id},
        )


class DispatchSubmissionFailedError(DispatchServiceError):
    def __init__(self, code: str, message: str):
        super().__init__(
            code=code,
            message=message,
            status_code=502,
        )


class AnalysisDispatchService:
    """
    Application service that orchestrates dispatching analysis jobs to serverless workers
    and processes progress/completion callbacks.
    """

    def __init__(
        self,
        job_repo: AnalysisJobRepository,
        session_repo: SessionRepository,
        media_repo: MediaRepository,
        dispatch_repo: WorkerDispatchRepository,
        modal_client: ModalDispatchClient,
        executor_registry: Optional[MethodologyExecutorRegistry] = None,
    ):
        self._job_repo = job_repo
        self._session_repo = session_repo
        self._media_repo = media_repo
        self._dispatch_repo = dispatch_repo
        self._modal_client = modal_client
        self._registry = executor_registry or create_production_registry()

    async def dispatch_job(
        self, job_id: str, *, start_frame: int = 0, max_frames: Optional[int] = None,
        audio_source_offset_s: float = 0.0, video_source_offset_s: float = 0.0,
        force_deterministic_fallback: bool = False,
        input_asset_role: Optional[str] = None,
        authoritative_source_sha256: Optional[str] = None,
        transport_copy_sha256: Optional[str] = None,
    ) -> Tuple[WorkerDispatch, bool]:
        """
        Dispatch an analysis job to the worker provider.
        Enforces atomic active-dispatch idempotency and updates job lifecycle on submission.
        Returns:
            Tuple[WorkerDispatch, bool]: (dispatch_record, was_idempotent_replay)
        """
        # 1. Validate job exists
        job = await self._job_repo.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        # 2. Fast-path check: If an active worker dispatch already exists for this job,
        # return it immediately as an idempotent replay without initiating another submission.
        active_dispatch = self._dispatch_repo.get_active_dispatch_for_job(job_id)
        if active_dispatch is not None:
            return active_dispatch, True

        # 3. Validate job is in QUEUED status to start a fresh dispatch attempt
        if job.status != JobStatus.QUEUED:
            raise JobStatusConflictError(job_id, job.status)


        # 4. Validate confirmed AND validated media exists for session
        # CRITICAL: UPLOADED alone is insufficient — authoritative probe validation is required.
        media_list = self._media_repo.list_session_media(job.session_id)
        video_asset = next(
            (m for m in media_list if m.media_type == MediaType.VIDEO and m.upload_status == UploadStatus.VALIDATED),
            None,
        )
        if not video_asset:
            raise RequiredMediaMissingError(
                job_id,
                f"No validated video asset exists for session '{job.session_id}'. "
                f"Media must pass authoritative container/codec validation before dispatch.",
            )

        # 5. Methodology Execution Readiness Gate (Strictly closed before Phase 4B)
        readiness_status, explanation = self._registry.get_readiness_status(job.methodology_id)
        if readiness_status != ExecutionReadinessStatus.READY_FOR_EXECUTION:
            raise MethodologyNotReadyError(job.methodology_id.value, explanation)

        # 6. Create initial dispatch record (CREATED state) with atomic constraint handling
        dispatch_id = str(uuid.uuid4())
        dispatch = WorkerDispatch(
            id=dispatch_id,
            job_id=job.id,
            provider="MODAL",
            provider_execution_id=None,
            state=WorkerDispatchState.CREATED,
            attempt=1,
            created_at=datetime.utcnow(),
        )
        try:
            self._dispatch_repo.create_dispatch(dispatch)
        except ActiveDispatchConflictError as ace:
            # Atomic database constraint caught concurrent dispatch attempt:
            # Safely retrieve and return already-active dispatch
            existing = ace.existing_dispatch or self._dispatch_repo.get_active_dispatch_for_job(job.id)
            if existing is not None:
                return existing, True
            raise

        # 7. Submit to worker provider
        req = WorkerDispatchRequest(
            job_id=job.id,
            session_id=job.session_id,
            methodology_id=job.methodology_id,
            dispatch_id=dispatch.id,
            video_storage_bucket=video_asset.storage_bucket,
            video_storage_path=video_asset.storage_path,
            audio_storage_bucket=audio_asset.storage_bucket if (audio_asset := next(
                (m for m in media_list if m.media_type == MediaType.COACH_AUDIO and m.upload_status in (UploadStatus.UPLOADED, UploadStatus.VALIDATED)), None
            )) else None,
            audio_storage_path=audio_asset.storage_path if audio_asset else None,
            callback_url=os.getenv("WORKER_CALLBACK_URL", "").replace("{job_id}", job.id) or None,
            calibration_mode=job.calibration_mode.value,
            application_mode=job.mode.value,
            audio_mode=job.audio_mode.value,
            start_frame=start_frame,
            max_frames=max_frames,
            audio_source_offset_s=audio_source_offset_s,
            video_source_offset_s=video_source_offset_s,
            force_deterministic_fallback=force_deterministic_fallback,
            input_asset_role=input_asset_role,
            authoritative_source_sha256=authoritative_source_sha256,
            transport_copy_sha256=transport_copy_sha256,
        )

        try:
            exec_id = self._modal_client.submit_job(req)
            latest_dispatch = self._dispatch_repo.get_dispatch(dispatch.id) or dispatch
            latest_dispatch.provider_execution_id = exec_id
            if latest_dispatch.state == WorkerDispatchState.CREATED:
                latest_dispatch.state = WorkerDispatchState.SUBMITTED
                latest_dispatch.started_at = datetime.utcnow()
            self._dispatch_repo.update_dispatch(latest_dispatch)

            # Transition AnalysisJob from QUEUED / UPLOADED -> PROCESSING / VALIDATING
            latest_job = await self._job_repo.get_job(job.id)
            if latest_job.status == JobStatus.QUEUED:
                await self._job_repo.update_job_lifecycle(
                    job_id=job.id,
                    status=JobStatus.PROCESSING,
                    current_stage=AnalysisStage.VALIDATING,
                    progress_percent=5.0,
                    stage_message="Job submitted to worker; validating inputs.",
                    modal_call_id=exec_id,
                )
            else:
                await self._job_repo.update_job_lifecycle(job_id=job.id, modal_call_id=exec_id)
            return latest_dispatch, False
        except ModalError as me:
            dispatch.state = WorkerDispatchState.FAILED
            dispatch.error_code = me.code
            dispatch.error_message = me.message
            dispatch.finished_at = datetime.utcnow()
            self._dispatch_repo.update_dispatch(dispatch)

            # Persist failed AnalysisJob outcome; do not leave active dispatch
            await self._job_repo.update_job_lifecycle(
                job_id=job.id,
                status=JobStatus.FAILED,
                error_code=me.code,
                error_details=me.message,
                stage_message=f"Dispatch failed: {me.message}",
                completed_at=datetime.utcnow(),
            )
            raise DispatchSubmissionFailedError(me.code, f"Worker provider rejected dispatch: {me.message}")
        except Exception as ex:
            dispatch.state = WorkerDispatchState.FAILED
            dispatch.error_code = "UNEXPECTED_PROVIDER_ERROR"
            dispatch.error_message = str(ex)
            dispatch.finished_at = datetime.utcnow()
            self._dispatch_repo.update_dispatch(dispatch)

            await self._job_repo.update_job_lifecycle(
                job_id=job.id,
                status=JobStatus.FAILED,
                error_code="UNEXPECTED_PROVIDER_ERROR",
                error_details=str(ex),
                stage_message=f"Unexpected error during dispatch: {str(ex)}",
                completed_at=datetime.utcnow(),
            )
            raise DispatchSubmissionFailedError("UNEXPECTED_PROVIDER_ERROR", f"Unexpected error during dispatch: {str(ex)}")

    async def handle_worker_callback(
        self,
        job_id: str,
        callback: WorkerProgressCallbackRequest,
    ) -> Tuple[AnalysisJob, WorkerDispatch, bool]:
        """
        Process authenticated worker execution progress/completion callback.
        Validates ownership, guards terminal job states, and safely handles retries/replays.
        Returns:
            Tuple[AnalysisJob, WorkerDispatch, bool]: (job, dispatch, was_ignored_or_replay)
        """
        # 1. Payload-to-path consistency check
        if callback.job_id != job_id:
            raise CallbackOwnershipMismatchError(
                job_id=job_id,
                dispatch_id=callback.dispatch_id,
                reason=f"Path job_id '{job_id}' does not match payload job_id '{callback.job_id}'",
            )

        # 2. Verify target job exists
        job = await self._job_repo.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        # 3. Verify target dispatch exists
        dispatch = self._dispatch_repo.get_dispatch(callback.dispatch_id)
        if not dispatch:
            raise DispatchNotFoundError(callback.dispatch_id)

        # 4. Verify dispatch ownership: dispatch must belong to this job
        if dispatch.job_id != job_id:
            raise CallbackOwnershipMismatchError(
                job_id=job_id,
                dispatch_id=callback.dispatch_id,
                reason=f"Dispatch '{callback.dispatch_id}' belongs to job '{dispatch.job_id}', not '{job_id}'",
            )

        # 5. Terminal State Invariant & Replay Protection:
        # If job is already in a terminal state (COMPLETED, COMPLETED_WITH_LIMITATIONS, FAILED),
        # a late or duplicate callback MUST NOT reopen or corrupt it.
        if job.status in TERMINAL_JOB_STATUSES:
            return job, dispatch, True

        if callback.progress_percent < job.progress_percent:
            raise DispatchServiceError(
                code="PROGRESS_REGRESSION",
                message="Worker callback progress cannot move backwards.",
                status_code=409,
            )

        now = datetime.utcnow()

        # 6. Apply state mapping based on callback dispatch_state
        if callback.dispatch_state == WorkerDispatchState.RUNNING:
            dispatch.state = WorkerDispatchState.RUNNING
            if dispatch.started_at is None:
                dispatch.started_at = now
            self._dispatch_repo.update_dispatch(dispatch)

            updated_job = await self._job_repo.update_job_lifecycle(
                job_id=job.id,
                status=JobStatus.PROCESSING,
                current_stage=callback.current_stage,
                progress_percent=callback.progress_percent,
                stage_message=callback.stage_message or f"Executing stage {callback.current_stage.value}",
            )
            return updated_job, dispatch, False

        elif callback.dispatch_state == WorkerDispatchState.SUCCEEDED:
            stored_result = await self._job_repo.get_result(job_id)
            if stored_result is None or stored_result.job_id != job_id:
                raise DispatchServiceError(
                    code="RESULT_NOT_PERSISTED",
                    message="A worker cannot complete a job before its canonical result is retrievable.",
                    status_code=409,
                )
            if callback.job_status != stored_result.job_status:
                raise DispatchServiceError(
                    code="RESULT_STATUS_MISMATCH",
                    message="Terminal callback status must match the persisted canonical result.",
                    status_code=409,
                )
            dispatch.state = WorkerDispatchState.SUCCEEDED
            dispatch.finished_at = now
            self._dispatch_repo.update_dispatch(dispatch)

            # Target status defaults to COMPLETED, or explicit valid callback job_status
            target_status = callback.job_status
            updated_job = await self._job_repo.update_job_lifecycle(
                job_id=job.id,
                status=target_status,
                current_stage=callback.current_stage,
                progress_percent=callback.progress_percent,
                stage_message=callback.stage_message or "Worker execution completed successfully.",
                completed_at=now,
            )
            return updated_job, dispatch, False

        elif callback.dispatch_state in (WorkerDispatchState.FAILED, WorkerDispatchState.CANCELLED):
            dispatch.state = callback.dispatch_state
            dispatch.finished_at = now
            dispatch.error_code = callback.error_code or "WORKER_FAILED"
            dispatch.error_message = callback.error_details
            self._dispatch_repo.update_dispatch(dispatch)

            # Preserve last reached stage, transition job to FAILED
            updated_job = await self._job_repo.update_job_lifecycle(
                job_id=job.id,
                status=JobStatus.FAILED,
                current_stage=callback.current_stage,
                progress_percent=callback.progress_percent,
                stage_message=callback.stage_message or f"Worker execution {callback.dispatch_state.value.lower()}.",
                error_code=callback.error_code or "WORKER_FAILED",
                error_details=callback.error_details,
                completed_at=now,
            )
            return updated_job, dispatch, False

        else:
            # Fallback for CREATED / SUBMITTED callback if any
            dispatch.state = callback.dispatch_state
            self._dispatch_repo.update_dispatch(dispatch)
            return job, dispatch, False
