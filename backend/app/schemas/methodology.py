from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class MethodologyId(str, Enum):
    """
    Canonical computer-vision methodology identifiers.

    MethodologyId describes WHICH detection/tracking pipeline processes a session.
    This is separate from ApplicationMode, which describes HOW the application operates.
    """
    METHOD_1_YOLO11_BOTSORT = "METHOD_1_YOLO11_BOTSORT"
    METHOD_2_RFDETR_GTATRACK = "METHOD_2_RFDETR_GTATRACK"
    METHOD_3_YOLO26_SRITRACK = "METHOD_3_YOLO26_SRITRACK"


AUTO_METHODOLOGY_TARGET = "AUTO"


class MethodologyAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    EXPERIMENTAL = "EXPERIMENTAL"


class MethodologyMetadata(BaseModel):
    """
    Methodology metadata for the GET /api/v1/methodologies endpoint.

    No methodology may be marked as "best".
    No invented scientific performance claims.
    """
    id: MethodologyId = Field(..., description="Canonical methodology identifier")
    display_name: str = Field(..., description="User-facing methodology name")
    short_description: str = Field(..., description="Brief methodology description")
    pipeline_summary: List[str] = Field(default_factory=list, description="Ordered pipeline component names")
    availability: MethodologyAvailability = Field(
        default=MethodologyAvailability.AVAILABLE,
        description="Operational readiness level"
    )
    available: bool = Field(default=True, description="Whether this methodology is currently runnable")
    availability_reason: Optional[str] = Field(None, description="Explanation when unavailable or experimental")

