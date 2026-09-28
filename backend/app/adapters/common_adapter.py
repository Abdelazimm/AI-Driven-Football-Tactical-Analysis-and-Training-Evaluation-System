"""
Common Vision Adapter Infrastructure & Geometric Transformation Helpers.
Provides coordinate transformations between VISION_WORKING_SPACE (1920x1080)
and MEDIA_SOURCE_SPACE (dynamic), coordinate normalization, and empty frame creation.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Sections 1, 2)
"""
from __future__ import annotations
from typing import Tuple, List, Optional, Dict, Any

from backend.app.schemas.canonical_vision import (
    CoordinateSpace,
    BoundingBox,
    NormalizedBoundingBox,
    TrackObservation,
    FrameVisionResult,
    SessionVisionResult,
    MethodProvenance,
    FormalIdentityStatus,
    RuntimeIdentityStatus,
    IdentityEvidenceBasis,
    CalibrationReference,
)


def validate_source_metadata(
    source_width: int,
    source_height: int,
    fps: float,
    total_frames: int,
) -> None:
    """
    Validate that media container dimensions and timebase are physically valid.
    """
    if source_width <= 0 or source_height <= 0:
        raise ValueError(f"Invalid source resolution: {source_width}x{source_height}")
    if fps <= 0.0:
        raise ValueError(f"Invalid source FPS: {fps}")
    if total_frames < 0:
        raise ValueError(f"Invalid total frame count: {total_frames}")


def project_box_working_to_source(
    box_working: Tuple[float, float, float, float],
    source_width: int,
    source_height: int,
    working_width: int = 1920,
    working_height: int = 1080,
) -> BoundingBox:
    """
    Project bounding box from VISION_WORKING_SPACE (1920x1080) to MEDIA_SOURCE_SPACE.
    Enforces coordinate boundaries and prevents double-scaling.
    
    Formula:
        scale_x = source_width / working_width
        scale_y = source_height / working_height
    """
    scale_x = float(source_width) / float(working_width)
    scale_y = float(source_height) / float(working_height)

    wx1, wy1, wx2, wy2 = box_working
    
    # Clip working coordinates to working canvas first
    wx1 = max(0.0, min(float(working_width), float(wx1)))
    wy1 = max(0.0, min(float(working_height), float(wy1)))
    wx2 = max(0.0, min(float(working_width), float(wx2)))
    wy2 = max(0.0, min(float(working_height), float(wy2)))

    # Project to source resolution
    sx1 = wx1 * scale_x
    sy1 = wy1 * scale_y
    sx2 = wx2 * scale_x
    sy2 = wy2 * scale_y

    # Ensure strictly valid positive box area
    sx1 = max(0.0, min(float(source_width) - 1.0, sx1))
    sy1 = max(0.0, min(float(source_height) - 1.0, sy1))
    sx2 = max(sx1 + 1.0, min(float(source_width), sx2))
    sy2 = max(sy1 + 1.0, min(float(source_height), sy2))

    return BoundingBox(
        x1=round(sx1, 2),
        y1=round(sy1, 2),
        x2=round(sx2, 2),
        y2=round(sy2, 2),
        coordinate_space=CoordinateSpace.MEDIA_SOURCE_SPACE,
    )


def compute_normalized_box(
    box_source: Optional[BoundingBox] = None,
    source_width: int = 1920,
    source_height: int = 1080,
    x1: Optional[float] = None,
    y1: Optional[float] = None,
    x2: Optional[float] = None,
    y2: Optional[float] = None,
) -> NormalizedBoundingBox:
    """
    Compute normalized coordinates [0.0, 1.0] from a MEDIA_SOURCE_SPACE BoundingBox or raw box coordinates.
    """
    if box_source is not None:
        bx1, by1, bx2, by2 = box_source.x1, box_source.y1, box_source.x2, box_source.y2
    elif x1 is not None and y1 is not None and x2 is not None and y2 is not None:
        bx1, by1, bx2, by2 = float(x1), float(y1), float(x2), float(y2)
    else:
        raise ValueError("Must provide either box_source or all of (x1, y1, x2, y2)")

    x1_norm = max(0.0, min(1.0, bx1 / float(source_width)))
    y1_norm = max(0.0, min(1.0, by1 / float(source_height)))
    x2_norm = max(0.0, min(1.0, bx2 / float(source_width)))
    y2_norm = max(0.0, min(1.0, by2 / float(source_height)))

    # Ensure strictly valid ordering for normalized coordinates
    if x2_norm <= x1_norm:
        x2_norm = min(1.0, x1_norm + 1e-4)
    if y2_norm <= y1_norm:
        y2_norm = min(1.0, y1_norm + 1e-4)

    return NormalizedBoundingBox(
        x1_norm=round(x1_norm, 6),
        y1_norm=round(y1_norm, 6),
        x2_norm=round(x2_norm, 6),
        y2_norm=round(y2_norm, 6),
    )


def create_empty_frame(
    frame_index: int,
    fps: Optional[float] = None,
    timestamp_s: Optional[float] = None,
) -> FrameVisionResult:
    """
    Create a valid empty FrameVisionResult for frames where no players were detected.
    Ensures stability and continuity without crashing downstream stages.
    """
    if timestamp_s is not None:
        ts = round(float(timestamp_s), 4)
    elif fps is not None and fps > 0.0:
        ts = round(frame_index / fps, 4)
    else:
        ts = 0.0

    return FrameVisionResult(
        frame_index=frame_index,
        timestamp_s=ts,
        is_empty_frame=True,
        observations=[],
    )


def build_track_observation(
    opaque_track_id: int,
    box_working: Tuple[float, float, float, float],
    confidence: float,
    source_width: int,
    source_height: int,
    working_width: int = 1920,
    working_height: int = 1080,
    class_id: int = 0,
    tracklet_id: Optional[int] = None,
    source_detection_id: Optional[str] = None,
    physical_player_pseudonym: Optional[str] = None,
) -> TrackObservation:
    """
    Construct a validated TrackObservation by projecting working-space coordinates
    to MEDIA_SOURCE_SPACE and generating normalized bounds.
    """
    bbox = project_box_working_to_source(
        box_working=box_working,
        source_width=source_width,
        source_height=source_height,
        working_width=working_width,
        working_height=working_height,
    )
    bbox_norm = compute_normalized_box(
        box_source=bbox,
        source_width=source_width,
        source_height=source_height,
    )
    return TrackObservation(
        opaque_track_id=int(opaque_track_id),
        physical_player_pseudonym=physical_player_pseudonym,
        bbox=bbox,
        bbox_norm=bbox_norm,
        confidence=round(float(confidence), 4),
        class_id=int(class_id),
        tracklet_id=tracklet_id,
        source_detection_id=source_detection_id,
    )
