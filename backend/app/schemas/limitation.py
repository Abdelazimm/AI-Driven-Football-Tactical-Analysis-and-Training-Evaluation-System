from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AnalysisLimitation(BaseModel):
    code: str = Field(..., description="Machine-readable limitation code")
    category: Literal["IDENTITY", "CALIBRATION", "TARGET_RESOLUTION", "AUDIO_QUALITY", "MODEL_GROUNDING"] = Field(
        ...,
        description="Category of the limitation"
    )
    severity: Literal["INFO", "WARNING", "CRITICAL"] = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable limitation summary")
    technical_details: Optional[str] = Field(None, description="Detailed scientific or technical explanation")
