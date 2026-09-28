# CM3070 P0 Contract Test Plan — Revision 2 (REV2)

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 2 Final Patch)  
**Document**: Pre-Implementation Contract Test Specification  
**Status**: `P0_CONTRACT_FREEZE_REV2_READY_FOR_FINAL_REVIEW`

This document defines the 29 pre-implementation contract test suites governing the production AI pipeline integration. In strict adherence to P0 REV2 requirements, this test plan does not artificially cap test suites at 20 tests. It rigorously codifies coordinate space separation, decoupled identity assurance, complete frozen ASR execution parameters, LLM benchmark vs provisional timeouts, the geometric calibration permission matrix, dynamic job manifest schemas, and verified artifact provenance.

---

## Master Contract Test Suite Registry

| # | Test Suite Identifier | Target Module / Contract | Key Invariants Asserted |
| :- | :--- | :--- | :--- |
| **01** | `test_m1_adapter_coordinate_and_baseline_invariants` | `backend/app/adapters/m1_adapter.py` | Asserts M1 baseline: 3-tile YOLO11m (`ad908a9caf...`), conf 0.20, IoU 0.70; BoT-SORT `track_high=0.35`, `track_low=0.10`, `new_track=0.35`, `buffer=120`, `match=0.85`, `gmc=none`. Scale projection: $1280 \times 1280 \rightarrow 1920 \times 1080 \rightarrow 3840 \times 2160$ ($s=2.0$). |
| **02** | `test_m2_adapter_coordinate_and_baseline_invariants` | `backend/app/adapters/m2_adapter.py` | Asserts M2 baseline: RF-DETR-L (`7539cfb3ec...`) operating point $\ge 0.50$, `external_nms=False`, OSNet-x1.0, Deep-EIoU, GTA-Track. Scale projection: $704 \times 704 \rightarrow 1920 \times 1080 \rightarrow 3840 \times 2160$ ($s=2.0$). |
| **03** | `test_m3_adapter_coordinate_and_baseline_invariants` | `backend/app/adapters/m3_adapter.py` | Asserts M3 baseline: YOLO26 (`ea9b3e434f...`, 44,081,689 bytes) operating point $\ge 0.30$, SRITrack `M3_SRC_DEFAULT` with amended `track_new_th=0.30`, `track_high_th=0.60`, `track_buffer=1000`. Working space is $1920 \times 1080$ (NOT $1280 \times 720$), projected to $3840 \times 2160$ ($s=2.0$). |
| **04** | `test_methodology_explicit_manual_selection_and_isolation` | `backend/app/pipeline/registry.py` | Asserts M1, M2, and M3 are explicitly manually selectable. Runner instantiates strictly the requested pipeline components; no cross-contamination, no unselected weight loading, no silent fallback between methods. |
| **05** | `test_canonical_bounding_box_and_coordinate_space_separation` | `backend/app/schemas/canonical_vision.py` | Asserts separation of `MEDIA_SOURCE_SPACE`, `VISION_WORKING_SPACE`, and `MODEL_INFERENCE_SPACE`. Canonical `BoundingBox` is strictly in `MEDIA_SOURCE_SPACE` $[x_1, y_1, x_2, y_2]$ with factor-of-two protection from $1920 \times 1080$. |
| **06** | `test_bbox_and_timebase_normalization` | `backend/app/schemas/canonical_vision.py` | Asserts unified ordering $[x_1, y_1, x_2, y_2]$ and normalized coordinates $[0.0, 1.0]$. Timestamp dynamically derived as $t = \text{source\_frame\_index} / \text{source\_fps}$ from probed video metadata. |
| **07** | `test_empty_frame_handling` | `backend/app/adapters/common_adapter.py` | Asserts frames with zero detections emit `is_empty_frame=True` with empty observations list, preserving downstream stability without crashing. |
| **08** | `test_formal_vs_runtime_identity_status_separation` | `backend/app/services/identity_safety_service.py` | Asserts `method_formal_identity_status = FAIL_UNSAFE_MERGE` with `FORMAL_DENSE_GT`, while uploaded runs record `runtime_identity_evidence_basis = RUNTIME_HEURISTIC_ONLY`. Runtime heuristics cannot claim formal unsafe merge. |
| **09** | `test_automated_identity_gate_withholds_player_level_analytics` | `backend/app/services/identity_safety_service.py` | Asserts that when `method_formal_identity_status != PASS_RELIABLE` (automated runs), `player_level_analysis_allowed is False`. Accumulated player metrics (`distance_covered_m`, `average_speed_kmh`) are strictly `None`. |
| **10** | `test_opaque_track_id_cannot_become_player_pseudonym` | `backend/app/schemas/canonical_vision.py` | Asserts that `opaque_track_id` remains an anonymous trajectory integer and CANNOT populate `physical_player_pseudonym` unless `identity_evidence_basis == HUMAN_ORACLE`. |
| **11** | `test_frontend_limitation_wording_reflects_evidence_basis` | `frontend/tactical-ai-insights-main/...` | Asserts frontend limitation banner states that automated methodology did not demonstrate safe persistent identity under formal GT benchmark evaluation; does NOT falsely claim the user upload itself proved `FAIL_UNSAFE_MERGE`. |
| **12** | `test_calibration_permission_matrix_geometric_solve_only` | `backend/app/services/calibration_service.py` | Asserts mode `GEOMETRIC_SOLVE_ONLY` (user 4-point homography) allows bounded 2D pitch visualization but STRICTLY SUPPRESSES metres, km/h, distance, and speed (`null`). `independent_rmse_m is None`. |
| **13** | `test_calibration_permission_matrix_no_calibration` | `backend/app/services/calibration_service.py` | Asserts mode `NO_METRIC_CALIBRATION` or `INVALID_CALIBRATION` suppresses all pitch coordinates, metres, km/h, and physical distance claims. |
| **14** | `test_calibration_permission_matrix_camera_specific_validated` | `backend/app/services/calibration_service.py` | Asserts mode `CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED` permits metric reporting only for verified camera geometry (`d0e9680fdc...`, RMSE $0.6505\text{ m}$). Silently applying to uncalibrated video raises validation error. |
| **15** | `test_kinematics_outlier_rejection_excludes_over_36kmh` | `backend/app/services/kinematics_service.py` | Asserts speeds $> 36.0\text{ km/h}$ are rejected (`REJECT_AND_EXCLUDE_OUTLIER`), excluded from accepted distance and velocity statistics, and NEVER clamped. Tracking gaps $> 0.5\text{s}$ reset kinematics. |
| **16** | `test_frozen_asr_execution_parameters` | `backend/app/services/asr_service.py` | Asserts exact frozen faster-whisper parameters: `faster-whisper==1.2.1`, `base.en`, CTranslate2 CPU int8, 8 threads, 16 kHz mono WAV, beam 5, `word_timestamps=True`, `vad_filter=True`, VAD 500ms, `condition_on_previous_text=False`. |
| **17** | `test_asr_tactical_extraction_and_failure_semantics` | `backend/app/services/asr_service.py` | Asserts 6 normalization rules, 5 schema categories, parent-segment timestamp inheritance, fail-closed target resolution. Explicit failure transitions to Vision-only mode (`COMPLETED_WITH_LIMITATIONS`); zero historical fallback. |
| **18** | `test_fusion_temporal_response_window` | `backend/app/pipeline/fusion.py` | Asserts scientifically frozen post-command reaction window: $[t_{\text{end}} + 2.0\text{s}, t_{\text{end}} + 6.0\text{s}]$, strictly rejecting legacy $[-2\text{s}, +5\text{s}]$ window. |
| **19** | `test_fusion_consumes_real_evidence_only` | `backend/app/pipeline/fusion.py` | Asserts fusion emits zero research mocks: no literal `"PLAYER_01"`, no fixed $339.87\text{s}$, no fixed $2500$ rows, no synthetic $4.5\text{m}$ / $8.2\text{km/h}$. |
| **20** | `test_fusion_forbids_player_scope_under_automated_mode` | `backend/app/pipeline/fusion.py` | Asserts all emitted evidence items under automated mode have `scope` in `[TEAM, SPATIAL, EVENT, ANONYMOUS_TRACK]`. Emitting `scope = PLAYER` raises validation error. |
| **21** | `test_oracle_mode_preserves_verified_readback_metrics` | `backend/app/pipeline/fusion.py` | Asserts mode `VALIDATED_SHOWCASE` preserves verified metrics without recomputation: C04 ($14.30\text{m} \rightarrow 7.96\text{m}$), C06 ($0.70\text{m}, 0.49\text{m}$), C03 (entry $81.20\text{s}$, $100\%$ retention). |
| **22** | `test_llm_model_digest_and_prompt_hash_enforcement` | `backend/app/services/llm_report_service.py` | Asserts Ollama digest `46e0c10c0252...` (Llama 3.1 8B Instruct q4_K_M) and prompt SHA-256 `ab95a835fa9ea77f5e1ad3cb9e9a4f6645fd1fb129486c99ec2447990b7e2124`. Mismatches raise configuration error. |
| **23** | `test_llm_generation_parameters_frozen` | `backend/app/services/llm_report_service.py` | Asserts generation parameters: `temperature = 0.0`, `seed = 42`, `top_p = 1.0`, `num_ctx = 4096`, `retries = 0`. |
| **24** | `test_formal_120s_llm_benchmark_timeout_vs_provisional_timeout` | `backend/app/services/llm_report_service.py` | Asserts `FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120` and `PRODUCTION_LLM_TIMEOUT_SECONDS = 45` labeled `PROVISIONAL_PRODUCT_POLICY`. Timeout engages `ReportStatus.DETERMINISTIC_FALLBACK`. |
| **25** | `test_patch_001_exact_8_gates_validation` | `backend/app/services/llm_report_service.py` | Asserts all 8 gates of `LLM_GROUNDING_VALIDATOR_PATCH_001` (Identity, Psych, Privacy, Numeric with `all_numbers_patched`, Negation, Missing speed, Categories, Actions). |
| **26** | `test_dynamic_job_execution_manifest_probed_metadata` | `backend/app/schemas/manifest.py` | Asserts `JobExecutionManifest` records actual probed container values (`duration_s`, `fps`, `width`, `height`). Rejects hardcoded $339.99\text{s}$, $59.972\text{ FPS}$, $3840 \times 2160$ as universal constants. |
| **27** | `test_manifest_calibration_and_rmse_fields_nullable` | `backend/app/schemas/manifest.py` | Asserts `homography_sha256 is None` unless calibration is active; `rmse_m is None` unless independent validation exists. Separates formal methodology provenance from runtime job diagnostics. |
| **28** | `test_artifact_provenance_and_checkpoint_completeness` | `scripts/verify_checkpoints.py` | Asserts all model weights, configs, and homographies exist with verified SHA-256 hashes (M1 YOLO11m, M2 RF-DETR-L, M3 adapted YOLO26, Research Homography). |
| **29** | `test_media_duration_policy_and_asynchronous_orchestrator` | `backend/app/services/media_validation_service.py` | Asserts probed duration ceiling $360.0\text{s}$ accepts $339.99\text{s}$ session; verifies monotonic progress, heartbeats, and unique active dispatch constraint `uq_active_worker_dispatch_per_job`. |

---

## Detailed Test Case Specifications

### Test Suite 01: M1 Adapter Coordinate & Baseline Invariants
- **Target File**: `backend/app/adapters/m1_adapter.py`
- **Assertions**:
  - `detector_provenance["checkpoint_sha256"] == "ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b"`
  - `detector_operating_point == 0.20`, `global_nms_iou == 0.70`, `tile_overlap == 0.15`.
  - `tracker_config["track_high_thresh"] == 0.35`, `tracker_config["track_low_thresh"] == 0.10`, `tracker_config["new_track_thresh"] == 0.35`, `tracker_config["track_buffer"] == 120`, `tracker_config["match_thresh"] == 0.85`, `tracker_config["gmc_method"] == "none"`.
  - Coordinates scale verification:
    - Input tile coordinates $(x_t, y_t)$ in $[0, 1280]$.
    - Reconstructed full working frame $(x_w, y_w)$ in $[0, 1920] \times [0, 1080]$.
    - Canonical `BoundingBox` $(x_s, y_s)$ in $[0, 3840] \times [0, 2160]$ where $x_s = x_w \times 2.0$, $y_s = y_w \times 2.0$.
    - `physical_player_pseudonym is None`, `opaque_track_id` is typed integer.

### Test Suite 02: M2 Adapter Coordinate & Baseline Invariants
- **Target File**: `backend/app/adapters/m2_adapter.py`
- **Assertions**:
  - `detector_provenance["checkpoint_sha256"] == "7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85"`
  - `detector_operating_point == 0.50` (detections $< 0.50$ strictly discarded).
  - `external_nms is False` (native bipartite matching).
  - Scale projection: internal model inference $(704 \times 704) \rightarrow$ working space $(1920 \times 1080) \rightarrow$ canonical source space $(3840 \times 2160)$ ($s_x = 2.0, s_y = 2.0$).
  - Deep-EIoU tracklet recorded in `tracklet_id`; GTA-Track final trajectory mapped to `opaque_track_id`.

### Test Suite 03: M3 Adapter Coordinate & Baseline Invariants
- **Target File**: `backend/app/adapters/m3_adapter.py`
- **Assertions**:
  - `detector_provenance["checkpoint_path"] == "methodology_comparison/runs/method_3/M3_FORMAL_001_DOMAIN_ADAPTED/checkpoints/M3_ADAPTED_YOLO26M.pt"`
  - `detector_provenance["checkpoint_sha256"] == "ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf"`
  - `detector_provenance["checkpoint_size_bytes"] == 44081689`
  - `detector_operating_point == 0.30`
  - `tracker_config["track_new_th"] == 0.30` (P5A birth gate), `tracker_config["track_high_th"] == 0.60`, `tracker_config["track_buffer"] == 1000`.
  - Working space invariant: `working_space_resolution == (1920, 1080)` (verifies $1920 \times 1080$ and rejects unproven $1280 \times 720$).
  - Canonical `BoundingBox` scale: $x_s = x_w \times 2.0, y_s = y_w \times 2.0$ for 4K source.

### Test Suite 04: Explicit Methodology Selection and Component Isolation
- **Target File**: `backend/app/pipeline/registry.py`
- **Assertions**:
  - Requesting `METHOD_1_YOLO11_BOTSORT` initializes M1 detector/tracker only. M2 and M3 weights are not loaded into memory.
  - Requesting `METHOD_2_RFDETR_GTATRACK` initializes M2 detector/tracker only.
  - Requesting `METHOD_3_YOLO26_SRITRACK` initializes M3 detector/tracker only.
  - No fallback between methods if one fails: failure raises typed execution error.

### Test Suite 05: Coordinate Space Separation & Factor-of-Two Protection
- **Target File**: `backend/app/schemas/canonical_vision.py`
- **Assertions**:
  - `BoundingBox.coordinate_space == CoordinateSpace.MEDIA_SOURCE_SPACE`.
  - For $1920 \times 1080$ working frame and $3840 \times 2160$ source video, bounding box $(100, 200, 300, 400)$ in working space transforms to canonical $(200, 400, 600, 800)$.
  - Factor-of-two protection: asserts $x_{\text{scale}} = \text{width}_{\text{source}} / \text{width}_{\text{working}} = 2.0$.
  - Passing working coordinates directly as source coordinates triggers validation failure.

### Test Suite 08: Formal vs Runtime Identity Status Separation
- **Target File**: `backend/app/services/identity_safety_service.py`
- **Fixture**: Standard user video upload processed with M1, M2, or M3 without manual ground truth.
- **Assertions**:
  - `manifest.method_formal_identity_status == "FAIL_UNSAFE_MERGE"`
  - `manifest.method_formal_identity_evidence_basis == "FORMAL_DENSE_GT"`
  - `job_result.runtime_identity_status in ["UNVERIFIED_HEURISTIC_PASS", "HEURISTIC_FRAGMENTATION_WARNING"]`
  - `job_result.runtime_identity_evidence_basis == "RUNTIME_HEURISTIC_ONLY"`
  - Asserts runtime heuristics CANNOT emit `FAIL_UNSAFE_MERGE` or claim ground-truth verification.
  - `player_level_analysis_allowed is False`.

### Test Suite 11: Frontend Limitation Wording
- **Target File**: `frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.results.tsx`
- **Assertions**:
  - Limitation banner text asserts: `"Automated tracking methodology has not demonstrated sufficiently safe persistent physical-player identity under formal benchmark evaluation. Accumulated player-level analytics are withheld."`
  - Asserts text DOES NOT state that the uploaded video itself proved `FAIL_UNSAFE_MERGE`.

### Test Suite 12: Calibration Permission Matrix — GEOMETRIC_SOLVE_ONLY
- **Target File**: `backend/app/services/calibration_service.py`
- **Fixture**: Job submitted with user-provided 4-point corner calibration.
- **Assertions**:
  - `calibration_mode == CalibrationMode.GEOMETRIC_SOLVE_ONLY`
  - `independent_rmse_m is None`
  - `allow_pitch_radar_visualization is True`
  - `allow_metric_physical_reporting is False`
  - All output speed ($km/h$) and distance ($m$) fields are `None`.

### Test Suite 16: Complete Frozen ASR Execution Parameters
- **Target File**: `backend/app/services/asr_service.py`
- **Assertions**:
  - Engine: `faster-whisper==1.2.1`
  - Model: `base.en`, CTranslate2, `device="cpu"`, `compute_type="int8"`, `cpu_threads=8`.
  - Audio extraction: 16,000 Hz, single channel (mono), 16-bit PCM WAV.
  - Transcription call: `task="transcribe"`, `language="en"`, `beam_size=5`, `word_timestamps=True`, `vad_filter=True`, `vad_parameters={"min_silence_duration_ms": 500}`, `condition_on_previous_text=False`.
  - Hotwords, LLM ASR repair, and external transcript fallbacks are strictly absent.

### Test Suite 24: Formal 120s Benchmark Timeout vs Provisional 45s Product Timeout
- **Target File**: `backend/app/services/llm_report_service.py`
- **Assertions**:
  - `FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS == 120`
  - `PRODUCTION_LLM_TIMEOUT_SECONDS == 45`
  - `timeout_policy_classification == "PROVISIONAL_PRODUCT_POLICY"`
  - Mocking a 50s Ollama response under production policy triggers timeout, logs `LLM_TIMEOUT_FALLBACK_ENGAGED`, and returns deterministic fallback report without crashing.

### Test Suite 26: Dynamic Job Execution Manifest Probed Metadata
- **Target File**: `backend/app/schemas/manifest.py`
- **Fixture**: Probed video with duration $142.5\text{s}$, FPS $29.97$, resolution $1920 \times 1080$.
- **Assertions**:
  - `manifest.media_metadata.duration_s == 142.5`
  - `manifest.media_metadata.fps == 29.97`
  - `manifest.media_metadata.width == 1920`
  - `manifest.media_metadata.height == 1080`
  - Asserts values are NOT overwritten by research session constants ($339.99, 59.972, 3840 \times 2160$).

### Test Suite 27: Manifest Calibration & RMSE Fields Nullable
- **Target File**: `backend/app/schemas/manifest.py`
- **Assertions**:
  - Uncalibrated job: `manifest.calibration_metadata.homography_sha256 is None`, `manifest.calibration_metadata.rmse_m is None`.
  - User 4-point calibrated job: `manifest.calibration_metadata.homography_sha256` is non-empty hex, `manifest.calibration_metadata.rmse_m is None`.
  - Research benchmark job: `manifest.calibration_metadata.homography_sha256 == "d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507"`, `manifest.calibration_metadata.rmse_m == 0.6505`.
