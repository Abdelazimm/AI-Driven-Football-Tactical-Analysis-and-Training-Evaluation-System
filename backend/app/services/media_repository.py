"""
Media repository interfaces and implementations.
Handles persistence of uploaded videos, coach audio, and generated outputs.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime
from supabase import Client
from backend.app.schemas.media import MediaAsset, MediaType, UploadStatus


class MediaRepository(ABC):
    """Abstract interface for media asset persistence."""

    @abstractmethod
    def create_media_asset(self, asset: MediaAsset) -> MediaAsset:
        """Persist a newly registered media asset."""
        pass

    @abstractmethod
    def get_media_asset(self, media_id: str) -> Optional[MediaAsset]:
        """Retrieve media asset metadata by its unique UUID."""
        pass

    @abstractmethod
    def update_media_status(
        self,
        media_id: str,
        status: UploadStatus,
        size_bytes: Optional[int] = None
    ) -> Optional[MediaAsset]:
        """Update the upload status and optionally confirmed file size."""
        pass

    @abstractmethod
    def update_media_validation(
        self,
        media_id: str,
        *,
        upload_status: UploadStatus,
        duration_seconds: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
        container_format: Optional[str] = None,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
        validation_status: Optional[str] = None,
        validation_error_code: Optional[str] = None,
    ) -> Optional[MediaAsset]:
        """
        Persist authoritative probe validation results.
        Overwrites client-declared duration/width/height/fps with server-verified values.
        """
        pass

    @abstractmethod
    def link_job(self, media_id: str, job_id: str) -> Optional[MediaAsset]:
        """Link a media asset to an analysis job."""
        pass

    @abstractmethod
    def list_session_media(self, session_id: str) -> List[MediaAsset]:
        """List all media assets associated with a session."""
        pass


class SupabaseMediaRepository(MediaRepository):
    """Supabase PostgreSQL media asset repository implementation."""

    def __init__(self, client: Client):
        self._client = client

    def create_media_asset(self, asset: MediaAsset) -> MediaAsset:
        payload = {
            "id": asset.id,
            "session_id": asset.session_id,
            "job_id": asset.job_id,
            "media_type": asset.media_type.value,
            "storage_bucket": asset.storage_bucket,
            "storage_path": asset.storage_path,
            "original_filename": asset.original_filename,
            "mime_type": asset.mime_type,
            "size_bytes": asset.size_bytes,
            "duration_seconds": asset.duration_seconds,
            "width": asset.width,
            "height": asset.height,
            "fps": asset.fps,
            "upload_status": asset.upload_status.value,
            "container_format": asset.container_format,
            "video_codec": asset.video_codec,
            "audio_codec": asset.audio_codec,
            "validation_status": asset.validation_status,
            "validation_error_code": asset.validation_error_code,
            "created_at": asset.created_at.isoformat(),
            "updated_at": asset.updated_at.isoformat(),
        }
        res = self._client.table("media_assets").insert(payload).execute()
        if not res.data:
            raise RuntimeError(f"Failed to insert media asset into Supabase: {res}")
        return asset

    def get_media_asset(self, media_id: str) -> Optional[MediaAsset]:
        res = self._client.table("media_assets").select("*").eq("id", media_id).execute()
        if not res.data or len(res.data) == 0:
            return None
        row = res.data[0]
        return self._row_to_model(row)

    def update_media_status(
        self,
        media_id: str,
        status: UploadStatus,
        size_bytes: Optional[int] = None
    ) -> Optional[MediaAsset]:
        now = datetime.utcnow().isoformat()
        payload = {
            "upload_status": status.value,
            "updated_at": now,
        }
        if size_bytes is not None:
            payload["size_bytes"] = size_bytes

        res = self._client.table("media_assets").update(payload).eq("id", media_id).execute()
        if not res.data or len(res.data) == 0:
            return None
        return self._row_to_model(res.data[0])

    def update_media_validation(
        self,
        media_id: str,
        *,
        upload_status: UploadStatus,
        duration_seconds: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
        container_format: Optional[str] = None,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
        validation_status: Optional[str] = None,
        validation_error_code: Optional[str] = None,
    ) -> Optional[MediaAsset]:
        now = datetime.utcnow().isoformat()
        payload = {
            "upload_status": upload_status.value,
            "updated_at": now,
        }
        # Overwrite client-declared values with server-authoritative values
        if duration_seconds is not None:
            payload["duration_seconds"] = duration_seconds
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if fps is not None:
            payload["fps"] = fps
        if container_format is not None:
            payload["container_format"] = container_format
        if video_codec is not None:
            payload["video_codec"] = video_codec
        if audio_codec is not None:
            payload["audio_codec"] = audio_codec
        if validation_status is not None:
            payload["validation_status"] = validation_status
        if validation_error_code is not None:
            payload["validation_error_code"] = validation_error_code

        res = self._client.table("media_assets").update(payload).eq("id", media_id).execute()
        if not res.data or len(res.data) == 0:
            return None
        return self._row_to_model(res.data[0])

    def link_job(self, media_id: str, job_id: str) -> Optional[MediaAsset]:
        now = datetime.utcnow().isoformat()
        payload = {"job_id": job_id, "updated_at": now}
        res = self._client.table("media_assets").update(payload).eq("id", media_id).execute()
        if not res.data or len(res.data) == 0:
            return None
        return self._row_to_model(res.data[0])

    def list_session_media(self, session_id: str) -> List[MediaAsset]:
        res = self._client.table("media_assets").select("*").eq("session_id", session_id).execute()
        if not res.data:
            return []
        return [self._row_to_model(row) for row in res.data]

    def _row_to_model(self, row: dict) -> MediaAsset:
        return MediaAsset(
            id=row["id"],
            session_id=row["session_id"],
            job_id=row.get("job_id"),
            media_type=MediaType(row["media_type"]),
            storage_bucket=row["storage_bucket"],
            storage_path=row["storage_path"],
            original_filename=row["original_filename"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            duration_seconds=row.get("duration_seconds"),
            width=row.get("width"),
            height=row.get("height"),
            fps=row.get("fps"),
            upload_status=UploadStatus(row["upload_status"]),
            container_format=row.get("container_format"),
            video_codec=row.get("video_codec"),
            audio_codec=row.get("audio_codec"),
            validation_status=row.get("validation_status"),
            validation_error_code=row.get("validation_error_code"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
        )


class InMemoryMediaRepository(MediaRepository):
    """
    In-memory media asset repository implementation.
    FOR LOCAL CONTRACT AND UNIT TESTING ONLY.
    """

    def __init__(self):
        self._assets: Dict[str, MediaAsset] = {}

    def create_media_asset(self, asset: MediaAsset) -> MediaAsset:
        self._assets[asset.id] = asset
        return asset

    def get_media_asset(self, media_id: str) -> Optional[MediaAsset]:
        return self._assets.get(media_id)

    def update_media_status(
        self,
        media_id: str,
        status: UploadStatus,
        size_bytes: Optional[int] = None
    ) -> Optional[MediaAsset]:
        asset = self._assets.get(media_id)
        if not asset:
            return None
        updated_data = asset.model_dump()
        updated_data["upload_status"] = status
        updated_data["updated_at"] = datetime.utcnow()
        if size_bytes is not None:
            updated_data["size_bytes"] = size_bytes
        updated_asset = MediaAsset(**updated_data)
        self._assets[media_id] = updated_asset
        return updated_asset

    def update_media_validation(
        self,
        media_id: str,
        *,
        upload_status: UploadStatus,
        duration_seconds: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
        container_format: Optional[str] = None,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
        validation_status: Optional[str] = None,
        validation_error_code: Optional[str] = None,
    ) -> Optional[MediaAsset]:
        asset = self._assets.get(media_id)
        if not asset:
            return None
        updated_data = asset.model_dump()
        updated_data["upload_status"] = upload_status
        updated_data["updated_at"] = datetime.utcnow()
        if duration_seconds is not None:
            updated_data["duration_seconds"] = duration_seconds
        if width is not None:
            updated_data["width"] = width
        if height is not None:
            updated_data["height"] = height
        if fps is not None:
            updated_data["fps"] = fps
        if container_format is not None:
            updated_data["container_format"] = container_format
        if video_codec is not None:
            updated_data["video_codec"] = video_codec
        if audio_codec is not None:
            updated_data["audio_codec"] = audio_codec
        if validation_status is not None:
            updated_data["validation_status"] = validation_status
        if validation_error_code is not None:
            updated_data["validation_error_code"] = validation_error_code
        updated_asset = MediaAsset(**updated_data)
        self._assets[media_id] = updated_asset
        return updated_asset

    def link_job(self, media_id: str, job_id: str) -> Optional[MediaAsset]:
        asset = self._assets.get(media_id)
        if not asset:
            return None
        updated_data = asset.model_dump()
        updated_data["job_id"] = job_id
        updated_data["updated_at"] = datetime.utcnow()
        updated_asset = MediaAsset(**updated_data)
        self._assets[media_id] = updated_asset
        return updated_asset

    def list_session_media(self, session_id: str) -> List[MediaAsset]:
        return [a for a in self._assets.values() if a.session_id == session_id]

    def clear(self) -> None:
        self._assets.clear()
