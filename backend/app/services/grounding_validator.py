"""
Authoritative Grounding Validator implementing LLM_GROUNDING_VALIDATOR_PATCH_001.
Governed by:
- P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A (Contract Suite 25)
- LLM_FINAL_INTEGRATION_FREEZE.json
- LLM_GROUNDING_VALIDATOR_PATCH_001.md

Enforces 8 deterministic grounding gates without weakening safety invariants:
Gate 1: IDENTITY_SAFETY_NEW_PLAYER_ID
Gate 2: PROHIBITED_PSYCHOLOGICAL_INFERENCE
Gate 3: PRIVACY_NAME_LEAK
Gate 4: UNSUPPORTED_NUMERIC_VALUES (Patched: Full payload leaf traversal + exact float normalization)
Gate 5: UNRESOLVED_TARGET_BECAME_RESOLVED (Patched: Negation-aware attribution vs safe limitations)
Gate 6: MISSING_SPEED_INFERRED
Gate 7: UNSUPPORTED_EVENT_CATEGORY
Gate 8: UNSUPPORTED_EVENT_ACTION
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional, Set, Union

from backend.app.schemas.report import (
    GroundingValidationResult,
    GroundingViolation,
    LLMReport,
)

NUM_PAT = re.compile(r"(?<![A-Za-z_0-9\[])\d+(?:\.\d+)?(?![0-9])")
PLAYER_ID = re.compile(r"\bPlayer[_ -]?\d+\b", re.I)
PROHIBITED_PSYCH = re.compile(
    r"\b(lazy|unmotivated|frustrated|angry|afraid|anxious|disinterested|undisciplined|rebellious|fatigued|exhausted|blame)\b",
    re.I,
)
PRIVATE_NAMES = re.compile(r"\b(John|Alex|Dave|Mike|Sarah|Emma|Aly|Abdelazim)\b", re.I)

UNSUPPORTED_EVENT_ACTIONS: Set[str] = {
    "cross",
    "score",
    "sprint",
    "overlap",
    "counterattack",
    "dribble",
    "tackle",
    "shoot",
}


def all_numbers_patched(obj: Any) -> List[float]:
    """
    Recursively extracts numbers from all leaves including string literals.
    Implements Section 4.1 of LLM_GROUNDING_VALIDATOR_PATCH_001.md.
    """
    vals: List[float] = []
    if isinstance(obj, dict):
        for v in obj.values():
            vals.extend(all_numbers_patched(v))
    elif isinstance(obj, list):
        for v in obj:
            vals.extend(all_numbers_patched(v))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        vals.append(float(obj))
    elif isinstance(obj, str):
        for num_str in NUM_PAT.findall(obj):
            try:
                vals.append(float(num_str))
            except ValueError:
                pass
    return vals


def flatten_text(obj: Any) -> str:
    """Flattens any nested data structure into a single string for regex inspection."""
    if isinstance(obj, dict):
        return " ".join(flatten_text(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(flatten_text(v) for v in obj)
    return str(obj)


class Patch001GroundingValidator:
    """
    Deterministic Grounding Validator enforcing all 8 gates with zero retries.
    """

    def validate(
        self,
        report: Union[LLMReport, Dict[str, Any], str],
        evidence: Union[Dict[str, Any], Any],
    ) -> GroundingValidationResult:
        """
        Validates an LLMReport or candidate dict against structured evidence.
        """
        if isinstance(report, LLMReport):
            data = report.model_dump()
        elif isinstance(report, dict):
            data = report
        else:
            data = {"raw_text": str(report)}

        text = flatten_text(data)

        if hasattr(evidence, "model_dump"):
            evidence_dict = evidence.model_dump()
        elif isinstance(evidence, dict):
            evidence_dict = evidence
        else:
            evidence_dict = {"content": str(evidence)}

        evidence_text = flatten_text(evidence_dict)
        violations: List[str] = []
        error_categories: List[str] = []
        gate_results: Dict[str, bool] = {
            "Gate 1": True,
            "Gate 2": True,
            "Gate 3": True,
            "Gate 4": True,
            "Gate 5": True,
            "Gate 6": True,
            "Gate 7": True,
            "Gate 8": True,
        }

        # Gate 1: IDENTITY_SAFETY_NEW_PLAYER_ID
        player_level_reporting_enabled = evidence_dict.get(
            "player_level_reporting_enabled",
            evidence_dict.get("player_level_analysis_allowed", False),
        )
        identity_evidence_basis = evidence_dict.get(
            "identity_evidence_basis",
            evidence_dict.get("source_provenance", {}).get("identity_evidence_basis", ""),
        )

        if (not player_level_reporting_enabled or identity_evidence_basis != "HUMAN_ORACLE") and PLAYER_ID.search(text):
            violations.append("IDENTITY_SAFETY_NEW_PLAYER_ID")
            error_categories.append("UNSUPPORTED_PLAYER_IDENTITY")
            gate_results["Gate 1"] = False

        # Gate 2: PROHIBITED_PSYCHOLOGICAL_INFERENCE
        if PROHIBITED_PSYCH.search(text):
            violations.append("PROHIBITED_PSYCHOLOGICAL_INFERENCE")
            error_categories.append("OVERSTATED_CERTAINTY")
            gate_results["Gate 2"] = False

        # Gate 3: PRIVACY_NAME_LEAK
        if PRIVATE_NAMES.search(text):
            violations.append("PRIVACY_NAME_LEAK")
            error_categories.append("PRIVACY_POLICY_VIOLATION")
            gate_results["Gate 3"] = False

        # Gate 4: UNSUPPORTED_NUMERIC_VALUES (PATCHED: Full payload leaf traversal + exact float normalization)
        allowed = set(all_numbers_patched(evidence_dict))
        generated = [float(x) for x in NUM_PAT.findall(text)]
        unsupported = [n for n in generated if not any(abs(n - a) < 1e-4 for a in allowed)]
        if unsupported:
            violations.append("UNSUPPORTED_NUMERIC_VALUES:" + ",".join(map(str, unsupported)))
            error_categories.append("UNSUPPORTED_NUMERIC_CLAIM")
            gate_results["Gate 4"] = False

        # Gate 5: UNRESOLVED_TARGET_BECAME_RESOLVED (PATCHED: Negation-aware attribution handling)
        coaching_events = (
            evidence_dict.get("coaching_events")
            or evidence_dict.get("events")
            or evidence_dict.get("evidence_items", [])
        )
        if coaching_events:
            all_unresolved = all(
                e.get("target_resolution_status") == "UNRESOLVED_TARGET"
                or e.get("target_player") is None
                for e in coaching_events
                if isinstance(e, dict)
            )
            if all_unresolved:
                # Check 1: Explicit target attribution to a specific player ID
                pos_player_target = re.finditer(
                    r"(?:\bPlayer[_ -]?\d+\s+(?:received|was\s+(?:instructed|targeted|given)|executed)\b|\b(?:belongs|attributed|directed)\s+to\s+Player[_ -]?\d+\b)",
                    text,
                    re.I,
                )
                for m in pos_player_target:
                    prefix = text[max(0, m.start() - 30):m.start()].lower()
                    if not re.search(r"\b(not|never|no|neither|without|unresolved|unavailable)\b", prefix):
                        violations.append(f"UNRESOLVED_TARGET_ATTRIBUTED_TO_PLAYER:{m.group(0)}")
                        error_categories.append("CONTRADICTS_INPUT")
                        gate_results["Gate 5"] = False

                # Check 2: Affirmative resolution/attribution claim (distinguishing safe negated limitations)
                gen_attrib = re.finditer(
                    r"\b(resolved|identified|attributed)\s+(?:to|as)\s+(?:a|the|specific\s+player|player)",
                    text,
                    re.I,
                )
                for m in gen_attrib:
                    prefix = text[max(0, m.start() - 35):m.start()].lower()
                    if not re.search(
                        r"\b(not|never|no|neither|without|unresolved|unavailable|refrain|withheld|cannot|can\s+not)\b",
                        prefix,
                    ):
                        violations.append(f"UNRESOLVED_TARGET_BECAME_RESOLVED:{m.group(0)}")
                        error_categories.append("CONTRADICTS_INPUT")
                        gate_results["Gate 5"] = False

        # Gate 6: MISSING_SPEED_INFERRED
        limitations = evidence_dict.get("limitations") or evidence_dict.get("global_limitations", [])
        metric_units_allowed = evidence_dict.get("metric_units_allowed", True)
        has_speed_missing_limitation = (
            not metric_units_allowed
            or any("Metric speed is unavailable" in str(lim) or "SPEED_UNAVAILABLE" in str(lim) for lim in limitations)
        )
        if has_speed_missing_limitation:
            if re.search(r"\b(?:speed|velocity)\s+(?:was|is|reached|averaged)\s+\d", text, re.I):
                violations.append("MISSING_SPEED_INFERRED")
                error_categories.append("UNAVAILABLE_EVIDENCE_USED")
                gate_results["Gate 6"] = False

        # Gate 7: UNSUPPORTED_EVENT_CATEGORY
        evidence_categories: Set[str] = set()
        for e in coaching_events:
            if isinstance(e, dict):
                cat = e.get("instruction_category") or e.get("category") or e.get("event_category") or ""
                if cat:
                    evidence_categories.add(str(cat).lower())

        category_terms = {"defensive", "offensive", "pressing", "passing", "positioning / hold ground"}
        introduced = sorted(t for t in category_terms if t in text.lower() and t not in evidence_categories)
        if introduced:
            violations.append("UNSUPPORTED_EVENT_CATEGORY:" + ",".join(introduced))
            error_categories.append("UNSUPPORTED_FACT")
            gate_results["Gate 7"] = False

        # Gate 8: UNSUPPORTED_EVENT_ACTION
        invented = sorted(
            term
            for term in UNSUPPORTED_EVENT_ACTIONS
            if re.search(rf"\b{term}(?:s|ed|ing)?\b", text.lower())
            and not re.search(rf"\b{term}(?:s|ed|ing)?\b", evidence_text.lower())
        )
        if invented:
            violations.append("UNSUPPORTED_EVENT_ACTION:" + ",".join(invented))
            error_categories.append("UNSUPPORTED_FACT")
            gate_results["Gate 8"] = False

        return GroundingValidationResult(
            passed=(len(violations) == 0),
            violations=violations,
            error_categories=list(set(error_categories)),
            gate_results=gate_results,
            checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )


def validate_grounding(
    report: Union[LLMReport, Dict[str, Any], str],
    evidence: Union[Dict[str, Any], Any],
) -> GroundingValidationResult:
    """Convenience functional wrapper matching research pipeline interface."""
    validator = Patch001GroundingValidator()
    return validator.validate(report, evidence)
