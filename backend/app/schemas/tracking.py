from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class TrackObservation(BaseModel):
    frame_index: int = Field(..., ge=0, description="0-indexed frame index")
    timestamp_s: float = Field(..., ge=0.0, description="Timestamp in seconds")
    track_id: int = Field(..., description="Short-term BoT-SORT track identifier")
    x1: float = Field(..., description="Bounding box x1")
    y1: float = Field(..., description="Bounding box y1")
    x2: float = Field(..., description="Bounding box x2")
    y2: float = Field(..., description="Bounding box y2")
    footpoint_x: float = Field(..., description="Tracking space footpoint x (midpoint of bottom edge)")
    footpoint_y: float = Field(..., description="Tracking space footpoint y (bottom edge)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    metric_x: Optional[float] = Field(None, description="Calibrated metric pitch position x in metres")
    metric_y: Optional[float] = Field(None, description="Calibrated metric pitch position y in metres")
