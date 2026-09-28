"""
Media validation service.
Orchestrates authoritative server-side media validation after upload completion.

Flow: Storage signed URL → ffprobe → validate constraints → persist verified metadata.

CRITICAL: Client-declared metadata is ADVISORY ONLY. All persisted values come from ffprobe.
CRITICAL: Duration limit is enforced from the actual stored object, not client claims.
"""
from typing import Optional, Tuple
from backend.app.schemas.media import MediaAsset, UploadStatus
from backend.app.services.media_repository import MediaRepository
from backend.app.services.storage_service import StorageService, StorageError
from backend.app.services.media_probe import (
    MediaProbeService,
    MediaProbeResult,
    ProbeStatus,
)
from backend.app.core.config import settings


# =============================================================================
# TYPED VALIDATION ERROR CODES
# =============================================================================

class MediaValidationErrorCode:
    """Machine-readable validation error codes for media validation failures."""
    VIDEO_DURATION_EXCEEDED = "VIDEO_DURATION_EXCEEDED"
    NO_VIDEO_STREAM = "NO_VIDEO_STREAM"
    INVALID_CONTAINER = "INVALID_CONTAINER"
    CORRUPT_MEDIA = "CORRUPT_MEDIA"
    INVALID_DIMENSIONS = "INVALID_DIMENSIONS"
    INVALID_FPS = "INVALID_FPS"
    MIME_CONTAINER_MISMATCH = "MIME_CONTAINER_MISMATCH"
    PROBE_TIMEOUT = "PROBE_TIMEOUT"
    FFPROBE_NOT_AVAILABLE = "FFPROBE_NOT_AVAILABLE"
    PROBE_ERROR = "PROBE_ERROR"
    STORAGE_ACCESS_ERROR = "STORAGE_ACCESS_ERROR"


# =============================================================================
# MIME / CONTAINER COMPATIBILITY MAPPING
# =============================================================================
# Documented mapping: declared MIME types to acceptable ffprobe container formats.
# Not naive string equality — MP4 and MOV share the ISOBMFF container family.

MIME_CONTAINER_COMPATIBILITY = {
    "video/mp4": {
        "mov,mp4,m4a,3gp,3g2,mj2",  # Standard ffprobe output for MP4
        "mp4",
        "m4v",
    },
    "video/quicktime": {
        "mov,mp4,m4a,3gp,3g2,mj2",  # MOV shares ISOBMFF with MP4
        "mov",
        "mp4",
    },
}


class MediaValidationResult:
    """Result of the media validation process."""
    def __init__(
        self,
        *,
        is_valid: bool,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        probe_result: Optional[MediaProbeResult] = None,
        updated_asset: Optional[MediaAsset] = None,
    ):
        self.is_valid = is_valid
        self.error_code = error_code
        self.error_message = error_message
        self.probe_result = probe_result
        self.updated_asset = updated_asset


class MediaValidationService:
    """
    Orchestrates authoritative media validation after upload completion.
    
    1. Generates a short-lived signed download URL for the stored object
    2. Runs ffprobe to extract container/codec metadata
    3. Validates: has video stream, valid dimensions, finite FPS, duration <= MAX
    4. Checks MIME/container consistency
    5. Persists authoritative metadata to media_assets
    6. Sets upload_status = VALIDATED or VALIDATION_FAILED
    """

    def __init__(
        self,
        media_repo: MediaRepository,
        storage_service: StorageService,
        probe_service: MediaProbeService,
        max_duration_seconds: Optional[float] = None,
    ):
        self._media_repo = media_repo
        self._storage = storage_service
        self._probe = probe_service
        self._max_duration = max_duration_seconds or settings.MAX_VIDEO_DURATION_SECONDS

    def validate_media(self, media_id: str) -> MediaValidationResult:
        """
        Run authoritative validation on a media asset.
        The asset must already be in UPLOADED status.
        """
        asset = self._media_repo.get_media_asset(media_id)
        if not asset:
            return MediaValidationResult(
                is_valid=False,
                error_code="MEDIA_NOT_FOUND",
                error_message=f"Media asset '{media_id}' not found.",
            )

        # Mark as VALIDATING
        self._media_repo.update_media_status(media_id, UploadStatus.VALIDATING)

        # 1. Generate signed download URL for private storage
        try:
            signed_url = self._storage.create_signed_download_url(
                bucket=asset.storage_bucket,
                path=asset.storage_path,
                expires_in=120,  # 2 minutes is more than enough for ffprobe
            )
        except StorageError as se:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.STORAGE_ACCESS_ERROR,
                f"Cannot access stored object for validation: {se.message}",
                probe_status="STORAGE_ERROR",
            )

        # 2. Run ffprobe
        probe_result = self._probe.probe(signed_url)

        # 3. Evaluate probe outcome
        if probe_result.probe_status == ProbeStatus.FFPROBE_NOT_AVAILABLE:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.FFPROBE_NOT_AVAILABLE,
                probe_result.error_message or "ffprobe not available.",
                probe_status=probe_result.probe_status.value,
            )

        if probe_result.probe_status == ProbeStatus.PROBE_TIMEOUT:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.PROBE_TIMEOUT,
                probe_result.error_message or "ffprobe timed out.",
                probe_status=probe_result.probe_status.value,
            )

        if probe_result.probe_status == ProbeStatus.INVALID_CONTAINER:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.INVALID_CONTAINER,
                probe_result.error_message or "Not a valid video container.",
                probe_status=probe_result.probe_status.value,
            )

        if probe_result.probe_status == ProbeStatus.CORRUPT_FILE:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.CORRUPT_MEDIA,
                probe_result.error_message or "File appears corrupt.",
                probe_status=probe_result.probe_status.value,
            )

        if probe_result.probe_status == ProbeStatus.NO_VIDEO_STREAM:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.NO_VIDEO_STREAM,
                probe_result.error_message or "No video stream found in container.",
                probe_status=probe_result.probe_status.value,
            )

        if probe_result.probe_status == ProbeStatus.PROBE_ERROR:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.PROBE_ERROR,
                probe_result.error_message or "Unexpected probe error.",
                probe_status=probe_result.probe_status.value,
            )

        if probe_result.probe_status != ProbeStatus.SUCCESS:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.PROBE_ERROR,
                f"Unexpected probe status: {probe_result.probe_status.value}",
                probe_status=probe_result.probe_status.value,
            )

        # 4. Validate dimensions
        if not probe_result.width or not probe_result.height or probe_result.width <= 0 or probe_result.height <= 0:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.INVALID_DIMENSIONS,
                f"Invalid dimensions: {probe_result.width}x{probe_result.height}",
                probe_status=probe_result.probe_status.value,
                probe_result=probe_result,
            )

        # 5. Validate FPS
        if not probe_result.fps or probe_result.fps <= 0:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.INVALID_FPS,
                f"Invalid or zero FPS: {probe_result.fps}",
                probe_status=probe_result.probe_status.value,
                probe_result=probe_result,
            )

        # 6. Validate duration
        if probe_result.duration_seconds is None or probe_result.duration_seconds <= 0:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.CORRUPT_MEDIA,
                f"Invalid or zero duration: {probe_result.duration_seconds}",
                probe_status=probe_result.probe_status.value,
                probe_result=probe_result,
            )

        if probe_result.duration_seconds > self._max_duration:
            return self._persist_failure(
                media_id,
                MediaValidationErrorCode.VIDEO_DURATION_EXCEEDED,
                f"Video duration ({probe_result.duration_seconds:.1f}s) exceeds "
                f"maximum allowed limit of {self._max_duration:.0f} seconds.",
                probe_status=probe_result.probe_status.value,
                probe_result=probe_result,
            )

        # 7. MIME/container consistency check
        mime_lower = asset.mime_type.lower()
        if mime_lower in MIME_CONTAINER_COMPATIBILITY:
            acceptable = MIME_CONTAINER_COMPATIBILITY[mime_lower]
            if probe_result.container_format and probe_result.container_format not in acceptable:
                return self._persist_failure(
                    media_id,
                    MediaValidationErrorCode.MIME_CONTAINER_MISMATCH,
                    f"Declared MIME '{asset.mime_type}' is inconsistent with probed "
                    f"container '{probe_result.container_format}'.",
                    probe_status=probe_result.probe_status.value,
                    probe_result=probe_result,
                )

        # 8. All checks passed — persist authoritative metadata
        updated = self._media_repo.update_media_validation(
            media_id,
            upload_status=UploadStatus.VALIDATED,
            duration_seconds=probe_result.duration_seconds,
            width=probe_result.width,
            height=probe_result.height,
            fps=probe_result.fps,
            container_format=probe_result.container_format,
            video_codec=probe_result.video_codec,
            audio_codec=probe_result.audio_codec,
            validation_status=ProbeStatus.SUCCESS.value,
            validation_error_code=None,
        )

        return MediaValidationResult(
            is_valid=True,
            probe_result=probe_result,
            updated_asset=updated,
        )

    def _persist_failure(
        self,
        media_id: str,
        error_code: str,
        error_message: str,
        probe_status: str,
        probe_result: Optional[MediaProbeResult] = None,
    ) -> MediaValidationResult:
        """Persist validation failure state and return typed result."""
        update_kwargs = {
            "upload_status": UploadStatus.VALIDATION_FAILED,
            "validation_status": probe_status,
            "validation_error_code": error_code,
        }
        # Persist whatever partial probe data we have
        if probe_result:
            if probe_result.container_format:
                update_kwargs["container_format"] = probe_result.container_format
            if probe_result.video_codec:
                update_kwargs["video_codec"] = probe_result.video_codec
            if probe_result.audio_codec:
                update_kwargs["audio_codec"] = probe_result.audio_codec
            if probe_result.duration_seconds is not None:
                update_kwargs["duration_seconds"] = probe_result.duration_seconds
            if probe_result.width:
                update_kwargs["width"] = probe_result.width
            if probe_result.height:
                update_kwargs["height"] = probe_result.height
            if probe_result.fps:
                update_kwargs["fps"] = probe_result.fps

        self._media_repo.update_media_validation(media_id, **update_kwargs)

        return MediaValidationResult(
            is_valid=False,
            error_code=error_code,
            error_message=error_message,
            probe_result=probe_result,
        )
