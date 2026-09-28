from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class Detection(BaseModel):
    frame_index: int = Field(..., ge=0, description="0-indexed video frame number")
    timestamp_s: float = Field(..., ge=0.0, description="Timestamp in seconds from video start")
    x1: float = Field(..., description="Bounding box top-left x")
    y1: float = Field(..., description="Bounding box top-left y")
    x2: float = Field(..., description="Bounding box bottom-right x")
    y2: float = Field(..., description="Bounding box bottom-right y")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence score")
    class_id: int = Field(default=0, description="Class ID (0 = person)")
    track_id: Optional[int] = Field(None, description="Assigned short-term tracker ID")
    source_width: int = Field(..., description="Source frame width")
    source_height: int = Field(..., description="Source frame height")
    detector_manifest_id: Optional[str] = Field(None, description="Identifier of detector model used")
