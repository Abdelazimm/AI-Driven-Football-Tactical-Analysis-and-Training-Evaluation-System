from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    duration_seconds: float = Field(..., ge=0.0, le=360.0, description="Video duration in seconds (max 360s)")
    width: int = Field(..., gt=0, description="Native frame width")
    height: int = Field(..., gt=0, description="Native frame height")
    fps: float = Field(..., gt=0.0, description="Dynamically extracted frames per second")
    total_frames: int = Field(..., ge=0, description="Total frame count")
    codec: str = Field(..., description="Video codec name")
    format: str = Field(..., description="Container format name")
    file_size_bytes: int = Field(..., gt=0, description="File size in bytes")
    has_audio: bool = Field(..., description="Flag indicating presence of audio stream")
    checksum_sha256: Optional[str] = Field(None, description="SHA-256 hash of raw video payload")
