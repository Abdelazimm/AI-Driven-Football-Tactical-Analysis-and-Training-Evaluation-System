# Master Audit Context: AI-Driven Football Tactical Analysis and Training Evaluation System

> **Auditor Note**: This document provides the authoritative overview of the application integration, control plane, persistence, and compute orchestration implemented in the **Antigravity Track** (Phases 1 through 4A.1). It is prepared for an independent Claude instance conducting a formal code, architecture, and security audit.

---

## 1. Project Identity & Separation of Tracks

- **Project Title**: AI-Driven Football Tactical Analysis and Training Evaluation System
- **Academic Context**: University of London / Goldsmiths BSc Computer Science Final Year Project.
- **Track Separation**:
  - **Antigravity Track (This Repository)**: Owns the product engineering, application architecture, API control plane, database persistence, cloud storage, client interfaces, job lifecycle state machines, and compute orchestration infrastructure.
  - **Codex Track (Separate Research Track)**: Owns the scientific methodology research, computer vision experiments (E0–E6), YOLO11m / RF-DETR / YOLO26 model validation, tracking algorithms (BoT-SORT, GTA, SRITrack), Whisper ASR extraction, tactical instruction parsing, and metric pitch calibration experiments.
  - **Strict Boundary**: All research notebooks, historical runs, and capability showcase artifacts are frozen and read-only. No models are retrained or run locally in this track.

---

## 2. End-to-End Product Architecture

```
                                  +---------------------------------------+
                                  |       Next.js / Vite Frontend         |
                                  |   (TanStack Router + Query, Tailwind) |
                                  +---------------------------------------+
                                         |                         |
               1. Request Signed URL     |                         | 2. Direct Chunked Upload
               4. Create Job / Poll      |                         |    (Video / Audio Media)
                                         v                         v
                          +-------------------------+     +-------------------------+
                          |   FastAPI Control Plane |     |    Supabase Storage     |
                          |   (Python >= 3.10)      |     | (Private Buckets)       |
                          +-------------------------+     | - analysis-inputs       |
                             |                   |        | - analysis-outputs      |
      3. Verify & Persist    |                   |        +-------------------------+
                             v                   v                     |
              +-----------------------+    +-----------------------+   |
              |  Supabase PostgreSQL  |    |     Modal Compute     |   |
              |  - sessions           |    |     Infrastructure    |<--+ 5. Secure Signed Read
              |  - media_assets       |    |  - CPU Orchestrator   |
              |  - analysis_jobs      |    |  - Future GPU Workers |
              |  - worker_dispatches  |    +-----------------------+
              +-----------------------+
```

1. **Frontend**: Modern web interface supporting direct signed media upload, analysis job dispatch, real-time stage monitoring, and grounded tactical report rendering.
2. **FastAPI Control Plane**: Python $\ge$ 3.10 application providing REST endpoints for sessions, upload intent generation, authoritative media verification, analysis job lifecycle management, and worker dispatch orchestration.
3. **Supabase PostgreSQL & Private Storage**: Cloud-hosted relational persistence with Row-Level Security (RLS). Media files are stored in private buckets (`analysis-inputs`, `analysis-outputs`) and accessed exclusively via short-lived signed URLs.
4. **Worker Dispatch Architecture**: Persisted state machine tracking provider dispatches (`worker_dispatches` table), enforcing single-dispatch idempotency and provider failure normalization.
5. **Modal Execution Infrastructure**: Serverless compute provider configured for on-demand cloud execution. Currently verified for CPU infrastructure smoke testing; frozen and gated against methodology execution.

---

## 3. Completed Phases & Verification Status

### Phase 1: Shared Contracts & Canonical Vocabularies
- **Deliverables**: Canonical data contracts mirrored across Pydantic v2 (Python) and TypeScript schemas.
- **Key Concepts**: Explicit alignment of job status, pipeline stages, calibration modes, identity reliability statuses, and kinematics constraints.

### Phase 2: FastAPI Foundation & Job Orchestration
- **Deliverables**: FastAPI control-plane skeleton, job creation, status polling, result retrieval endpoints, and frontend typed query hooks.
- **Guarantees**: Jobs strictly initialized in canonical initial state (`QUEUED` status, `UPLOADED` stage); unready results return HTTP 409 `ANALYSIS_NOT_READY`.

### Phase 3: Supabase Cloud Persistence & Direct Upload Architecture
- **Deliverables**: Database migrations (`001_phase3_initial_schema.sql`), Supabase repository implementations (`SessionRepository`, `MediaRepository`, `JobRepository`), direct signed browser upload workflow, and media format/duration validation.
- **Security**: Supabase storage buckets `analysis-inputs` and `analysis-outputs` are private (`public=False`). Direct uploads require pre-signed URLs generated by the control plane. Media ownership is authoritatively verified via Supabase storage API before creating jobs.

### Phase 3.5 / 3.6: Lifecycle Contract Hardening & Live Verification
- **Deliverables**: Separation of `JobStatus` (overall lifecycle) from `AnalysisStage` (pipeline processing step).
- **Introduction of `COMPLETED_WITH_LIMITATIONS`**: Added across SQL schema, Pydantic, TypeScript, and frontend UI to distinguish successful jobs that fail scientific safety gates from runtime system errors.
- **Live Cloud Activation**: Verification of live cloud Supabase project, successful signed upload of synthetic audio/video assets, and automated teardown.

### Phase 4A: Async Worker Dispatch Backbone & Methodology Gate
- **Deliverables**: Database migration `002_worker_dispatches.sql`, `WorkerDispatchRepository` (Supabase + In-Memory), `AnalysisDispatchService`, `ModalDispatchClient` adapter, and `MethodologyExecutorRegistry`.
- **Idempotency**: Prevents duplicate executions by returning the existing active dispatch (`CREATED`, `SUBMITTED`, `RUNNING`) if a dispatch is requested repeatedly for the same job.
- **Methodology Gate**: Strictly locks all three research methodologies (`METHOD_1_YOLO11_BOTSORT`, `METHOD_2_RFDETR_GTATRACK`, `METHOD_3_YOLO26_SRITRACK`) as `NOT_READY_FOR_EXECUTION`. Attempts to dispatch return HTTP 409 `METHODOLOGY_EXECUTOR_NOT_READY`.
- **Remote CPU Smoke**: Real execution on Modal cloud containers proving connectivity without loading models or allocating GPUs.

### Phase 4A.1: Runtime Hardening & De-Monkey-Patching
- **Deliverables**: Removal of temporary diagnostic version-spoofing (`modal_version.__version__`) and legacy builder overrides (`MODAL_IMAGE_BUILDER_VERSION`).
- **Environment**: Formal adoption of isolated project virtual environment (`.venv`) on modern Python (3.13 / $\ge$ 3.10) with modern official Modal SDK (`modal>=1.5.0,<2.0.0`).
- **Dependency Reconciliation**: Clean dependency specifications in `backend/pyproject.toml`, `backend/requirements.txt`, and `requirements-modal.txt`.

### Pre-Phase-4B Hardening Pack 1: Job Lifecycle, Worker Callback & Atomic Idempotency
- **Deliverables**: Migration `003_job_lifecycle_and_dispatch_idempotency.sql`, atomic partial unique index `uq_active_worker_dispatch_per_job` on `worker_dispatches (job_id)` WHERE `state IN ('CREATED', 'SUBMITTED', 'RUNNING')`.
- **Job Lifecycle Persistence**: Added columns to `public.analysis_jobs` for `progress_percent` (0..100), `stage_message`, `error_code`, `error_details`, `modal_call_id`, and `completed_at`.
- **Authenticated Worker Callback**: Internal endpoint `POST /api/v1/internal/worker/callback` secured by constant-time secret verification (`X-Worker-Secret`), allowing running workers to publish stage transitions, progress, and terminal completion/failure safely.
- **Verification**: Live verified on active Supabase instance; 12 unit/integration tests in `test_hardening_pack1.py`.

### Pre-Phase-4B Hardening Pack 2: Authoritative Media Validation & Storage Error Semantics
- **Deliverables**: Migration `004_media_validation.sql`, `MediaValidationService`, `MediaProbeService` (`FFProbeMediaProbeService` for production, `InMemoryMediaProbeService` for test doubles).
- **Authoritative Video Metadata**: Extracts duration, width, height, fps, container format, video codec, and audio codec directly from stored media via short-lived signed URLs. Client-declared durations are strictly untrusted and overwritten.
- **Duration & Content Bounds**: Enforces 300.0s maximum duration cap (`MAX_VIDEO_DURATION_SECONDS`), rejects corrupt files, renamed non-video containers, and missing video streams.
- **Expanded Upload Status**: Added `VALIDATING`, `VALIDATED`, and `VALIDATION_FAILED` to `upload_status` enum across PostgreSQL, Pydantic, and TypeScript schemas.
- **Analysis Eligibility Gate**: Enforced in `jobs.py` and `dispatch_service.py` requiring `UploadStatus.VALIDATED` for video media before jobs can be created or dispatched.
- **Typed Storage Error Semantics**: Replaced monolithic storage error handling with explicit exception hierarchy (`StorageObjectNotFound`, `StorageAuthError`, `StorageTimeout`, `StorageUnavailable`, `StorageProviderError`) to prevent infrastructure/network blips from collapsing into false 404s.
- **Verification**: Live verified on active Supabase instance via `scripts/verify_hp2_live.py`; 59 unit/integration tests in `test_hardening_pack2.py`.

---

## 4. Canonical Vocabularies & State Machines

### 4.1 JobStatus (Overall Lifecycle)
```text
QUEUED                      -> Job created and awaiting compute dispatch
PROCESSING                  -> Worker actively executing pipeline stages
COMPLETED                   -> Finished successfully; all scientific safety gates passed
COMPLETED_WITH_LIMITATIONS  -> Finished successfully, but scientific gate failed (e.g. Identity Fragmentation);
                               player-level conclusions withheld, spatial/team evidence preserved
FAILED                      -> System error, unhandled exception, or corrupt media
```

### 4.2 AnalysisStage (Strictly 16 Processing Stages)
```text
1.  UPLOADED               9.  AUDIO_EXTRACTION
2.  VALIDATING             10. TRANSCRIBING
3.  PREPROCESSING          11. INSTRUCTION_PARSING
4.  DETECTING              12. FUSION
5.  TRACKING               13. GENERATING_EVIDENCE
6.  IDENTITY_EVALUATION    14. GENERATING_REPORT
7.  CALIBRATING            15. RENDERING
8.  KINEMATICS             16. UPLOADING_RESULTS
```

### 4.3 IdentityStatus (Seven Scientific Outcomes)
```text
NOT_EVALUATED              -> Initial state before tracking/ReID evaluation
EVALUATING                 -> Identity gate actively processing
PASS_RELIABLE              -> Fragmentation ratio <= 1.5; automated player-level metrics allowed
FAIL_HIGH_FRAGMENTATION    -> Fragmentation ratio > 1.5; player-level assessment withheld
FAIL_IDENTITY_CONFLICT     -> Two physical tracks assigned same persistent identity
FAIL_UNSAFE_MERGE          -> Micro-track stitching crossed spatial-temporal impossibility threshold
FAIL_INVALID_OUTPUT        -> Tracker output corrupted or empty
```

### 4.4 WorkerDispatchState (Six Dispatch Lifecycle States)
```text
CREATED                    -> Record inserted in database; external provider dispatch pending
SUBMITTED                  -> Handed off to Modal serverless orchestrator (call ID acquired)
RUNNING                    -> Remote container initialized and executing
SUCCEEDED                  -> Worker completed processing and updated analysis job
FAILED                     -> Worker execution raised an error or timed out
CANCELLED                  -> Job was cancelled before worker completed
```

---

## 5. Methodology Registry & Execution Gate

The platform specifies three distinct tactical analysis methodologies:
1. `METHOD_1_YOLO11_BOTSORT`: YOLO11m detector (3-tile horizontal inference) + BoT-SORT tracker.
2. `METHOD_2_RFDETR_GTATRACK`: RF-DETR detector + GTA track association.
3. `METHOD_3_YOLO26_SRITRACK`: YOLO26 detector + SRITrack association.

### Authoritative Readiness State
```python
METHOD_1_YOLO11_BOTSORT = "NOT_READY_FOR_EXECUTION"
METHOD_2_RFDETR_GTATRACK = "NOT_READY_FOR_EXECUTION"
METHOD_3_YOLO26_SRITRACK = "NOT_READY_FOR_EXECUTION"
```

- **Enforcement**: `MethodologyExecutorRegistry.is_executable(methodology_id)` returns `False` for all three methods.
- **Dispatch Protection**: `POST /api/v1/analysis/jobs/{job_id}/dispatch` aborts with HTTP 409:
  ```json
  {
    "detail": {
      "code": "METHODOLOGY_EXECUTOR_NOT_READY",
      "message": "Methodology METHOD_1_YOLO11_BOTSORT is not ready for production execution. Research validation is in progress."
    }
  }
  ```
- **Invariant**: No mock or simulated pipeline results are generated. The system fails closed and preserves data integrity.

---

## 6. Scientific Safety Invariants

1. **Identity Safety Gate**: Automated tracking in full sessions exhibits a fragmentation ratio of $6.1667$ (acceptance threshold $\le 1.5$). Automated player-specific tactical adherence (e.g. "Did Player #7 press?") **must be withheld** whenever identity evaluation fails.
2. **Safe Degradation (`COMPLETED_WITH_LIMITATIONS`)**: An identity failure must never crash the job. Observable spatial and team-level metrics (e.g. defensive line depth, team centroid compactness) remain valid and reportable.
3. **No Fabricated Zeros**: If ground truth distance, speed, or tactical target is unavailable or withheld, the system reports `None` / `unavailable`. It must **never** report `0.00 m` or `0.00 km/h`.
4. **Homography Calibration Boundaries**: The physical research pitch ($19.31\text{ m} \times 19.88\text{ m}$) fixed homography matrix ($RMSE = 0.651\text{ m}$) is camera-geometry-specific. It must **never** be silently applied to arbitrary user uploads. Uncalibrated videos operate strictly under `NO_METRIC_CALIBRATION` (pixel-space only).
5. **Separation of Golden Showcase**: The oracle-assisted showcase (use cases C03, C04, C06) features manually verified identity and instruction targets. Showcase fixtures are immutable and must never be represented as automated pipeline outputs.

---

## 7. Cloud Infrastructure & Security Architecture

### 7.1 Supabase Cloud
- **Database Schema**:
  - `sessions`: Training session metadata.
  - `media_assets`: Uploaded video and audio assets with verification checksums, durations, and storage paths.
  - `analysis_jobs`: Analysis job state machine (`status`, `current_stage`, `identity_status`).
  - `worker_dispatches`: Asynchronous worker execution records (`state`, `provider`, `provider_execution_id`).
- **Security & RLS**:
  - Row-Level Security (RLS) is enabled on all tables.
  - Storage buckets `analysis-inputs` and `analysis-outputs` are strictly private (`public = false`).
  - Frontend access to media requires temporary signed download/upload URLs generated by the FastAPI backend using service role permissions.
  - The `worker_dispatches` table is internal infrastructure and is never queried directly by the frontend.

### 7.2 Modal Cloud Compute
- **Application Definition**: Single authoritative `modal.App("football-tactical-analysis")` in `modal_app/app.py`.
- **Execution Lifecycle**: Clean ephemeral context (`with modal.enable_output(): with app.run():`).
- **Container Environment**: Official Debian Slim container with Python 3.10, Pydantic v2, and HTTPX.
- **Resource Constraints**:
  - Phase 4A/4A.1 verification: `cpu=1.0`, `memory=512MB`, `gpu=None`.
  - Zero GPU allocation, zero AI model weights loaded, zero network data egress.
- **Authentication**: Managed via `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` in server environment; no tokens or secrets exposed in frontend bundles or client logs.

---

## 8. Verification & Test Evidence

As of Pre-Phase-4B Hardening Pack 2 completion:
- **Backend Test Suite**: 150 unit, integration, and contract tests passing in `backend/tests/` (100% pass rate across all 8 test modules).
- **Frontend TypeScript Check**: `npx tsc --noEmit` exited with code `0` (0 errors).
- **Frontend Production Build**: `npm run build` exited with code `0` (Vite client, SSR, and Nitro server bundles successfully built).
- **Live Cloud Persistence (HP1 & HP2)**: Verified live database row creation, update, query, constraint checks, and clean teardown on active Supabase instance for both Migration 003 (`uq_active_worker_dispatch_per_job`) and Migration 004 (`container_format`, `video_codec`, `audio_codec`, `validation_status`, expanded `upload_status` check constraint) via `scripts/verify_hp2_live.py`.
- **Remote Modal Execution**: Verified real cloud execution returning typed `InfrastructureSmokeResponse` from container Python 3.10 runtime via `scripts/verify_modal_smoke.py`.

---

## 9. Future Boundary: Phase 4B Gate

The Antigravity product track is formally **FROZEN** at Phase 4A.1.

**Conditions for Phase 4B Execution**:
1. Codex research track must complete formal validation and evaluation for M1, M2, and M3.
2. Verified model checkpoints, configuration artifacts, and pipeline modules must be finalized.
3. All three methodology executors will then be integrated into `backend/app/pipeline/` and `modal_app/worker.py` in a single synchronized release.
4. **NO Phase 4B work may be started in this audit phase.**
