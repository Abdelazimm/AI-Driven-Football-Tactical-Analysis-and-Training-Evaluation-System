# CM3070 P0 Contract Test Plan — Revision 1 (REV1)

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 1)  
**Document**: Pre-Implementation Contract Test Specification  
**Status**: `P0_CONTRACT_FREEZE_REV1_READY_FOR_REVIEW`

This document defines the 20 revised pre-implementation contract test suites reflecting all Revision 1 corrections, exact baseline thresholds, decoupled identity assurance, validated fusion windows, and real filesystem targets.

---

## Master Contract Test Suite Registry

| # | Test Suite Identifier | Target Module / Contract | Key Invariants Asserted |
| :- | :--- | :--- | :--- |
| **01** | `test_m1_adapter_to_canonical_vision_result` | `backend/app/adapters/m1_adapter.py` | Asserts exact M1 baseline: `track_high=0.35`, `track_low=0.10`, `new_track=0.35`, `buffer=120`, `match=0.85`, `gmc=none`, checkpoint `ad908a9caf...`. Coordinates $[x_1, y_1, x_2, y_2]$, `opaque_track_id`. |
| **02** | `test_m2_adapter_to_canonical_vision_result` | `backend/app/adapters/m2_adapter.py` | Asserts exact M2 baseline: RF-DETR-L with **score threshold $\ge 0.50$**, `external_nms=False`, OSNet-x1.0 ReID, Deep-EIoU, GTA-Track trajectory mapped to `opaque_track_id`. |
| **03** | `test_m3_adapter_to_canonical_vision_result` | `backend/app/adapters/m3_adapter.py` | Asserts exact M3 baseline: YOLO26 **score threshold $\ge 0.30$**, SRITrack `M3_SRC_DEFAULT` with amended `track_new_th=0.30`, `track_high_th=0.60`, `track_buffer=1000`. |
| **04** | `test_bbox_and_timebase_normalization` | `backend/app/schemas/canonical_vision.py` | Asserts unified single canonical ordering $[x_1, y_1, x_2, y_2]$ for both source pixels and normalized bounds (`x1_norm`, `y1_norm`, `x2_norm`, `y2_norm`). Timestamp derived as $t = \text{frame} / \text{fps}$. |
| **05** | `test_empty_frame_handling` | `backend/app/adapters/common_adapter.py` | Asserts that zero-detection frames emit `is_empty_frame=True` with empty observations list, preserving downstream stability without crashing. |
| **06** | `test_automated_runtime_heuristic_cannot_unlock_player_analytics` | `backend/app/services/identity_safety_service.py` | Asserts that for automated runs (`RUNTIME_HEURISTIC_ONLY`), heuristics cannot grant `PASS_RELIABLE`. `player_level_analysis_allowed` is strictly False; player physical metrics are WITHHELD (`null`). |
| **07** | `test_opaque_track_id_cannot_become_player_pseudonym` | `backend/app/schemas/canonical_vision.py` | Asserts that `opaque_track_id` remains an anonymous trajectory integer and CANNOT populate `physical_player_pseudonym` unless `identity_evidence_basis == HUMAN_ORACLE`. |
| **08** | `test_four_point_calibration_cannot_claim_independent_rmse` | `backend/app/services/calibration_service.py` | Asserts that a user-supplied 4-point homography is classified as `GEOMETRIC_SOLVE_ONLY` and cannot claim independent RMSE. Under `NO_METRIC_CALIBRATION`, metres and km/h are strictly suppressed. |
| **09** | `test_kinematics_outlier_rejection_excludes_over_36kmh` | `backend/app/services/kinematics_service.py` | Asserts outlier semantics are `REJECT_AND_EXCLUDE_OUTLIER`: speeds $> 36.0\text{ km/h}$ are excluded from accepted steps, distance, and speed statistics, and are NEVER clamped. |
| **10** | `test_asr_explicit_failure_no_historical_fallback` | `backend/app/services/asr_service.py` | Asserts that audio extraction or ASR failure emits typed `ASRFailure`, transitions to Vision-only mode (`COMPLETED_WITH_LIMITATIONS`), and NEVER accesses historical Drive transcripts. |
| **11** | `test_fusion_temporal_response_window` | `backend/app/pipeline/fusion.py` | Asserts the scientifically frozen post-command reaction window: $[t_{\text{end}} + 2.0\text{s}, t_{\text{end}} + 6.0\text{s}]$, strictly rejecting the legacy exploratory $[-2\text{s}, +5\text{s}]$ window for response evaluation. |
| **12** | `test_fusion_consumes_real_evidence_only` | `backend/app/pipeline/fusion.py` | Asserts that Fusion output contains zero research mocks: no literal `"PLAYER_01"`, no fixed $339.87\text{s}$, no fixed $2500$ rows, no synthetic $4.5\text{m}$ / $8.2\text{km/h}$. |
| **13** | `test_fusion_forbids_player_scope_under_automated_mode` | `backend/app/pipeline/fusion.py` | Asserts that for automated runs, all emitted evidence items have `scope` in `[TEAM, SPATIAL, EVENT, ANONYMOUS_TRACK]`. Emitting `scope = PLAYER` raises validation error. |
| **14** | `test_oracle_mode_preserves_verified_readback_metrics` | `backend/app/pipeline/fusion.py` | Asserts that mode `VALIDATED_SHOWCASE` preserves verified metrics without recomputation: C04 ($14.30\text{m} \rightarrow 7.96\text{m}$), C06 ($0.70\text{m}, 0.49\text{m}$), C03 (entry $81.20\text{s}$, $100\%$ retention). |
| **15** | `test_llama_model_digest_and_prompt_hash_enforcement` | `backend/app/services/llm_report_service.py` | Asserts Ollama digest `46e0c10c...` and prompt SHA-256 `ab95a835...`. Mismatched digest or modified prompt raises configuration error. |
| **16** | `test_patch_001_exact_8_gates_validation` | `backend/app/services/llm_report_service.py` | Asserts all 8 gates of `LLM_GROUNDING_VALIDATOR_PATCH_001` (Gate 1 Identity Safety, Gate 2 Psych, Gate 3 Privacy, Gate 4 Numeric with `all_numbers_patched`, Gate 5 Negation-aware target, Gate 6 Missing speed, Gate 7 Categories, Gate 8 Actions). |
| **17** | `test_patch_001_rejection_triggers_safe_fallback` | `backend/app/services/llm_report_service.py` | Asserts that validator rejection or Ollama timeout ($> 45\text{s}$) automatically engages `ReportStatus.DETERMINISTIC_FALLBACK` from `StructuredEvidence`. |
| **18** | `test_auto_methodology_resolves_to_m2` | `backend/app/api/jobs.py` | Asserts that submitting `requested_methodology = "AUTO"` resolves to `resolved_methodology = "METHOD_2_RFDETR_GTATRACK"`. |
| **19** | `test_media_duration_policy_accepts_340s_session` | `backend/app/services/media_validation_service.py` | Asserts that media validation service accepts the $339.99\text{s}$ research match video under the harmonized $360.0\text{s}$ ceiling. |
| **20** | `test_asynchronous_orchestrator_heartbeat_and_idempotency` | `backend/app/orchestrator/analysis_orchestrator.py` | Asserts asynchronous execution with monotonically increasing `progress_percent`, stage heartbeats, and unique dispatch constraint `uq_active_worker_dispatch_per_job`. |

---

## Detailed Test Case Specifications

### Test Suite 01: M1 Adapter Baseline Verification
- **Target File**: `backend/app/adapters/m1_adapter.py`
- **Assertions**:
  - `tracker_config["track_high_thresh"] == 0.35`
  - `tracker_config["track_low_thresh"] == 0.10`
  - `tracker_config["new_track_thresh"] == 0.35`
  - `tracker_config["track_buffer"] == 120`
  - `tracker_config["match_thresh"] == 0.85`
  - `tracker_config["gmc_method"] == "none"`
  - `detector_provenance["checkpoint_sha256"] == "ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b"`
  - Emitted `TrackObservation` records coordinate box as $[x_1, y_1, x_2, y_2]$ in source pixels, `opaque_track_id` as int, and `physical_player_pseudonym is None`.

### Test Suite 02: M2 Adapter Baseline Verification
- **Target File**: `backend/app/adapters/m2_adapter.py`
- **Assertions**:
  - `detector_operating_point == 0.50` (formal score threshold $\ge 0.50$; rejects detections below $0.50$)
  - `external_nms is False`
  - `detector_checkpoint_sha256 == "7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85"`
  - Deep-EIoU tracklet preserved in `tracklet_id`
  - GTA-Track final trajectory ID mapped to `opaque_track_id`

### Test Suite 03: M3 Adapter Baseline Verification
- **Target File**: `backend/app/adapters/m3_adapter.py`
- **Assertions**:
  - `detector_operating_point == 0.30` (formal score threshold $\ge 0.30$)
  - `tracker_config["track_new_th"] == 0.30` (P5A amended birth gate)
  - `tracker_config["track_high_th"] == 0.60`
  - `tracker_config["track_buffer"] == 1000`
  - Resolved config hash equals `feeeb76e365a7e2c255e5946e7f7e7c67162530ab06112b6a8b83fbd8403f8ed`

### Test Suite 04: Bounding Box and Timebase Normalization
- **Target File**: `backend/app/schemas/canonical_vision.py`
- **Assertions**:
  - $x_1 < x_2$ and $y_1 < y_2$ strictly enforced.
  - Normalized fields satisfy:
    $$0.0 \le x_1\text{\_norm} < x_2\text{\_norm} \le 1.0 \quad \text{and} \quad 0.0 \le y_1\text{\_norm} < y_2\text{\_norm} \le 1.0$$
  - `source_timestamp_s == round(source_frame_index / source_fps, 4)`

### Test Suite 06: Automated Runtime Heuristic Cannot Unlock Player Analytics
- **Target File**: `backend/app/services/identity_safety_service.py`
- **Fixture**: Automated upload with `identity_evidence_basis == "RUNTIME_HEURISTIC_ONLY"`, clean tracking ($0$ conflicts, ratio $1.1$).
- **Assertions**:
  - `result.identity_status == IdentityStatus.FAIL_UNSAFE_MERGE` (or fail-closed diagnostic)
  - `result.player_level_analysis_allowed is False`
  - `result.withholding_reason` is non-empty.
  - Accumulated player metrics (`distance_covered_m`, `average_speed_kmh`) are strictly `None`.

### Test Suite 09: Kinematics Outlier Rejection Semantics
- **Target File**: `backend/app/services/kinematics_service.py`
- **Fixture**: Trajectory containing instantaneous velocity step of $38.5\text{ km/h}$.
- **Assertions**:
  - Velocity step is flagged with `is_valid = False` and `rejection_reason = "EXCEEDS_36_KMH_OUTLIER_THRESHOLD"`.
  - Step is **excluded** from `distance_covered` and `average_speed`.
  - Velocity is NOT clamped to $36.0\text{ km/h}$.

### Test Suite 11: Multimodal Fusion Temporal Response Window
- **Target File**: `backend/app/pipeline/fusion.py`
- **Fixture**: Instruction event spanning $t = 100.0\text{s}$ to $t = 102.5\text{s}$.
- **Assertions**:
  - `evaluation_start == 104.5` ($t_{\text{end}} + 2.0\text{s}$)
  - `evaluation_end == 108.5` ($t_{\text{end}} + 6.0\text{s}$)
  - Observations occurring prior to $t = 104.5\text{s}$ or after $t = 108.5\text{s}$ are excluded from the reaction evaluation metric.

### Test Suite 16: Exact 8 Gates Validation (Patch 001)
- **Target File**: `backend/app/services/llm_report_service.py`
- **Assertions**:
  - Gate 1: Rejects `Player_01` when player reporting disabled (`UNSUPPORTED_PLAYER_IDENTITY`).
  - Gate 2: Rejects disciplinary word `lazy` (`OVERSTATED_CERTAINTY`).
  - Gate 3: Rejects raw participant name (`PRIVACY_POLICY_VIOLATION`).
  - Gate 4: Traverses all evidence string leaves (`all_numbers_patched`); allows `6.17` when present in string; rejects unlisted `8.42` (`UNSUPPORTED_NUMERIC_CLAIM`).
  - Gate 5: Negation awareness allows `"was not attributed to a specific player"`; rejects affirmative `"attributed to Player 1"` on unresolved target (`CONTRADICTS_INPUT`).
  - Gate 6: Rejects asserted speeds when metric speed declared unavailable (`MISSING_SPEED_INFERRED`).
  - Gate 7: Rejects tactical category not in evidence events (`UNSUPPORTED_EVENT_CATEGORY`).
  - Gate 8: Rejects invented action verbs not in evidence text (`UNSUPPORTED_EVENT_ACTION`).
