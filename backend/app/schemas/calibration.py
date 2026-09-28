from __future__ import annotations
from typing import Optional, List, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.modes import CalibrationMode
from backend.app.schemas.confidence import MetricConfidence


class Calibration(BaseModel):
    id: str = Field(..., description="Unique calibration identifier")
    session_id: str = Field(..., description="Associated session identifier")
    mode: CalibrationMode = Field(..., description="Calibration mode")
    confidence: MetricConfidence = Field(..., description="Confidence assessment level")
    pitch_length_m: float = Field(..., gt=0.0, description="Pitch length in metres")
    pitch_width_m: float = Field(..., gt=0.0, description="Pitch width in metres")
    homography_matrix: Optional[List[List[float]]] = Field(None, description="3x3 planar perspective transform matrix")
    landmark_rmse_m: Optional[float] = Field(None, description="Independent landmark RMSE in metres")
    source_resolution: Tuple[int, int] = Field(..., description="Source video frame dimensions (width, height)")
    tracking_resolution: Tuple[int, int] = Field(..., description="Tracking frame dimensions (width, height)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
