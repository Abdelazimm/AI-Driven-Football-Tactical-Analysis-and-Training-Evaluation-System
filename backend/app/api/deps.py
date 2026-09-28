"""
FastAPI dependency providers.
Provides access to SessionRepository, MediaRepository, AnalysisJobRepository,
StorageService, MediaProbeService, MediaValidationService, and dispatch infrastructure.
Uses Supabase persistence when configured, with clean in-memory fallbacks for offline testing.
"""
from typing import Optional
from backend.app.services.job_repository import (
    AnalysisJobRepository,
    InMemoryJobRepository,
    SupabaseAnalysisJobRepository,
)
from backend.app.services.session_repository import (
    SessionRepository,
    InMemorySessionRepository,
    SupabaseSessionRepository,
)
from backend.app.services.media_repository import (
    MediaRepository,
    InMemoryMediaRepository,
    SupabaseMediaRepository,
)
from backend.app.services.storage_service import (
    StorageService,
    InMemoryStorageService,
    SupabaseStorageService,
)
from backend.app.services.media_probe import (
    MediaProbeService,
    MediaProbeResult,
    ProbeStatus,
    FFProbeMediaProbeService,
    InMemoryMediaProbeService,
)
from backend.app.services.media_validation_service import MediaValidationService
from backend.app.services.dispatch_repository import (
    WorkerDispatchRepository,
    InMemoryWorkerDispatchRepository,
    SupabaseWorkerDispatchRepository,
)
from backend.app.services.modal_client import (
    ModalDispatchClient,
    InMemoryModalClient,
    ProductionModalClient,
)
from backend.app.services.dispatch_service import AnalysisDispatchService
from backend.app.services.supabase_client import get_supabase_client, is_supabase_configured

# Fallback in-memory singletons for offline testing
_in_memory_jobs = InMemoryJobRepository()
_in_memory_sessions = InMemorySessionRepository()
_in_memory_media = InMemoryMediaRepository()
_in_memory_storage = InMemoryStorageService()
_in_memory_dispatch = InMemoryWorkerDispatchRepository()
_in_memory_modal = InMemoryModalClient()
_in_memory_probe = InMemoryMediaProbeService()
_in_memory_probe.set_default_result(
    MediaProbeResult(
        probe_status=ProbeStatus.SUCCESS,
        container_format="mov,mp4,m4a,3gp,3g2,mj2",
        duration_seconds=120.0,
        video_streams=1,
        audio_streams=1,
        video_codec="h264",
        audio_codec="aac",
        width=1920,
        height=1080,
        fps=30.0,
    )
)

# Explicit override handles (used by tests)
_override_job_repo: Optional[AnalysisJobRepository] = None
_override_session_repo: Optional[SessionRepository] = None
_override_media_repo: Optional[MediaRepository] = None
_override_storage: Optional[StorageService] = None
_override_dispatch_repo: Optional[WorkerDispatchRepository] = None
_override_modal_client: Optional[ModalDispatchClient] = None
_override_probe_service: Optional[MediaProbeService] = None
_override_validation_service: Optional[MediaValidationService] = None


def get_session_repository() -> SessionRepository:
    """Provide the active SessionRepository."""
    if _override_session_repo is not None:
        return _override_session_repo
    client = get_supabase_client()
    if client is not None:
        return SupabaseSessionRepository(client)
    return _in_memory_sessions


def get_media_repository() -> MediaRepository:
    """Provide the active MediaRepository."""
    if _override_media_repo is not None:
        return _override_media_repo
    client = get_supabase_client()
    if client is not None:
        return SupabaseMediaRepository(client)
    return _in_memory_media


def get_job_repository() -> AnalysisJobRepository:
    """Provide the active AnalysisJobRepository."""
    if _override_job_repo is not None:
        return _override_job_repo
    client = get_supabase_client()
    if client is not None:
        return SupabaseAnalysisJobRepository(client)
    return _in_memory_jobs


def get_storage_service() -> StorageService:
    """Provide the active StorageService."""
    if _override_storage is not None:
        return _override_storage
    client = get_supabase_client()
    if client is not None:
        return SupabaseStorageService(client)
    return _in_memory_storage


def get_media_probe_service() -> MediaProbeService:
    """Provide the active MediaProbeService."""
    if _override_probe_service is not None:
        return _override_probe_service
    client = get_supabase_client()
    if client is not None:
        return FFProbeMediaProbeService()
    return _in_memory_probe


def get_media_validation_service() -> MediaValidationService:
    """Provide the active MediaValidationService."""
    if _override_validation_service is not None:
        return _override_validation_service
    return MediaValidationService(
        media_repo=get_media_repository(),
        storage_service=get_storage_service(),
        probe_service=get_media_probe_service(),
    )


def set_override_job_repository(repo: Optional[AnalysisJobRepository]) -> None:
    global _override_job_repo
    _override_job_repo = repo


def set_override_session_repository(repo: Optional[SessionRepository]) -> None:
    global _override_session_repo
    _override_session_repo = repo


def set_override_media_repository(repo: Optional[MediaRepository]) -> None:
    global _override_media_repo
    _override_media_repo = repo


def set_override_storage_service(service: Optional[StorageService]) -> None:
    global _override_storage
    _override_storage = service


def set_override_media_probe_service(service: Optional[MediaProbeService]) -> None:
    global _override_probe_service
    _override_probe_service = service


def set_override_media_validation_service(service: Optional[MediaValidationService]) -> None:
    global _override_validation_service
    _override_validation_service = service


def get_dispatch_repository() -> WorkerDispatchRepository:
    """Provide the active WorkerDispatchRepository."""
    if _override_dispatch_repo is not None:
        return _override_dispatch_repo
    client = get_supabase_client()
    if client is not None:
        return SupabaseWorkerDispatchRepository(client)
    return _in_memory_dispatch


def get_modal_client() -> ModalDispatchClient:
    """Provide the active ModalDispatchClient."""
    if _override_modal_client is not None:
        return _override_modal_client
    return ProductionModalClient()


def get_dispatch_service() -> AnalysisDispatchService:
    """Provide the active AnalysisDispatchService."""
    return AnalysisDispatchService(
        job_repo=get_job_repository(),
        session_repo=get_session_repository(),
        media_repo=get_media_repository(),
        dispatch_repo=get_dispatch_repository(),
        modal_client=get_modal_client(),
    )


def set_override_dispatch_repository(repo: Optional[WorkerDispatchRepository]) -> None:
    global _override_dispatch_repo
    _override_dispatch_repo = repo


def set_override_modal_client(client: Optional[ModalDispatchClient]) -> None:
    global _override_modal_client
    _override_modal_client = client


import hmac
from fastapi import Header, HTTPException, status
from backend.app.core.config import settings

_override_worker_secret: Optional[str] = None


def set_override_worker_secret(secret: Optional[str]) -> None:
    global _override_worker_secret
    _override_worker_secret = secret


def verify_worker_secret(
    x_worker_secret: Optional[str] = Header(None, alias="X-Worker-Secret"),
    authorization: Optional[str] = Header(None),
) -> None:
    """
    Authenticate internal worker progress callbacks via constant-time comparison.
    Accepts X-Worker-Secret header or Authorization: Bearer <secret>.
    Never exposes or logs secret contents.
    """
    expected = _override_worker_secret if _override_worker_secret is not None else settings.WORKER_CALLBACK_SECRET
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Worker callback authentication secret is not configured on server.",
        )

    provided = x_worker_secret
    if not provided and authorization and authorization.startswith("Bearer "):
        provided = authorization.split("Bearer ", 1)[1].strip()

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing worker callback secret.",
        )
