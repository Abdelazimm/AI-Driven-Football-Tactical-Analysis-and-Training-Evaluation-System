"""
Pipeline Stage: Identity Evaluation & Safety Gate.
Dispatches to IdentitySafetyService to enforce scientific identity gate semantics.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 1)
"""
from typing import List, Optional
from backend.app.schemas.tracking import TrackObservation
from backend.app.schemas.identity import IdentityEvaluation, IdentityStatus
from backend.app.schemas.canonical_vision import SessionVisionResult
from backend.app.services.identity_safety_service import (
    IdentitySafetyService,
    IdentitySafetyAssessment,
)


class IdentityGatePipeline:
    """
    Pipeline wrapper enforcing the scientific identity safety gate.
    """

    def __init__(self, acceptance_threshold: float = 1.5):
        self.acceptance_threshold = acceptance_threshold
        self._service = IdentitySafetyService()

    def evaluate_identity(
        self,
        observations: List[TrackObservation],
        expected_players: int = 6,
    ) -> IdentityEvaluation:
        """
        Evaluate tracklet observations and enforce fail-closed identity withholding.
        """
        unique_ids = {obs.track_id for obs in observations} if observations else set()
        raw_count = len(unique_ids)
        frag_ratio = float(raw_count) / float(expected_players) if expected_players > 0 else 0.0

        is_reliable = (
            frag_ratio <= self.acceptance_threshold and raw_count == expected_players
        )

        withholding_text = (
            "Automated tracking methodology has not demonstrated sufficiently safe persistent "
            "physical-player identity under formal benchmark evaluation. Accumulated player-level analytics are withheld."
        )

        return IdentityEvaluation(
            identity_status=IdentityStatus.FAIL_HIGH_FRAGMENTATION if not is_reliable else IdentityStatus.PASS_RELIABLE,
            player_level_analysis_allowed=False,  # Automated runs strictly false
            withholding_reason=withholding_text,
            raw_track_ids=raw_count,
            meaningful_identities=expected_players,
            fragmentation_ratio=round(frag_ratio, 4),
            acceptance_threshold=self.acceptance_threshold,
        )

    def evaluate_session(
        self,
        session_result: SessionVisionResult,
    ) -> IdentitySafetyAssessment:
        """
        Evaluate full canonical session vision result.
        """
        return self._service.evaluate_session_identity(session_result)
