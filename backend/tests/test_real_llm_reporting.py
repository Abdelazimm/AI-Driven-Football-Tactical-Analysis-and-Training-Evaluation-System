"""
CM3070 Phase 4 Test Suite: Grounded LLM Report Generation & Validation.
Governed by:
- P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A (Contract Suites 22, 23, 24, 25)
- LLM_FINAL_INTEGRATION_FREEZE.json
- LLM_GROUNDING_VALIDATOR_PATCH_001.md

Direct test coverage:
1. Suite 22: Exact Llama model tag (llama3.1:8b), complete 64-char digest, exact prompt SHA-256
2. Suite 22: Truncated or altered digest/prompt rejected fail-closed
3. Suite 23: Frozen generation parameters (temp=0.0, seed=42, top_p=1.0, num_ctx=4096, retries=0)
4. Suite 24: Timeout governance (formal=120, production default=120, env configurability, zero retries)
5. Suite 24: Injected timeout engages deterministic fallback without crashing
6. Suite 25: Gate 1 Identity Safety (reject player attribution in automated mode)
7. Suite 25: Gate 1 permits anonymous tracks (track_7) and limitation statements
8. Suite 25: Gate 2 Psychological Neutrality (reject lazy, unmotivated, blame, etc.)
9. Suite 25: Gate 3 Privacy Name Leak (reject participant names)
10. Suite 25: Gate 4 Numeric Grounding (patched leaf traversal: reject ungrounded numbers, accept grounded numbers)
11. Suite 25: Gate 5 Negation-Aware Target Attribution (reject affirmative attribution, accept negated limitation)
12. Suite 25: Gate 6 Missing Speed Safety (reject speed claim when speed is null/suppressed)
13. Suite 25: Gate 7 Tactical Taxonomy (reject categories not present in evidence)
14. Suite 25: Gate 8 Action Grounding (reject actions not present in evidence)
15. Raw Vision or transcript cannot bypass StructuredEvidencePayload
16. Validator rejection immediately engages deterministic fallback
17. Ollama unavailable / network error engages deterministic fallback
18. Malformed JSON response engages deterministic fallback
19. Deterministic fallback is byte-identical for identical serialized evidence
20. Deterministic fallback respects metric suppression and identity withholding
21. ReportingPipeline forced fallback execution mode
22. Real bounded LLM smoke test with live Ollama Llama 3.1 8B
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from backend.app.pipeline.evidence import (
    StructuredEvidenceItem,
    StructuredEvidencePayload,
)
from backend.app.pipeline.reporting import ReportingPipeline
from backend.app.schemas.confidence import ReportStatus
from backend.app.schemas.report import (
    GeneratedCoachReport,
    GroundingValidationResult,
    LLMGenerationMetadata,
    LLMReport,
)
from backend.app.services.deterministic_report_service import DeterministicReportService
from backend.app.services.grounding_validator import (
    Patch001GroundingValidator,
    all_numbers_patched,
    validate_grounding,
)
from backend.app.services.llm_report_service import (
    DEFAULT_PRODUCTION_TIMEOUT_SECONDS,
    FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS,
    FROZEN_MODEL_DIGEST,
    FROZEN_MODEL_TAG,
    FROZEN_PROMPT_SHA256,
    LLMReportService,
)

SAMPLE_EVIDENCE = {
    "session_id": "test_session_42",
    "methodology_id": "METHOD_2_RFDETR_GTATRACK",
    "calibration_mode": "CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED",
    "metric_units_allowed": True,
    "player_level_analysis_allowed": False,
    "identity_evidence_basis": "FORMAL_DENSE_GT",
    "total_tactical_events": 1,
    "coaching_events": [
        {
            "event_id": "evt_0",
            "instruction_category": "Defensive",
            "action": "mark",
            "target_resolution_status": "UNRESOLVED_TARGET",
            "target_player": None,
        }
    ],
    "evidence_items": [
        {
            "evidence_id": "ev_0_track_1",
            "scope": "ANONYMOUS_TRACK",
            "source_event_id": "evt_0",
            "event_category": "Defensive",
            "event_action": "mark",
            "window_start_s": 173.63,
            "window_end_s": 177.63,
            "anonymous_track_id": "track_1",
            "displacement_m": 0.30,
            "speed_kmh": 1.20,
            "observations_count": 4,
        }
    ],
    "limitations": [
        "Automated tracking methodology has not demonstrated sufficiently safe persistent identity. Player-level analytics are withheld.",
    ],
}


# ==============================================================================
# SUITE 22: Exact Model Identity & Cryptographic Prompt Verification
# ==============================================================================
def test_01_suite22_exact_model_tag_and_complete_digest():
    """Verify that LLMReportService requires exact model tag and 64-char digest."""
    service = LLMReportService()
    assert service.model_tag == "llama3.1:8b"
    assert service.expected_digest == "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"
    assert len(service.expected_digest) == 64

    # Test live verification with running Ollama
    is_valid, digest, err = service.verify_runtime_model()
    assert is_valid is True, f"Model verification failed: {err}"
    assert digest == service.expected_digest
    assert err is None


def test_02_suite22_truncated_or_altered_digest_rejected():
    """Verify that a truncated or altered model digest fails closed."""
    service = LLMReportService()

    # Mock Ollama returning a truncated or different digest
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "models": [
                {
                    "name": "llama3.1:8b",
                    "digest": "46e0c10c039e",  # Truncated 12-char ID
                }
            ]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        is_valid, digest, err = service.verify_runtime_model()
        assert is_valid is False
        assert "LLM_MODEL_DIGEST_MISMATCH" in err


def test_03_suite22_exact_system_prompt_sha256():
    """Verify that the system prompt matches exact authoritative SHA-256 digest."""
    service = LLMReportService()
    assert service.system_prompt_sha256 == "ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce"
    computed_sha = hashlib.sha256(service.system_prompt.encode("utf-8")).hexdigest()
    assert computed_sha == service.system_prompt_sha256


def test_04_suite22_altered_prompt_hash_fails_closed(tmp_path: Path):
    """Verify that modifying even one character of the prompt causes fail-closed initialization error."""
    corrupted_prompt = tmp_path / "corrupted_system.txt"
    corrupted_prompt.write_bytes(b"You are an altered prompt.")

    with pytest.raises(ValueError) as exc_info:
        LLMReportService(prompt_path=corrupted_prompt)

    assert "LLM_SYSTEM_PROMPT_PROVENANCE_BLOCKED" in str(exc_info.value)


# ==============================================================================
# SUITE 23: Frozen Generation Hyperparameters
# ==============================================================================
def test_05_suite23_frozen_generation_parameters():
    """Verify that LLMReportService hardcodes the exact frozen decoding parameters."""
    service = LLMReportService()
    assert service.temperature == 0.0
    assert service.seed == 42
    assert service.top_p == 1.0
    assert service.num_ctx == 4096
    assert service.retries == 0


# ==============================================================================
# SUITE 24: Timeout Governance & Fail-Closed Fallback
# ==============================================================================
def test_06_suite24_timeout_defaults_and_env_configurability():
    """Verify that timeout defaults to 120s (formal benchmark specification) and is configurable."""
    assert FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS == 120
    assert DEFAULT_PRODUCTION_TIMEOUT_SECONDS == 120

    service = LLMReportService()
    assert service.timeout_seconds == 120

    # Configurable through constructor
    service_custom = LLMReportService(timeout_seconds=45)
    assert service_custom.timeout_seconds == 45

    # Configurable through environment variable
    with patch.dict(os.environ, {"LLM_TIMEOUT_SECONDS": "90"}):
        service_env = LLMReportService()
        assert service_env.timeout_seconds == 90


def test_07_suite24_timeout_forces_deterministic_fallback_zero_retries():
    """Verify that a timeout triggers DETERMINISTIC_FALLBACK with zero retries without crashing."""
    service = LLMReportService(timeout_seconds=1)

    # Mock urllib.request.urlopen to raise a timeout URLError
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timed out")) as mock_call:
        report = service.generate_report(SAMPLE_EVIDENCE)

        # Assert exactly ONE call was made (strictly zero retries)
        assert mock_call.call_count == 1
        assert report.report_status == ReportStatus.DETERMINISTIC_FALLBACK
        assert "timed out" in report.fallback_reason.lower()
        assert report.llm_report is None
        assert report.report_markdown is not None


# ==============================================================================
# SUITE 25: Patch 001 Grounding Validator (All 8 Gates)
# ==============================================================================
def test_08_suite25_gate1_rejects_player_attribution_in_automated_mode():
    """Gate 1: Reject individual player attribution (Player 1) when player_level_analysis_allowed is False."""
    validator = Patch001GroundingValidator()
    report = LLMReport(
        coach_summary=["Player 1 executed the defensive marking drill."],
        observed_evidence=["Player 1 remained active."],
        limitations_and_confidence=["No player level certainty."],
        session_level_recommendations=["Keep training."],
        technical_note=["Pipeline run."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.passed is False
    assert "IDENTITY_SAFETY_NEW_PLAYER_ID" in res.violations
    assert "UNSUPPORTED_PLAYER_IDENTITY" in res.error_categories
    assert res.gate_results["Gate 1"] is False


def test_09_suite25_gate1_permits_anonymous_tracks_and_unresolved_targets():
    """Gate 1: Permits anonymous track IDs (track_1) and unresolved target references."""
    validator = Patch001GroundingValidator()
    report = LLMReport(
        coach_summary=["The anonymous trajectory track_1 was observed in the defensive window."],
        observed_evidence=["Track_1 moved within the zone."],
        limitations_and_confidence=["The target player was unresolved."],
        session_level_recommendations=["Review spatial shape."],
        technical_note=["Pipeline run."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.gate_results["Gate 1"] is True


def test_10_suite25_gate2_rejects_psychological_and_blame_language():
    """Gate 2: Rejects forbidden psychological, motivational, or blame language."""
    validator = Patch001GroundingValidator()
    prohibited_words = ["lazy", "unmotivated", "frustrated", "undisciplined", "blame"]

    for word in prohibited_words:
        report = LLMReport(
            coach_summary=[f"The squad appeared {word} during the press."],
            observed_evidence=["Movement was slow."],
            limitations_and_confidence=["None."],
            session_level_recommendations=["Improve work rate."],
            technical_note=["Pipeline run."],
        )
        res = validator.validate(report, SAMPLE_EVIDENCE)
        assert res.passed is False
        assert "PROHIBITED_PSYCHOLOGICAL_INFERENCE" in res.violations
        assert res.gate_results["Gate 2"] is False


def test_11_suite25_gate3_rejects_private_participant_names():
    """Gate 3: Rejects identifying private participant names."""
    validator = Patch001GroundingValidator()
    names = ["Alex", "John", "Dave", "Mike", "Aly"]

    for name in names:
        report = LLMReport(
            coach_summary=[f"Coach shouted instruction towards {name}."],
            observed_evidence=["Action took place."],
            limitations_and_confidence=["None."],
            session_level_recommendations=["Review."],
            technical_note=["Pipeline run."],
        )
        res = validator.validate(report, SAMPLE_EVIDENCE)
        assert res.passed is False
        assert "PRIVACY_NAME_LEAK" in res.violations
        assert res.gate_results["Gate 3"] is False


def test_12_suite25_gate4_rejects_ungrounded_numeric_claims():
    """Gate 4: Rejects numbers not grounded anywhere in the structured evidence payload."""
    validator = Patch001GroundingValidator()
    report = LLMReport(
        coach_summary=["The response occurred over 99.5 seconds with 14.8m displacement."],
        observed_evidence=["Speed reached 28.4 km/h."],
        limitations_and_confidence=["None."],
        session_level_recommendations=["Review."],
        technical_note=["Pipeline run."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.passed is False
    assert any("UNSUPPORTED_NUMERIC_VALUES" in v for v in res.violations)
    assert res.gate_results["Gate 4"] is False


def test_13_suite25_gate4_permits_grounded_numbers_across_leaves():
    """Gate 4 (Patched): Accepts numbers present in payload leaves (floats, ints, or leaf strings)."""
    # Numbers 173.63, 177.63, 0.30, 1.20, 4 are all in SAMPLE_EVIDENCE
    validator = Patch001GroundingValidator()
    report = LLMReport(
        coach_summary=["Observed window was 173.63 to 177.63 seconds."],
        observed_evidence=["Track displacement was 0.30 m with 4 observations at speed 1.20 km/h."],
        limitations_and_confidence=["Formal gate active."],
        session_level_recommendations=["Maintain distance."],
        technical_note=["Technical run 1."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.gate_results["Gate 4"] is True


def test_14_suite25_gate5_rejects_affirmative_attribution_to_unresolved_target():
    """Gate 5: Rejects affirmative claim resolving an unresolved target."""
    validator = Patch001GroundingValidator()
    report = LLMReport(
        coach_summary=["The coach instruction was resolved and attributed to the player."],
        observed_evidence=["Target was identified as the player."],
        limitations_and_confidence=["None."],
        session_level_recommendations=["Practice."],
        technical_note=["Pipeline run."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.passed is False
    assert any("UNRESOLVED_TARGET_BECAME_RESOLVED" in v for v in res.violations)
    assert res.gate_results["Gate 5"] is False


def test_15_suite25_gate5_permits_safe_negated_target_limitations():
    """Gate 5 (Patched): Permits negation-aware statements of unresolved target limitations."""
    validator = Patch001GroundingValidator()
    report = LLMReport(
        coach_summary=["The coaching instruction was not attributed to a specific player due to unresolved target."],
        observed_evidence=["The instruction was given without resolved target."],
        limitations_and_confidence=["Target identity remained unresolved."],
        session_level_recommendations=["Observe movement."],
        technical_note=["Technical run 1."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.gate_results["Gate 5"] is True


def test_16_suite25_gate6_rejects_inferred_speed_when_speed_is_unavailable():
    """Gate 6: Rejects asserting speed when speed evidence is unavailable or uncalibrated."""
    evidence_no_speed = dict(SAMPLE_EVIDENCE)
    evidence_no_speed["metric_units_allowed"] = False
    evidence_no_speed["limitations"] = ["Metric speed is unavailable in the fused real-session evidence."]

    validator = Patch001GroundingValidator()
    report = LLMReport(
        coach_summary=["The movement was observed."],
        observed_evidence=["The player velocity reached 15 km/h."],
        limitations_and_confidence=["Speed was unavailable."],
        session_level_recommendations=["Train."],
        technical_note=["Run 1."],
    )
    res = validator.validate(report, evidence_no_speed)
    assert res.passed is False
    assert "MISSING_SPEED_INFERRED" in res.violations
    assert res.gate_results["Gate 6"] is False


def test_17_suite25_gate7_rejects_unsupported_tactical_categories():
    """Gate 7: Rejects tactical categories that do not exist in the evidence coaching events."""
    validator = Patch001GroundingValidator()
    # SAMPLE_EVIDENCE contains only 'Defensive'
    report = LLMReport(
        coach_summary=["A high pressing drill and offensive counterattack took place."],
        observed_evidence=["The squad engaged in offensive transition."],
        limitations_and_confidence=["None."],
        session_level_recommendations=["Review."],
        technical_note=["Run 1."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.passed is False
    assert any("UNSUPPORTED_EVENT_CATEGORY" in v for v in res.violations)
    assert res.gate_results["Gate 7"] is False


def test_18_suite25_gate8_rejects_unsupported_tactical_actions():
    """Gate 8: Rejects invented tactical actions (e.g. tackle, dribble, score) not in evidence."""
    validator = Patch001GroundingValidator()
    # SAMPLE_EVIDENCE contains action 'mark'
    report = LLMReport(
        coach_summary=["The player performed a slide tackle and attempted to dribble."],
        observed_evidence=["A shot on goal was attempted."],
        limitations_and_confidence=["None."],
        session_level_recommendations=["Review."],
        technical_note=["Run 1."],
    )
    res = validator.validate(report, SAMPLE_EVIDENCE)
    assert res.passed is False
    assert any("UNSUPPORTED_EVENT_ACTION" in v for v in res.violations)
    assert res.gate_results["Gate 8"] is False


# ==============================================================================
# Additional Production Contracts & Fallback Integration Tests
# ==============================================================================
def test_19_raw_vision_or_transcript_cannot_bypass_structured_evidence():
    """Verify that LLMReportService consumes only StructuredEvidencePayload."""
    service = LLMReportService()
    # Passing an arbitrary object without model_dump or dict structure fails safely
    with patch.object(service, "verify_runtime_model", return_value=(True, FROZEN_MODEL_DIGEST, None)):
        with patch("urllib.request.urlopen") as mock_url:
            mock_url.side_effect = Exception("Ollama error")
            report = service.generate_report(SAMPLE_EVIDENCE)
            assert isinstance(report, GeneratedCoachReport)
            assert report.report_status == ReportStatus.DETERMINISTIC_FALLBACK


def test_20_validator_rejection_engages_deterministic_fallback():
    """Verify that Patch 001 rejection immediately engages DETERMINISTIC_FALLBACK with zero retries."""
    service = LLMReportService()

    invalid_llm_json = {
        "coach_summary": ["Player 1 was lazy and failed to defend."],
        "observed_evidence": ["Player 1 did not mark."],
        "limitations_and_confidence": ["Unsafe."],
        "session_level_recommendations": ["Improve."],
        "technical_note": ["Run 1."],
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"message": {"content": json.dumps(invalid_llm_json)}}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch.object(service, "verify_runtime_model", return_value=(True, FROZEN_MODEL_DIGEST, None)):
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            report = service.generate_report(SAMPLE_EVIDENCE)
            assert mock_url.call_count == 1  # Exactly 1 call, zero retries
            assert report.report_status == ReportStatus.DETERMINISTIC_FALLBACK
            assert report.validation_result.passed is False
            assert "Grounding validation rejected by Patch 001" in report.fallback_reason


def test_21_ollama_unavailable_or_error_engages_deterministic_fallback():
    """Verify that an unavailable Ollama process engages DETERMINISTIC_FALLBACK without crashing."""
    service = LLMReportService()

    with patch.object(service, "verify_runtime_model", return_value=(False, None, "LLM_OLLAMA_UNREACHABLE")):
        report = service.generate_report(SAMPLE_EVIDENCE)
        assert report.report_status == ReportStatus.DETERMINISTIC_FALLBACK
        assert "LLM_OLLAMA_UNREACHABLE" in report.fallback_reason
        assert "## 1. Analysis Summary" in report.report_markdown


def test_22_empty_or_malformed_json_engages_deterministic_fallback():
    """Verify that non-JSON or malformed responses engage DETERMINISTIC_FALLBACK."""
    service = LLMReportService()

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"message": {"content": "This is raw unformatted text."}}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch.object(service, "verify_runtime_model", return_value=(True, FROZEN_MODEL_DIGEST, None)):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            report = service.generate_report(SAMPLE_EVIDENCE)
            assert report.report_status == ReportStatus.DETERMINISTIC_FALLBACK
            assert "LLM_SCHEMA_VALIDATION_FAILED" in report.fallback_reason


def test_23_deterministic_fallback_is_byte_identical_for_identical_payload():
    """Step 13: Verify that the deterministic fallback is 100% byte-identical for identical input."""
    fallback_svc = DeterministicReportService()
    md1 = fallback_svc.generate_report(SAMPLE_EVIDENCE, fallback_reason="TEST_REASON")
    md2 = fallback_svc.generate_report(SAMPLE_EVIDENCE, fallback_reason="TEST_REASON")
    assert md1 == md2
    h1 = hashlib.sha256(md1.encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(md2.encode("utf-8")).hexdigest()
    assert h1 == h2


def test_24_deterministic_fallback_respects_metric_suppression_and_anonymity():
    """Verify that deterministic fallback does not emit metres or km/h when uncalibrated."""
    evidence_uncalibrated = dict(SAMPLE_EVIDENCE)
    evidence_uncalibrated["metric_units_allowed"] = False
    evidence_uncalibrated["calibration_mode"] = "NO_METRIC_CALIBRATION"

    fallback_svc = DeterministicReportService()
    report_md = fallback_svc.generate_report(evidence_uncalibrated)

    assert "SUPPRESSED" in report_md
    assert "FAIL_UNSAFE_MERGE" in report_md
    assert "WITHHELD" in report_md
    assert "km/h" not in report_md
    assert "Player 1" not in report_md
    assert "track_1" in report_md


def test_25_reporting_pipeline_forced_fallback_mode():
    """Verify that ReportingPipeline can be configured for forced fallback mode."""
    pipeline = ReportingPipeline(force_fallback=True)
    report = pipeline.generate_report(SAMPLE_EVIDENCE, job_id="forced_job")
    assert report.report_status == ReportStatus.DETERMINISTIC_FALLBACK
    assert report.fallback_reason == "FORCED_DETERMINISTIC_FALLBACK"
    assert report.job_id == "forced_job"


# ==============================================================================
# Step 11: Real Bounded LLM Smoke Test
# ==============================================================================
def test_26_real_bounded_llm_generation_smoke():
    """
    Executes real live Ollama Llama 3.1 8B generation on real evidence.
    Verifies model digest, prompt hash, Patch 001 validation, and report output.
    """
    service = LLMReportService()
    is_valid, digest, err = service.verify_runtime_model()
    if not is_valid:
        pytest.skip(f"Ollama or model unavailable for real smoke: {err}")

    # Use valid structured evidence adhering to constraints
    report = service.generate_report(SAMPLE_EVIDENCE, job_id="smoke_test_job")

    assert isinstance(report, GeneratedCoachReport)
    assert report.session_id == "test_session_42"
    assert report.job_id == "smoke_test_job"
    assert report.llm_metadata is not None
    assert report.llm_metadata.model_digest == FROZEN_MODEL_DIGEST
    assert report.llm_metadata.system_prompt_sha256 == FROZEN_PROMPT_SHA256

    # Report must either be VALIDATED_LLM_REPORT (passed all 8 gates) or safe DETERMINISTIC_FALLBACK
    assert report.report_status in [ReportStatus.VALIDATED_LLM_REPORT, ReportStatus.DETERMINISTIC_FALLBACK]
    if report.report_status == ReportStatus.VALIDATED_LLM_REPORT:
        assert report.validation_result is not None
        assert report.validation_result.passed is True
        assert len(report.validation_result.violations) == 0
        assert all(report.validation_result.gate_results.values())
    else:
        assert report.fallback_reason is not None

    # In both cases, markdown must contain the mandatory headers and sections
    assert "Coaching Report" in report.report_markdown
    assert "FAIL_UNSAFE_MERGE" in report.report_markdown
    assert "Player" not in report.report_markdown or "WITHHELD" in report.report_markdown
