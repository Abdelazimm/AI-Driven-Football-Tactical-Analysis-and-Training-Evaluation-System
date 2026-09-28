# Pre-Audit Known Concerns & Reviewer Points of Inspection

> **Auditor Notice**: This document records known technical debt, potential architectural friction points, and specific areas where the independent reviewer should focus scrutiny. None of these items represent broken runtime behavior today, but they highlight areas for review prior to Phase 4B GPU/AI integration.

---

## 1. Pytest Deprecation Warnings on Modern Python (3.12+)

- **Observation**: Running the backend test suite under Python 3.13 produces 129 deprecation warnings across 79 tests.
- **Root Causes**:
  - `datetime.datetime.utcnow()`: Python 3.12+ deprecated `utcnow()` in favor of timezone-aware `datetime.now(timezone.utc)`. While updated in `scripts/verify_modal_smoke.py`, it still lingers in `backend/app/services/media_repository.py`, `backend/app/services/job_repository.py`, and certain Pydantic test fixtures.
  - `StarletteDeprecationWarning`: FastAPI and Starlette flag that `HTTP_422_UNPROCESSABLE_ENTITY` is deprecated in favor of `HTTP_422_UNPROCESSABLE_CONTENT`.
  - `StarletteDeprecationWarning`: Starlette's `TestClient` emits an informational notice regarding `httpx` vs `httpx2`.
- **Reviewer Question**: Should a clean sweep of timezone-aware UTC timestamps be scheduled across the entire backend before Phase 4B?

---

## 2. Worker Dispatch Lifecycle & Callback Architecture

- **Observation**: Currently, `AnalysisDispatchService.dispatch_job` records the dispatch in `worker_dispatches` (`CREATED` -> `SUBMITTED`) and invokes `ModalDispatchClient.submit_job`.
- **Current State**: Phase 4A verified the submission and persistence mechanics, but the remote execution currently runs as a placeholder because methodology executors are locked.
- **Reviewer Question for Phase 4B**: When real long-running GPU jobs execute on Modal (processing videos up to 300 seconds), how should the worker communicate intermediate stage updates (`DETECTING`, `TRACKING`, `KINEMATICS`) back to Supabase?
  - Option A: Worker writes directly to Supabase via service role key.
  - Option B: Worker invokes a signed FastAPI control-plane webhook endpoint.
  - Recommended Review: Assess the security and coupling implications of Option A vs Option B.

---

## 3. Supabase Row-Level Security (RLS) on Internal Tables

- **Observation**: Migration `002_worker_dispatches.sql` explicitly executed `ALTER TABLE worker_dispatches ENABLE ROW LEVEL SECURITY;` without adding permissive public policies.
- **Current Security**: Because no public policies exist, the Supabase anonymous key cannot select or mutate `worker_dispatches`. Only the backend using `SUPABASE_SERVICE_ROLE_KEY` can access it.
- **Reviewer Question**: Should migration `002` be hardened with an explicit deny-all policy for `anon` and `authenticated` roles to ensure defense-in-depth against accidental future permission grants?

---

## 4. Direct Signed Upload Expiration & Interrupted Uploads

- **Observation**: In `backend/app/api/media.py`, upload intent generates a pre-signed URL with a 3600-second expiration.
- **Current State**: The browser uploads directly to the Supabase storage bucket and then calls `POST /api/v1/media/{asset_id}/verify-upload` for authoritative confirmation.
- **Reviewer Question**: If a user's upload is stalled or interrupted, how gracefully does the frontend client catch the HTTP 403 / signature expiration? Ensure the frontend UI supports automatic refresh of expired upload tokens without losing the selected session form state.

---

## 5. Modal Container Execution Timeouts Sizing

- **Observation**: In `modal_app/worker.py`, `infrastructure_smoke` and `dispatch_placeholder` specify `timeout=60` seconds and `memory=512`.
- **Current State**: This was purposefully lightweight for CPU infrastructure smoke tests.
- **Reviewer Question for Phase 4B**: When Stage 4B YOLO11m, BoT-SORT, Faster-Whisper, and kinematic calculations execute on 300-second 4K video clips, the execution timeout must be sized realistically (e.g. 600–900s) and container memory increased to at least 8–16 GB.

---

## 6. Pitch Landmark Validation in Custom Homography Mode

- **Observation**: When `calibration_mode` is `CUSTOM_PITCH_CALIBRATION`, the user specifies 4 pitch landmarks.
- **Current State**: Backend schemas enforce 4-point coordinate inputs.
- **Reviewer Question**: Does the geometry validation logic in `backend/app/pipeline/geometry.py` sufficiently reject degenerate quadrilaterals (e.g., self-intersecting, collinear, or concave polygons) before calculating the homography matrix to prevent mathematical singularities?

---

## 7. Synchronization with Codex Methodology Track

- **Observation**: All three methodologies (`METHOD_1_YOLO11_BOTSORT`, `METHOD_2_RFDETR_GTATRACK`, `METHOD_3_YOLO26_SRITRACK`) return `NOT_READY_FOR_EXECUTION` from `MethodologyExecutorRegistry`.
- **Current Invariant**: The Antigravity track enforces that partial or single-method deployment is disallowed until all three methodologies have completed formal evaluation in Codex.
- **Reviewer Question**: Verify that this gate cannot be bypassed by client request parameters or query flags.
