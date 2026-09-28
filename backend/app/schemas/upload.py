from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.schemas.media import MediaType


class UploadIntentRequest(BaseModel):
    media_type: MediaType = Field(..., description="Type of media asset to upload")
    filename: str = Field(..., description="Original filename of media asset")
    mime_type: str = Field(..., description="Client MIME content type")
    size_bytes: int = Field(..., gt=0, description="Declared file size in bytes")
    duration_seconds: Optional[float] = Field(None, ge=0.0, description="Probed duration in seconds")


class UploadIntentResponse(BaseModel):
    media_id: str = Field(..., description="Allocated media asset UUID")
    session_id: str = Field(..., description="Target session UUID")
    media_type: MediaType = Field(..., description="Type of media asset")
    storage_bucket: str = Field(..., description="Target Supabase storage bucket")
    storage_path: str = Field(..., description="Target storage path inside bucket")
    signed_upload_url: str = Field(..., description="Scoped signed upload URL for direct transfer")
    expires_in: int = Field(default=3600, description="Validity period of signed URL in seconds")


class CompleteUploadRequest(BaseModel):
    size_bytes: Optional[int] = Field(None, ge=0, description="Actual uploaded size in bytes if known")
