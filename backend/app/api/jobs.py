"""
Analysis job and result endpoints.
Handles job creation, status inspection, and result retrieval.
"""
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from backend.app.schemas.job import AnalysisJob, CreateAnalysisJobRequest
from backend.app.schemas.result import AnalysisResult
from backend.app.schemas.modes import CalibrationMode, AudioMode
from backend.app.schemas.media import MediaType, UploadStatus
from backend.app.schemas.error import ApiError
from backend.app.schemas.dispatch import WorkerDispatchResponse
from backend.app.services.job_repository import AnalysisJobRepository
from backend.app.services.session_repository import SessionRepository
from backend.app.services.media_repository import MediaRepository
from backend.app.services.dispatch_service import AnalysisDispatchService, DispatchServiceError
from backend.app.services.storage_service import StorageService, StorageError
from backend.app.core.config import settings
from backend.app.api.deps import (
    get_job_repository,
    get_session_repository,
    get_media_repository,
    get_dispatch_service,
    get_storage_service,
)

router = APIRouter(prefix="/analysis/jobs", tags=["jobs"])


@router.get("/{job_id}/demo-input-video")
async def get_demo_input_video(
    job_id: str,
    request: Request,
    repository: AnalysisJobRepository = Depends(get_job_repository),
    media_repo: MediaRepository = Depends(get_media_repository),
    storage: StorageService = Depends(get_storage_service),
):
    """Short-lived read access to the completed demo input on this computer only."""
    if request.client is None or request.client.host not in {"127.0.0.1", "::1"} or job_id != settings.PRESENTATION_DEMO_JOB_ID:
        return JSONResponse(status_code=404, content={"code": "NOT_FOUND", "message": "Demo media unavailable"})
    job = await repository.get_job(job_id)
    if job is None or job.status.value not in {"COMPLETED", "COMPLETED_WITH_LIMITATIONS"}:
        return JSONResponse(status_code=404, content={"code": "NOT_FOUND", "message": "Completed demo job unavailable"})
    video = next((asset for asset in media_repo.list_session_media(job.session_id)
                  if asset.job_id == job_id and asset.media_type == MediaType.VIDEO and asset.upload_status == UploadStatus.VALIDATED), None)
    if video is None:
        return JSONResponse(status_code=404, content={"code": "NOT_FOUND", "message": "Validated demo input unavailable"})
    try:
        url = storage.create_signed_download_url(video.storage_bucket, video.storage_path, expires_in=900)
    except StorageError:
        return JSONResponse(status_code=502, content={"code": "STORAGE_UNAVAILABLE", "message": "Private video playback is temporarily unavailable"})
    return {"url": url, "label": "Analyzed Session Video", "expires_in_seconds": 900, "media_id": video.id}


@router.post(
    "",
    response_model=AnalysisJob,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ApiError, "description": "Session not found"},
        422: {"model": ApiError, "description": "Validation error"},
    },
)
async def create_analysis_job(
    request: CreateAnalysisJobRequest,
    repository: AnalysisJobRepository = Depends(get_job_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    media_repo: MediaRepository = Depends(get_media_repository),
) -> AnalysisJob:
    """
    Register a new analysis job.
    CRITICAL: Requires explicit methodology_id and a persisted session with confirmed media.
    Scientific guardrail: DEMO_FIXED_CALIBRATION is rejected for arbitrary user uploads.
    """
    # 1. Scientific safety guardrail: Demo calibration rejected for arbitrary uploaded sessions
    if request.calibration_mode == CalibrationMode.DEMO_FIXED_CALIBRATION:
        error = ApiError(
            code="INVALID_CALIBRATION_MODE",
            message=(
                "Validated Demo Calibration is strictly calibrated for frozen research demonstration footage "
                "and cannot be applied to arbitrary uploaded videos. Select NO_METRIC_CALIBRATION or CUSTOM_PITCH_CALIBRATION."
            ),
            details={"calibration_mode": request.calibration_mode.value},
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

    # 2. Verify session exists
    session = session_repo.get_session(request.session_id)
    if not session:
        error = ApiError(
            code="SESSION_NOT_FOUND",
            message=f"Associated session '{request.session_id}' does not exist.",
            details={"session_id": request.session_id},
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error.model_dump())

    # 3. Verify required media assets exist and are VALIDATED
    # CRITICAL: UPLOADED alone is insufficient — authoritative probe validation is required.
    media_list = media_repo.list_session_media(request.session_id)
    video_asset = next(
        (m for m in media_list if m.media_type == MediaType.VIDEO and m.upload_status == UploadStatus.VALIDATED),
        None,
    )
    if not video_asset:
        # Check if there's an uploaded-but-unvalidated or failed-validation video
        unvalidated = next(
            (m for m in media_list if m.media_type == MediaType.VIDEO and m.upload_status == UploadStatus.UPLOADED),
            None,
        )
        failed_validation = next(
            (m for m in media_list if m.media_type == MediaType.VIDEO and m.upload_status == UploadStatus.VALIDATION_FAILED),
            None,
        )
        if failed_validation:
            error = ApiError(
                code="MEDIA_VALIDATION_FAILED",
                message=f"Video validation failed: {failed_validation.validation_error_code or 'unknown'}. Upload a valid video.",
                details={"session_id": request.session_id, "validation_error_code": failed_validation.validation_error_code},
            )
        elif unvalidated:
            error = ApiError(
                code="MEDIA_NOT_VALIDATED",
                message="Video has been uploaded but not yet validated. Complete the upload verification first.",
                details={"session_id": request.session_id},
            )
        else:
            error = ApiError(
                code="REQUIRED_MEDIA_MISSING",
                message="A validated video asset is required before creating an analysis job.",
                details={"session_id": request.session_id, "required_media": "VIDEO"},
            )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

    audio_asset = None
    if request.audio_mode == AudioMode.SEPARATE_AUDIO_FILE:
        audio_asset = next(
            (m for m in media_list if m.media_type == MediaType.COACH_AUDIO and m.upload_status in (UploadStatus.UPLOADED, UploadStatus.VALIDATED)),
            None,
        )
        if not audio_asset:
            error = ApiError(
                code="REQUIRED_AUDIO_MISSING",
                message="Separate coach audio upload is required when audio_mode is set to SEPARATE_AUDIO_FILE.",
                details={"session_id": request.session_id, "required_media": "COACH_AUDIO"},
            )
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

    # 4. Create analysis job record
    job = await repository.create_job(request)

    # 5. Link media assets to created job
    media_repo.link_job(video_asset.id, job.id)
    if audio_asset:
        media_repo.link_job(audio_asset.id, job.id)

    return job


@router.get(
    "/{job_id}",
    response_model=AnalysisJob,
    responses={
        404: {"model": ApiError, "description": "Job not found"},
    },
)
async def get_analysis_job(
    job_id: str,
    repository: AnalysisJobRepository = Depends(get_job_repository),
):
    """
    Retrieve analysis job status and progress.
    """
    job = await repository.get_job(job_id)
    if not job:
        error = ApiError(
            code="JOB_NOT_FOUND",
            message=f"Analysis job '{job_id}' was not found.",
            details={"job_id": job_id},
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error.model_dump())
    return job


@router.get(
    "/{job_id}/result",
    response_model=AnalysisResult,
    responses={
        404: {"model": ApiError, "description": "Job not found"},
        409: {"model": ApiError, "description": "Result not ready"},
    },
)
async def get_analysis_result(
    job_id: str,
    repository: AnalysisJobRepository = Depends(get_job_repository),
):
    """
    Retrieve completed analysis results for a job.
    Returns 409 Conflict if the job is still processing or has no computed result.
    NEVER returns fabricated metrics.
    """
    job = await repository.get_job(job_id)
    if not job:
        error = ApiError(
            code="JOB_NOT_FOUND",
            message=f"Analysis job '{job_id}' was not found.",
            details={"job_id": job_id},
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error.model_dump())

    result = await repository.get_result(job_id)
    if not result:
        error = ApiError(
            code="RESULT_NOT_READY",
            message=f"Analysis result is not ready for job '{job_id}'. Current stage: {job.current_stage.value} ({job.progress_percent:.1f}%).",
            details={
                "job_id": job_id,
                "current_stage": job.current_stage.value,
                "progress_percent": job.progress_percent,
                "stage_message": job.stage_message,
            },
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=error.model_dump())

    return result


@router.post(
    "/{job_id}/dispatch",
    response_model=WorkerDispatchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ApiError, "description": "Job not found"},
        409: {"model": ApiError, "description": "Job not QUEUED or methodology executor not ready"},
        422: {"model": ApiError, "description": "Required media missing"},
        502: {"model": ApiError, "description": "Worker provider submission failed"},
    },
)
async def dispatch_analysis_job(
    job_id: str,
    dispatch_service: AnalysisDispatchService = Depends(get_dispatch_service),
):
    """
    Dispatch an analysis job to the serverless compute provider.
    Enforces idempotency, job status, media presence, and methodology readiness gates.
    """
    try:
        dispatch, was_idempotent = await dispatch_service.dispatch_job(job_id)
        message = (
            "Active worker dispatch already exists for this job."
            if was_idempotent
            else "Job dispatched successfully."
        )
        return WorkerDispatchResponse(
            dispatch_id=dispatch.id,
            job_id=dispatch.job_id,
            provider=dispatch.provider,
            provider_execution_id=dispatch.provider_execution_id,
            state=dispatch.state,
            created_at=dispatch.created_at,
            message=message,
        )
    except DispatchServiceError as dse:
        error = ApiError(
            code=dse.code,
            message=dse.message,
            details=dse.details,
        )
        return JSONResponse(status_code=dse.status_code, content=error.model_dump())
