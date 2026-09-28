"""
Pipeline Stage: Grounded Report Generation & Deterministic Fallback.
Governed by:
- P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A (Contract Suites 22, 23, 24, 25)
- LLM_FINAL_INTEGRATION_FREEZE.json
- LLM_GROUNDING_VALIDATOR_PATCH_001.md

Responsibilities:
- Ingest typed StructuredEvidencePayload from Multimodal Fusion (Phase 3)
- Execute frozen Llama 3.1 8B report generation via Ollama with 120s timeout and zero retries
- Pass candidate reports through LLM_GROUNDING_VALIDATOR_PATCH_001 (all 8 deterministic gates)
- Deliver VALIDATED_LLM_REPORT on grounding success
- Deliver DETERMINISTIC_FALLBACK on timeout, network error, schema error, or validator rejection
- Zero awareness of raw YOLO tensors, RF-DETR internals, tracker state, or Whisper audio buffers
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from backend.app.pipeline.evidence import StructuredEvidencePayload
from backend.app.schemas.confidence import ReportStatus
from backend.app.schemas.report import GeneratedCoachReport
from backend.app.services.deterministic_report_service import DeterministicReportService
from backend.app.services.grounding_validator import Patch001GroundingValidator
from backend.app.services.llm_report_service import LLMReportService

# Blocker 4 / LLM Timeout Contract
# Authoritative value: FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120 seconds.
# Default production timeout is 120 s; overrideable via LLM_TIMEOUT_SECONDS environment variable.
# Any documentation referencing 45 s as the timeout is superseded by this contract.
FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS: int = 120
DEFAULT_PRODUCTION_TIMEOUT_SECONDS: int = 120


class ReportingPipeline:
    """
    Production reporting pipeline orchestrating grounded LLM generation
    and deterministic fallback without cross-pipeline leakage.
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:11434",
        force_fallback: bool = False,
        timeout_seconds: Optional[int] = None,
        llm_service: Optional[LLMReportService] = None,
        fallback_service: Optional[DeterministicReportService] = None,
        validator: Optional[Patch001GroundingValidator] = None,
    ):
        self.force_fallback = force_fallback
        self.validator = validator or Patch001GroundingValidator()
        self.fallback_service = fallback_service or DeterministicReportService()
        self.llm_service = llm_service or LLMReportService(
            endpoint=endpoint,
            timeout_seconds=timeout_seconds,
            validator=self.validator,
            fallback_service=self.fallback_service,
        )

    def generate_report(
        self,
        evidence: Union[StructuredEvidencePayload, Dict[str, Any]],
        job_id: Optional[str] = None,
        force_fallback: bool = False,
    ) -> GeneratedCoachReport:
        """
        Generates a verified coaching report from structured evidence.
        Returns a typed GeneratedCoachReport object.
        """
        # If forced fallback is requested (e.g. testing or explicit config)
        if self.force_fallback or force_fallback:
            if hasattr(evidence, "model_dump"):
                data = evidence.model_dump()
            else:
                data = dict(evidence)

            fallback_md = self.fallback_service.generate_report(
                data, fallback_reason="FORCED_DETERMINISTIC_FALLBACK"
            )
            return GeneratedCoachReport(
                session_id=data.get("session_id", "UNKNOWN"),
                job_id=job_id,
                methodology_id=data.get("methodology_id", "METHOD_2_RFDETR_GTATRACK"),
                calibration_mode=data.get("calibration_mode", "NO_METRIC_CALIBRATION"),
                player_level_analysis_allowed=data.get("player_level_analysis_allowed", False),
                report_status=ReportStatus.DETERMINISTIC_FALLBACK,
                report_markdown=fallback_md,
                fallback_reason="FORCED_DETERMINISTIC_FALLBACK",
            )

        # Standard grounded execution via LLMReportService
        return self.llm_service.generate_report(evidence, job_id=job_id)
