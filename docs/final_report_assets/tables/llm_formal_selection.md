# LLM frozen formal selection evidence

Both candidates avoided unsupported player identity and unavailable-evidence misuse. Llama 3.1 was selected after 15/16 schema-valid runs versus Qwen3's 5/16.

| candidate | completed_of_16 | timeout_of_16 | schema_valid_of_16 | raw_pre_patch_gate_pass_of_16 |
| --- | --- | --- | --- | --- |
| Qwen3 8B | 5 | 11 | 5 | 2 |
| Llama 3.1 8B | 15 | 1 | 15 | 0 |

**Guardrail:** Raw pre-patch gate flags misclassified authorized numbers from string observations; do not interpret 0/16 as 16 hallucinations. Post-patch full benchmark was not rerun.

**Sources:** G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\llm\LLM_SELECTION_DECISION.json; G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\llm\LLM_FINAL_INTEGRATION_FREEZE.json
