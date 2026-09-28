"""
Session and Media Upload API endpoints.
Manages session creation, scoped upload authorization, and authoritative upload completion.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.schemas.session import Session
from backend.app.schemas.media import MediaAsset, MediaType, UploadStatus
from backend.app.schemas.upload import (
    UploadIntentRequest,
    UploadIntentResponse,
    CompleteUploadRequest,
)
from backend.app.schemas.error import ApiError
from backend.app.services.session_repository import SessionRepository
from backend.app.services.media_repository import MediaRepository
from backend.app.services.storage_service import (
    StorageService,
    StorageError,
    StorageObjectNotFound,
    StorageAuthError,
    StorageTimeout,
    StorageUnavailable,
)
from backend.app.services.media_validation_service import MediaValidationService
from backend.app.api.deps import (
    get_session_repository,
    get_media_repository,
    get_storage_service,
    get_media_validation_service,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

SUPPORTED_VIDEO_MIMES = {"video/mp4", "video/quicktime"}
SUPPORTED_AUDIO_MIMES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/m4a",
    "audio/x-m4a",
    "audio/aac",
}


class CreateSessionRequest(BaseModel):
    title: str = Field(default="Tactical Training Session", description="Session title")
    coach_name: Optional[str] = Field(None, description="Coach name")
    team_name: Optional[str] = Field(None, description="Team name")
    notes: Optional[str] = Field(None, description="Coaching context or session notes")


@router.post("", response_model=Session, status_code=status.HTTP_201_CREATED)
def create_session(
    request: CreateSessionRequest,
    repo: SessionRepository = Depends(get_session_repository),
) -> Session:
    """Create a new session record for grouping uploads and analysis jobs."""
    session = Session(
        id=str(uuid.uuid4()),
        title=request.title,
        coach_name=request.coach_name,
        team_name=request.team_name,
        notes=request.notes,
    )
    return repo.create_session(session)


@router.get(
    "/{session_id}",
    response_model=Session,
    responses={404: {"model": ApiError}},
)
def get_session(
    session_id: str,
    repo: SessionRepository = Depends(get_session_repository),
):
    """Retrieve session details by session ID."""
    session = repo.get_session(session_id)
    if not session:
        error = ApiError(code="SESSION_NOT_FOUND", message=f"Session {session_id} not found")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error.model_dump())
    return session


@router.post(
    "/{session_id}/media/upload-intent",
    response_model=UploadIntentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ApiError},
        404: {"model": ApiError},
        422: {"model": ApiError},
    },
)
def create_upload_intent(
    session_id: str,
    intent: UploadIntentRequest,
    session_repo: SessionRepository = Depends(get_session_repository),
    media_repo: MediaRepository = Depends(get_media_repository),
    storage_svc: StorageService = Depends(get_storage_service),
):
    """
    Validate upload parameters and issue a scoped, temporary signed upload URL.
    Direct browser -> storage upload prevents proxying large video files through the API.
    """
    # 1. Verify session exists
    session = session_repo.get_session(session_id)
    if not session:
        error = ApiError(code="SESSION_NOT_FOUND", message=f"Session {session_id} not found")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error.model_dump())

    # 2. Authoritative format / MIME validation
    if intent.media_type == MediaType.VIDEO:
        if intent.mime_type.lower() not in SUPPORTED_VIDEO_MIMES:
            error = ApiError(
                code="UNSUPPORTED_VIDEO_FORMAT",
                message=f"MIME type '{intent.mime_type}' is not supported. Only MP4 and QuickTime MOV are accepted.",
            )
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

        # Advisory client duration check (not authoritative — real check happens at validation)
        if intent.duration_seconds is not None and intent.duration_seconds > settings.MAX_VIDEO_DURATION_SECONDS:
            error = ApiError(
                code="VIDEO_DURATION_EXCEEDED",
                message=f"Video duration ({intent.duration_seconds:.1f}s) exceeds the maximum allowed limit of {settings.MAX_VIDEO_DURATION_SECONDS:.0f} seconds (6 minutes).",
            )
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

    elif intent.media_type == MediaType.COACH_AUDIO:
        if intent.mime_type.lower() not in SUPPORTED_AUDIO_MIMES:
            error = ApiError(
                code="UNSUPPORTED_AUDIO_FORMAT",
                message=f"Audio MIME type '{intent.mime_type}' is not supported. Supported: WAV, MP3, M4A, AAC.",
            )
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

    # 3. File size validation
    if intent.size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        file_mb = intent.size_bytes / (1024 * 1024)
        error = ApiError(
            code="FILE_SIZE_EXCEEDED",
            message=f"File size ({file_mb:.1f} MB) exceeds maximum allowed size of {max_mb:.0f} MB.",
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

    # 4. Generate media record
    media_id = str(uuid.uuid4())
    bucket = settings.STORAGE_BUCKET_INPUTS
    safe_filename = "".join(c for c in intent.filename if c.isalnum() or c in "._-")
    storage_path = f"{session_id}/{intent.media_type.value.lower()}/{media_id}_{safe_filename}"

    asset = MediaAsset(
        id=media_id,
        session_id=session_id,
        media_type=intent.media_type,
        storage_bucket=bucket,
        storage_path=storage_path,
        original_filename=intent.filename,
        mime_type=intent.mime_type,
        size_bytes=intent.size_bytes,
        duration_seconds=intent.duration_seconds,
        upload_status=UploadStatus.PENDING,
    )
    media_repo.create_media_asset(asset)

    # 5. Issue scoped signed upload URL
    upload_auth = storage_svc.create_signed_upload_url(bucket=bucket, path=storage_path)

    return UploadIntentResponse(
        media_id=media_id,
        session_id=session_id,
        media_type=intent.media_type,
        storage_bucket=bucket,
        storage_path=storage_path,
        signed_upload_url=upload_auth["signed_url"],
        expires_in=3600,
    )


@router.post(
    "/{session_id}/media/{media_id}/complete",
    response_model=MediaAsset,
    responses={
        400: {"model": ApiError},
        404: {"model": ApiError},
        422: {"model": ApiError},
        502: {"model": ApiError},
        503: {"model": ApiError},
    },
)
def complete_upload(
    session_id: str,
    media_id: str,
    request: CompleteUploadRequest,
    media_repo: MediaRepository = Depends(get_media_repository),
    storage_svc: StorageService = Depends(get_storage_service),
    validation_svc: MediaValidationService = Depends(get_media_validation_service),
):
    """
    Authoritative upload completion and media validation.
    1. Confirms the object exists in Supabase Storage (with typed error semantics)
    2. Marks status UPLOADED
    3. Runs authoritative ffprobe validation
    4. Returns VALIDATED or VALIDATION_FAILED asset
    """
    asset = media_repo.get_media_asset(media_id)
    if not asset or asset.session_id != session_id:
        error = ApiError(code="MEDIA_NOT_FOUND", message=f"Media asset {media_id} not found in session {session_id}")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error.model_dump())

    # If already validated, return idempotently
    if asset.upload_status == UploadStatus.VALIDATED:
        return asset

    # If validation already failed, return the failure state
    if asset.upload_status == UploadStatus.VALIDATION_FAILED:
        error = ApiError(
            code="MEDIA_VALIDATION_FAILED",
            message=f"Media validation previously failed: {asset.validation_error_code or 'unknown'}.",
            details={
                "media_id": media_id,
                "validation_error_code": asset.validation_error_code,
                "validation_status": asset.validation_status,
            },
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

    # Authoritative storage verification with typed error semantics
    try:
        exists = storage_svc.verify_object_exists(bucket=asset.storage_bucket, path=asset.storage_path)
    except StorageObjectNotFound:
        exists = False
    except (StorageAuthError, StorageTimeout, StorageUnavailable) as se:
        # Infrastructure failure — retryable, do NOT report as "not found"
        error = ApiError(
            code="STORAGE_TEMPORARILY_UNAVAILABLE",
            message=f"Storage service is temporarily unavailable. Please retry. ({se.code.value})",
            details={"storage_error_code": se.code.value},
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error.model_dump())
    except StorageError as se:
        # Provider error — non-retryable
        error = ApiError(
            code="STORAGE_PROVIDER_ERROR",
            message=f"Storage provider error: {se.message}",
            details={"storage_error_code": se.code.value},
        )
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=error.model_dump())

    if not exists:
        error = ApiError(
            code="OBJECT_NOT_FOUND_IN_STORAGE",
            message=f"Object not found in storage at path '{asset.storage_path}'. Upload may not have completed.",
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error.model_dump())

    # Confirm size
    try:
        confirmed_size = storage_svc.get_object_size(asset.storage_bucket, asset.storage_path)
    except StorageError:
        confirmed_size = None
    actual_size = confirmed_size or request.size_bytes or asset.size_bytes

    # Mark as UPLOADED (pre-validation)
    media_repo.update_media_status(
        media_id=media_id,
        status=UploadStatus.UPLOADED,
        size_bytes=actual_size,
    )

    # Run authoritative media validation (ffprobe)
    # For VIDEO assets, runs full container/codec/duration validation.
    # For non-video assets (audio, etc.), skip probe and mark validated directly.
    if asset.media_type == MediaType.VIDEO:
        validation_result = validation_svc.validate_media(media_id)
        if not validation_result.is_valid:
            # Return the failed validation state
            failed_asset = media_repo.get_media_asset(media_id)
            error = ApiError(
                code=validation_result.error_code or "MEDIA_VALIDATION_FAILED",
                message=validation_result.error_message or "Media validation failed.",
                details={
                    "media_id": media_id,
                    "validation_error_code": validation_result.error_code,
                },
            )
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error.model_dump())

        # Return validated asset
        return validation_result.updated_asset or media_repo.get_media_asset(media_id)
    else:
        # Non-video assets: mark as validated directly (no ffprobe needed for audio)
        updated = media_repo.update_media_validation(
            media_id,
            upload_status=UploadStatus.VALIDATED,
            validation_status="SUCCESS",
        )
        return updated or media_repo.get_media_asset(media_id)


@router.get("/{session_id}/media", response_model=List[MediaAsset])
def list_session_media(
    session_id: str,
    media_repo: MediaRepository = Depends(get_media_repository),
) -> List[MediaAsset]:
    """List all media assets associated with a session."""
    return media_repo.list_session_media(session_id)
