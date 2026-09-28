from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field
from backend.app.schemas.confidence import MetricConfidence


class MovementMetric(BaseModel):
    name: str = Field(..., description="Name of the movement metric")
    value: Optional[float] = Field(None, description="Physical measured value (null if uncalibrated/withheld)")
    unit: str = Field(..., description="Measurement unit (e.g. 'm', 'km/h', 'px')")
    confidence: MetricConfidence = Field(..., description="Metric calibration confidence")
    calibration_id: Optional[str] = Field(None, description="Associated calibration record identifier")
    display_value: str = Field(..., description="Human-readable formatted display string")
    limitations: List[str] = Field(default_factory=list, description="Applicable limitations or caveats")
