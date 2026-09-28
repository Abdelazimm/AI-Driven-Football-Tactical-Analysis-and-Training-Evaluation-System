"""
Methodology endpoints.
Exposes canonical computer-vision pipeline configuration metadata.
"""
from typing import List
from fastapi import APIRouter
from backend.app.schemas.methodology import (
    MethodologyId,
    MethodologyMetadata,
    MethodologyAvailability,
)

router = APIRouter(prefix="/methodologies", tags=["methodologies"])

CANONICAL_METHODOLOGIES: List[MethodologyMetadata] = [
    MethodologyMetadata(
        id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
        display_name="Original Hybrid",
        short_description="Hybrid player detection, short-term tracking and constrained tracklet reconciliation.",
        pipeline_summary=["YOLO11m", "BoT-SORT", "Constrained Reconciliation"],
        availability=MethodologyAvailability.EXPERIMENTAL,
        available=False,
        availability_reason="Original project methodology. Formal Method 1 comparative implementation and validation are in progress.",
    ),
    MethodologyMetadata(
        id=MethodologyId.METHOD_2_RFDETR_GTATRACK,
        display_name="Global Association",
        short_description="Transformer-based detection with sports-oriented tracking and global tracklet association.",
        pipeline_summary=["RF-DETR-L", "Deep-EIoU", "GTA"],
        availability=MethodologyAvailability.EXPERIMENTAL,
        available=False,
        availability_reason="Transformer tracking adapter in development; planned for future deployment.",
    ),
    MethodologyMetadata(
        id=MethodologyId.METHOD_3_YOLO26_SRITRACK,
        display_name="Re-entry Focused",
        short_description="Re-entry-focused sports tracking designed to improve player identity recovery after frame re-entry.",
        pipeline_summary=["YOLO26m", "SRITrack", "DINOv3 ReID"],
        availability=MethodologyAvailability.EXPERIMENTAL,
        available=False,
        availability_reason="Re-entry tracking pipeline in evaluation; planned for future deployment.",
    ),
]


@router.get("", response_model=List[MethodologyMetadata])
def list_methodologies() -> List[MethodologyMetadata]:
    """
    List configured computer-vision methodologies.
    Returns operational readiness status without scientific rankings or fabricated benchmarks.
    """
    return CANONICAL_METHODOLOGIES
