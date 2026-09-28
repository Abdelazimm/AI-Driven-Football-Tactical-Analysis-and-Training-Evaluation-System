# Claude Independent Audit Manifest: Included File Inventory & Roles

> **Audit Package**: `claude_antigravity_audit_bundle.zip`  
> **Prepared For**: Independent Claude Auditor  
> **Scope**: All integration and product infrastructure code implemented in the Antigravity Track (Phases 1–4A.1).

---

## 1. Security & Redaction Boundaries

The audit bundle strictly complies with the following redaction standards:
- **Zero Real Secrets**: Excludes `.env`, `.env.local`, `.env.production`, active Supabase service-role keys, database passwords, and Modal token credentials.
- **Example Template**: Includes only [.env.example](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/.env.example) containing sanitized placeholders.
- **Zero Heavy / Transient Artifacts**: Excludes `.venv/`, `node_modules/`, `.output/`, `dist/`, `.pytest_cache/`, `__pycache__/`, `.git/`, binary model weights (`*.pt`, `*.onnx`), and raw video footage.
- **No Research Code Interference**: The separate Codex methodology research workspace is completely excluded.

---

## 2. Inventory of Included Audit Files

### 2.1 Audit Master Documents & Project Governance
| File Path | Role & Importance |
| :--- | :--- |
| `ANTIGRAVITY_MASTER_AUDIT_CONTEXT.md` | Authoritative system overview, architecture, completed phases, canonical contracts, and safety gates. |
| `PRE_AUDIT_KNOWN_CONCERNS.md` | Explicit record of technical debt, deprecation warnings, and specific questions for the auditor. |
| `CLAUDE_AUDIT_MANIFEST.md` | This file; inventory and justification of all bundled assets. |
| `AGENTS.md` | Mandatory system rules, scientific invariants, persistent identity reality, and detector decisions. |
| `README.md` | Top-level project purpose, operating modes, and directory layout. |
| `.env.example` | Sanitized configuration template demonstrating expected environment keys without secrets. |
| `.gitignore` | Ignore rules preventing accidental commits of virtual environments, secrets, and binary weights. |
| `requirements-modal.txt` | Explicit modern dependency specification for Modal compute tooling. |

---

### 2.2 Backend Application (`backend/`)
| File Path | Role & Importance |
| :--- | :--- |
| `backend/pyproject.toml` | Backend package definition; declares official runtime policy (`requires-python = ">=3.10"`). |
| `backend/requirements.txt` | Pinned control-plane dependencies (FastAPI, Pydantic, Supabase, Modal, etc.). |
| `backend/app/main.py` | FastAPI application entry point, CORS configuration, lifecycle events, and route mounting. |
| `backend/app/core/config.py` | Pydantic BaseSettings configuration parsing environment variables. |
| `backend/app/core/models.py` | Model manifest specifying official deployment detector (YOLO11m), tracker, and Whisper. |
| `backend/app/api/deps.py` | Dependency injection container providing repository and service instances to route handlers. |
| `backend/app/api/sessions.py` | REST endpoints for creating and querying football training sessions. |
| `backend/app/api/media.py` | REST endpoints for requesting pre-signed upload URLs and verifying storage upload completion. |
| `backend/app/api/jobs.py` | REST endpoints for job creation, status polling, result retrieval, and worker dispatch. |
| `backend/app/schemas/` | Pydantic v2 data contracts: `session.py`, `media.py`, `job.py`, `stages.py`, `dispatch.py`, `identity.py`, `calibration.py`, `kinematics.py`, `tactics.py`, `report.py`. |
| `backend/app/services/session_repository.py` | Session persistence adapter supporting Supabase Cloud and in-memory mock. |
| `backend/app/services/media_repository.py` | Media asset persistence, metadata verification, and signed upload token generation. |
| `backend/app/services/job_repository.py` | Analysis job state machine persistence and stage updates. |
| `backend/app/services/dispatch_repository.py` | Worker dispatch persistence (`worker_dispatches` table) supporting single-dispatch queries. |
| `backend/app/services/dispatch_service.py` | Orchestrates idempotent job dispatches and provider execution tracking. |
| `backend/app/services/modal_client.py` | Abstract provider adapter + `ProductionModalClient` + `InMemoryModalClient`. |
| `backend/app/pipeline/registry.py` | Methodology readiness registry enforcing the Phase 4B execution gate. |
| `backend/app/pipeline/geometry.py` | 3-tile generation (15% overlap) and bounding-box remapping logic. |
| `backend/app/pipeline/detection.py` | Global NMS deduplication and detection schema parsing. |
| `backend/app/pipeline/audio.py` | Audio extraction and transcription placeholder interfaces. |
| `backend/migrations/001_phase3_initial_schema.sql` | Production PostgreSQL DDL for `sessions`, `media_assets`, and `analysis_jobs`. |
| `backend/migrations/002_worker_dispatches.sql` | Production PostgreSQL DDL for `worker_dispatches` table and indices. |
| `backend/tests/` | 79 automated tests validating API, schemas, contracts, tile geometry, upload flows, and dispatch. |

---

### 2.3 Shared Contracts (`shared/`)
| File Path | Role & Importance |
| :--- | :--- |
| `shared/constants/modes.ts` | Canonical TypeScript enums for `ApplicationMode`, `CalibrationMode`, `AudioMode`, and `MethodologyId`. |
| `shared/constants/stages.ts` | Canonical TypeScript definitions for 5 `JobStatus` and 16 `AnalysisStage` values. |
| `shared/constants/confidence.ts` | Canonical TypeScript definitions for identity reliability statuses and metric confidence. |
| `shared/schemas/` | TypeScript interfaces strictly mirrored with Python backend Pydantic schemas. |

---

### 2.4 Modal Serverless Compute Scaffold (`modal_app/`)
| File Path | Role & Importance |
| :--- | :--- |
| `modal_app/app.py` | Primary `modal.App("football-tactical-analysis")` and Debian slim CPU container definition. |
| `modal_app/worker.py` | Serverless worker functions (`infrastructure_smoke` and `dispatch_placeholder`). |
| `modal_app/contracts.py` | Pydantic request and response schemas for Modal container communication. |
| `modal_app/README.md` | Worker architecture, planned pipeline stages, and compute constraints. |

---

### 2.5 Frontend Web Application (`frontend/tactical-ai-insights-main/`)
| File Path | Role & Importance |
| :--- | :--- |
| `package.json`, `tsconfig.json` | Frontend dependencies, scripts, and TypeScript compilation targets. |
| `vite.config.ts`, `tailwind.config.ts` | Vite bundling, styling system, and server configuration. |
| `src/routes/` | TanStack Router route definitions (`index.tsx`, `analysis.new.tsx`, `analysis.$jobId.tsx`, etc.). |
| `src/components/` | Modular UI components (media upload zone, tactical radar, event timeline, stage progress). |
| `src/hooks/` | React Query hooks interfacing with the FastAPI control plane. |

---

### 2.6 Golden Capability Demonstration (`golden/`)
| File Path | Role & Importance |
| :--- | :--- |
| `golden/manifest.json` | Immutable manifest defining oracle-assisted showcase use cases (C03, C04, C06). |
| `golden/README.md` | Scientific boundaries documenting manual verification of golden evidence. |

---

### 2.7 Verification & Operational Scripts (`scripts/`)
| File Path | Role & Importance |
| :--- | :--- |
| `scripts/verify_modal_smoke.py` | Live verification script testing remote Modal CPU execution and validating typed response. |
| `scripts/validate_scaffold.py` | Architectural test script asserting contract parity and schema alignment. |
| `scripts/copy_golden_fixtures.py` | Utility syncing frozen showcase fixtures without regenerating data. |

---

### 2.8 Architecture & Systems Documentation (`docs/`)
| File Path | Role & Importance |
| :--- | :--- |
| `docs/architecture.md` | Comprehensive system design, stage pipeline, and failure-handling strategies. |
| `docs/deployment_targets.md` | Target compute platforms (Vercel, FastAPI container, Supabase, Modal). |
