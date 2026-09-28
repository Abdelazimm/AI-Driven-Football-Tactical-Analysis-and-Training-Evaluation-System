"""
Identity Safety Service & Decoupled Identity Gate.
Separates formal ground-truth evaluation from runtime heuristic diagnostics.
Enforces fail-closed withholding of individual player-level analytics for all automated runs.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 1)
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from backend.app.schemas.canonical_vision import (
    SessionVisionResult,
    FormalIdentityStatus,
    RuntimeIdentityStatus,
    IdentityEvidenceBasis,
)


class RuntimeIdentityDiagnostics(BaseModel):
    """Runtime heuristic identity diagnostics evaluated on uploaded media."""
    raw_track_ids_count: int = 0
    meaningful_ids_count: int = 0
    fragmentation_ratio: float = 1.0
    simultaneous_tracks_max: int = 6
    warnings: List[str] = Field(default_factory=list)


class IdentitySafetyAssessment(BaseModel):
    """
    Structured outcome of the identity safety evaluation.
    Decouples formal methodology evaluation from runtime heuristics.
    """
    method_formal_identity_status: FormalIdentityStatus = FormalIdentityStatus.FAIL_UNSAFE_MERGE
    method_formal_identity_evidence_basis: IdentityEvidenceBasis = IdentityEvidenceBasis.FORMAL_DENSE_GT
    runtime_identity_status: RuntimeIdentityStatus = RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS
    runtime_identity_evidence_basis: IdentityEvidenceBasis = IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY
    player_level_analysis_allowed: bool = False
    withholding_reason: Optional[str] = None
    total_distinct_tracks: int = 0
    max_simultaneous_tracks: int = 0
    mean_tracks_per_frame: float = 0.0
    heuristic_warnings: List[str] = Field(default_factory=list)


class IdentitySafetyService:
    """
    Service enforcing the scientific identity gate.
    
    CRITICAL SCIENTIFIC INVARIANT:
    Automated tracking (M1, M2, M3) remains FAIL_UNSAFE_MERGE under FORMAL_DENSE_GT.
    Runtime heuristics CANNOT unlock player-level analytics.
    The runtime must NOT claim the uploaded video itself was proven to contain an unsafe merge.
    """

    def __init__(self, expected_players: int = 6):
        self.expected_players = expected_players

    def evaluate_identity_safety(
        self,
        methodology: Optional[Any] = None,
        runtime_diagnostics: Optional[RuntimeIdentityDiagnostics] = None,
        is_oracle: bool = False,
    ) -> IdentitySafetyAssessment:
        """
        Evaluate identity safety from diagnostics and methodology.
        """
        if is_oracle:
            return IdentitySafetyAssessment(
                method_formal_identity_status=FormalIdentityStatus.PASS_RELIABLE,
                method_formal_identity_evidence_basis=IdentityEvidenceBasis.HUMAN_ORACLE,
                runtime_identity_status=RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS,
                runtime_identity_evidence_basis=IdentityEvidenceBasis.HUMAN_ORACLE,
                player_level_analysis_allowed=True,
                withholding_reason=None,
            )

        # Automated pipeline runs: FAIL-CLOSED WITHHOLDING
        if runtime_diagnostics and (runtime_diagnostics.fragmentation_ratio > 1.5 or runtime_diagnostics.warnings):
            runtime_status = RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_FAIL
        else:
            runtime_status = RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS

        withholding_text = (
            "The selected automated tracking methodology has not demonstrated sufficiently safe persistent "
            "physical-player identity under formal benchmark evaluation (dense-GT benchmark). Therefore, accumulated "
            "player-level analytics are withheld; runtime diagnostics on the current upload are heuristic only."
        )

        return IdentitySafetyAssessment(
            method_formal_identity_status=FormalIdentityStatus.FAIL_UNSAFE_MERGE,
            method_formal_identity_evidence_basis=IdentityEvidenceBasis.FORMAL_DENSE_GT,
            runtime_identity_status=runtime_status,
            runtime_identity_evidence_basis=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
            player_level_analysis_allowed=False,
            withholding_reason=withholding_text,
            total_distinct_tracks=runtime_diagnostics.raw_track_ids_count if runtime_diagnostics else 0,
            max_simultaneous_tracks=runtime_diagnostics.simultaneous_tracks_max if runtime_diagnostics else 0,
            heuristic_warnings=runtime_diagnostics.warnings if runtime_diagnostics else [],
        )

    def evaluate_session_identity(
        self,
        session_result: SessionVisionResult,
    ) -> IdentitySafetyAssessment:
        """
        Evaluate identity safety for a processed session.
        Calculates real runtime heuristics on the frame observations.
        """
        all_track_ids: Set[int] = set()
        max_simultaneous = 0
        frame_track_counts: List[int] = []

        for frame in session_result.frames:
            count = len(frame.observations)
            frame_track_counts.append(count)
            if count > max_simultaneous:
                max_simultaneous = count
            for obs in frame.observations:
                all_track_ids.add(obs.opaque_track_id)

        mean_tracks = (
            sum(frame_track_counts) / len(frame_track_counts)
            if frame_track_counts
            else 0.0
        )

        warnings: List[str] = []
        if len(all_track_ids) > self.expected_players * 2:
            warnings.append(
                f"Track count ({len(all_track_ids)}) significantly exceeds expected players ({self.expected_players}). "
                "Significant tracklet fragmentation observed."
            )
        if max_simultaneous > self.expected_players + 2:
            warnings.append(
                f"Peak simultaneous tracks ({max_simultaneous}) exceeds expected count ({self.expected_players}). "
                "Spurious false-positive tracks detected."
            )

        # Check if this is a verified human oracle demonstration
        is_oracle = (
            session_result.formal_identity_evidence_basis == IdentityEvidenceBasis.HUMAN_ORACLE
            and session_result.formal_identity_status == FormalIdentityStatus.PASS_RELIABLE
        )

        if is_oracle:
            return IdentitySafetyAssessment(
                method_formal_identity_status=FormalIdentityStatus.PASS_RELIABLE,
                method_formal_identity_evidence_basis=IdentityEvidenceBasis.HUMAN_ORACLE,
                runtime_identity_status=RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS,
                runtime_identity_evidence_basis=IdentityEvidenceBasis.HUMAN_ORACLE,
                player_level_analysis_allowed=True,
                withholding_reason=None,
                total_distinct_tracks=len(all_track_ids),
                max_simultaneous_tracks=max_simultaneous,
                mean_tracks_per_frame=round(mean_tracks, 2),
                heuristic_warnings=warnings,
            )

        # Automated pipeline runs: FAIL-CLOSED WITHHOLDING
        runtime_status = (
            RuntimeIdentityStatus.HEURISTIC_FRAGMENTATION_WARNING
            if warnings
            else RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS
        )

        withholding_text = (
            "The selected automated tracking methodology has not demonstrated sufficiently safe persistent "
            "physical-player identity under formal benchmark evaluation (dense-GT benchmark). Therefore, accumulated "
            "player-level analytics are withheld; runtime diagnostics on the current upload are heuristic only."
        )

        return IdentitySafetyAssessment(
            method_formal_identity_status=FormalIdentityStatus.FAIL_UNSAFE_MERGE,
            method_formal_identity_evidence_basis=IdentityEvidenceBasis.FORMAL_DENSE_GT,
            runtime_identity_status=runtime_status,
            runtime_identity_evidence_basis=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
            player_level_analysis_allowed=False,
            withholding_reason=withholding_text,
            total_distinct_tracks=len(all_track_ids),
            max_simultaneous_tracks=max_simultaneous,
            mean_tracks_per_frame=round(mean_tracks, 2),
            heuristic_warnings=warnings,
        )
