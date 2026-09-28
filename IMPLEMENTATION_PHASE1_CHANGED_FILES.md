# Implementation Phase 1 — Changed Files Record

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: Implementation Phase 1 — Core Contracts, Vision Adapters & Safety Layer  
**Contract Version**: `P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A`  
**Date**: 2026-09-26  
**Status**: `IMPLEMENTATION_PHASE1_READY_FOR_REVIEW`  

---

## 1. Newly Created Files (13)

| # | File Path | Category | Purpose |
| :- | :--- | :--- | :--- |
| **01** | `IMPLEMENTATION_PHASE1_PRECHANGE_SNAPSHOT.md` | Pre-Implementation Snapshot | Captures workspace state, git/repo status, and baseline test suite pass rate prior to Phase 1 edits. |
| **02** | `config/3v3_homography_measured_metric_corrected.json` | Configuration / Homography | Authoritative research homography matrix (SHA-256: `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507`, pitch $19.31\text{m} \times 19.88\text{m}$, independent RMSE $0.6505\text{m}$). |
| **03** | `backend/app/schemas/canonical_vision.py` | Core Canonical Schemas | Pydantic v2 schemas: `CoordinateSpace`, `BoundingBox`, `NormalizedBoundingBox`, `MethodProvenance`, `TrackObservation`, `FrameVisionResult`, `SessionVisionResult`, `CalibrationReference`, `FormalIdentityStatus`, `RuntimeIdentityStatus`, `IdentityEvidenceBasis`. Enforces fail-closed identity gate. |
| **04** | `backend/app/schemas/manifest.py` | Runtime Execution Schemas | Dynamic `JobExecutionManifest`, `MediaProbedMetadata`, `ManifestMethodologyProvenance`, `ManifestRuntimeDiagnostics`, `ManifestCalibrationMetadata`. Eliminates hardcoded research constants as universal defaults. |
| **05** | `backend/app/adapters/common_adapter.py` | Common Infrastructure | Coordinate projection (`project_box_working_to_source`), bounding box clipping, normalization, empty frame creation (`create_empty_frame`), metadata validation (`validate_source_metadata`). |
| **06** | `backend/app/adapters/m1_adapter.py` | Vision Pipeline Adapter | M1 adapter consuming native $1920 \times 1080$ tracking and emitting canonical `SessionVisionResult`. Frozen baseline: `epoch28.pt` (SHA: `ad908a9caf75...`), `yolo26n-reid.onnx` (SHA: `8529c383197a...`), candidate floor 0.05, qualification 0.25, tile NMS 0.70, global NMS 0.50, BoT-SORT parameters. Anti-double-scaling verified. |
| **07** | `backend/app/adapters/m2_adapter.py` | Vision Pipeline Adapter | M2 adapter consuming native $1920 \times 1080$ RF-DETR + Deep-EIoU + GTA-Track outputs. Frozen baseline: `checkpoint_best_total.pth` (SHA: `7539cfb3eca3...`), `sports_model.pth.tar-60` (SHA: `8d5b2fd8763d...`), operating point $\ge 0.50$, external NMS False. Anti-double-scaling guarantee ($704 \rightarrow 1920$ prohibited). |
| **08** | `backend/app/adapters/m3_adapter.py` | Vision Pipeline Adapter | M3 adapter consuming native $1920 \times 1080$ YOLO26m + SRITrack-v1 outputs. Frozen baseline: `M3_ADAPTED_YOLO26M.pt` (SHA: `ea9b3e434ffd...`), operating point $\ge 0.30$, P5A amended `track_new_th = 0.30`, `track_high_th = 0.60`, `track_buffer = 1000`. Anti-double-scaling verified. |
| **09** | `backend/app/services/identity_safety_service.py` | Safety Service | Decouples formal ground-truth benchmark status (`FAIL_UNSAFE_MERGE`, `FORMAL_DENSE_GT`) from upload runtime diagnostics (`RUNTIME_HEURISTIC_ONLY`). Strictly enforces `player_level_analysis_allowed = False` for automated runs. |
| **10** | `backend/app/services/calibration_service.py` | Metric Service | Governs the 4 calibration modes (`CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED`, `GEOMETRIC_SOLVE_ONLY`, `NO_METRIC_CALIBRATION`, `INVALID_CALIBRATION`). Enforces verified research geometry (iPhone 16 source SHA `0e676f4327d1...`) and suppresses metric claims under geometric-only/uncalibrated modes. |
| **11** | `backend/app/services/kinematics_service.py` | Kinematics Service | Implements 7-observation rolling median smoothing, time-based velocity continuity gap reset ($\Delta t > 0.50\text{s}$ resets continuity without spatial interpolation), and outlier speed rejection ($> 36.0\text{ km/h} \implies \text{REJECT\_AND\_EXCLUDE\_OUTLIER}$, never clamped). |
| **12** | `backend/tests/test_contract_phase1.py` | Contract Test Suite | 19 automated test suites asserting frozen M1/M2/M3 provenance, anti-double-scaling, identity safety withholding, calibration permission matrix, kinematics time gaps, outlier rejection, dynamic manifests, and duration ceiling. |
| **13** | `IMPLEMENTATION_PHASE1_TEST_RESULTS.json` | Execution Evidence | Machine-readable JSON summary of all 169 passed tests (19 Phase 1 contract suites + 150 regression tests). |

---

## 2. Modified Existing Files (12)

| # | File Path | Modification Summary |
| :- | :--- | :--- |
| **01** | `backend/app/pipeline/identity.py` | Adapted `IdentityPipeline` placeholder to wrap the authoritative `IdentitySafetyService`. |
| **02** | `backend/app/pipeline/calibration.py` | Adapted `CalibrationPipeline` placeholder to wrap `CalibrationService` for planar projections and compatibility checks. |
| **03** | `backend/app/pipeline/kinematics.py` | Adapted `KinematicsPipeline` placeholder to wrap `KinematicsService` for 7-point median smoothing and track kinematics. |
| **04** | `backend/app/pipeline/registry.py` | Added `resolve_methodology` (routing `AUTO` to `METHOD_2_RFDETR_GTATRACK`), `get_executor` fail-closed verification, and `MethodologyRegistry` alias. |
| **05** | `backend/app/core/config.py` | Updated `MAX_VIDEO_DURATION_SECONDS` from 300.0 to 360.0. Added REV2A LLM timeout constants (`FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120`, `PRODUCTION_LLM_TIMEOUT_SECONDS = 120`, `LLM_TIMEOUT_SECONDS = 120`). |
| **06** | `backend/app/schemas/video.py` | Updated `duration_seconds: float = Field(..., ge=0.0, le=360.0)` from 300.0s to 360.0s. |
| **07** | `backend/app/api/sessions.py` | Updated upload intent validation error message from "5 minutes" to "6 minutes" to align with 360s ceiling. |
| **08** | `.env` | Updated `MAX_VIDEO_DURATION_SECONDS=360.0` (was 300). |
| **09** | `.env.example` | Updated `MAX_VIDEO_DURATION_SECONDS=360.0` (was 300). |
| **10** | `frontend/tactical-ai-insights-main/src/routes/analysis.new.tsx` | Updated frontend duration validation to `MAX_DURATION_SECONDS = 360` (6 minutes) and user-facing copy. |
| **11** | `backend/tests/test_hardening_pack2.py` | Aligned duration test boundary from 300.0s to 360.0s (`test_duration_359_9s_accepted`, `test_duration_360_0s_accepted`, `test_duration_360_1s_rejected`). |
| **12** | `backend/tests/test_phase3_storage_and_upload.py` | Aligned test video duration exceeding limit from 360.0s to 360.1s to test rejection above the new 360.0s ceiling. |

---

## 3. Strict Boundary & Read-Only Invariants Preserved

1. **Research Workspace Untouched**:
   - `01_vision_pipeline.ipynb`, `02_audio_pipeline.ipynb`, `03_orchestrator_fusion.ipynb`, `04_report_generation.ipynb`, and `Autonomus_scout.ipynb` were NOT modified.
   - Ground truth, benchmark run directories, and training checkpoints were NOT modified, moved, or retuned.
2. **Production Registry Remains Fail-Closed**:
   - `METHODOLOGY_EXECUTOR_NOT_READY` remains actively enforced on `MethodologyRegistry.get_executor`. Adapters existing does NOT prematurely declare GPU runners production-ready.
3. **Lazy Dependency Policy**:
   - No heavy GPU or ML frameworks (RF-DETR, Ultralytics, SRITrack, GTA, DINO, CTranslate2) are imported at API startup or within adapter module scopes.
   - All 169 unit and contract tests execute cleanly in under 1 second on standard CPU.
