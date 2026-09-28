"""
Dynamic Job Execution Manifest Schema.
Records authoritative per-job runtime metadata, cryptographic checkpoint provenance,
decoupled identity assurance states, and conditional calibration references.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 7)
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, model_validator

from backend.app.schemas.canonical_vision import (
    FormalIdentityStatus,
    RuntimeIdentityStatus,
    IdentityEvidenceBasis,
)


class MediaProbedMetadata(BaseModel):
    """
    Authoritative media metadata probed dynamically from the container via ffprobe.
    NEVER populated with universal research session constants.
    """
    source_media_sha256: Optional[str] = Field(None, description="SHA-256 of raw media file")
    duration_s: float = Field(..., gt=0.0, description="Actual probed video duration in seconds")
    fps: float = Field(..., gt=0.0, description="Actual probed video framerate")
    resolution_width: int = Field(..., gt=0, description="Container frame width in pixels")
    resolution_height: int = Field(..., gt=0, description="Container frame height in pixels")
    container_format: str = Field(..., description="Container format (e.g. mov, mp4)")
    video_codec: Optional[str] = Field(None, description="Video codec name (e.g. h264, hevc)")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "width" in data and "resolution_width" not in data:
                data["resolution_width"] = data["width"]
            if "height" in data and "resolution_height" not in data:
                data["resolution_height"] = data["height"]
            if "container" in data and "container_format" not in data:
                data["container_format"] = data["container"]
        return data

    @property
    def width(self) -> int:
        return self.resolution_width

    @property
    def height(self) -> int:
        return self.resolution_height

    @property
    def container(self) -> str:
        return self.container_format


class ManifestMethodologyProvenance(BaseModel):
    """
    Formal methodology configuration and checkpoint integrity.
    """
    requested_methodology: str
    resolved_methodology: str
    method_formal_identity_status: FormalIdentityStatus = FormalIdentityStatus.FAIL_UNSAFE_MERGE
    method_formal_identity_evidence_basis: IdentityEvidenceBasis = IdentityEvidenceBasis.FORMAL_DENSE_GT
    detector_checkpoint: Optional[str] = None
    detector_sha256: Optional[str] = None
    detector_size_bytes: Optional[int] = None
    reid_checkpoint: Optional[str] = None
    reid_sha256: Optional[str] = None
    reid_size_bytes: Optional[int] = None
    tracker_config: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def populate_methodology_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "requested" in data and "requested_methodology" not in data:
                data["requested_methodology"] = str(
                    data["requested"].value if hasattr(data["requested"], "value") else data["requested"]
                )
            if "resolved" in data and "resolved_methodology" not in data:
                data["resolved_methodology"] = str(
                    data["resolved"].value if hasattr(data["resolved"], "value") else data["resolved"]
                )
        return data


class ManifestRuntimeDiagnostics(BaseModel):
    """
    Runtime diagnostics measured on the specific uploaded video.
    Separated from formal ground-truth evaluation.
    """
    runtime_identity_status: RuntimeIdentityStatus = RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS
    runtime_identity_evidence_basis: IdentityEvidenceBasis = IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY
    player_level_analysis_allowed: bool = False
    withholding_reason: Optional[str] = Field(
        default=(
            "Automated tracking methodology has not demonstrated sufficiently safe persistent "
            "physical-player identity under formal benchmark evaluation. Accumulated player-level analytics are withheld."
        ),
        description="Explicit limitation text explaining why player-specific metrics are withheld"
    )
    observed_track_count: Optional[int] = None
    empty_frame_count: Optional[int] = None


class ManifestCalibrationMetadata(BaseModel):
    """
    Conditional calibration metadata.
    Fields remain null unless calibration was actively provided/validated.
    """
    calibration_mode: str = "NO_METRIC_CALIBRATION"
    homography_sha256: Optional[str] = Field(None, description="SHA-256 of homography matrix, or None")
    rmse_m: Optional[float] = Field(None, description="Independent validation RMSE, or None")
    pitch_dimensions_m: Optional[Tuple[float, float]] = None
    is_metric_reporting_allowed: bool = False
    is_pitch_visualization_allowed: bool = False

    @model_validator(mode="before")
    @classmethod
    def populate_mode(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "mode" in data and "calibration_mode" not in data:
                data["calibration_mode"] = str(data["mode"].value if hasattr(data["mode"], "value") else data["mode"])
        return data

    @property
    def mode(self) -> str:
        return self.calibration_mode


class JobExecutionManifest(BaseModel):
    """
    Dynamic per-job execution manifest capturing real media properties,
    methodology provenance, and runtime outcomes.
    """
    job_id: str
    session_id: str
    input_asset_role: Optional[str] = None
    authoritative_source_sha256: Optional[str] = Field(None, pattern=r"^[0-9a-f]{64}$")
    transport_copy_sha256: Optional[str] = Field(None, pattern=r"^[0-9a-f]{64}$")
    execution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    media_metadata: MediaProbedMetadata
    methodology: ManifestMethodologyProvenance
    runtime_diagnostics: ManifestRuntimeDiagnostics = Field(default_factory=ManifestRuntimeDiagnostics)
    calibration_metadata: ManifestCalibrationMetadata = Field(default_factory=ManifestCalibrationMetadata)
    artifact_registry: Dict[str, str] = Field(default_factory=dict)
