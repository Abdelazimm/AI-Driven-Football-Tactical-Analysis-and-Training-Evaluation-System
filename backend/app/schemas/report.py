"""
Pydantic Schemas for Grounded LLM Coaching Reports and Validation Contracts.
Governed by P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A and LLM_FINAL_INTEGRATION_FREEZE.json.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.confidence import ReportStatus


class LLMReport(BaseModel):
    """
    Pydantic schema matching the frozen 5-field LLMReport format.
    Every field is a list of descriptive, evidence-grounded statements.
    """
    coach_summary: List[str] = Field(
        ...,
        description="High-level session tactical observations suitable for an amateur football coach."
    )
    observed_evidence: List[str] = Field(
        ...,
        description="Directly supported facts from supplied structured evidence without invention."
    )
    limitations_and_confidence: List[str] = Field(
        ...,
        description="Mandatory limitations, identity withholding notices, and physical measurement uncertainties."
    )
    session_level_recommendations: List[str] = Field(
        ...,
        description="Actionable next steps for coaches and analysts, strictly grounded in the session."
    )
    technical_note: List[str] = Field(
        ...,
        description="Pipeline execution metadata, calibration confidence, and algorithmic safety context."
    )


class GroundingViolation(BaseModel):
    """Structured representation of a single deterministic grounding violation."""
    gate_name: str = Field(..., description="Name of the deterministic gate that triggered (e.g. Gate 1)")
    violation_code: str = Field(..., description="Machine-readable violation identifier")
    details: Optional[str] = Field(None, description="Detailed explanatory context")
    unsupported_tokens: List[str] = Field(default_factory=list, description="Specific offending tokens or values")


class GroundingValidationResult(BaseModel):
    """Result of running LLM_GROUNDING_VALIDATOR_PATCH_001 across all 8 gates."""
    passed: bool = Field(..., description="True if all 8 gates passed without violation")
    violations: List[str] = Field(default_factory=list, description="List of string violation codes")
    error_categories: List[str] = Field(default_factory=list, description="Taxonomic error classifications")
    gate_results: Dict[str, bool] = Field(default_factory=dict, description="Pass/fail status per gate (Gate 1 - Gate 8)")
    checked_at_utc: str = Field(..., description="ISO-8601 UTC timestamp of validation")


class LLMGenerationMetadata(BaseModel):
    """Auditable execution metadata for Ollama Llama 3.1 8B generation."""
    model_name: str = Field(default="Meta-Llama-3.1-8B-Instruct")
    model_tag: str = Field(default="llama3.1:8b")
    model_digest: str = Field(default="46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e")
    system_prompt_sha256: str = Field(default="ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce")
    temperature: float = Field(default=0.0)
    seed: int = Field(default=42)
    top_p: float = Field(default=1.0)
    num_ctx: int = Field(default=4096)
    retries: int = Field(default=0)
    timeout_seconds: int = Field(default=120)
    wall_clock_seconds: float = Field(default=0.0)


class GeneratedCoachReport(BaseModel):
    """
    Authoritative production report artifact emitted by ReportingPipeline.
    Encapsulates rendered markdown, source evidence provenance, grounding results, and fallback tracking.
    """
    session_id: str = Field(..., description="Associated session identifier")
    job_id: Optional[str] = Field(None, description="Associated job identifier")
    methodology_id: str = Field(..., description="Computer vision methodology identifier")
    calibration_mode: str = Field(..., description="Calibration mode used (e.g. CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED)")
    player_level_analysis_allowed: bool = Field(..., description="Identity safety gate disposition")
    report_status: ReportStatus = Field(..., description="Final report delivery status")
    report_markdown: str = Field(..., description="Fully rendered coach report in Markdown")
    llm_report: Optional[LLMReport] = Field(None, description="Structured LLM report if LLM succeeded and passed validation")
    validation_result: Optional[GroundingValidationResult] = Field(None, description="Validation result from Patch 001")
    llm_metadata: Optional[LLMGenerationMetadata] = Field(None, description="Ollama execution metadata")
    fallback_reason: Optional[str] = Field(None, description="Detailed reason if deterministic fallback was engaged")
    evidence_summary: Optional[Dict[str, Any]] = Field(None, description="Summary counts from StructuredEvidencePayload")
    created_at: datetime = Field(default_factory=datetime.utcnow)
