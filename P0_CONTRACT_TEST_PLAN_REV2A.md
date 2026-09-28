# CM3070 P0 Contract Test Plan — Revision 2A (REV2A)

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 2A Final Consistency Hotfix)  
**Document**: Pre-Implementation Contract Test Specification  
**Status**: `P0_CONTRACT_FREEZE_REV2A_READY_FOR_APPROVAL`

This document defines the 29 pre-implementation contract test suites governing the production AI pipeline integration. It strictly incorporates all Revision 2A consistency hotfixes: exact two-tier M1 baseline thresholds (purging historical Stage 4B values), real adapter coordinate-space lifecycles (anti-double-scaling), full 64-character LLM cryptographic hashes, time-based kinematics continuity ($\Delta t > 0.50\text{s}$), exact 5-category ASR tactical taxonomy, and unified 120s initial production LLM timeout.

---

## Master Contract Test Suite Registry

| # | Test Suite Identifier | Target Module / Contract | Key Invariants Asserted |
| :- | :--- | :--- | :--- |
| **01** | `test_m1_adapter_coordinate_and_baseline_invariants` | `backend/app/adapters/m1_adapter.py` | Asserts exact frozen M1 baseline: detector `epoch28.pt` (`ad908a9caf75...`, 104,950,959 bytes) and ReID `yolo26n-reid.onnx` (`8529c383197a...`, 9,873,245 bytes). Thresholds: `candidate_floor = 0.05`, `qualification = 0.25`, `tile_nms = 0.70`, `global_nms = 0.50` (purges historical 0.20/0.70 values). Tracker: `high = 0.35`, `low = 0.10`, `new = 0.35`, `buffer = 120`, `match = 0.85`, `gmc = none`, `reid = true`, `fuse_score = true`. Coordinates: native $1920 \times 1080$ working space projected to source space ($s_x = 2.0, s_y = 2.0$); no double-scaling. |
| **02** | `test_m2_adapter_coordinate_and_baseline_invariants` | `backend/app/adapters/m2_adapter.py` | Asserts M2 baseline: RF-DETR-L `checkpoint_best_total.pth` (`7539cfb3eca3...`, 134,747,227 bytes) with operating point $\ge 0.50$, `external_nms = False`, and ReID `sports_model.pth.tar-60` (`8d5b2fd8763d...`, 30,393,613 bytes). Coordinate lifecycle: runner outputs native $1920 \times 1080$ working space; adapter does NOT apply $704 \rightarrow 1920$ scale; adapter applies ONLY source transform ($s_x = W_{\text{source}}/1920.0, s_y = H_{\text{source}}/1080.0$). |
| **03** | `test_m3_adapter_coordinate_and_baseline_invariants` | `backend/app/adapters/m3_adapter.py` | Asserts M3 baseline: YOLO26 (`ea9b3e434ffd...`, 44,081,689 bytes) operating point $\ge 0.30$, SRITrack `track_new_th = 0.30` (amended from source-default 0.70), `track_high_th = 0.60`, `track_buffer = 1000`. Working space is verified $1920 \times 1080$ (rejects unproven 720p); adapter does NOT scale from 1280; applies source transform to $3840 \times 2160$ ($s = 2.0$). |
| **04** | `test_methodology_explicit_manual_selection_and_isolation` | `backend/app/pipeline/registry.py` | Asserts M1, M2, and M3 are explicitly manually selectable. Runner instantiates strictly the requested pipeline components; zero cross-contamination, zero unselected weight loading, zero silent fallback between methods. |
| **05** | `test_canonical_bounding_box_and_coordinate_space_separation` | `backend/app/schemas/canonical_vision.py` | Asserts separation of `MEDIA_SOURCE_SPACE`, `VISION_WORKING_SPACE`, and `MODEL_INFERENCE_SPACE`. Canonical `BoundingBox` is strictly in `MEDIA_SOURCE_SPACE` $[x_1, y_1, x_2, y_2]$ with factor-of-two protection from $1920 \times 1080$. Anti-double-scaling verified. |
| **06** | `test_bbox_and_timebase_normalization` | `backend/app/schemas/canonical_vision.py` | Asserts unified ordering $[x_1, y_1, x_2, y_2]$ and normalized coordinates $[0.0, 1.0]$. Timestamp dynamically derived as $t = \text{source\_frame\_index} / \text{source\_fps}$ from probed video metadata. |
| **07** | `test_empty_frame_handling` | `backend/app/adapters/common_adapter.py` | Asserts frames with zero detections emit `is_empty_frame=True` with empty observations list, preserving downstream stability without crashing. |
| **08** | `test_formal_vs_runtime_identity_status_separation` | `backend/app/services/identity_safety_service.py` | Asserts `method_formal_identity_status = FAIL_UNSAFE_MERGE` with `FORMAL_DENSE_GT`, while uploaded runs record `runtime_identity_evidence_basis = RUNTIME_HEURISTIC_ONLY`. Runtime heuristics cannot claim formal unsafe merge. |
| **09** | `test_automated_identity_gate_withholds_player_level_analytics` | `backend/app/services/identity_safety_service.py` | Asserts that when `method_formal_identity_status != PASS_RELIABLE` (automated runs), `player_level_analysis_allowed is False`. Accumulated player metrics (`distance_covered_m`, `average_speed_kmh`) are strictly `None`. |
| **10** | `test_opaque_track_id_cannot_become_player_pseudonym` | `backend/app/schemas/canonical_vision.py` | Asserts that `opaque_track_id` remains an anonymous trajectory integer and CANNOT populate `physical_player_pseudonym` unless `identity_evidence_basis == HUMAN_ORACLE`. |
| **11** | `test_frontend_limitation_wording_reflects_evidence_basis` | `frontend/tactical-ai-insights-main/...` | Asserts limitation banner text states automated methodology did not demonstrate safe persistent identity under formal GT benchmark evaluation; does NOT falsely claim the user upload itself proved `FAIL_UNSAFE_MERGE`. |
| **12** | `test_calibration_permission_matrix_geometric_solve_only` | `backend/app/services/calibration_service.py` | Asserts mode `GEOMETRIC_SOLVE_ONLY` (user 4-point homography) allows bounded 2D pitch visualization but STRICTLY SUPPRESSES metres, km/h, distance, and speed (`null`). `independent_rmse_m is None`. |
| **13** | `test_calibration_permission_matrix_no_calibration` | `backend/app/services/calibration_service.py` | Asserts mode `NO_METRIC_CALIBRATION` or `INVALID_CALIBRATION` suppresses all pitch coordinates, metres, km/h, and physical distance claims. |
| **14** | `test_calibration_permission_matrix_camera_specific_validated` | `backend/app/services/calibration_service.py` | Asserts mode `CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED` permits metric reporting only for verified camera geometry (`d0e9680fdcdf...`, RMSE $0.6505\text{ m}$). Silently applying to uncalibrated video raises validation error. |
| **15** | `test_kinematics_velocity_continuity_and_outlier_rejection` | `backend/app/services/kinematics_service.py` | Asserts velocity continuity is strictly time-based: $\Delta t = (\text{frame}_i - \text{frame}_{i-1})/\text{fps}$. If $\Delta t > 0.50\text{ s}$, reset velocity continuity without interpolation. Rejects 120-frame continuity rule (clarifies 120 frames is BoT-SORT track buffer). Speeds $> 36.0\text{ km/h}$ rejected (`REJECT_AND_EXCLUDE_OUTLIER`), never clamped. 7-point median filtering verified. |
| **16** | `test_frozen_asr_execution_parameters` | `backend/app/services/asr_service.py` | Asserts exact frozen faster-whisper parameters: `faster-whisper==1.2.1`, `base.en`, CTranslate2 CPU int8, 8 threads, 16 kHz mono WAV, beam 5, `word_timestamps=True`, `vad_filter=True`, VAD 500ms, `condition_on_previous_text=False`. |
| **17** | `test_asr_tactical_taxonomy_and_keyword_mapping` | `backend/app/services/asr_service.py` | Asserts exact 5 tactical categories: `Defensive`, `Offensive`, `Pressing`, `Passing`, `Positioning / Hold Ground`. Strictly rejects `COVERAGE`, `TRANSITION`, `TACTICAL_DISCIPLINE`. Asserts deterministic keyword mapping, parent-segment timestamp inheritance, and fail-closed targets. Explicit error emission with zero historical fallback. |
| **18** | `test_fusion_temporal_response_window` | `backend/app/pipeline/fusion.py` | Asserts scientifically frozen post-command reaction window: $[t_{\text{end}} + 2.0\text{s}, t_{\text{end}} + 6.0\text{s}]$, strictly rejecting legacy $[-2\text{s}, +5\text{s}]$ window. |
| **19** | `test_fusion_consumes_real_evidence_only` | `backend/app/pipeline/fusion.py` | Asserts fusion emits zero research mocks: no literal `"PLAYER_01"`, no fixed $339.87\text{s}$, no fixed $2500$ rows, no synthetic $4.5\text{m}$ / $8.2\text{km/h}$. |
| **20** | `test_fusion_forbids_player_scope_under_automated_mode` | `backend/app/pipeline/fusion.py` | Asserts all emitted evidence items under automated mode have `scope` in `[TEAM, SPATIAL, EVENT, ANONYMOUS_TRACK]`. Emitting `scope = PLAYER` raises validation error. |
| **21** | `test_oracle_mode_preserves_verified_readback_metrics` | `backend/app/pipeline/fusion.py` | Asserts mode `VALIDATED_SHOWCASE` preserves verified metrics without recomputation: C04 ($14.30\text{m} \rightarrow 7.96\text{m}$), C06 ($0.70\text{m}, 0.49\text{m}$), C03 (entry $81.20\text{s}$, $100\%$ retention). |
| **22** | `test_llm_model_digest_and_prompt_hash_enforcement` | `backend/app/services/llm_report_service.py` | Asserts complete exact model digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` (Llama 3.1 8B Instruct q4_K_M) and prompt SHA-256 `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`. Mismatches raise configuration error. |
| **23** | `test_llm_generation_parameters_frozen` | `backend/app/services/llm_report_service.py` | Asserts generation parameters: `temperature = 0.0`, `seed = 42`, `top_p = 1.0`, `num_ctx = 4096`, `retries = 0`. |
| **24** | `test_llm_timeout_unification_and_fallback_engagement` | `backend/app/services/llm_report_service.py` | Asserts `FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120` and initial `PRODUCTION_LLM_TIMEOUT_SECONDS = 120`, configurable via `LLM_TIMEOUT_SECONDS`. Labeled 45s strictly as provisional candidate policy. Timeout engages `ReportStatus.DETERMINISTIC_FALLBACK` without crashing. |
| **25** | `test_patch_001_exact_8_gates_validation` | `backend/app/services/llm_report_service.py` | Asserts all 8 gates of `LLM_GROUNDING_VALIDATOR_PATCH_001` (Identity, Psych, Privacy, Numeric with `all_numbers_patched`, Negation, Missing speed, Taxonomy, Actions). |
| **26** | `test_dynamic_job_execution_manifest_probed_metadata` | `backend/app/schemas/manifest.py` | Asserts `JobExecutionManifest` records actual probed container values (`duration_s`, `fps`, `width`, `height`). Rejects hardcoded $339.99\text{s}$, $59.972\text{ FPS}$, $3840 \times 2160$ as universal constants. |
| **27** | `test_manifest_calibration_and_rmse_fields_nullable` | `backend/app/schemas/manifest.py` | Asserts `homography_sha256 is None` unless calibration is active; `rmse_m is None` unless independent validation exists. Separates formal methodology provenance from runtime job diagnostics. |
| **28** | `test_artifact_provenance_and_checkpoint_completeness` | `scripts/verify_checkpoints.py` | Asserts all model weights, configs, and homographies exist with verified SHA-256 hashes (M1 YOLO11m `epoch28.pt`, M2 RF-DETR-L `checkpoint_best_total.pth` & `sports_model.pth.tar-60`, M3 adapted YOLO26, Research Homography). |
| **29** | `test_media_duration_policy_and_asynchronous_orchestrator` | `backend/app/services/media_validation_service.py` | Asserts probed duration ceiling $360.0\text{s}$ accepts $339.99\text{s}$ session; verifies monotonic progress, heartbeats, and unique active dispatch constraint `uq_active_worker_dispatch_per_job`. |

---

## Detailed Test Case Specifications

### Test Suite 01: M1 Adapter Thresholds & Anti-Double-Scaling
- **Target File**: `backend/app/adapters/m1_adapter.py`
- **Assertions**:
  - `detector_provenance["checkpoint_path"] == "runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt"`
  - `detector_provenance["checkpoint_filename"] == "epoch28.pt"`
  - `detector_provenance["checkpoint_sha256"] == "ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b"`
  - `detector_provenance["checkpoint_size_bytes"] == 104950959`
  - `reid_provenance["checkpoint_path"] == "runs/method_1/M1_FINAL_EVALUATION_BASELINE/checkpoints/yolo26n-reid.onnx"`
  - `reid_provenance["checkpoint_sha256"] == "8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb"`
  - `reid_provenance["checkpoint_size_bytes"] == 9873245`
  - `tracker_input_candidate_confidence_floor == 0.05`
  - `standalone_qualification_confidence == 0.25`
  - `tile_nms_iou == 0.70`
  - `global_nms_iou == 0.50`
  - Asserts historical Stage 4B values (`conf = 0.20`, `global_nms = 0.70`, size 40.5MB) are NOT present in final M1 configuration.
  - `tracker_config["track_high_thresh"] == 0.35`, `tracker_config["track_low_thresh"] == 0.10`, `tracker_config["new_track_thresh"] == 0.35`, `tracker_config["track_buffer"] == 120`, `tracker_config["match_thresh"] == 0.85`, `tracker_config["gmc_method"] == "none"`, `tracker_config["proximity_thresh"] == 0.15`, `tracker_config["appearance_thresh"] == 0.88`, `tracker_config["with_reid"] is True`, `tracker_config["fuse_score"] is True`.
  - Coordinates verification:
    - Ultralytics restores tile detections to tile pixel coordinates.
    - Remapped boxes are stitched into $1920 \times 1080$ `VISION_WORKING_SPACE`.
    - Adapter projects to `MEDIA_SOURCE_SPACE` using $s_x = W_{\text{source}}/1920.0, s_y = H_{\text{source}}/1080.0$.
    - Verifies adapter does NOT apply an artificial $1280 \rightarrow 1920$ rescale.

### Test Suite 02: M2 Adapter Anti-Double-Scaling Verification
- **Target File**: `backend/app/adapters/m2_adapter.py`
- **Assertions**:
  - `detector_provenance["checkpoint_path"] == "runs/method_2/M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth"`
  - `detector_provenance["checkpoint_filename"] == "checkpoint_best_total.pth"`
  - `detector_provenance["checkpoint_sha256"] == "7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85"`
  - `detector_provenance["checkpoint_size_bytes"] == 134747227`
  - `reid_provenance["checkpoint_path"] == "runs/method_2/M2_P0_preflight/checkpoints/sports_model.pth.tar-60"`
  - `reid_provenance["checkpoint_filename"] == "sports_model.pth.tar-60"`
  - `reid_provenance["checkpoint_sha256"] == "8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd"`
  - `reid_provenance["checkpoint_size_bytes"] == 30393613`
  - `detector_operating_point == 0.50` (detections $< 0.50$ discarded).
  - `external_nms is False`.
  - Asserts RF-DETR runner postprocesses internal $704 \times 704$ tensor detections directly to $1920 \times 1080$ `VISION_WORKING_SPACE` before Deep-EIoU tracklet association.
  - Asserts adapter receives $1920 \times 1080$ coordinates and applies ONLY the source transform ($s_x = 2.0, s_y = 2.0$ for 4K).
  - Asserts adapter does NOT apply a second $704 \rightarrow 1920$ scaling factor.

### Test Suite 03: M3 Adapter Coordinate & Checkpoint Invariants
- **Target File**: `backend/app/adapters/m3_adapter.py`
- **Assertions**:
  - `detector_provenance["checkpoint_path"] == "methodology_comparison/runs/method_3/M3_FORMAL_001_DOMAIN_ADAPTED/checkpoints/M3_ADAPTED_YOLO26M.pt"`
  - `detector_provenance["checkpoint_sha256"] == "ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf"`
  - `detector_provenance["checkpoint_size_bytes"] == 44081689`
  - `detector_operating_point == 0.30`
  - `tracker_config["track_new_th"] == 0.30` (amended from source-default 0.70 via P5A score compatibility amendment), `tracker_config["track_high_th"] == 0.60`, `tracker_config["track_buffer"] == 1000`.
  - Asserts SRITrack operates directly on $1920 \times 1080$ working space; rejects unproven 720p assumptions.
  - Asserts adapter applies ONLY source projection ($1920 \times 1080 \rightarrow 3840 \times 2160$, $s_x = 2.0, s_y = 2.0$).

### Test Suite 15: Kinematics Time-Based Velocity Continuity
- **Target File**: `backend/app/services/kinematics_service.py`
- **Assertions**:
  - Consecutive observations with $\Delta t = (\text{frame}_i - \text{frame}_{i-1}) / \text{fps} \le 0.50\text{ s}$ maintain velocity continuity.
  - Temporal gap with $\Delta t > 0.50\text{ s}$ triggers velocity continuity reset; no velocity is computed across the gap, and no spatial interpolation occurs.
  - Rejects any hardcoded frame-count threshold independent of FPS. Clarifies that the 120-frame quantity belongs strictly to BoT-SORT's `track_buffer = 120`.
  - Velocity step $> 36.0\text{ km/h}$ flagged with `is_valid = False` (`REJECT_AND_EXCLUDE_OUTLIER`), excluded from accepted distance and velocity calculations, and NEVER clamped to $36.0\text{ km/h}$.
  - 7-point median filtering verified on planar coordinate series.

### Test Suite 17: ASR Tactical Taxonomy & Keyword Mapping
- **Target File**: `backend/app/services/asr_service.py`
- **Assertions**:
  - Schema contains EXACTLY the five frozen tactical categories:
    1. `Defensive`
    2. `Offensive`
    3. `Pressing`
    4. `Passing`
    5. `Positioning / Hold Ground`
  - Schema STRICTLY EXCLUDES `COVERAGE`, `TRANSITION`, and `TACTICAL_DISCIPLINE`.
  - Keyword extractor deterministically maps:
    - `"defend"`, `"defence"`, `"defense"`, `"drop back"`, `"mark"`, `"cover"` $\rightarrow$ `Defensive`
    - `"attack"`, `"shoot"`, `"go forward"`, `"make a run"`, `"run forward"` $\rightarrow$ `Offensive`
    - `"press"`, `"close down"`, `"pressure"`, `"sprint"` $\rightarrow$ `Pressing`
    - `"pass"`, `"play the ball"`, `"switch the ball"` $\rightarrow$ `Passing`
    - `"hold your position"`, `"hold position"`, `"hold your ground"`, `"stay in position"`, `"stick to your zone"`, `"stay in your zone"`, `"keep your shape"` $\rightarrow$ `Positioning / Hold Ground`
  - Parent-segment timestamp inheritance: tactical event inherits $[t_{\text{start}}, t_{\text{end}}]$ from parent Whisper segment.
  - Target player defaults to `None` (`UNRESOLVED_TARGET`).
  - Audio extraction or Whisper error emits explicit `ASRFailure` with zero historical transcript fallback.

### Test Suite 22: Complete LLM Cryptographic Identity
- **Target File**: `backend/app/services/llm_report_service.py`
- **Assertions**:
  - Query to local Ollama verifies model `llama3.1:8b`.
  - Exact model digest asserted:
    `digest == "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"`
  - Exact system prompt SHA-256 asserted:
    `prompt_sha256 == "ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce"`
  - Asserts that truncated hash prefixes or altered digests raise configuration error.

### Test Suite 24: Unified LLM Timeout & Deterministic Fallback
- **Target File**: `backend/app/services/llm_report_service.py`
- **Assertions**:
  - `FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS == 120`
  - Initial `PRODUCTION_LLM_TIMEOUT_SECONDS == 120`
  - Production timeout is configurable via environment variable `LLM_TIMEOUT_SECONDS`.
  - Labeled 45s cutoff strictly as a historical provisional candidate policy awaiting E2E benchmarking.
  - Zero-retry policy: `retries == 0`.
  - Mocking an Ollama timeout automatically engages `ReportStatus.DETERMINISTIC_FALLBACK` from `StructuredEvidence` without failing the job.
