"""
Canonical Vision Schemas & Common Coordinate Space Contracts.
Governs all vision method adapter outputs, coordinate lifecycles, and identity boundaries.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Sections 1, 2)
"""
from __future__ import annotations
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field, model_validator


# =============================================================================
# 1. Coordinate Space Enumeration & Semantics
# =============================================================================

class CoordinateSpace(str, Enum):
    """
    Explicit coordinate spaces separating source media, working canvas, and model inference tensors.
    """
    MEDIA_SOURCE_SPACE = "MEDIA_SOURCE_SPACE"        # Native video container pixels (e.g. 3840x2160)
    VISION_WORKING_SPACE = "VISION_WORKING_SPACE"    # Fixed 1920x1080 tracking & homography canvas
    MODEL_INFERENCE_SPACE = "MODEL_INFERENCE_SPACE"  # Model tensor dimensions (e.g. 1280, 704)


class IdentityEvidenceBasis(str, Enum):
    """
    Evidence tier establishing identity attribution validity.
    """
    FORMAL_DENSE_GT = "FORMAL_DENSE_GT"            # Formal benchmark ground-truth identity scoring
    RUNTIME_HEURISTIC_ONLY = "RUNTIME_HEURISTIC_ONLY"  # Production runtime tracking heuristics
    HUMAN_ORACLE = "HUMAN_ORACLE"                  # Manually verified capability showcase evidence
    NONE = "NONE"


class FormalIdentityStatus(str, Enum):
    """
    Status of the methodology under formal scientific ground-truth evaluation.
    """
    FAIL_UNSAFE_MERGE = "FAIL_UNSAFE_MERGE"
    PASS_RELIABLE = "PASS_RELIABLE"
    UNCHECKED = "UNCHECKED"


class RuntimeIdentityStatus(str, Enum):
    """
    Runtime diagnostic heuristic classification for a specific uploaded video.
    MUST NOT be conflated with FormalIdentityStatus.
    """
    UNVERIFIED_HEURISTIC_PASS = "UNVERIFIED_HEURISTIC_PASS"
    UNVERIFIED_HEURISTIC_FAIL = "UNVERIFIED_HEURISTIC_FAIL"
    HEURISTIC_FRAGMENTATION_WARNING = "HEURISTIC_FRAGMENTATION_WARNING"
    UNCHECKED = "UNCHECKED"


# =============================================================================
# 2. Geometric Primitives
# =============================================================================

class BoundingBox(BaseModel):
    """
    Bounding box in MEDIA_SOURCE_SPACE coordinates [x1, y1, x2, y2].
    """
    x1: float = Field(..., description="Top-left x in source pixels")
    y1: float = Field(..., description="Top-left y in source pixels")
    x2: float = Field(..., description="Bottom-right x in source pixels")
    y2: float = Field(..., description="Bottom-right y in source pixels")
    source_width: Optional[float] = Field(None, description="Optional container width in source pixels")
    source_height: Optional[float] = Field(None, description="Optional container height in source pixels")
    coordinate_space: CoordinateSpace = Field(
        default=CoordinateSpace.MEDIA_SOURCE_SPACE,
        description="Target canonical coordinate space"
    )

    @model_validator(mode="after")
    def validate_box_coordinates(self) -> BoundingBox:
        if self.x1 < 0.0 or self.y1 < 0.0:
            raise ValueError(f"BoundingBox coordinates must be >= 0: ({self.x1}, {self.y1})")
        if self.x2 <= self.x1:
            raise ValueError(f"BoundingBox x2 ({self.x2}) must be strictly > x1 ({self.x1})")
        if self.y2 <= self.y1:
            raise ValueError(f"BoundingBox y2 ({self.y2}) must be strictly > y1 ({self.y1})")
        if self.source_width is not None and self.x2 > self.source_width:
            raise ValueError(f"BoundingBox x2 ({self.x2}) exceeds source_width ({self.source_width})")
        if self.source_height is not None and self.y2 > self.source_height:
            raise ValueError(f"BoundingBox y2 ({self.y2}) exceeds source_height ({self.source_height})")
        return self


class NormalizedBoundingBox(BaseModel):
    """
    Normalized bounding box in [0.0, 1.0] relative to frame width and height.
    Ordering strictly preserves [x1_norm, y1_norm, x2_norm, y2_norm].
    """
    x1_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized top-left x")
    y1_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized top-left y")
    x2_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom-right x")
    y2_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom-right y")

    @model_validator(mode="after")
    def validate_normalized_coordinates(self) -> NormalizedBoundingBox:
        if self.x2_norm <= self.x1_norm:
            raise ValueError(f"Normalized x2 ({self.x2_norm}) must be > x1 ({self.x1_norm})")
        if self.y2_norm <= self.y1_norm:
            raise ValueError(f"Normalized y2 ({self.y2_norm}) must be > y1 ({self.y1_norm})")
        return self


# =============================================================================
# 3. Provenance & Calibration Metadata
# =============================================================================

class MethodProvenance(BaseModel):
    """
    Cryptographic and algorithmic provenance of the vision methodology run.
    """
    methodology_id: str
    detector_checkpoint_sha256: str
    detector_checkpoint_path: Optional[str] = None
    detector_architecture: Optional[str] = None
    reid_checkpoint_sha256: Optional[str] = None
    reid_checkpoint_path: Optional[str] = None
    reid_architecture: Optional[str] = None
    operating_point: float
    tracker_parameters: Dict[str, Any] = Field(default_factory=dict)
    native_runner_output_space: CoordinateSpace = CoordinateSpace.VISION_WORKING_SPACE
    source_resolution: Tuple[int, int]  # (width, height)
    working_resolution: Tuple[int, int] = (1920, 1080)
    scale_factors: Tuple[float, float]  # (scale_x, scale_y)


class CalibrationReference(str, Enum):
    """
    Authoritative Calibration Reference categories per P0 REV2A permission matrix.
    """
    CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED = "CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED"
    GEOMETRIC_SOLVE_ONLY = "GEOMETRIC_SOLVE_ONLY"
    NO_METRIC_CALIBRATION = "NO_METRIC_CALIBRATION"
    INVALID_CALIBRATION = "INVALID_CALIBRATION"


class CalibrationPayload(BaseModel):
    """
    Detailed calibration state attached to vision results.
    """
    calibration_mode: CalibrationReference = CalibrationReference.NO_METRIC_CALIBRATION
    homography_sha256: Optional[str] = None
    rmse_m: Optional[float] = None
    pitch_length_m: Optional[float] = None
    pitch_width_m: Optional[float] = None
    is_metric_reporting_allowed: bool = False
    is_pitch_visualization_allowed: bool = False


# =============================================================================
# 4. Observation & Framewise Vision Schemas
# =============================================================================

class TrackObservation(BaseModel):
    """
    Individual tracked player observation within a single frame.
    
    SAFETY INVARIANT:
    opaque_track_id is an anonymous trajectory identifier only.
    It MUST NOT be interpreted as persistent physical-player identity.
    physical_player_pseudonym remains None unless HUMAN_ORACLE is verified.
    """
    opaque_track_id: int = Field(..., description="Method-local trajectory integer identifier")
    physical_player_pseudonym: Optional[str] = Field(
        default=None,
        description="Verified physical player pseudonym (strictly None for automated runs)"
    )
    bbox: BoundingBox
    bbox_norm: NormalizedBoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    frame_index: Optional[int] = Field(default=None, description="0-based frame index")
    timestamp_s: Optional[float] = Field(default=None, description="Timestamp in seconds")
    footpoint_x: Optional[float] = Field(default=None, description="Footpoint x coordinate")
    footpoint_y: Optional[float] = Field(default=None, description="Footpoint y coordinate")
    metric_x: Optional[float] = Field(default=None, description="Pitch metric x position")
    metric_y: Optional[float] = Field(default=None, description="Pitch metric y position")
    class_id: int = Field(default=0, description="Class identifier (0 = person)")
    tracklet_id: Optional[int] = Field(default=None, description="Pre-association tracklet ID (e.g. Deep-EIoU)")
    source_detection_id: Optional[str] = Field(default=None, description="Row-aligned raw detection identifier")
    identity_evidence_basis: IdentityEvidenceBasis = Field(
        default=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
        description="Evidence basis for identity attribution"
    )

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "box" in data and "bbox" not in data:
                data["bbox"] = data["box"]
            if "box_normalized" in data and "bbox_norm" not in data:
                data["bbox_norm"] = data["box_normalized"]
        return data

    @property
    def box(self) -> BoundingBox:
        return self.bbox

    @property
    def box_normalized(self) -> NormalizedBoundingBox:
        return self.bbox_norm

    @model_validator(mode="after")
    def validate_identity_safety(self) -> TrackObservation:
        if self.physical_player_pseudonym is not None and self.identity_evidence_basis != IdentityEvidenceBasis.HUMAN_ORACLE:
            raise ValueError(
                "physical_player_pseudonym must remain null for automated runs unless verified under HUMAN_ORACLE evidence basis."
            )
        return self


class FrameVisionResult(BaseModel):
    """
    Vision detection and tracking result for a single frame.
    """
    frame_index: int = Field(..., ge=0, description="0-based source video frame index")
    timestamp_s: float = Field(..., ge=0.0, description="Source video timestamp in seconds (frame_index / fps)")
    is_empty_frame: bool = Field(default=False, description="True if no players were detected")
    observations: List[TrackObservation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_empty_frame_consistency(self) -> FrameVisionResult:
        if self.is_empty_frame and len(self.observations) > 0:
            raise ValueError("is_empty_frame is True but observations list is non-empty")
        if len(self.observations) == 0:
            self.is_empty_frame = True
        return self


class SessionVisionResult(BaseModel):
    """
    Complete framewise tracking result for an entire processed video session.
    Enforces strict identity gating and coordinate provenance.
    """
    session_id: str
    job_id: str
    source_width: int = Field(..., gt=0)
    source_height: int = Field(..., gt=0)
    fps: float = Field(..., gt=0.0)
    total_frames: int = Field(..., ge=0)
    method_provenance: MethodProvenance
    coordinate_space: CoordinateSpace = CoordinateSpace.MEDIA_SOURCE_SPACE
    formal_identity_status: FormalIdentityStatus = FormalIdentityStatus.FAIL_UNSAFE_MERGE
    formal_identity_evidence_basis: IdentityEvidenceBasis = IdentityEvidenceBasis.FORMAL_DENSE_GT
    runtime_identity_status: RuntimeIdentityStatus = RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS
    runtime_identity_evidence_basis: IdentityEvidenceBasis = IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY
    player_level_analysis_allowed: bool = False
    withholding_reason: Optional[str] = (
        "Automated tracking methodology has not demonstrated sufficiently safe persistent "
        "physical-player identity under formal benchmark evaluation. Accumulated player-level analytics are withheld."
    )
    calibration: Optional[CalibrationReference] = None
    frames: List[FrameVisionResult] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def populate_session_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "provenance" in data and "method_provenance" not in data:
                data["method_provenance"] = data["provenance"]
            if "method_formal_identity_status" in data and "formal_identity_status" not in data:
                data["formal_identity_status"] = data["method_formal_identity_status"]
            if "method_formal_identity_evidence_basis" in data and "formal_identity_evidence_basis" not in data:
                data["formal_identity_evidence_basis"] = data["method_formal_identity_evidence_basis"]
            if "calibration_reference" in data and data.get("calibration") is None:
                data["calibration"] = data["calibration_reference"]
        return data

    @property
    def provenance(self) -> MethodProvenance:
        return self.method_provenance

    @property
    def method_formal_identity_status(self) -> FormalIdentityStatus:
        return self.formal_identity_status

    @property
    def method_formal_identity_evidence_basis(self) -> IdentityEvidenceBasis:
        return self.formal_identity_evidence_basis

    @property
    def calibration_reference(self) -> Optional[CalibrationReference]:
        return self.calibration

    @model_validator(mode="after")
    def enforce_identity_safety_gate(self) -> SessionVisionResult:
        """
        Enforce fail-closed withholding: automated runs MUST NOT have
        player_level_analysis_allowed=True or populate physical_player_pseudonym.
        """
        if (
            self.formal_identity_status != FormalIdentityStatus.PASS_RELIABLE
            and self.formal_identity_evidence_basis != IdentityEvidenceBasis.HUMAN_ORACLE
        ):
            if self.player_level_analysis_allowed:
                raise ValueError(
                    "player_level_analysis_allowed cannot be True when formal identity status is not PASS_RELIABLE"
                )
            for frame in self.frames:
                for obs in frame.observations:
                    if obs.physical_player_pseudonym is not None:
                        raise ValueError(
                            f"Automated session vision result contains unauthorized physical_player_pseudonym "
                            f"'{obs.physical_player_pseudonym}' for track {obs.opaque_track_id}"
                        )
        return self
