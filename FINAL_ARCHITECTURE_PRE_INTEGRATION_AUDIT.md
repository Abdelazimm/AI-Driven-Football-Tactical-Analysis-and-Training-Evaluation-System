# FINAL PRE-INTEGRATION ARCHITECTURE AUDIT
## CM3070 Final Project: AI-Driven Football Tactical Analysis and Training Evaluation System

- **Audit Date**: 2026-09-26
- **Audit Type**: Strict Read-Only Complete System & Architecture Audit
- **Authoritative Product Workspace**: `d:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System`
- **Secondary Research Workspace**: `G:\My Drive\Football_Training_Assistant_MVP`
- **Audit Status**: COMPLETE — READ-ONLY BASELINE ESTABLISHED

---

## 1. Executive Summary

This architecture audit establishes the exact implementation state of the **AI-Driven Football Tactical Analysis and Training Evaluation System** prior to final production integration and prototype closure.

### Key Audit Findings

1. **Dual-Track Decoupled Reality**:
   - The system exists across two distinct workspaces:
     - **Primary Product Workspace** (`d:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System`): Contains the authoritative modern web application (React 19, TanStack Start SSR, Vite, Tailwind CSS, shadcn/ui), FastAPI control plane, Supabase PostgreSQL database schema with 4 applied migrations, server-authoritative media validation via `ffprobe`, atomic worker dispatch idempotency, worker callback verification, golden fixture service, and 150 passed automated tests (100% pass rate).
     - **Secondary Research Workspace** (`G:\My Drive\Football_Training_Assistant_MVP`): Contains the frozen scientific methodology, evaluation protocols, training runs, frozen ASR (`faster-whisper base.en`), frozen LLM (`llama3.1:8b` with Patch 001 grounding validator), homography calibration matrices, and validated pipeline scripts.
   - The primary product workspace's control plane is **genuinely operational**. However, its internal pipeline modules (`backend/app/pipeline/`) are currently **fail-closed stubs** (`NotImplementedError`), and the job dispatch endpoint safely returns HTTP 409 `METHODOLOGY_EXECUTOR_NOT_READY`.

2. **Vision Subsystem Status**:
   - Production slot status: `VISION_METHOD_PENDING_FINAL_EVALUATION_SELECTION`.
   - The Stage 4B fine-tuned YOLO11m detector (`best.pt`, 40.5 MB, SHA-256 `f6b3fe6f...`) with 3-tile horizontal slicing (15% overlap, global NMS IoU 0.70) is fully implemented in `backend/app/pipeline/detection.py`.
   - However, the final tracking/identity methodology selection between **M1** (YOLO11 + BoT-SORT), **M2** (RF-DETR + GTA-Track), and **M3** (YOLO26 + SriTrack) is formally pending the completion and freeze of human dense-GT annotations on the 4 iPhone 16 challenge clips.

3. **ASR Subsystem Status**:
   - **FROZEN**. Selected model: `faster-whisper base.en` executed via `CTranslate2` on CPU int8 (8 threads).
   - Provenance and contract: 16 kHz mono PCM, `task="transcribe"`, `language="en"`, `beam_size=5`, `word_timestamps=True`, `vad_filter=True`, deterministic tactical instruction classification, and parent-segment timestamp inheritance. Fully verified in the research workspace (`REAL_3V3_SMOKE_TEST_001`).

4. **LLM Subsystem Status**:
   - **FROZEN**. Selected model: `llama3.1:8b` (authoritative digest: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`).
   - System prompt SHA-256: `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`.
   - Grounding validator: `LLM_GROUNDING_VALIDATOR_PATCH_001` with 8 deterministic grounding gates (13/13 regression tests passed). Fallback to deterministic markdown report verified.

5. **Scientific Identity Boundary**:
   - Automated persistent identity in real sessions definitively remains `FAIL_HIGH_FRAGMENTATION` (115 raw IDs $\rightarrow$ 37 meaningful IDs; fragmentation ratio $6.1667 > 1.50$).
   - Full-session player-level assessment is safely **WITHHELD** across all production and research pipelines, returning `COMPLETED_WITH_LIMITATIONS`.
   - The golden capability showcase (`golden/`, C03, C04, C06) remains strictly `ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION` with human-verified identities.

---

## 2. Workspace Authority and Cross-Workspace Boundary

### 2.1 Workspace Roles & Sources of Truth

| Domain | Primary Product Workspace (`D:\...`) | Secondary Research Workspace (`G:\My Drive\...`) | Authoritative Authority |
| :--- | :--- | :--- | :--- |
| **Frontend Application** | TanStack Start SSR + React 19 + Vite + Tailwind CSS + shadcn/ui | 3-file static prototype (`index.html`, `index.css`, `app.js`) | **Primary Product Workspace** |
| **Backend API Control Plane** | FastAPI (`/api/v1`), Uvicorn, Pydantic v2, dependency injection | Monolithic `server.py` prototype | **Primary Product Workspace** |
| **Database & Migrations** | Supabase PostgreSQL, Migrations 001–004, RLS, partial unique indexes | None (No database or migration tracking) | **Primary Product Workspace** |
| **Storage & Media Probing** | `SupabaseStorageService`, `MediaValidationService`, `ffprobe` | Local file paths (`data/custom/`) | **Primary Product Workspace** |
| **Job Dispatch & Idempotency** | Atomic `WorkerDispatchRepository`, `uq_active_worker_dispatch_per_job` | In-memory local script execution | **Primary Product Workspace** |
| **Worker Callback Security** | Authenticated `/internal/jobs/{id}/progress`, constant-time HMAC | Direct in-process callbacks | **Primary Product Workspace** |
| **Modal Cloud Compute** | `modal_app/worker.py`, deployment harness, Supabase secrets | None (Local execution against localhost Ollama) | **Primary Product Workspace** |
| **Product Test Suite** | 150 pytest unit/contract tests, live verification scripts | None (Integration test scripts for research scripts) | **Primary Product Workspace** |
| **Golden Showcase Fixtures** | `golden/` immutable fixtures, media files, checksum manifests | `05_final_showcase/` research source files | **Primary Product Workspace** (for app) / Research (origin) |
| **Vision Methodology (M1/M2/M3)** | Stubs (`raise NotImplementedError`), Stage 4B detector logic | Notebooks, weights (`best.pt`), configs, TrackEval harnesses | **Secondary Research Workspace** |
| **ASR Pipeline Logic** | Stubs (`audio.py`, `instructions.py`) | Frozen `backend/pipeline/asr.py`, Faster-Whisper int8 | **Secondary Research Workspace** |
| **LLM Grounding & Reporting** | Stubs (`evidence.py`, `reporting.py`), stale manifest reference | Frozen `validator.py`, `llm_client.py`, `reporter.py` | **Secondary Research Workspace** |
| **Homography & Kinematics** | Stubs (`calibration.py`, `kinematics.py`), calibration guards | Frozen `homography.py`, validated RMSE 0.651 m | **Secondary Research Workspace** |
| **Dense-GT Challenge Clips** | None | 4 iPhone 16 challenge clips + annotation packages | **Secondary Research Workspace** |

### 2.2 Duplicated or Overlapping Files

1. **Frontend Duplication**:
   - The secondary research workspace contains `frontend/index.html`, `frontend/index.css`, and `frontend/app.js`.
   - **Audit Verdict**: This is a legacy vanilla JS proof-of-concept created during local smoke testing (`REAL_3V3_SMOKE_TEST_001`). It is **completely superseded** by the primary workspace's modern TanStack Start application. It must NEVER be copied or merged into the primary product.
2. **Backend Duplication**:
   - The secondary research workspace contains `backend/server.py` and `backend/contracts/`.
   - **Audit Verdict**: `server.py` is a monolithic local mock. The primary workspace's FastAPI control plane (`backend/app/main.py`) with versioned routers and database repositories is the sole authoritative backend.
3. **Pipeline Logic Disconnect**:
   - In the secondary workspace, pipeline logic was extracted into clean modules (`backend/pipeline/homography.py`, `asr.py`, `fusion.py`, `validator.py`, `llm_client.py`, `reporter.py`, `orchestrator.py`).
   - In the primary workspace, `backend/app/pipeline/` contains modular interface stubs that raise `NotImplementedError` (except `detection.py`, which is fully implemented).

### 2.3 Artifacts to be Imported / Adapted from Research Workspace

When integration commences (post-audit and post-Vision freeze), the following exact artifacts must be ported into the primary product workspace:
1. `backend/pipeline/asr.py` $\rightarrow$ Adapt into `backend/app/pipeline/audio.py` and `asr.py`.
2. `backend/pipeline/homography.py` $\rightarrow$ Adapt into `backend/app/pipeline/calibration.py` and `kinematics.py`.
3. `backend/pipeline/fusion.py` $\rightarrow$ Adapt into `backend/app/pipeline/fusion.py`.
4. `backend/pipeline/validator.py` $\rightarrow$ Adapt into `backend/app/pipeline/grounding.py` (enforcing `LLM_GROUNDING_VALIDATOR_PATCH_001`).
5. `backend/pipeline/llm_client.py` & `reporter.py` $\rightarrow$ Adapt into `backend/app/pipeline/reporting.py`.
6. Final winning Vision pipeline (once M1, M2, or M3 is selected via dense-GT TrackEval) $\rightarrow$ Adapt into `backend/app/pipeline/tracking.py` and `identity.py`.
7. Physical calibration configuration: `config/3v3_homography_measured_metric_corrected.json` (SHA-256 `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507`).

### 2.4 Artifacts That Must Remain Strictly in Primary Product Workspace

1. All database migrations (`backend/migrations/001_...` through `004_...`).
2. FastAPI routing, dependency injection, and repository implementations (`backend/app/api/`, `backend/app/repositories/`).
3. Authoritative storage and media probing services (`backend/app/services/storage.py`, `backend/app/services/media_validation.py`).
4. Worker dispatch idempotency service and repository (`backend/app/services/dispatch_service.py`).
5. Complete TanStack Start frontend application (`frontend/tactical-ai-insights-main/`).
6. Golden showcase fixtures and verification services (`golden/`, `backend/app/services/golden.py`).
7. Complete 150-test automated verification suite (`backend/tests/`).

### 2.5 Cross-Workspace Ambiguities for Later Reconciliation

1. **LLM Reference Discrepancy**:
   - In primary workspace `backend/app/core/model_manifest.yaml` (line 96), `qwen3:8b` is mentioned as a research baseline.
   - In secondary research workspace `FINAL_IMPLEMENTATION_FREEZE.json`, `llama3.1:8b` (digest `46e0c10c...`) is frozen with system prompt SHA-256 `ab95a835...`.
   - **Resolution Required**: Update `model_manifest.yaml` to lock `llama3.1:8b` and its SHA digest.
2. **Modal Compute Role**:
   - In primary workspace, `modal_app/worker.py` is configured as a lightweight CPU smoke runner.
   - When pipeline logic is integrated, Modal must be configured with appropriate container dependencies (CTranslate2, Faster-Whisper, PyTorch, Ultralytics, and Ollama/vLLM client or remote inference endpoint).
3. **Showcase UI Wiring**:
   - In primary workspace `frontend/tactical-ai-insights-main/src/routes/showcase.tsx`, UI cards are static mocks.
   - The backend provides `GoldenFixtureService` (`/api/v1/showcase`), and `golden/media/` contains real overlay videos.
   - **Resolution Required**: Wire the frontend showcase route to fetch from `/api/v1/showcase`.

---

## 3. Repository and System Map

The primary product workspace contains 247 non-ignored files organized as follows:

```
AI-Driven Football Tactical Analysis and Training Evaluation System/
├── .env.example                               # Production environment variable template
├── AGENTS.md                                  # Scientific boundaries and system rules
├── ANTIGRAVITY_MASTER_AUDIT_CONTEXT.md        # Comprehensive master context for independent audit
├── CLAUDE_AUDIT_MANIFEST.md                   # Verification and audit file manifest
├── PRE_AUDIT_KNOWN_CONCERNS.md                # Confirmed technical concerns pre-audit
├── README.md                                  # Project overview and setup instructions
├── requirements-modal.txt                     # Pinned dependencies for Modal worker container
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/                            # Versioned REST API endpoints
│   │   │       ├── calibrations.py            # Calibration creation and validation routes
│   │   │       ├── internal.py                # Authenticated worker callback endpoints
│   │   │       ├── jobs.py                    # Analysis job creation, query, and dispatch
│   │   │       ├── sessions.py                # Session lifecycle and upload intent/completion
│   │   │       └── showcase.py                # Immutable golden showcase endpoints
│   │   ├── core/
│   │   │   ├── config.py                      # Pydantic BaseSettings environment configuration
│   │   │   ├── logging.py                     # Structured JSON logging
│   │   │   └── model_manifest.yaml            # Deployment model and configuration manifest
│   │   ├── pipeline/                          # AI Pipeline abstraction and execution
│   │   │   ├── audio.py                       # Audio extraction stub (raise NotImplementedError)
│   │   │   ├── calibration.py                 # Homography calibration stub (raise NotImplementedError)
│   │   │   ├── detection.py                   # Stage 4B YOLO11m detector (IMPLEMENTED)
│   │   │   ├── evidence.py                    # Structured evidence builder stub (NotImplementedError)
│   │   │   ├── fusion.py                      # Spatio-temporal multimodal fusion stub (NotImplementedError)
│   │   │   ├── identity.py                    # Identity safety gate stub (raise NotImplementedError)
│   │   │   ├── instructions.py                # Tactical instruction extraction stub (NotImplementedError)
│   │   │   ├── kinematics.py                  # Kinematics engine stub (raise NotImplementedError)
│   │   │   ├── registry.py                    # MethodologyExecutorRegistry (HTTP 409 safe guard)
│   │   │   ├── reporting.py                   # LLM & deterministic report stub (NotImplementedError)
│   │   │   └── tracking.py                    # Multi-object tracking stub (raise NotImplementedError)
│   │   ├── repositories/                      # Supabase PostgreSQL persistence layer
│   │   │   ├── calibration_repository.py      # Calibration records
│   │   │   ├── dispatch_repository.py         # Worker dispatch atomic idempotency repository
│   │   │   ├── job_repository.py              # AnalysisJob lifecycle and progress persistence
│   │   │   └── session_repository.py          # Sessions, media assets, and artifacts
│   │   ├── services/                          # Business logic and domain services
│   │   │   ├── dispatch_service.py            # Job dispatch orchestration and state validation
│   │   │   ├── golden.py                      # Golden showcase fixture service
│   │   │   ├── media_validation.py            # ffprobe media probing and container validation
│   │   │   └── storage.py                     # Supabase Storage client with typed error semantics
│   │   └── main.py                            # FastAPI application factory and middleware
│   ├── migrations/                            # PostgreSQL migrations executed on live Supabase
│   │   ├── 001_phase3_initial_schema.sql      # Core tables (sessions, jobs, media, artifacts)
│   │   ├── 002_fix_immutability_and_rls.sql   # RLS policies and immutability triggers
│   │   ├── 003_job_lifecycle_and_dispatch_idempotency.sql # Partial unique index & job columns
│   │   └── 004_media_validation.sql           # Media validation status enum & probed metadata
│   └── tests/                                 # 150 automated pytest suites (100% pass)
│       ├── test_contract_alignment.py         # API contract & enum consistency tests
│       ├── test_detection_tile_pipeline.py    # YOLO11m tiling and NMS coordinate tests
│       ├── test_hardening_pack1.py            # Job lifecycle, worker callback, dispatch tests
│       ├── test_hardening_pack2.py            # Authoritative ffprobe and storage error tests
│       ├── test_phase3_storage_and_upload.py  # Session and upload intent lifecycle tests
│       ├── test_phase4a_dispatch.py           # Worker dispatch idempotency tests
│       └── test_schemas.py                    # Domain model serialization and gate tests
│
├── frontend/tactical-ai-insights-main/        # Authoritative modern web application
│   ├── src/
│   │   ├── components/                        # UI components (shadcn/ui, radar, video player)
│   │   ├── hooks/
│   │   │   └── use-analysis.ts                # React Query hooks for sessions, uploads, jobs
│   │   ├── lib/
│   │   │   ├── api-client.ts                  # Fully typed API client for backend v1 endpoints
│   │   │   └── utils.ts                       # Tailwind merge and styling utilities
│   │   ├── routes/                            # TanStack Router filesystem routes
│   │   │   ├── index.tsx                      # Landing page with telemetry overview
│   │   │   ├── analysis.new.tsx               # Direct upload wizard with XHR progress bar
│   │   │   ├── analysis.$jobId.tsx            # Live job tracking with progress and stage polling
│   │   │   ├── analysis.$jobId.results.tsx    # 7-tab tactical dashboard with 409 retry handling
│   │   │   ├── showcase.tsx                   # Golden showcase demonstration view
│   │   │   ├── comparisons.tsx                # Methodology comparison information
│   │   │   └── research.tsx                   # Research background and scientific limits
│   │   └── router.tsx                         # Client/SSR router definition
│   └── package.json                           # Dependencies (React 19, TanStack Start, Vite 8)
│
├── golden/                                    # Immutable showcase fixtures & media
│   ├── fixtures/                              # Frozen JSON payloads and Markdown coach reports
│   ├── media/                                 # Overlay videos (C03, C06) and contact sheets (C04)
│   ├── manifest.json                          # Cryptographic checksums and resolution metadata
│   └── media_map.json                         # Logical media reference mapping
│
├── modal_app/                                 # Modal cloud execution harness
│   ├── entrypoint.py                          # CLI entrypoint for container execution
│   └── worker.py                              # Modal App definition and worker callback logic
│
└── shared/                                    # Shared domain schemas
    └── schemas/                               # Cross-boundary Pydantic data contracts
        ├── calibration.py                     # Homography matrix and pitch geometry contracts
        ├── job.py                             # AnalysisJob, JobStatus, AnalysisStage contracts
        ├── media.py                           # MediaAsset, UploadIntent, UploadStatus contracts
        ├── results.py                         # AnalysisResult, TacticalEvent, Limitations contracts
        └── session.py                         # AnalysisSession contracts
```

---

## 4. Current Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    CURRENT OPERATIONAL ARCHITECTURE                                |
+----------------------------------------------------------------------------------------------------+

  [ USER / BROWSER ]
          |
          | 1. Select Video & Audio
          v
  [ FRONTEND (TanStack Start / React 19) ]
          |
          | 2. POST /api/v1/sessions  (create session)
          | 3. POST /api/v1/sessions/{id}/upload-intent (request signed PUT URL)
          v
  [ FASTAPI CONTROL PLANE ]
          |
          | 4. Generate signed upload URL via SupabaseStorageService
          v
  [ FRONTEND ] -----------------------------------------------------> [ SUPABASE STORAGE ]
          |  5. Direct XHR PUT (Chunked, with progress bar 0..100%)             |
          |                                                                     | (Binary stored)
          | 6. POST /api/v1/sessions/{id}/complete                              |
          v                                                                     v
  [ FASTAPI CONTROL PLANE ] <---------------------------------------------------+
          |  7. Authoritative Media Validation:
          |     - Download object / stream to ffprobe
          |     - Verify container (MP4/MOV whitelist)
          |     - Verify video codec & audio stream
          |     - Verify duration <= 300.0s (server-enforced)
          |     - Extract exact dimensions & FPS
          |     - Update public.media_assets (status = VALIDATED, probed_metadata)
          |
          | 8. POST /api/v1/jobs  (create analysis job, status = QUEUED)
          | 9. POST /api/v1/jobs/{id}/dispatch
          v
  [ WORKER DISPATCH SERVICE ]
          |
          | 10. Check atomic idempotency via public.worker_dispatches
          |     (Predicate: state IN ('CREATED', 'SUBMITTED', 'RUNNING'))
          | 11. Query MethodologyExecutorRegistry
          v
  [ METHODOLOGY EXECUTOR REGISTRY ]
          |
          +---> [ FAIL-CLOSED SAFEGUARD TRIGGERED ]
                - No methodology executors registered
                - Returns HTTP 409 Conflict: METHODOLOGY_EXECUTOR_NOT_READY
                - Job remains safely in QUEUED state in Supabase DB
                - No corrupted data or fake inference emitted

  ====================================================================================================
  [ UNWIRED / EXTERNAL SUBSYSTEMS CURRENTLY OUTSIDE THE RUNTIME PATH ]
  ====================================================================================================

  [ backend/app/pipeline/ ]
      ├── detection.py      ---> IMPLEMENTED (Stage 4B YOLO11m tiling + NMS)
      ├── tracking.py       ---> STUB (raises NotImplementedError)
      ├── identity.py       ---> STUB (raises NotImplementedError)
      ├── calibration.py    ---> STUB (raises NotImplementedError)
      ├── kinematics.py     ---> STUB (raises NotImplementedError)
      ├── audio.py          ---> STUB (raises NotImplementedError)
      ├── instructions.py   ---> STUB (raises NotImplementedError)
      ├── fusion.py         ---> STUB (raises NotImplementedError)
      ├── evidence.py       ---> STUB (raises NotImplementedError)
      └── reporting.py      ---> STUB (raises NotImplementedError)

  [ modal_app/worker.py ]   ---> CPU smoke test harness only; no GPU inference loaded
  [ Research Workspace ]   ---> Frozen methodology (Faster-Whisper, Llama 3.1 8B, Homography)
```

---

## 5. Frontend Audit

### 5.1 Technology Stack & Build Tooling
- **Framework**: TanStack Start `1.170.18` on Nitro `3.0.260603-beta` (SSR enabled).
- **Core Library**: React `19.0.0` / React DOM `19.0.0`.
- **Router**: TanStack Router `1.170.18` (file-based routing with full TypeScript path inference).
- **Client State**: `@tanstack/react-query` `5.90.21` (configured with automatic polling and retry logic).
- **Styling**: Tailwind CSS `4.2.1` with custom theme variables, `@tailwindcss/vite`, `clsx`, `tailwind-merge`.
- **UI Primitives**: Radix UI (`@radix-ui/react-tabs`, `@radix-ui/react-slot`), Lucide React icons.
- **Build Status**: Verified 100% clean compilation (`npm run build` completed in 534ms with zero errors or warnings).

### 5.2 Route-by-Route Implementation Audit

| Route Path | File Location | Classification | Operational State & Implementation Details |
| :--- | :--- | :--- | :--- |
| `/` | `src/routes/index.tsx` | `WORKING / PARTIAL` | Landing dashboard. Renders telemetry cards, pipeline overview, and quick links. System status metrics currently show static placeholders (`—`). |
| `/analysis/new` | `src/routes/analysis.new.tsx` | `IMPLEMENTED AND WORKING` | Complete direct upload wizard. Handles file drag-and-drop, client-side container validation (MP4/MOV, WAV/MP3), client duration check (<300s), session creation via API, upload intent acquisition, direct browser-to-Supabase XHR PUT with live percentage progress bar, upload completion notification, and redirects to `/analysis/$jobId`. |
| `/analysis/$jobId` | `src/routes/analysis.$jobId.tsx` | `IMPLEMENTED AND WORKING` | Active job monitoring view. Connects via `useAnalysisJob` hook, polls backend at 2000ms intervals, displays animated multi-stage progress bar (0..100%), current stage label, and detailed status/error messages. Automatically navigates to `/results` on `COMPLETED` or `COMPLETED_WITH_LIMITATIONS`. |
| `/analysis/$jobId/results` | `src/routes/analysis.$jobId.results.tsx` | `WORKING / PARTIAL` | Tactical results dashboard. Elegantly handles backend HTTP 409 Conflict ("Result Not Ready") by rendering an active processing progress state. When results are present, renders 7 comprehensive tabs: Executive Summary, Tactical Events, Radar View (2D canvas pitch), Kinematics, Identity Safety Gate, Full Report, and Raw Artifacts. (Currently displays limitations banner because backend AI is stubbed). |
| `/analysis/processing` | `src/routes/analysis.processing.tsx` | `LEGACY / PREVIEW` | Static preview route displaying simulated pipeline progress. Contains an explicit banner directing users to active `$jobId` workflows. |
| `/results` | `src/routes/results.tsx` | `LEGACY / PREVIEW` | Static preview dashboard displaying mock data. Kept for UI design reference; contains banner pointing to dynamic `$jobId/results` routes. |
| `/showcase` | `src/routes/showcase.tsx` | `PARTIAL / MOCKED` | Golden showcase demonstration page. Displays structured case cards for C03 (Hold Position), C04 (Defensive Marking), and C06 (Pressing Response). However, cards use hardcoded frontend constants rather than consuming the backend `/api/v1/showcase` endpoint. |
| `/comparisons` | `src/routes/comparisons.tsx` | `IMPLEMENTED AND WORKING` | Informational page rendering methodology comparison tables (Vision M1/M2/M3, ASR models, LLM grounding rates). |
| `/research` | `src/routes/research.tsx` | `IMPLEMENTED AND WORKING` | Scientific documentation page outlining experimental protocols, camera geometry, and identity fragmentation boundaries. |

### 5.3 Frontend Authentication State
- **Status**: `MISSING / DEV_MODE`.
- No login, registration, or JWT session handling is present in the frontend UI.
- All requests default to the development tenant ID (`00000000-0000-0000-0000-000000000001`).

---

## 6. Backend Audit

### 6.1 Control Plane Architecture
- **Framework**: FastAPI `0.115.6`, Uvicorn `0.34.0`, Pydantic v2 `2.10.4`.
- **Application Factory**: `backend/app/main.py` configuring CORS, structured exception handlers, request ID middleware, and API router mounting under `/api/v1`.
- **Database Client**: Official Supabase Python SDK `2.11.0` with connection pooling and typed response parsing.

### 6.2 API Route Map & Contracts

| Endpoint | Method | Router Module | Status | Request / Response Behavior |
| :--- | :---: | :--- | :--- | :--- |
| `/api/v1/sessions` | `POST` | `sessions.py` | `WORKING` | Creates a new session in `public.sessions` with user ID and title. |
| `/api/v1/sessions/{id}` | `GET` | `sessions.py` | `WORKING` | Retrieves session metadata and associated media assets. |
| `/api/v1/sessions/{id}/upload-intent` | `POST` | `sessions.py` | `WORKING` | Validates file type and size; generates signed Supabase Storage PUT URL. |
| `/api/v1/sessions/{id}/complete` | `POST` | `sessions.py` | `WORKING` | **Server-Authoritative Validation**: Checks object existence in storage, probes file with `ffprobe`, enforces 300s limit and container whitelist, persists probed metadata, transitions status to `VALIDATED`. |
| `/api/v1/jobs` | `POST` | `jobs.py` | `WORKING` | Creates analysis job in `public.analysis_jobs`. Enforces that media status is `VALIDATED` and blocks `DEMO_FIXED_CALIBRATION` for user uploads. |
| `/api/v1/jobs/{id}` | `GET` | `jobs.py` | `WORKING` | Returns live job status, progress percentage (0..100), stage message, error code. |
| `/api/v1/jobs/{id}/dispatch` | `POST` | `jobs.py` | `WORKING` | Gated by `WorkerDispatchService` and `MethodologyExecutorRegistry`. Returns HTTP 409 `METHODOLOGY_EXECUTOR_NOT_READY` in current stubbed state. |
| `/api/v1/jobs/{id}/result` | `GET` | `jobs.py` | `WORKING` | Returns `AnalysisResult` from database. Returns HTTP 409 if job is not completed. |
| `/api/v1/internal/jobs/{id}/progress` | `POST` | `internal.py` | `WORKING` | **Worker Callback Endpoint**: Authenticated via `X-Worker-Secret` using constant-time HMAC comparison. Updates job progress, stage, error details, and completed timestamp in database. |
| `/api/v1/showcase` | `GET` | `showcase.py` | `WORKING` | Returns metadata and signed URLs for golden capability showcase cases. |
| `/api/v1/showcase/{case_id}` | `GET` | `showcase.py` | `WORKING` | Returns individual golden showcase payload (C03, C04, C06). |
| `/api/v1/calibrations` | `POST` | `calibrations.py` | `WORKING` | Creates custom pitch calibration record with geometry validation. |

---

## 7. Database and Supabase Audit

### 7.1 Applied Database Migrations

The database is managed via 4 sequential migrations, verified live on Supabase PostgreSQL:

1. **`001_phase3_initial_schema.sql`**:
   - Created core tables: `sessions`, `media_assets`, `analysis_jobs`, `calibrations`, `instruction_events`, `analysis_results`, `artifacts`.
   - Defined enums: `upload_status`, `job_status`, `analysis_stage`, `identity_status`, `calibration_mode`.
   - Established foreign key constraints and timestamp triggers.

2. **`002_fix_immutability_and_rls.sql`**:
   - Implemented Row Level Security (RLS) policies for tenant isolation.
   - Enforced immutability triggers on completed analysis results and frozen artifacts.

3. **`003_job_lifecycle_and_dispatch_idempotency.sql`**:
   - Added persistent job lifecycle fields to `public.analysis_jobs`:
     - `progress_percent` (INTEGER, constrained `CHECK (progress_percent >= 0 AND progress_percent <= 100)`)
     - `stage_message` (TEXT)
     - `error_code` (TEXT)
     - `error_details` (JSONB)
     - `modal_call_id` (TEXT)
     - `completed_at` (TIMESTAMPTZ)
   - Created `public.worker_dispatches` table for atomic dispatch tracking.
   - Created critical partial unique index:
     ```sql
     CREATE UNIQUE INDEX uq_active_worker_dispatch_per_job
     ON public.worker_dispatches (job_id)
     WHERE state IN ('CREATED', 'SUBMITTED', 'RUNNING');
     ```
     This mathematically eliminates race conditions and ensures exactly-once worker dispatch.

4. **`004_media_validation.sql`**:
   - Extended `upload_status` enum to include `VALIDATED` and `VALIDATION_FAILED`.
   - Added `probed_metadata` (JSONB) to `public.media_assets` for storing server-verified container, codec, duration, FPS, and dimension attributes.
   - Enforced foreign key constraint preventing jobs from being created on unvalidated media.

---

## 8. Modal and Compute Audit

### 8.1 Current Implementation State
- **Directory**: `modal_app/`
- **Files**: `modal_app/worker.py`, `modal_app/entrypoint.py`, `requirements-modal.txt`.
- **Image Definition**: Debian-slim with Python 3.10+, FFmpeg, and Supabase client.
- **Current Role**: **Control plane smoke and callback testing harness**.
- **Functions Defined**:
  - `infrastructure_smoke`: Validates Modal environment initialization, environment variable injection, and outbound network access.
  - `dispatch_placeholder`: Simulates worker execution by acquiring a job, reporting staged progress (10% $\rightarrow$ 50% $\rightarrow$ 100%) back to FastAPI via `/api/v1/internal/jobs/{id}/progress`, and completing the job.
- **Compute Sizing**: Configured as CPU-only (`cpu=2.0, memory=2048`). No GPU (NVIDIA T4/A10G) is currently attached in `worker.py`.
- **Evaluation**: The Modal harness is structurally sound and verified for control-flow callbacks. However, it currently contains **NO live AI model weights, NO PyTorch/CUDA runtime, and NO inference pipelines**.

---

## 9. Current AI Pipeline Audit

### 9.1 Vision Pipeline
- **Production Status**: `VISION_METHOD_PENDING_FINAL_EVALUATION_SELECTION`.
- **Detector Implementation (`backend/app/pipeline/detection.py`)**:
  - Fully implemented and covered by unit tests (`test_detection_tile_pipeline.py`).
  - Architecture: Stage 4B YOLO11m fine-tuned detector (`best.pt`, 40.5 MB, SHA-256 `f6b3fe6f...`).
  - Tiling Strategy: 3 horizontal slices, 15% overlap, `imgsz=1280`, person class (`classes=[0]`), confidence threshold 0.20, global NMS IoU threshold 0.70.
  - Coordinate translation: Correctly shifts tile coordinates $(x_t, y_t)$ to source frame coordinates $(x_s, y_s)$ before global suppression.
- **Tracking & Identity Implementation (`backend/app/pipeline/tracking.py`, `identity.py`)**:
  - Currently **STUBS** raising `NotImplementedError`.
  - Stored in secondary research workspace: BoT-SORT fallback C config, deep ReID GTA-Track logic, and SriTrack evaluation notebooks.
- **Scientific Gate Status**: The identity gate contract in `shared/schemas/job.py` strictly encodes that `fragmentation_ratio > 1.50` triggers `FAIL_HIGH_FRAGMENTATION` and enforces `player_level_analysis_allowed = False`.

### 9.2 ASR Pipeline
- **Production Status**: `FROZEN_RESEARCH_EXTERNAL`.
- **Selected Model**: `faster-whisper base.en` executed via `CTranslate2` on CPU int8 (8 threads).
- **Primary Repo Implementation (`backend/app/pipeline/audio.py`, `instructions.py`)**:
  - Currently **STUBS** raising `NotImplementedError`.
- **Research Repo Implementation (`backend/pipeline/asr.py`)**:
  - Fully operational in research workspace.
  - Generates 16 kHz mono PCM via `ffmpeg`, extracts timestamped word-level transcripts with Silero VAD filtering (`min_silence_duration_ms=500`), categorizes tactical instructions via deterministic keyword rules, and enforces parent-segment timestamp inheritance.

### 9.3 LLM Grounding & Reporting Pipeline
- **Production Status**: `FROZEN_RESEARCH_EXTERNAL`.
- **Selected Model**: `llama3.1:8b` (authoritative digest: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`).
- **System Prompt**: Frozen template with SHA-256 `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`.
- **Grounding Validator**: `LLM_GROUNDING_VALIDATOR_PATCH_001` implementing 8 deterministic grounding gates:
  1. Forbidden Absolute Identity Claims Gate
  2. Forbidden Psychological/Disciplinary Words Gate
  3. Tactical Instruction Grounding Gate
  4. Numeric Consistency Gate (regex numeric extraction against evidence)
  5. Target Attribution Gate (negation-safe)
  6. Pitch Zone Grounding Gate
  7. Mandatory Limitations Mention Gate
  8. Output Format and Section Completeness Gate
- **Primary Repo Implementation (`backend/app/pipeline/evidence.py`, `reporting.py`)**:
  - Currently **STUBS** raising `NotImplementedError`.
  - Manifest discrepancy: `backend/app/core/model_manifest.yaml` line 96 still lists `qwen3:8b` as a research reference.
- **Research Repo Implementation (`backend/pipeline/validator.py`, `reporter.py`)**:
  - Fully operational; passed 13/13 patch regression tests and validated during `REAL_3V3_SMOKE_TEST_001`.

---

## 10. Multimodal Fusion Audit

- **Primary Repo Status**: `STUB_PLACEHOLDER`. `backend/app/pipeline/fusion.py` raises `NotImplementedError`.
- **Research Repo Status**: `OPERATIONAL_IN_RESEARCH`. `backend/pipeline/fusion.py` implements the deterministic fusion engine:
  - Ingests ASR tactical events with time intervals $[t_{start}, t_{end}]$.
  - Defines post-instruction evaluation windows (default $t_{event} + 2.0s$ to $t_{event} + 6.0s$).
  - Evaluates player track kinematics (speed, displacement, direction vector) within the window.
  - Maps player coordinates to tactical zones (Defensive Third, Middle Third, Attacking Third).
  - Enforces fail-closed identity gate: when identity is fragmented, player attributions are stripped, and observations are aggregated at team/spatial level only.

---

## 11. Homography and Kinematics Audit

- **Calibration Classification**: `MODERATE_CONFIDENCE_MEASURED_METRIC_ESTIMATE`.
- **Physical Pitch Dimensions**: Length **19.31 m**, Width **19.88 m** (corrected 3v3 pitch).
- **Homography Matrix Checksum**: `config/3v3_homography_measured_metric_corrected.json` (SHA-256 `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507`).
- **Independent Validation RMSE**: **0.651 m** (maximum error 0.841 m).
- **Kinematics Rules**:
  - 7-observation rolling median filter on coordinates before velocity derivation.
  - Outlier velocity rejection: speeds exceeding **36.0 km/h** are clamped/rejected as tracking jitter.
  - Gap policy: Velocity and distance are NEVER interpolated across tracking gaps $> 0.5s$.
  - Measurement unit safety: In non-calibrated videos, metric units (m, km/h) are strictly forbidden; coordinates remain in normalized pixel space $[0, 1]$.
- **Primary Repo Implementation**: `calibration.py` and `kinematics.py` are stubs. However, `jobs.py` correctly enforces calibration mode safety: user uploads cannot select `DEMO_FIXED_CALIBRATION`.

---

## 12. Report Generation Audit

- **Primary Repo Status**: `STUB_PLACEHOLDER`.
- **Research Repo Status**: Fully tested (`backend/pipeline/reporter.py`).
- **Execution Workflow**:
  1. Evidence compilation: JSON payload containing tactical events, team spatial metrics, identity status (`FAIL_HIGH_FRAGMENTATION`), and limitation notes.
  2. Prompt rendering: Injects structured evidence into system prompt `prompts/coach_report_system.txt`.
  3. LLM Query: Local Ollama invocation (`llama3.1:8b`, temperature 0.0, seed 42).
  4. Deterministic Validation: `validate_grounding()` evaluates all 8 gates.
  5. Fallback Decision: If LLM fails any gate or is unreachable, the system automatically emits the deterministic fallback report (`reports/final_real_session_coaching_report.md`), guaranteeing a scientifically grounded output with zero hallucinations.

---

## 13. Authentication and Security Audit

- **Authentication State**: `DISABLED_DEV_MODE`.
- **Tenant Isolation**: Database migrations 001 and 002 define RLS policies tied to `auth.uid() = user_id`. In development, requests default to tenant UUID `00000000-0000-0000-0000-000000000001`.
- **Storage Security**: Media objects in Supabase Storage buckets (`raw-videos`, `audio-extractions`, `artifacts`) are private. Access is mediated exclusively through short-lived signed URLs (default expiry 3600 seconds).
- **Worker Callback Security**: The internal worker progress endpoint (`POST /api/v1/internal/jobs/{id}/progress`) is secured via a shared secret (`WORKER_CALLBACK_SECRET`) verified using `hmac.compare_digest` to prevent timing attacks.

---

## 14. Testing State

### 14.1 Primary Product Workspace Test Suite
- **Framework**: `pytest 8.3.4` + `pytest-asyncio 0.25.2`.
- **Execution Result**: **150 / 150 PASSED** (100% pass rate in 1.30s).

| Test Module | Tests | Scope & Verified Invariants |
| :--- | :---: | :--- |
| `test_contract_alignment.py` | 13 | Cross-boundary enum synchronization, ISO 8601 timestamps, Pydantic v2 schemas. |
| `test_detection_tile_pipeline.py` | 15 | YOLO11m 3-tile horizontal slicing, coordinate offset translation, global NMS IoU 0.70. |
| `test_hardening_pack1.py` | 17 | Job lifecycle persistence, worker callback auth, dispatch idempotency conflict handling. |
| `test_hardening_pack2.py` | 46 | Server-authoritative `ffprobe` probing, 300s limit, container whitelist, typed storage errors. |
| `test_phase3_storage_and_upload.py` | 7 | Session creation, upload intent signed URLs, authoritative upload verification. |
| `test_phase4a_dispatch.py` | 14 | Worker dispatch state machine, atomic repository CRUD, methodology registry gates. |
| `test_schemas.py` | 38 | Pydantic data models, identity safety withholding contracts, metric confidence enums. |

### 14.2 Research Workspace Test Suite
- `test_deterministic_integration.py`: 13 validator patch regression tests (100% pass rate) + 14 E2E pipeline integration scenarios.
- `run_real_session_smoke_test.py`: Full real-session validation (`REAL_3V3_SMOKE_TEST_001`) executing on 339.87s match footage in 101.88s wall-clock time.

---

## 15. Legacy and Duplication Audit

1. **Obsolete Research Frontend**:
   - `G:\My Drive\Football_Training_Assistant_MVP\frontend/` (`index.html`, `index.css`, `app.js`).
   - Action: Retain in research workspace for historical provenance; do not import into product.
2. **Obsolete Research Server**:
   - `G:\My Drive\Football_Training_Assistant_MVP\backend\server.py`.
   - Action: Superseded by `backend/app/main.py`.
3. **Frontend Preview Routes**:
   - `frontend/tactical-ai-insights-main/src/routes/analysis.processing.tsx` and `results.tsx`.
   - Action: Informational banners are in place; deprecate or remove prior to production release.
4. **Stale Model Manifest Entry**:
   - `backend/app/core/model_manifest.yaml` references `qwen3:8b`.
   - Action: Update to authoritative frozen `llama3.1:8b`.

---

## 16. Dependency and Environment Audit

### 16.1 Backend Python Environment
- **Authoritative Supported Runtime**: Python `>= 3.10` (Modal container uses 3.10+; local dev running 3.8.10 is functional for current tests but deprecated for fresh installs).
- **Core Dependencies (`backend/requirements.txt`)**:
  - `fastapi==0.115.6`, `uvicorn==0.34.0`
  - `pydantic==2.10.4`, `pydantic-settings==2.7.1`
  - `supabase==2.11.0`, `postgrest==0.19.2`, `storage3==0.9.1`
  - `modal>=1.5.0,<2.0.0`
  - `ultralytics==8.3.58`, `opencv-python-headless==4.10.0.84`, `torch>=2.0.0`
  - `pytest==8.3.4`, `pytest-asyncio==0.25.2`, `httpx==0.28.1`
- **System Binaries Required**: `ffmpeg` and `ffprobe` (strictly required for server-authoritative media validation).

### 16.2 Frontend Node Environment
- **Node Runtime**: Node `>= 18.0.0`.
- **Build Tooling**: Vite `8.1.5`, Nitro `3.0.260603-beta`.
- **Core Dependencies**: React `19.0.0`, `@tanstack/react-router` `1.170.18`, `@tanstack/react-query` `5.90.21`, Tailwind CSS `4.2.1`.

---

## 17. Existing Documentation Accuracy Audit

The following documents exist in the secondary research workspace (`G:\My Drive\Football_Training_Assistant_MVP`):

1. **`FINAL_SYSTEM_ARCHITECTURE.md`**:
   - **Audit Verdict**: `PARTIALLY STALE / RESEARCH-FOCUSED`.
   - Accurately details the scientific pipeline and mathematical grounding gates. However, it describes a local script execution model rather than the primary workspace's distributed Supabase + Modal + TanStack Start architecture.
2. **`FINAL_MULTIMODAL_DATA_FLOW.md`**:
   - **Audit Verdict**: `ACCURATE FOR METHODOLOGY`.
   - Accurately details the step-by-step tensor and metadata flow from video/audio to structured coaching report.
3. **`FINAL_IMPLEMENTATION_FREEZE.json`**:
   - **Audit Verdict**: `ACCURATE / AUTHORITATIVE METHODOLOGY CONTRACT`.
   - Records the exact frozen hashes for Faster-Whisper, Llama 3.1 8B, and homography calibration. Formally notes that Vision methodology is unresolved pending dense-GT evaluation.
4. **`FINAL_END_TO_END_SMOKE_TEST.md`**:
   - **Audit Verdict**: `ACCURATE HISTORICAL RECORD`.
   - Documents the successful 101.88s execution of `REAL_3V3_SMOKE_TEST_001` on 2026-09-25.
5. **`FINAL_IMPLEMENTATION_TEST_RESULTS.json`**:
   - **Audit Verdict**: `ACCURATE`.
   - Documents 100% pass rate across 13 grounding validator patch tests and 14 E2E scenarios.

---

## 18. Target Architecture Map (After Vision Freeze)

```
+----------------------------------------------------------------------------------------------------+
|                                    TARGET INTEGRATED ARCHITECTURE                                  |
+----------------------------------------------------------------------------------------------------+

  [ BROWSER: TanStack Start SSR (React 19) ]
         |
         | 1. Upload Video & Coach Audio
         v
  [ FASTAPI CONTROL PLANE ]
         | 2. Direct signed upload to Supabase Storage
         | 3. Authoritative ffprobe validation (300s, MP4/MOV, codecs)
         | 4. Persist AnalysisJob (QUEUED) in Supabase PostgreSQL
         | 5. Dispatch job via WorkerDispatchService (Atomic Idempotency)
         v
  [ MODAL GPU WORKER CONTAINER ] (T4 / A10G GPU + CPU int8)
         |
         +---> 1. MEDIA INGESTION & PROBING
         |        Download video/audio from Supabase Storage via signed URLs
         |
         +---> 2. FINAL_SELECTED_VISION_METHOD (M1, M2, or M3)
         |        - Detector: Stage 4B YOLO11m / Selected checkpoint
         |        - Tracker: BoT-SORT / GTA-Track / SriTrack
         |        - Identity Quality Gate: Compute fragmentation ratio
         |          * IF ratio > 1.50 -> Set FAIL_HIGH_FRAGMENTATION
         |          * WITHHOLD player-level tactical attributions
         |
         +---> 3. CALIBRATED HOMOGRAPHY & KINEMATICS
         |        - Perspective projection to 19.31m x 19.88m pitch
         |        - 7-observation rolling median filter
         |        - Outlier velocity rejection (> 36 km/h clamped)
         |
         +---> 4. ASR SUBSYSTEM (faster-whisper base.en / CTranslate2 CPU int8)
         |        - 16 kHz mono extraction
         |        - Word-level timestamps & Silero VAD
         |        - Deterministic tactical event categorization
         |
         +---> 5. DETERMINISTIC SPATIO-TEMPORAL FUSION
         |        - Align tactical instructions with player track temporal windows
         |        - Map tracks to tactical zones (Defensive/Middle/Attacking)
         |        - Strip player attributions if identity gate failed
         |
         +---> 6. REPORT GENERATION & GROUNDING VALIDATION
         |        - Format structured evidence payload
         |        - Query llama3.1:8b (local Ollama / vLLM)
         |        - Run LLM_GROUNDING_VALIDATOR_PATCH_001 (8 gates)
         |        - IF validation fails -> Fall back to deterministic report
         |
         +---> 7. PERSISTENCE & WORKER CALLBACK
                  - Upload artifacts (overlays, reports, JSON) to Supabase Storage
                  - POST /api/v1/internal/jobs/{id}/progress (Authenticated HMAC)
                  - Update public.analysis_jobs to COMPLETED_WITH_LIMITATIONS
```

---

## 19. Gap Analysis and Prioritized Risk Register

### P0 — Blocks Final Prototype Integration
- **GAP-P0-1: Internal Pipeline Stubs Disconnect**:
  - *Description*: Primary workspace `backend/app/pipeline/` modules raise `NotImplementedError`, and `MethodologyExecutorRegistry` blocks dispatch with HTTP 409.
  - *Remediation*: Port and adapt the tested pipeline modules from research workspace (`asr.py`, `homography.py`, `fusion.py`, `validator.py`, `reporter.py`) into the primary backend.
- **GAP-P0-2: Vision Methodology Unresolved**:
  - *Description*: Selection between M1, M2, and M3 is awaiting human dense-GT annotation and TrackEval scoring on the 4 challenge clips.
  - *Remediation*: Complete dense-GT scoring, record winning methodology, and integrate its tracker into `backend/app/pipeline/tracking.py`.
- **GAP-P0-3: Modal GPU Pipeline Wiring**:
  - *Description*: `modal_app/worker.py` is currently a CPU smoke harness and does not load the AI pipeline.
  - *Remediation*: Configure Modal container with GPU, dependencies, and pipeline execution script.

### P1 — Must Fix Before Final Submission
- **GAP-P1-1: Model Manifest Synchronization**:
  - *Description*: `backend/app/core/model_manifest.yaml` lists `qwen3:8b` instead of frozen `llama3.1:8b`.
  - *Remediation*: Update manifest with `llama3.1:8b` digest and prompt SHA `ab95a835...`.
- **GAP-P1-2: Frontend Showcase Route Wiring**:
  - *Description*: `frontend/tactical-ai-insights-main/src/routes/showcase.tsx` uses static mock cards instead of fetching from `/api/v1/showcase`.
  - *Remediation*: Connect React Query to `/api/v1/showcase` to render real golden media.

### P2 — Important Hardening
- **GAP-P2-1: Python Runtime Standardization**:
  - *Description*: Local development is running Python 3.8.10, whereas Modal and backend contracts specify Python `>= 3.10`.
  - *Remediation*: Standardize local development virtual environment to Python 3.10+.
- **GAP-P2-2: Frontend Preview Routes Cleanup**:
  - *Description*: Legacy preview routes (`/analysis/processing`, `/results`) remain present in the build.
  - *Remediation*: Remove or redirect legacy routes cleanly.

### P3 — Optional / Future Work
- **GAP-P3-1: User Authentication & Multi-Tenancy**:
  - *Description*: System operates in single-tenant dev mode.
  - *Remediation*: Implement Supabase Auth UI and JWT verification in production release.

---

## 20. Critical Question: How Much Work Is Actually Left?

1. **Is the frontend fundamentally complete?**
   - **YES**. The TanStack Start / React 19 frontend is exceptionally mature: complete upload wizard with XHR progress, live polling job monitor, 7-tab tactical dashboard with 409 retry handling, and clean SSR compilation. Only showcase API wiring remains.
2. **Is the backend fundamentally complete?**
   - **YES (Control Plane) / NO (Pipeline Execution)**. The control plane, routing, Supabase integration, authoritative media probing, and dispatch idempotency are 100% complete and tested. The internal AI pipeline execution is stubbed.
3. **Is Supabase integration complete?**
   - **YES**. All 4 migrations are applied and verified live on PostgreSQL with RLS, check constraints, and partial unique indexes.
4. **Is Modal integration usable?**
   - **YES (Harness) / NO (GPU AI Runtime)**. The worker callback and dispatch lifecycle work. Attaching GPU dependencies and executing the AI pipeline is required.
5. **Is the AI orchestration real or partially mocked?**
   - In this primary product workspace, it is currently **safely stubbed** (raises `NotImplementedError` / returns HTTP 409). In the secondary research workspace, it is **100% real and tested**.
6. **Is frozen ASR genuinely production-wired?**
   - In research workspace: **YES**. In primary product workspace: **NOT YET WIRED**.
7. **Is frozen LLM genuinely production-wired?**
   - In research workspace: **YES**. In primary product workspace: **NOT YET WIRED**.
8. **What currently occupies the Vision production slot?**
   - It is designated `VISION_METHOD_PENDING_FINAL_EVALUATION_SELECTION`. Stage 4B YOLO11m detector logic is implemented, but tracker/identity selection (M1 vs M2 vs M3) awaits dense-GT evaluation.
9. **What exact work remains once Vision is selected?**
   - Port research pipeline modules (`asr.py`, `homography.py`, `fusion.py`, `validator.py`, `reporter.py`) and the winning Vision tracker into `backend/app/pipeline/`, update `model_manifest.yaml`, wire Modal worker to execute the pipeline, and connect frontend showcase route.
10. **Is full prototype closure a small integration task, medium task, or major rebuild?**
   - **MEDIUM INTEGRATION TASK** (Estimated 3 to 5 focused engineering days).
   - *Rationale*: Zero major rebuilding is needed. The heavy product engineering (frontend, database, storage, validation, dispatch idempotency) is already finished and passing 150 tests. The heavy research methodology (Faster-Whisper, Llama 3.1 8B, Patch 001 validator, Homography) is already developed and validated in the research workspace. Prototype closure is strictly an **adapter and integration exercise** to bridge the two.

---

## 21. Recommended Integration Sequence

1. **Step 1: Complete and Freeze Vision Methodology Selection**:
   - Complete human dense-GT annotations on the 4 iPhone 16 challenge clips.
   - Run TrackEval benchmark across M1, M2, and M3.
   - Record winning methodology and update project evidence logs.
2. **Step 2: Reconcile Primary Model Manifest**:
   - Update `backend/app/core/model_manifest.yaml` to lock `llama3.1:8b` and system prompt SHA-256 `ab95a835...`.
3. **Step 3: Port and Adapt Methodology Modules into Primary Backend**:
   - Port `backend/pipeline/asr.py` $\rightarrow$ `backend/app/pipeline/audio.py` & `asr.py`.
   - Port `backend/pipeline/homography.py` $\rightarrow$ `backend/app/pipeline/calibration.py` & `kinematics.py`.
   - Port `backend/pipeline/fusion.py` $\rightarrow$ `backend/app/pipeline/fusion.py`.
   - Port `backend/pipeline/validator.py` & `reporter.py` $\rightarrow$ `backend/app/pipeline/grounding.py` & `reporting.py`.
   - Integrate winning Vision tracker $\rightarrow$ `backend/app/pipeline/tracking.py` & `identity.py`.
4. **Step 4: Register Production Methodology Executor**:
   - Register the integrated pipeline executor in `backend/app/pipeline/registry.py` to lift the HTTP 409 gate.
5. **Step 5: Wire Modal GPU Worker**:
   - Update `modal_app/worker.py` container image with PyTorch, CUDA, CTranslate2, and Ultralytics.
   - Connect worker execution to invoke the ported pipeline.
6. **Step 6: Wire Frontend Showcase Route**:
   - Update `frontend/tactical-ai-insights-main/src/routes/showcase.tsx` to consume `/api/v1/showcase`.
7. **Step 7: Execute End-to-End System Smoke Test**:
   - Run full end-to-end match analysis through the web UI and verify live persistence.
