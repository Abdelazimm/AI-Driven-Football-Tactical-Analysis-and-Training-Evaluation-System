from __future__ import annotations
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MediaType(str, Enum):
    VIDEO = "VIDEO"
    COACH_AUDIO = "COACH_AUDIO"
    ANNOTATED_VIDEO = "ANNOTATED_VIDEO"
    REPORT = "REPORT"
    OTHER = "OTHER"


class UploadStatus(str, Enum):
    """
    Media asset upload and validation lifecycle.
    
    PENDING → UPLOADED → VALIDATING → VALIDATED   (happy path)
                                    → VALIDATION_FAILED (invalid media)
    PENDING → FAILED   (upload itself failed)
    
    Analysis jobs require VALIDATED status — UPLOADED alone is insufficient.
    """
    PENDING = "PENDING"
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    FAILED = "FAILED"


class MediaAsset(BaseModel):
    id: str = Field(..., description="Unique media asset UUID")
    session_id: str = Field(..., description="Associated session UUID")
    job_id: Optional[str] = Field(None, description="Associated analysis job UUID if linked")
    media_type: MediaType = Field(..., description="Category of media asset")
    storage_bucket: str = Field(..., description="Supabase storage bucket name")
    storage_path: str = Field(..., description="Relative storage path within bucket")
    original_filename: str = Field(..., description="User's original upload filename")
    mime_type: str = Field(..., description="MIME content type (client-declared, advisory)")
    size_bytes: int = Field(..., ge=0, description="Size in bytes")
    duration_seconds: Optional[float] = Field(None, ge=0.0, description="Duration in seconds (authoritative after validation)")
    width: Optional[int] = Field(None, gt=0, description="Native frame width (authoritative after validation)")
    height: Optional[int] = Field(None, gt=0, description="Native frame height (authoritative after validation)")
    fps: Optional[float] = Field(None, gt=0.0, description="Frame rate (authoritative after validation, NEVER hardcoded)")
    upload_status: UploadStatus = Field(default=UploadStatus.PENDING, description="Upload and validation lifecycle status")

    # Authoritative probe results (server-verified via ffprobe, NEVER client-declared)
    container_format: Optional[str] = Field(None, description="Probed container format, e.g. 'mov,mp4,m4a,3gp,3g2,mj2'")
    video_codec: Optional[str] = Field(None, description="Probed video codec, e.g. 'h264'")
    audio_codec: Optional[str] = Field(None, description="Probed audio codec, e.g. 'aac'")
    validation_status: Optional[str] = Field(None, description="ProbeStatus value from authoritative validation")
    validation_error_code: Optional[str] = Field(None, description="Typed validation error code if VALIDATION_FAILED")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
