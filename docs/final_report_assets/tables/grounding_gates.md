# Eight deterministic report-grounding gates

Patch-001 preserves eight checks for identity, privacy, missing data and unsupported claims.

| gate | frozen_check |
| --- | --- |
| 1 | IDENTITY_SAFETY_NEW_PLAYER_ID |
| 2 | PROHIBITED_PSYCHOLOGICAL_INFERENCE |
| 3 | PRIVACY_NAME_LEAK |
| 4 | UNSUPPORTED_NUMERIC_VALUES (Patched: Full payload leaf traversal + exact float normalization) |
| 5 | UNRESOLVED_TARGET_BECAME_RESOLVED (Patched: Affirmative resolution vs safe negated limitations) |
| 6 | MISSING_SPEED_INFERRED |
| 7 | UNSUPPORTED_EVENT_CATEGORY |
| 8 | UNSUPPORTED_EVENT_ACTION |

**Guardrail:** The gate list specifies intended validation scope; it is not an empirical pass-rate result.

**Sources:** G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\llm\LLM_FINAL_INTEGRATION_FREEZE.json
