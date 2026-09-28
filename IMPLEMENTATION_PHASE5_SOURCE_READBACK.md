# IMPLEMENTATION_PHASE5_SOURCE_READBACK.md
# Implementation Phase 5 Source-First Product Readback & Architectural Classification

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: Implementation Phase 5 — Production Orchestration, Modal Packaging, Persistence & Product Pipeline Wiring  
**Contract Version**: `P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A` (Approved)  
**Timestamp**: 2026-09-27T04:05:00Z  

---

## 1. Architectural Component Classification

Every primary component in the product workspace has been inspected line-by-line and classified according to its role in the production lifecycle:

| Component / File Path | Classification | Current State & Required Phase 5 Action |
| :--- | :--- | :--- |
| `backend/app/core/model_manifest.yaml` | `REPLACE_PLACEHOLDER` | **Stale**. Contains obsolete references to `qwen3:8b`, outdated `Stage 4B fine-tuned YOLO11m` as single deployment detector, and `cpu_threads: 4`. Must be synchronized to the current frozen contract (AUTO -> M2, exact M1/M2/M3 checkpoint SHA-256s, Llama 3.1 8B digest, system prompt SHA-256, research homography SHA-256). |
| `backend/app/pipeline/orchestrator.py` | `REPLACE_PLACEHOLDER` | **Missing**. Does not exist yet. Must be implemented as the unified production orchestrator composing verified modules (`execute_analysis_job(...) -> AnalysisResult`). |
| `backend/app/pipeline/registry.py` | `READY_REUSE` | **Verified**. Implements `create_production_registry()` with lazy-loading of `M1VisionRunner`, `M2VisionRunner`, `M3VisionRunner`. `resolve_methodology()` strictly resolves `AUTO` -> `METHOD_2_RFDETR_GTATRACK`. |
| `backend/app/pipeline/audio.py` | `READY_REUSE` | **Verified**. Phase 3 `AudioPipeline` extracting audio and running Faster-Whisper with 25 frozen taxonomy keywords. |
| `backend/app/pipeline/fusion.py` | `READY_REUSE` | **Verified**. Phase 3 `MultimodalFusionEngine` / `FusionPipeline` enforcing reaction window $[t_{\text{end}} + 2.0\text{s}, t_{\text{end}} + 6.0\text{s}]$, kinematics bounds (36.0 km/h limit), and metric suppression under uncalibrated modes. |
| `backend/app/pipeline/evidence.py` | `READY_REUSE` | **Verified**. Phase 3 `EvidencePipeline` validating `StructuredEvidencePayload` schema and identity boundaries. |
| `backend/app/pipeline/reporting.py` | `READY_REUSE` | **Verified**. Phase 4 `ReportingPipeline` connecting structured evidence to `LLMReportService` or deterministic fallback. |
| `backend/app/pipeline/calibration.py` | `READY_REUSE` | **Verified**. Handles `NO_METRIC_CALIBRATION`, `DEMO_FIXED_CALIBRATION`, and `CUSTOM_PITCH_CALIBRATION`. |
| `backend/app/pipeline/kinematics.py` | `READY_REUSE` | **Verified**. Calculates velocities and distances, applying outlier exclusion ($> 36$ km/h). |
| `backend/app/pipeline/detection.py` | `DO_NOT_TOUCH` | Frozen abstract stubs from Phase 1. Production vision runners directly execute Ultralytics/RF-DETR. |
| `backend/app/pipeline/tracking.py` | `DO_NOT_TOUCH` | Frozen abstract stub. Production runners encapsulate tracking algorithms (BoT-SORT, GTA-Track, SRI-Track) directly. |
| `backend/app/pipeline/instructions.py`| `DO_NOT_TOUCH` | Frozen stub. Tactical instruction parsing is executed by `ASRService` in `backend/app/services/asr_service.py`. |
| `backend/app/services/dispatch_service.py` | `READY_REUSE` | **Verified**. Handles dispatch lifecycle, atomic active-dispatch idempotency (`uq_active_worker_dispatch_per_job`), status transitions, and HMAC callback validation. |
| `backend/app/services/media_validation_service.py` | `READY_REUSE` | **Verified**. Authoritative server-side ffprobe validation, already enforces `MAX_VIDEO_DURATION_SECONDS = 360.0`. |
| `backend/app/services/job_repository.py` | `ADAPT` | `SupabaseAnalysisJobRepository.get_result()` currently returns `None` as a placeholder. Must implement durable `store_result` and `get_result` backed by `analysis_results` table or persistent storage. |
| `backend/app/api/jobs.py` | `READY_REUSE` | Clean REST endpoints for job creation, status querying, result retrieval, and worker dispatch. |
| `backend/app/api/internal.py` | `READY_REUSE` | Protected endpoint for worker progress/completion callbacks with HMAC verification. |
| `backend/app/api/deps.py` | `ADAPT` | Ensure `get_dispatch_service()` receives `create_production_registry()` so methodology readiness gate evaluates to `READY_FOR_EXECUTION` for M1/M2/M3. |
| `modal_app/worker.py` | `ADAPT` | Currently contains `infrastructure_smoke` and `dispatch_placeholder`. Must be upgraded to execute the real orchestrator in serverless compute. |
| `modal_app/app.py` | `ADAPT` | Base container configuration for Modal. Must support required dependencies and volume/model configurations. |
| `requirements-modal.txt` | `ADAPT` | Modal dependency specification; needs verification for orchestrator dependencies. |
| `shared/schemas/result.ts` | `READY_REUSE` | Matches backend `AnalysisResult` schema. |
| `shared/constants/confidence.ts` | `READY_REUSE` | Aligned with Python `ReportStatus` (including `VALIDATED_LLM_REPORT`). |
| `frontend/.../analysis.new.tsx` | `READY_REUSE` | Verified. Already configured with `MAX_DURATION_SECONDS = 360` (6 minutes). |
| `frontend/.../analysis.$jobId.tsx` | `READY_REUSE` | Verified. Renders real job telemetry and stage progression. |
| `frontend/.../analysis.$jobId.results.tsx` | `READY_REUSE` | Verified. Renders real `AnalysisResult` data; properly displays 409 conflict when result is not yet ready. |
| Research Notebooks & Checkpoints | `DO_NOT_TOUCH` | Strictly read-only research foundation. |

---

## 2. Explicit Audit of Known Technical Debt & Placeholders

### 2.1 `NotImplementedError` Audit
- `backend/app/pipeline/tracking.py` (Line 23): Abstract placeholder from early scaffold. *Resolution: DO_NOT_TOUCH (production runners do not invoke this file).*
- `backend/app/pipeline/instructions.py` (Line 24): Abstract placeholder. *Resolution: DO_NOT_TOUCH (instruction extraction is performed deterministically by `ASRService`).*
- `backend/app/pipeline/detection.py` (Lines 256, 270): Abstract method stubs. *Resolution: DO_NOT_TOUCH.*

### 2.2 Placeholder Worker Behavior
- `modal_app/worker.py` (`dispatch_placeholder`): Currently returns `{"status": "NOT_READY_FOR_EXECUTION"}`.
  *Resolution: Must be upgraded to invoke the unified production orchestrator, execute pipeline stages, emit monotonic progress callbacks, and persist final outputs.*

### 2.3 Mock Result Construction Audit
- `SupabaseAnalysisJobRepository.get_result()` (`backend/app/services/job_repository.py` line 334): Currently returns `None`.
  *Resolution: Implement `store_result` and `get_result` in `AnalysisJobRepository`, `InMemoryJobRepository`, and `SupabaseAnalysisJobRepository` to persist and retrieve canonical `AnalysisResult` instances.*
- `frontend`: Zero mock results found. Frontend components strictly query `/api/v1/analysis/jobs/{job_id}/result` and handle 409 Conflict.

### 2.4 Hard-Coded Job Responses Audit
- No hard-coded tactical events, metric distances, or speeds exist in API routes.

### 2.5 Stale Model Manifest Entries Audit
- `backend/app/core/model_manifest.yaml`:
  - Contains stale `qwen3:8b` reference.
  - Contains outdated `Stage 4B fine-tuned YOLO11m` as single deployment detector.
  - Specifies `cpu_threads: 4` instead of 8 for Faster-Whisper.
  - Missing M1, M2, M3 cryptographic hashes, Llama 3.1 8B digest, prompt SHA-256, and research homography hash.
  *Resolution: Step 2 synchronizes this file completely to the frozen Rev2A contract.*

### 2.6 Duration Limit Audit
- Backend: `settings.MAX_VIDEO_DURATION_SECONDS = 360.0`.
- Media Validation Service: Enforces `MAX_VIDEO_DURATION_SECONDS = 360.0`.
- Frontend: `analysis.new.tsx` enforces `MAX_DURATION_SECONDS = 360; // 6 minutes`.
- Legacy 300-second limits: Completely absent from active code. No active path rejects the ~340s research session.

---

## 3. Implementation Plan for Phase 5

1. **Step 2**: Rewrite `backend/app/core/model_manifest.yaml` with the complete, frozen Rev2A specification.
2. **Step 3**: Implement `backend/app/pipeline/orchestrator.py` (`UnifiedAnalysisOrchestrator`, `execute_analysis_job`).
3. **Step 4 & 5**: Enforce exact methodology resolution (AUTO -> M2, fail-closed on cross-method fallback) and explicit stage failure semantics.
4. **Step 6 & 7**: Assemble canonical `AnalysisResult` with dynamic `JobExecutionManifest`.
5. **Step 9 & 10**: Wire durable persistence in `AnalysisJobRepository` and deterministic artifact paths in storage.
6. **Step 11 & 12**: Ensure monotonic progress callbacks and preserve dispatch idempotency.
7. **Step 13, 14, 15, 16**: Modal preflight, container packaging, and worker upgrade.
8. **Step 18, 19, 20**: Bounded real smoke test, frontend contract verification, controlled failure path test.
9. **Step 21 & 22**: Comprehensive unit/integration tests and full regression verification.
