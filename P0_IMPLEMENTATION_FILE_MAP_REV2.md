# CM3070 P0 Implementation File Map — Revision 2 (REV2)

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 2 Final Patch)  
**Document**: Authoritative Implementation File Registry & Subsystem Map  
**Status**: `P0_CONTRACT_FREEZE_REV2_READY_FOR_FINAL_REVIEW`

This document details the concrete, verified filesystem paths for all implementation targets under the P0 REV2 architecture contract freeze. Every file has been cross-referenced against the actual repository tree to prevent parallel duplicate modules or dead-end paths.

---

## Action Classification Schema
- **`EXISTING_ADAPT`**: File currently exists in the primary product repository and requires bounded, verified modifications.
- **`REPLACE_STUB`**: File currently exists in the repository as a placeholder raising `NotImplementedError`; will be replaced with real contract-compliant logic.
- **`NEW_REQUIRED`**: File does not exist and will be created as a new module.
- **`REDESIGN_EXISTING`**: Existing product file contains research-incompatible or mock logic and will be redesigned from scratch while preserving valid scientific algorithms.

---

## Master Implementation File Registry

| # | Verified Primary Filesystem Path | Classification | Subsystem Responsibility | Source Research Lineage | Validating Contract Test |
| :- | :--- | :--- | :--- | :--- | :--- |
| **01** | `backend/app/schemas/canonical_vision.py` | **NEW_REQUIRED** | Framewise common Vision contract schemas (`SessionVisionResult`, `FrameVisionResult`, `TrackObservation`, `BoundingBox`). Defines coordinate space enum (`MEDIA_SOURCE_SPACE`, `VISION_WORKING_SPACE`, `MODEL_INFERENCE_SPACE`). Canonical bounding box strictly in `MEDIA_SOURCE_SPACE` $[x_1, y_1, x_2, y_2]$. Documents exact scale transforms. | Redesigned framewise common schema | `test_canonical_bounding_box_and_coordinate_space_separation`, `test_bbox_and_timebase_normalization` |
| **02** | `backend/app/schemas/manifest.py` | **NEW_REQUIRED** | Schema for dynamic `JobExecutionManifest`. Records probed video metadata (`duration_s`, `fps`, `resolution_width`, `resolution_height`). Separates formal methodology provenance (`method_formal_identity_status`) from runtime job diagnostics (`runtime_identity_status`). Calibration fields (`homography_sha256`, `rmse_m`) are nullable/conditional. | Dynamic Manifest Specification | `test_dynamic_job_execution_manifest_probed_metadata`, `test_manifest_calibration_and_rmse_fields_nullable` |
| **03** | `backend/app/adapters/m1_adapter.py` | **NEW_REQUIRED** | M1 adapter: Projects YOLO11m 3-tile global NMS detections + BoT-SORT tracks to canonical coordinates ($1280 \times 1280 \rightarrow 1920 \times 1080 \rightarrow 3840 \times 2160$); assigns `opaque_track_id`. Factor-of-two protection enforced. | `runs/method_1/M1_FINAL_EVALUATION_BASELINE/` | `test_m1_adapter_coordinate_and_baseline_invariants` |
| **04** | `backend/app/adapters/m2_adapter.py` | **NEW_REQUIRED** | M2 adapter: Projects RF-DETR-L ($\text{conf} \ge 0.50$, no NMS) + Deep-EIoU tracklets + GTA-Track global IDs to canonical coordinates ($704 \times 704 \rightarrow 1920 \times 1080 \rightarrow 3840 \times 2160$). Factor-of-two protection enforced. | `runs/method_2/M2_FINAL_EVALUATION_BASELINE/` | `test_m2_adapter_coordinate_and_baseline_invariants` |
| **05** | `backend/app/adapters/m3_adapter.py` | **NEW_REQUIRED** | M3 adapter: Projects YOLO26 (`ea9b3e434f...`, $\text{conf} \ge 0.30$) + SRITrack-v1 (amended birth gate $0.30$) + DINOv3 to canonical coordinates. Native working space is verified $1920 \times 1080$ (NOT $1280 \times 720$), projected to $3840 \times 2160$ ($s=2.0$). | `runs/method_3/M3_P5_identity_calibration/` | `test_m3_adapter_coordinate_and_baseline_invariants` |
| **06** | `backend/app/adapters/common_adapter.py` | **NEW_REQUIRED** | Base adapter classes, frame sequence validation, coordinate projection helpers, and graceful empty-frame handling (`is_empty_frame=True`). | None (Common Architecture) | `test_empty_frame_handling` |
| **07** | `backend/app/services/identity_safety_service.py` | **NEW_REQUIRED** | Evaluates decoupled identity assurance. Stores `method_formal_identity_status = FAIL_UNSAFE_MERGE` with `FORMAL_DENSE_GT` and `runtime_identity_evidence_basis = RUNTIME_HEURISTIC_ONLY`. Enforces fail-closed withholding (`player_level_analysis_allowed = false`). | `vision_contract.py` fail-closed validator | `test_formal_vs_runtime_identity_status_separation`, `test_automated_identity_gate_withholds_player_level_analytics` |
| **08** | `backend/app/pipeline/identity.py` | **REPLACE_STUB** | Replaces existing `NotImplementedError` stub to dispatch to `IdentitySafetyService`. | None (Primary Pipeline) | `test_automated_identity_gate_withholds_player_level_analytics` |
| **09** | `backend/app/services/calibration_service.py` | **NEW_REQUIRED** | Implements Calibration Permission Matrix (`CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED`, `GEOMETRIC_SOLVE_ONLY`, `NO_METRIC_CALIBRATION`, `INVALID_CALIBRATION`). Suppresses metric units under `GEOMETRIC_SOLVE_ONLY`. | `config/3v3_homography_measured_metric_corrected.json` | `test_calibration_permission_matrix_geometric_solve_only`, `test_calibration_permission_matrix_camera_specific_validated` |
| **10** | `backend/app/pipeline/calibration.py` | **REPLACE_STUB** | Replaces existing `NotImplementedError` stub to dispatch to `CalibrationService`. | None (Primary Pipeline) | `test_calibration_permission_matrix_geometric_solve_only` |
| **11** | `backend/app/services/kinematics_service.py` | **NEW_REQUIRED** | 7-point median filtering, gap resets across $> 0.5\text{s}$, and outlier rejection (`speed > 36 km/h` excluded from accepted steps, never clamped). | `physical_metric_upgrade/` | `test_kinematics_outlier_rejection_excludes_over_36kmh` |
| **12** | `backend/app/pipeline/kinematics.py` | **REPLACE_STUB** | Replaces existing `NotImplementedError` stub to dispatch to `KinematicsService`. | None (Primary Pipeline) | `test_kinematics_outlier_rejection_excludes_over_36kmh` |
| **13** | `backend/app/services/asr_service.py` | **NEW_REQUIRED** | Frozen ASR execution: `faster-whisper==1.2.1`, `base.en`, CTranslate2 CPU int8, 8 threads, 16 kHz mono WAV, beam 5, VAD 500ms, `condition_on_previous_text=False`. 6 normalization rules, 5 schema categories, timestamp inheritance, fail-closed targets, zero historical fallback. | `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json` | `test_frozen_asr_execution_parameters`, `test_asr_tactical_extraction_and_failure_semantics` |
| **14** | `backend/app/pipeline/audio.py` | **REPLACE_STUB** | Replaces existing `NotImplementedError` stub to dispatch to `ASRService`. | None (Primary Pipeline) | `test_frozen_asr_execution_parameters` |
| **15** | `backend/app/pipeline/fusion.py` | **REDESIGN_EXISTING** | Multimodal temporal alignment engine using validated $[t_{\text{end}} + 2\text{s}, t_{\text{end}} + 6\text{s}]$ window. Strips research mocks (`PLAYER_01`). Forbids player scope under automated mode. Preserves Oracle showcase readback metrics. | `backend/pipeline/fusion.py` (temporal logic only) | `test_fusion_temporal_response_window`, `test_fusion_consumes_real_evidence_only`, `test_oracle_mode_preserves_verified_readback_metrics` |
| **16** | `backend/app/pipeline/evidence.py` | **REPLACE_STUB** | Replaces existing `NotImplementedError` stub to build structured evidence across typed scopes (`TEAM`, `SPATIAL`, `EVENT`, `ANONYMOUS_TRACK`). | None (Primary Pipeline) | `test_fusion_forbids_player_scope_under_automated_mode` |
| **17** | `backend/app/services/llm_report_service.py` | **NEW_REQUIRED** | Local Ollama Llama 3.1 8B client (digest `46e0c10c0252...`), prompt SHA-256 validation (`ab95a835fa...`), `FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120` vs `PRODUCTION_LLM_TIMEOUT_SECONDS = 45` (`PROVISIONAL_PRODUCT_POLICY`), `LLM_GROUNDING_VALIDATOR_PATCH_001` (8 gates), deterministic fallback. Frozen generation: temp 0, seed 42, top_p 1.0, context 4096, zero-retry. | `LLM_GROUNDING_VALIDATOR_PATCH_001.md` | `test_llm_model_digest_and_prompt_hash_enforcement`, `test_llm_generation_parameters_frozen`, `test_formal_120s_llm_benchmark_timeout_vs_provisional_timeout`, `test_patch_001_exact_8_gates_validation` |
| **18** | `backend/app/pipeline/reporting.py` | **REPLACE_STUB** | Replaces existing `NotImplementedError` stub to dispatch to `LLMReportService`. | None (Primary Pipeline) | `test_formal_120s_llm_benchmark_timeout_vs_provisional_timeout` |
| **19** | `backend/app/pipeline/detection.py` | **EXISTING_ADAPT** | Existing file containing Stage 4B horizontal tiling functions (`generate_horizontal_tiles`, `remap_tile_bbox_to_full_frame`, `apply_global_nms`). Export functions for M1 adapter. | Stage 4B Tiling Utility | `test_m1_adapter_coordinate_and_baseline_invariants` |
| **20** | `backend/app/pipeline/tracking.py` | **REPLACE_STUB** | Replaces existing `NotImplementedError` stub to route tracking requests to selected methodology adapter. | None (Primary Pipeline) | `test_methodology_explicit_manual_selection_and_isolation` |
| **21** | `backend/app/pipeline/registry.py` | **EXISTING_ADAPT** | Registers production executors for M1, M2, and M3; enforces strict component isolation and manual selection; prevents unselected method loading. | None (Primary Pipeline) | `test_methodology_explicit_manual_selection_and_isolation` |
| **22** | `backend/app/services/dispatch_service.py` | **EXISTING_ADAPT** | Verified dispatch service; adapts methodology resolution (`AUTO` $\rightarrow$ `METHOD_2_RFDETR_GTATRACK`) and enforces unique active dispatch (`uq_active_worker_dispatch_per_job`). | None (Product Control Plane) | `test_methodology_explicit_manual_selection_and_isolation`, `test_media_duration_policy_and_asynchronous_orchestrator` |
| **23** | `backend/app/services/media_validation_service.py` | **EXISTING_ADAPT** | Verified media validation service; adapts authoritative ffprobe video duration ceiling to 360.0s. Records dynamic container values. | None (Product Ingestion) | `test_dynamic_job_execution_manifest_probed_metadata`, `test_media_duration_policy_and_asynchronous_orchestrator` |
| **24** | `backend/app/core/config.py` | **EXISTING_ADAPT** | Updates `MAX_VIDEO_DURATION_SECONDS` from 300.0 to 360.0; defines LLM benchmark and provisional timeout settings. | None (System Config) | `test_formal_120s_llm_benchmark_timeout_vs_provisional_timeout`, `test_media_duration_policy_and_asynchronous_orchestrator` |
| **25** | `backend/app/schemas/video.py` | **EXISTING_ADAPT** | Updates `VideoMetadata` duration validation schema constraint to `le=360.0`. | None (API Schemas) | `test_media_duration_policy_and_asynchronous_orchestrator` |
| **26** | `backend/app/schemas/media.py` | **EXISTING_ADAPT** | Verified schema defining `MediaAsset` and probe fields; documents server-authoritative duration. | None (Database Models) | `test_dynamic_job_execution_manifest_probed_metadata` |
| **27** | `backend/app/schemas/result.py` | **EXISTING_ADAPT** | Aligns `AnalysisResult` Pydantic model with frozen Oracle readback evidence for C03/C04/C06 and handles withheld player metrics. | `showcase_final_summary.json` | `test_oracle_mode_preserves_verified_readback_metrics`, `test_automated_identity_gate_withholds_player_level_analytics` |
| **28** | `backend/app/api/jobs.py` | **EXISTING_ADAPT** | Validates job creation requests, resolves `AUTO` methodology to M2, initializes job in `QUEUED/UPLOADED`. | None (API Routes) | `test_methodology_explicit_manual_selection_and_isolation` |
| **29** | `modal_app/worker.py` | **EXISTING_ADAPT** | Adapts serverless worker from CPU smoke to provisional isolated GPU execution for M1, M2, and M3 with heartbeat updates. | `modal_app/worker.py` baseline | `test_media_duration_policy_and_asynchronous_orchestrator` |
| **30** | `frontend/tactical-ai-insights-main/src/routes/analysis.new.tsx` | **EXISTING_ADAPT** | Updates UI validation ceiling to 360s, adds AUTO methodology selector, sets default to M2. | None (Frontend UI) | `test_methodology_explicit_manual_selection_and_isolation` |
| **31** | `frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.results.tsx` | **EXISTING_ADAPT** | Displays amber limitations banner with decoupled evidence basis wording; disables individual player metric cards; renders radar top-down bounded visualization under `GEOMETRIC_SOLVE_ONLY` without metric labels. | None (Frontend UI) | `test_frontend_limitation_wording_reflects_evidence_basis`, `test_calibration_permission_matrix_geometric_solve_only` |

---

## Subsystem Architecture Verification Flow

```mermaid
graph TD
    subgraph Ingestion & Validation
        CFG[core/config.py] --> MVS[services/media_validation_service.py]
        MVS --> SCH_V[schemas/video.py]
        MVS --> SCH_M[schemas/media.py]
        MVS --> MAN[schemas/manifest.py]
    end

    subgraph Common Vision & Adapters
        M1[adapters/m1_adapter.py] --> CV[schemas/canonical_vision.py]
        M2[adapters/m2_adapter.py] --> CV
        M3[adapters/m3_adapter.py] --> CV
        DET[pipeline/detection.py] -.->|tiling utility| M1
        REG[pipeline/registry.py] -->|isolated invocation| M1
        REG -->|isolated invocation| M2
        REG -->|isolated invocation| M3
    end

    subgraph Scientific Processing
        CV --> IDS[services/identity_safety_service.py]
        CV --> CAL[services/calibration_service.py]
        CAL --> KIN[services/kinematics_service.py]
        ASR[services/asr_service.py] --> FUS[pipeline/fusion.py]
        CV --> FUS
        IDS --> FUS
        KIN --> FUS
    end

    subgraph Reporting & Dispatch
        FUS --> LLM[services/llm_report_service.py]
        LLM --> RES[schemas/result.py]
        DSP[services/dispatch_service.py] --> MODAL[modal_app/worker.py]
    end

    subgraph Frontend Routes
        NEW_UI[routes/analysis.new.tsx] --> DSP
        RES_UI[routes/analysis.$jobId.results.tsx] --> RES
    end
```
