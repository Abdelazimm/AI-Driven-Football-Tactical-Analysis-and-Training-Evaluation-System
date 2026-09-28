"""
Pipeline Stage: Deterministic Evidence Generation & Machine-Validatable Schema.
Governed by P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A and Implementation Phase 3 rules.

Scientific Invariants:
1. Machine-validatable typed evidence contracts.
2. Evidence scopes: TEAM, SPATIAL, EVENT, ANONYMOUS_TRACK.
   PLAYER scope is strictly prohibited for automated runs (fails closed when identity is unsafe).
3. Calibration-gated metric units: metres and km/h emitted ONLY when independently validated.
4. Kinematics-aware: gap resets (>0.50s) and outlier rejection (>36 km/h) respected.
5. Missing values remain explicitly None; no fabricated defaults or historical constants.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.canonical_vision import CalibrationReference
from backend.app.schemas.limitation import AnalysisLimitation


EvidenceScope = Literal["TEAM", "SPATIAL", "EVENT", "ANONYMOUS_TRACK", "PLAYER"]


class StructuredEvidenceItem(BaseModel):
    """
    Machine-validatable typed evidence item representing visual and kinematic
    observations during the post-command reaction window [t_end + 2.0s, t_end + 6.0s].
    """
    evidence_id: str = Field(..., description="Unique evidence item identifier, e.g. 'ev_evt0_track3'")
    scope: EvidenceScope = Field(..., description="Evidence scope: TEAM, SPATIAL, EVENT, ANONYMOUS_TRACK, or PLAYER")
    source_event_id: str = Field(..., description="ID of the motivating tactical event from ASR")
    event_category: str = Field(..., description="Tactical category from frozen taxonomy")
    event_action: str = Field(..., description="Matched tactical keyword")
    window_start_s: float = Field(..., ge=0.0, description="Reaction evaluation start timestamp (t_end + 2.0s)")
    window_end_s: float = Field(..., ge=0.0, description="Reaction evaluation end timestamp (t_end + 6.0s)")

    # Anonymous / Spatial / Team descriptors
    anonymous_track_id: Optional[str] = Field(None, description="Opaque method-local track ID, e.g. 'track_3'")
    team_context: Optional[str] = Field(None, description="Team-level movement context, e.g. 'team_centroid'")
    spatial_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pitch or bounding-box spatial coordinates")
    zone: Optional[str] = Field(None, description="Pitch third or tactical zone")

    # Kinematics metrics (None when non-metric or invalid)
    displacement_m: Optional[float] = Field(None, ge=0.0, description="Physical displacement in metres (null if non-metric)")
    speed_kmh: Optional[float] = Field(None, ge=0.0, le=36.0, description="Peak or mean speed in km/h (null if non-metric or outlier)")
    direction_deg: Optional[float] = Field(None, ge=0.0, lt=360.0, description="Displacement heading in degrees [0, 360)")
    retention_metric: Optional[float] = Field(None, ge=0.0, description="Position retention metric for hold ground commands")
    distance_to_target_m: Optional[float] = Field(None, ge=0.0, description="Physical distance to nearest target in metres")

    # Governance & Provenance
    calibration_mode: str = Field(..., description="Operating calibration mode")
    metric_units_allowed: bool = Field(..., description="True only if calibration mode permits metric units")
    identity_evidence_basis: str = Field(..., description="Identity safety gate evidence basis")
    observations_count: int = Field(0, ge=0, description="Number of visual track observations in response window")
    source_provenance: Dict[str, Any] = Field(default_factory=dict, description="Methodology and model provenance")
    missing_fields: List[str] = Field(default_factory=list, description="Fields unavailable due to limitations")
    limitations: List[str] = Field(default_factory=list, description="Explicit scientific limitations for this evidence item")


class StructuredEvidencePayload(BaseModel):
    """
    Session-level multimodal structured evidence payload ready for downstream
    grounded LLM report generation (Phase 4).
    """
    session_id: str = Field(..., description="Unique session identifier")
    methodology_id: str = Field(..., description="Vision methodology identifier (e.g. METHOD_2_YOLO11_DEEP_EIOU)")
    calibration_mode: str = Field(..., description="Operating calibration mode")
    metric_units_allowed: bool = Field(..., description="Whether metric units (metres, km/h) are permitted")
    player_level_analysis_allowed: bool = Field(default=False, description="Whether persistent player analysis is allowed (false for automated runs)")
    identity_evidence_basis: str = Field(..., description="Identity safety gate evidence basis")
    total_tactical_events: int = Field(..., ge=0, description="Total ASR tactical events processed")
    evidence_items: List[StructuredEvidenceItem] = Field(default_factory=list, description="List of structured evidence items")
    global_limitations: List[str] = Field(default_factory=list, description="Global session limitations")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Session execution provenance")


class EvidencePipeline:
    """
    Service responsible for assembling, validating, and structuring multimodal evidence.
    Enforces fail-closed rules and guarantees machine-validatable payloads.
    """

    def assemble_evidence(
        self,
        session_id: str,
        methodology_id: str,
        calibration_mode: str,
        metric_units_allowed: bool,
        player_level_analysis_allowed: bool,
        identity_evidence_basis: str,
        evidence_items: List[StructuredEvidenceItem],
        global_limitations: Optional[List[str]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> StructuredEvidencePayload:
        """
        Assembles and validates a structured evidence payload.
        Enforces that PLAYER scope is never emitted for automated runs.
        """
        limitations = list(global_limitations or [])

        # Validate fail-closed identity constraint
        if not player_level_analysis_allowed:
            for item in evidence_items:
                if item.scope == "PLAYER":
                    raise ValueError(
                        f"Prohibited PLAYER scope in automated evidence item '{item.evidence_id}'. "
                        "When player_level_analysis_allowed is False, scopes must be TEAM, SPATIAL, EVENT, or ANONYMOUS_TRACK."
                    )

        # Validate metric units permission constraint
        if not metric_units_allowed:
            for item in evidence_items:
                if item.displacement_m is not None or item.speed_kmh is not None or item.distance_to_target_m is not None:
                    raise ValueError(
                        f"Prohibited metric values in non-metric evidence item '{item.evidence_id}'. "
                        "When metric_units_allowed is False, displacement_m, speed_kmh, and distance_to_target_m must be null."
                    )

        return StructuredEvidencePayload(
            session_id=session_id,
            methodology_id=methodology_id,
            calibration_mode=calibration_mode,
            metric_units_allowed=metric_units_allowed,
            player_level_analysis_allowed=player_level_analysis_allowed,
            identity_evidence_basis=identity_evidence_basis,
            total_tactical_events=len({item.source_event_id for item in evidence_items if item.source_event_id}),
            evidence_items=evidence_items,
            global_limitations=limitations,
            provenance=provenance or {},
        )
