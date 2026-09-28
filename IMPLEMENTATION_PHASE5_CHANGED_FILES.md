# IMPLEMENTATION_PHASE5_CHANGED_FILES.md
# Phase 5 Implementation — Changed Files Inventory

**Phase:** CM3070 Final Project — Implementation Phase 5 (Production Orchestration, Modal Packaging, Persistence & Product Pipeline Wiring)  
**Date:** 2026-09-27  
**Status:** `IMPLEMENTATION_PHASE5_FINAL_VERIFICATION_PASS` — genuine bounded Modal/Supabase lifecycle passed. The earlier inventory below records prior work and remains historically useful.

## Remote closure changes (Codex, 2026-09-27)

- `backend/app/services/job_repository.py`: resolves AUTO before persisted job creation and stores canonical results plus report/manifest artifacts in private Supabase Storage, with readback and immutable retry behavior. Removes the nonexistent `analysis_results` table dependency.
- `backend/app/services/dispatch_service.py`, `backend/app/services/modal_client.py`: production M2 readiness, validated private media references, bounded source offsets, real Modal worker dispatch, callback URL, monotonic lifecycle, and result-before-completion gate.
- `backend/app/schemas/job.py`, `backend/app/schemas/dispatch.py`: AUTO input and serialized remote worker contract.
- `shared/schemas/job.ts`: frontend request type accepts explicit AUTO, and job response type includes persisted audio mode.
- `backend/app/pipeline/orchestrator.py`: video source offset aligns bounded Vision frames to source-session time.
- `backend/app/runners/m2_runner.py`, `backend/app/runners/vendor/m2/**`: configurable checkpoint root and byte-identical packaged frozen tracking source; no runtime research-drive dependency.
- `modal_app/app.py`, `modal_app/worker.py`, `modal_app/entrypoint.py`, `modal_app/callback_api.py`: complete Python 3.11 GPU image, model volume, import/hash preflight, private media worker, persistence, authenticated callback-only endpoint, and deployment registration.
- `backend/tests/conftest.py`, `backend/tests/test_hardening_pack1.py`, `backend/tests/test_phase4a_dispatch.py`, `backend/tests/test_phase5_remote_closure.py`: local reference checkpoint setup and regression coverage for result gating, production dispatch, AUTO resolution, hash checks, callback serialization, and Storage roundtrip.
- `IMPLEMENTATION_PHASE5_REMOTE_CLOSURE.md`, `IMPLEMENTATION_PHASE5_REAL_CLOUD_SMOKE.json`, `IMPLEMENTATION_PHASE5_FINAL_VERIFICATION.md`, `IMPLEMENTATION_PHASE5_REPORT.md`, `IMPLEMENTATION_PHASE5_TEST_RESULTS.json`: verified remote evidence and final disposition.

The exact frozen detector and ReID weights were copied read only from the research reference into the Modal volume `football-model-checkpoints`. The research artifacts themselves were not changed. One bounded video excerpt and its audio were uploaded to private Supabase Storage for the smoke.

## Interrupted recovery changes (Codex, 2026-09-27)

- `backend/app/pipeline/orchestrator.py`: retained the earlier source-offset and formal-identity corrections; added offset validity/missing bounded-audio guards, checked ASR absolute-time contract, forwarded explicit deterministic fallback, and removed invented fps/resolution/duration fallback metadata.
- `backend/app/pipeline/fusion.py`: records source offset and actual Vision timestamps in evidence provenance; rejects unavailable fps instead of applying a research constant.
- `backend/app/pipeline/reporting.py`: honors the per-job deterministic fallback request.
- `backend/app/services/llm_report_service.py`: removed the read-only research drive runtime prompt fallback; packaged prompt remains SHA-verified.
- `modal_app/worker.py`: the earlier recovery forwarded `audio_source_offset_s`; the subsequent remote closure above completed and verified its full lifecycle.
- `backend/tests/test_production_orchestration.py`: asserts real bounded C04 overlap and positive Fusion observations, tests 120-second LLM default and 45-second explicit override, and tests bounded-offset fail-closed behavior.
- `IMPLEMENTATION_PHASE5_INTERRUPTED_RECOVERY.md`, `IMPLEMENTATION_PHASE5_FINAL_VERIFICATION.md`, `IMPLEMENTATION_PHASE5_REPORT.md`, `IMPLEMENTATION_PHASE5_TEST_RESULTS.json`: recovery and corrected verification records.
- `IMPLEMENTATION_PHASE5_LOCAL_ORCHESTRATOR_SMOKE.json`: added authenticated infrastructure blocker evidence.
- `IMPLEMENTATION_PHASE5_INVALIDATED_CLOUD_CLAIM.json`: invalidated old cloud-success label while preserving its original local record.
- `IMPLEMENTATION_PHASE5_PRIOR_REPORT_UNVERIFIED.md`, `IMPLEMENTATION_PHASE5_PRIOR_TEST_RESULTS_UNVERIFIED.json`: preserved superseded pre-recovery reports.

The workspace has no Git metadata, so exact before/after attribution for the interrupted agent cannot be reconstructed. The inventory below describes files present before this recovery; it is not a Git diff.

---

## 1. Backend Core & Configuration

### `backend/app/core/model_manifest.yaml`
- **Role:** Authoritative configuration manifest for production pipelines.
- **Modifications:**
  - Removed stale active `qwen3:8b` reference; locked primary reporting to `llama3.1:8b` (digest: `46e0c10c...`, prompt SHA: `ab95a835...`).
  - Added cryptographic SHA-256 digests for all 3 vision methodologies (M1 YOLO11m + BoT-SORT / PRTReID, M2 RF-DETR + GTA-Track / Deep-EIoU, M3 YOLO26 + SRITrack / DINOv3).
  - Specified faster-whisper `base.en` CPU int8 with 8 threads.
  - Specified research homography SHA-256 (`d0e9680fdcdf...`) with camera-specific geometry constraint.
  - Configured 360.0s maximum duration policy.

---

## 2. Pipeline Orchestration & Execution

### `backend/app/pipeline/orchestrator.py`
- **Role:** Unified production orchestrator (`UnifiedAnalysisOrchestrator`, `execute_analysis_job`).
- **Modifications:**
  - Composes all 10 verified lifecycle stages into a single typed execution entrypoint:
    1. Probe media metadata via `MediaProbeService` / container probing (dynamic duration, fps, resolution).
    2. Enforce 360-second duration gate (`VideoDurationExceededError`).
    3. Methodology resolution (`AUTO -> M2`, manual `M1->M1`, `M2->M2`, `M3->M3`, fail-closed).
    4. Computer vision execution via registered production runners (`registry.get_executor()`).
    5. Persistent identity safety gate evaluation (formal `FAIL_UNSAFE_MERGE` under `FORMAL_DENSE_GT`; runtime `RUNTIME_HEURISTIC_ONLY`; player-level analytics withheld).
    6. Audio extraction and speech recognition via faster-whisper (`AudioPipeline`).
    7. Multimodal tactical fusion (`MultimodalFusionEngine`) correlating video frames and coach commands.
    8. Structured multimodal evidence validation (`EvidencePipeline`, `StructuredEvidencePayload`).
    9. Grounded coaching report generation (`ReportingPipeline`) with Patch 001 validation and deterministic fallback.
    10. Dynamic `JobExecutionManifest` generation and canonical `AnalysisResult` assembly with job-scoped storage artifact paths.

---

## 3. Schemas & Contract Synchronization

### `backend/app/schemas/result.py`
- **Role:** Backend canonical analysis result schema.
- **Modifications:**
  - Added optional `execution_manifest: Optional[JobExecutionManifest]`.
  - Added optional `structured_evidence: Optional[Dict[str, Any]]`.
  - Added `from typing import Any` and called `AnalysisResult.model_rebuild()`.

### `shared/schemas/result.ts`
- **Role:** Shared TypeScript interface for analysis results.
- **Modifications:**
  - Synchronized `execution_manifest?: any | null` and `structured_evidence?: any | null` to match backend schema.

### `backend/app/schemas/instruction.py`
- **Role:** Structured tactical instruction event model.
- **Modifications:**
  - Added optional `action: Optional[str] = Field(None, description="Matched tactical keyword or action phrase")`.

### `shared/schemas/instruction.ts`
- **Role:** Shared TypeScript interface for tactical instruction events.
- **Modifications:**
  - Added `action?: string | null`.

### `backend/app/schemas/artifact.py`
- **Role:** Storage artifact reference model.
- **Modifications:**
  - Added `"RESULT_JSON"` and `"EXECUTION_MANIFEST"` to `kind` literal union.

### `shared/schemas/artifact.ts`
- **Role:** Shared TypeScript interface for storage artifacts.
- **Modifications:**
  - Added `'RESULT_JSON' | 'EXECUTION_MANIFEST'` to `kind` union.

---

## 4. Repositories & Persistence

### `backend/app/services/job_repository.py`
- **Role:** Analysis job persistence contract and implementations.
- **Modifications:**
  - Added abstract `store_result(result: AnalysisResult) -> None` to `AnalysisJobRepository`.
  - Implemented `store_result` in `InMemoryJobRepository` (idempotent result storage and retrieval).
  - Implemented `store_result` in `SupabaseAnalysisJobRepository` (persists canonical JSON to Supabase Storage `analysis-outputs/jobs/{job_id}/results/result.json` and updates job status in database).

---

## 5. Modal Cloud Packaging & Workers

### `modal_app/app.py`
- **Role:** Modal serverless application and container image definition.
- **Modifications:**
  - Configured Debian 12 / Python 3.11 container with FFmpeg, Git, libgl1-mesa-glx, PyTorch 2.5.1+cu124, Ultralytics, rfdetr, faster-whisper, and supabase.
  - Defined volume mount `/data/models` for immutable cached checkpoints.

### `modal_app/worker.py`
- **Role:** Modal serverless execution function.
- **Modifications:**
  - Upgraded from placeholder smoke to real `execute_analysis_worker` orchestrating authenticated job acquisition, media download, production orchestrator execution, stage progress callbacks with HMAC authentication, and artifact persistence to Supabase Storage.

### `modal_app/entrypoint.py`
- **Role:** Standalone CLI entrypoint for container debugging and worker invocation.

---

## 6. Test Suite & Verification

### `backend/tests/test_production_orchestration.py`
- **Role:** Dedicated Phase 5 product orchestration and contract test suite.
- **Prior inventory coverage:** 23 named tests before interrupted recovery; current file also includes formal identity, timeout, source-offset, and real-overlap assertions. Current full-suite count is recorded in `IMPLEMENTATION_PHASE5_TEST_RESULTS.json`.
  1. Strict canonical stage ordering.
  2. `AUTO` resolution strictly to `METHOD_2_RFDETR_GTATRACK`.
  3. Strict prohibition of methodology fallback (fails closed).
  4. ASR failure fail-soft to `COMPLETED_WITH_LIMITATIONS`.
  5. Zero tactical events produces valid completed result.
  6. LLM timeout engages deterministic fallback.
  7. Patch 001 validator rejection engages deterministic fallback.
  8. Identity safety gate active withholds player-level metrics.
  9. Dynamic execution manifest uses probed container metadata.
  10. 360-second video duration limit enforcement.
  11. Result persistence idempotency.
  12. Dispatch idempotency (`uq_active_worker_dispatch_per_job`).
  13. Worker progress callback ownership and validation.
  14. Job-scoped deterministic artifact storage paths.
  15. Zero hardcoded local development paths in production orchestrator.
  16. Zero secret tokens or credentials committed to config or manifests.
  17. Stale `qwen3:8b` reference removed from active manifest.
  18. Exact frozen Llama 3.1 8B digest retained.
  19. Exact frozen coaching report prompt SHA-256 retained.
  20. Exact frozen Vision checkpoint SHA-256 hashes retained.
  21. Real bounded orchestrator smoke test (real 4K video + M2 RF-DETR + real C04 audio + Faster-Whisper + Fusion + Deterministic Report).
  22. Persisted `AnalysisResult` JSON serialization/deserialization roundtrip.
  23. Frontend result schema contract alignment.
