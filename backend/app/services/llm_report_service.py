"""
Production LLM Coaching Report Service.
Invokes local Ollama with frozen Meta-Llama-3.1-8B-Instruct (llama3.1:8b),
verifies exact model digest and system prompt hash, enforces 120s timeout,
and passes candidate reports to LLM_GROUNDING_VALIDATOR_PATCH_001.

Governed by:
- P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A (Contract Suites 22, 23, 24, 25)
- LLM_FINAL_INTEGRATION_FREEZE.json
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from backend.app.pipeline.evidence import StructuredEvidencePayload
from backend.app.schemas.confidence import ReportStatus
from backend.app.schemas.report import (
    GeneratedCoachReport,
    GroundingValidationResult,
    LLMGenerationMetadata,
    LLMReport,
)
from backend.app.services.deterministic_report_service import DeterministicReportService
from backend.app.services.grounding_validator import Patch001GroundingValidator

DEFAULT_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "coach_report_system.txt"
FROZEN_PROMPT_SHA256 = "ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce"
FROZEN_MODEL_TAG = "llama3.1:8b"
FROZEN_MODEL_DIGEST = "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"

FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120
DEFAULT_PRODUCTION_TIMEOUT_SECONDS = 120


class LLMReportService:
    """
    Production service orchestrating grounded Llama 3.1 8B report generation.
    Enforces fail-closed model digest verification, prompt integrity,
    zero retries, and Patch 001 grounding validation.
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:11434",
        prompt_path: Optional[Path] = None,
        timeout_seconds: Optional[int] = None,
        validator: Optional[Patch001GroundingValidator] = None,
        fallback_service: Optional[DeterministicReportService] = None,
    ):
        self.endpoint = endpoint
        self.model_tag = FROZEN_MODEL_TAG
        self.expected_digest = FROZEN_MODEL_DIGEST

        # Frozen generation parameters
        self.temperature = 0.0
        self.seed = 42
        self.top_p = 1.0
        self.num_ctx = 4096
        self.retries = 0

        # Timeout governance: env configurable, defaults to 120s
        env_timeout = os.getenv("LLM_TIMEOUT_SECONDS")
        if timeout_seconds is not None:
            self.timeout_seconds = int(timeout_seconds)
        elif env_timeout:
            self.timeout_seconds = int(env_timeout)
        else:
            self.timeout_seconds = DEFAULT_PRODUCTION_TIMEOUT_SECONDS

        # Load and cryptographically verify system prompt
        resolved_prompt_path = prompt_path or DEFAULT_PROMPT_PATH
        if not resolved_prompt_path.exists():
            raise FileNotFoundError(
                f"LLM_SYSTEM_PROMPT_PROVENANCE_BLOCKED: System prompt file missing at {resolved_prompt_path}"
            )

        raw_bytes = resolved_prompt_path.read_bytes()
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()
        if actual_hash != FROZEN_PROMPT_SHA256:
            raise ValueError(
                f"LLM_SYSTEM_PROMPT_PROVENANCE_BLOCKED: Expected SHA-256 '{FROZEN_PROMPT_SHA256}', "
                f"got '{actual_hash}' from {resolved_prompt_path}"
            )

        self.system_prompt = raw_bytes.decode("utf-8")
        self.system_prompt_sha256 = actual_hash
        self.validator = validator or Patch001GroundingValidator()
        self.fallback_service = fallback_service or DeterministicReportService()

    def verify_runtime_model(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Queries Ollama API tags and verifies exact model tag and 64-char digest.
        Returns (is_valid, digest, error_message).
        """
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.load(resp)

            matching_model = None
            for m in data.get("models", []):
                name = m.get("name", "")
                if name == self.model_tag or name == f"{self.model_tag}:latest":
                    matching_model = m
                    break

            if not matching_model:
                return (
                    False,
                    None,
                    f"LLM_MODEL_UNAVAILABLE: Model '{self.model_tag}' not registered in Ollama.",
                )

            actual_digest = matching_model.get("digest", "")
            if actual_digest != self.expected_digest:
                return (
                    False,
                    actual_digest,
                    f"LLM_MODEL_DIGEST_MISMATCH: Expected '{self.expected_digest}', got '{actual_digest}'.",
                )

            return True, actual_digest, None

        except Exception as ex:
            return (
                False,
                None,
                f"LLM_OLLAMA_UNREACHABLE: Failed to connect to Ollama at {self.endpoint}: {ex}",
            )

    def render_report_markdown(
        self,
        report: LLMReport,
        evidence: Dict[str, Any],
        validation: GroundingValidationResult,
    ) -> str:
        """Renders grounded LLMReport into the canonical 5-section structured markdown."""
        identity_status = evidence.get("source_provenance", {}).get(
            "identity_status", "FAIL_UNSAFE_MERGE (FORMAL_DENSE_GT)"
        )
        player_reporting = (
            "ENABLED" if evidence.get("player_level_analysis_allowed") else "WITHHELD"
        )
        metric_reporting = (
            "ENABLED" if evidence.get("metric_units_allowed") else "SUPPRESSED"
        )

        lines = [
            "# AI-Driven Football Tactical Analysis: Coaching Report",
            "",
            f"**Identity Status**: `{identity_status}`  ",
            f"**Player-Level Attribution**: `{player_reporting}`  ",
            f"**Metric Reporting**: `{metric_reporting}`  ",
            f"**Grounding Verification**: `PASS (All 8 deterministic gates satisfied)`  ",
            "",
            "---",
            "",
            "## 1. Coach Summary",
            "",
        ]
        for bullet in report.coach_summary:
            lines.append(f"- {bullet}")

        lines.extend([
            "",
            "## 2. Observed Evidence",
            "",
        ])
        for bullet in report.observed_evidence:
            lines.append(f"- {bullet}")

        lines.extend([
            "",
            "## 3. Limitations and Confidence",
            "",
        ])
        for bullet in report.limitations_and_confidence:
            lines.append(f"- {bullet}")

        lines.extend([
            "",
            "## 4. Session-Level Recommendations",
            "",
        ])
        for bullet in report.session_level_recommendations:
            lines.append(f"- {bullet}")

        lines.extend([
            "",
            "## 5. Technical Note",
            "",
        ])
        for bullet in report.technical_note:
            lines.append(f"- {bullet}")

        # Deterministic Provenance Appendix
        items_count = len(evidence.get("evidence_items", []))
        events_count = evidence.get("total_tactical_events", 0)
        lines.extend([
            "",
            "---",
            "### Deterministic Evidence Provenance",
            f"- **Timestamped Coaching Events**: `{events_count}`",
            f"- **Trajectory Evidence Items**: `{items_count}`",
            f"- **Calibration Mode**: `{evidence.get('calibration_mode', 'UNKNOWN')}`",
            "- **LLM Grounding Baseline**: Verified with `LLM_GROUNDING_VALIDATOR_PATCH_001` (8 gates active).",
            "- **Attribution Policy**: Fail-closed player attribution enforced; zero unverified physical/tactical claims permitted.",
        ])

        return "\n".join(lines)

    def generate_report(
        self,
        evidence_payload: Union[StructuredEvidencePayload, Dict[str, Any]],
        job_id: Optional[str] = None,
    ) -> GeneratedCoachReport:
        """
        Executes end-to-end report generation with strict fail-closed fallback.
        Consumes ONLY StructuredEvidencePayload; raw Vision/ASR bypass is prohibited.
        """
        if hasattr(evidence_payload, "model_dump"):
            evidence_dict = evidence_payload.model_dump()
        else:
            evidence_dict = dict(evidence_payload)

        session_id = evidence_dict.get("session_id", "UNKNOWN_SESSION")
        methodology_id = evidence_dict.get("methodology_id", "METHOD_2_RFDETR_GTATRACK")
        calib_mode = evidence_dict.get("calibration_mode", "NO_METRIC_CALIBRATION")
        player_allowed = evidence_dict.get("player_level_analysis_allowed", False)

        evidence_summary = {
            "total_tactical_events": evidence_dict.get("total_tactical_events", 0),
            "evidence_items_count": len(evidence_dict.get("evidence_items", [])),
            "metric_units_allowed": evidence_dict.get("metric_units_allowed", False),
            "player_level_analysis_allowed": player_allowed,
        }

        # Step 1: Preflight model digest
        is_model_valid, digest, model_err = self.verify_runtime_model()
        if not is_model_valid:
            fallback_md = self.fallback_service.generate_report(
                evidence_dict, fallback_reason=model_err
            )
            return GeneratedCoachReport(
                session_id=session_id,
                job_id=job_id,
                methodology_id=methodology_id,
                calibration_mode=calib_mode,
                player_level_analysis_allowed=player_allowed,
                report_status=ReportStatus.DETERMINISTIC_FALLBACK,
                report_markdown=fallback_md,
                fallback_reason=model_err,
                evidence_summary=evidence_summary,
            )

        # Step 2: Prepare deterministic request body
        schema = LLMReport.model_json_schema()
        evidence_json = json.dumps(evidence_dict, sort_keys=True, ensure_ascii=False)
        req_body = {
            "model": self.model_tag,
            "stream": False,
            "format": schema,
            "options": {
                "temperature": self.temperature,
                "seed": self.seed,
                "top_p": self.top_p,
                "num_ctx": self.num_ctx,
            },
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": evidence_json},
            ],
        }

        req_bytes = json.dumps(req_body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint}/api/chat",
            data=req_bytes,
            headers={"Content-Type": "application/json"},
        )

        t0 = time.time()
        raw_content: Optional[str] = None
        error_reason: Optional[str] = None

        # Step 3: Invoke Ollama (Strictly zero retries)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_data = json.load(resp)
            wall_clock = time.time() - t0
            raw_content = resp_data.get("message", {}).get("content", "")
        except urllib.error.URLError as ue:
            wall_clock = time.time() - t0
            error_reason = f"OLLAMA_TIMEOUT_OR_NETWORK_ERROR: {ue.reason}"
        except Exception as ex:
            wall_clock = time.time() - t0
            error_reason = f"LLM_INVOCATION_EXCEPTION: {str(ex)}"

        llm_meta = LLMGenerationMetadata(
            model_name="Meta-Llama-3.1-8B-Instruct",
            model_tag=self.model_tag,
            model_digest=self.expected_digest,
            system_prompt_sha256=self.system_prompt_sha256,
            temperature=self.temperature,
            seed=self.seed,
            top_p=self.top_p,
            num_ctx=self.num_ctx,
            retries=0,
            timeout_seconds=self.timeout_seconds,
            wall_clock_seconds=round(wall_clock, 2),
        )

        # Fallback on connection / timeout / execution error
        if error_reason or not raw_content:
            fallback_md = self.fallback_service.generate_report(
                evidence_dict, fallback_reason=error_reason or "EMPTY_LLM_RESPONSE"
            )
            return GeneratedCoachReport(
                session_id=session_id,
                job_id=job_id,
                methodology_id=methodology_id,
                calibration_mode=calib_mode,
                player_level_analysis_allowed=player_allowed,
                report_status=ReportStatus.DETERMINISTIC_FALLBACK,
                report_markdown=fallback_md,
                llm_metadata=llm_meta,
                fallback_reason=error_reason or "Empty content received from Ollama",
                evidence_summary=evidence_summary,
            )

        # Step 4: Parse into LLMReport Pydantic schema
        try:
            parsed_json = json.loads(raw_content)
            llm_report = LLMReport.model_validate(parsed_json)
        except Exception as parse_ex:
            fallback_reason = f"LLM_SCHEMA_VALIDATION_FAILED: {parse_ex}"
            fallback_md = self.fallback_service.generate_report(
                evidence_dict, fallback_reason=fallback_reason
            )
            return GeneratedCoachReport(
                session_id=session_id,
                job_id=job_id,
                methodology_id=methodology_id,
                calibration_mode=calib_mode,
                player_level_analysis_allowed=player_allowed,
                report_status=ReportStatus.DETERMINISTIC_FALLBACK,
                report_markdown=fallback_md,
                llm_metadata=llm_meta,
                fallback_reason=fallback_reason,
                evidence_summary=evidence_summary,
            )

        # Step 5: Enforce Patch 001 Grounding Validator (8 deterministic gates)
        val_res = self.validator.validate(llm_report, evidence_dict)

        if not val_res.passed:
            gate_reason = f"Grounding validation rejected by Patch 001: {';'.join(val_res.violations)}"
            fallback_md = self.fallback_service.generate_report(
                evidence_dict, fallback_reason=gate_reason
            )
            return GeneratedCoachReport(
                session_id=session_id,
                job_id=job_id,
                methodology_id=methodology_id,
                calibration_mode=calib_mode,
                player_level_analysis_allowed=player_allowed,
                report_status=ReportStatus.DETERMINISTIC_FALLBACK,
                report_markdown=fallback_md,
                validation_result=val_res,
                llm_metadata=llm_meta,
                fallback_reason=gate_reason,
                evidence_summary=evidence_summary,
            )

        # Step 6: Validated Grounded Report
        rendered_md = self.render_report_markdown(llm_report, evidence_dict, val_res)
        return GeneratedCoachReport(
            session_id=session_id,
            job_id=job_id,
            methodology_id=methodology_id,
            calibration_mode=calib_mode,
            player_level_analysis_allowed=player_allowed,
            report_status=ReportStatus.VALIDATED_LLM_REPORT,
            report_markdown=rendered_md,
            llm_report=llm_report,
            validation_result=val_res,
            llm_metadata=llm_meta,
            fallback_reason=None,
            evidence_summary=evidence_summary,
        )
