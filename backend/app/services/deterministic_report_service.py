"""
Deterministic Evidence-Based Fallback Report Service.
Generates fully grounded, readable coach-facing reports directly from StructuredEvidencePayload
without requiring an LLM. Governed by P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from backend.app.pipeline.evidence import StructuredEvidencePayload, StructuredEvidenceItem


class DeterministicReportService:
    """
    Compiles deterministic, identity-safe, and evidence-grounded coaching reports
    directly from StructuredEvidencePayload.
    """

    def generate_report(
        self,
        payload: Union[StructuredEvidencePayload, Dict[str, Any]],
        fallback_reason: Optional[str] = None,
    ) -> str:
        """Generates markdown report from structured evidence without invention."""
        if hasattr(payload, "model_dump"):
            data = payload.model_dump()
        else:
            data = dict(payload)

        session_id = data.get("session_id", "UNKNOWN_SESSION")
        methodology_id = data.get("methodology_id", "UNKNOWN_METHODOLOGY")
        calib_mode = data.get("calibration_mode", "NO_METRIC_CALIBRATION")
        metric_allowed = data.get("metric_units_allowed", False)
        player_allowed = data.get("player_level_analysis_allowed", False)
        identity_basis = data.get("identity_evidence_basis", "FORMAL_DENSE_GT")
        items: List[Dict[str, Any]] = data.get("evidence_items", [])
        limitations: List[str] = data.get("global_limitations", [])

        lines: List[str] = [
            "# AI-Driven Football Tactical Analysis: Coaching Report",
            "",
            f"**Session ID**: `{session_id}`  ",
            f"**Methodology**: `{methodology_id}`  ",
            f"**Calibration Mode**: `{calib_mode}`  ",
            f"**Metric Reporting**: `{'ENABLED' if metric_allowed else 'SUPPRESSED'}`  ",
            f"**Player-Level Attribution**: `{'ENABLED' if player_allowed else 'WITHHELD'}`  ",
            f"**Identity Status**: `FAIL_UNSAFE_MERGE ({identity_basis})`  ",
            f"**Generation Mode**: `DETERMINISTIC_FALLBACK`  ",
        ]

        if fallback_reason:
            lines.append(f"**Fallback Activation Reason**: *{fallback_reason}*  ")

        lines.extend([
            "",
            "---",
            "",
            "## 1. Analysis Summary",
            "",
        ])

        total_events = data.get("total_tactical_events", len({it.get("source_event_id") for it in items if it.get("source_event_id")}))
        lines.append(
            f"- Extracted **{total_events}** coach tactical instruction event(s) across the analyzed session interval."
        )

        if not player_allowed:
            lines.append(
                "- Under formal dense ground-truth evaluation, persistent identity is not certified (`FAIL_UNSAFE_MERGE`). "
                "All player-specific analytics are withheld; observations are reported strictly as anonymous tracked trajectories."
            )

        if not metric_allowed:
            lines.append(
                "- Metric spatial calibration is unvalidated or inactive for this session; physical metric distances and speeds are suppressed."
            )

        # 2. Detected Tactical Instructions
        events_seen: Dict[str, Dict[str, Any]] = {}
        for it in items:
            eid = it.get("source_event_id")
            if eid and eid not in events_seen:
                events_seen[eid] = {
                    "category": it.get("event_category"),
                    "action": it.get("event_action"),
                    "w_start": it.get("window_start_s"),
                    "w_end": it.get("window_end_s"),
                }

        if events_seen:
            lines.extend([
                "",
                "## 2. Detected Tactical Instructions",
                "",
            ])
            for eid, ev in sorted(events_seen.items()):
                lines.append(
                    f"- **Instruction [{eid}]**: Category `{ev['category']}`, Action `{ev['action']}`. "
                    f"Target is `UNRESOLVED_TARGET` (the system could not reliably attribute this instruction to an individual participant)."
                )

        # 3. Observed Response Evidence
        if items:
            lines.extend([
                "",
                "## 3. Observed Response Evidence",
                "",
                "Movement evidence observed during the reaction evaluation window [t_end + 2.0s, t_end + 6.0s]:",
                "",
            ])

            for it in items:
                eid = it.get("source_event_id", "UNKNOWN")
                scope = it.get("scope", "ANONYMOUS_TRACK")
                track_id = it.get("anonymous_track_id", "track_unknown")
                w_start = it.get("window_start_s")
                w_end = it.get("window_end_s")
                obs_count = it.get("observations_count", 0)
                disp = it.get("displacement_m")
                spd = it.get("speed_kmh")
                zone = it.get("zone")

                if obs_count == 0:
                    lines.append(
                        f"- **Event {eid} ({w_start}s - {w_end}s)**: Insufficient visual evidence in response window "
                        f"(0 tracking observations detected)."
                    )
                elif scope == "ANONYMOUS_TRACK":
                    desc_parts = [f"- **Trajectory `{track_id}` (Event {eid})**: Observed across {obs_count} frame(s) in window [{w_start}s - {w_end}s]"]
                    if zone:
                        desc_parts.append(f"in zone `{zone}`")
                    if metric_allowed and disp is not None:
                        desc_parts.append(f"with net displacement {disp:.2f}m")
                    if metric_allowed and spd is not None:
                        desc_parts.append(f"at average speed {spd:.2f} km/h")
                    lines.append(", ".join(desc_parts) + ".")
                else:
                    lines.append(f"- **Team-level observation ({eid})**: {obs_count} observations recorded in window.")

        # 4. Limitations
        lines.extend([
            "",
            "## 4. Active Analysis Limitations",
            "",
        ])
        if limitations:
            for lim in limitations:
                lines.append(f"- `{lim}`")
        else:
            lines.append("- No additional system limitations active.")

        # 5. Identity Reliability Notice
        lines.extend([
            "",
            "## 5. Identity Reliability Notice",
            "",
            "This automated tactical analysis operates under fail-closed identity assurance. "
            "Individual physical-player identities cannot be confirmed automatically from overhead/broadcast footage. "
            "Track identifiers represent local visual trajectories, not verified players.",
            "",
            "---",
            "*Report compiled deterministically by the tactical analysis reporting engine.*",
        ])

        return "\n".join(lines)
