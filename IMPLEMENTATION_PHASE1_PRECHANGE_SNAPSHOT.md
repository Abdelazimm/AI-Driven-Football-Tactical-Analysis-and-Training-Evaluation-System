# Implementation Phase 1 — Pre-Change Snapshot

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: Implementation Phase 1 — Core Contracts, Vision Adapters & Safety Layer  
**Date**: 2026-09-26  
**Status**: `PRE_CHANGE_SNAPSHOT_RECORDED`  
**P0 Contract Freeze Version**: `REV2A` (`P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md`, `P0_REV2A_VISION_PROVENANCE_CORRECTION.md`)  

---

## 1. Workspace & Git Environment State

- **Primary Product Workspace**: `D:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System`
- **Git Repository Status**: Not a git repository root (`.git` directory not present in workspace or immediate parent).
- **Untracked / Audit Deliverables Present in Root**:
  - `P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md`
  - `P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.json`
  - `P0_CONTRACT_TEST_PLAN_REV2A.md`
  - `P0_IMPLEMENTATION_FILE_MAP_REV2A.md`
  - `P0_REV2A_VISION_PROVENANCE_CORRECTION.md`
  - `P0_REV2A_CHANGELOG.md`
  - Historical audit and contract artifacts (`P0_REV1_*`, `P0_REV2_*`, `FINAL_SYSTEM_REVALIDATION_*`, `CODEX_*`)

---

## 2. Existing Product Regression Test Results

Executed baseline test command:
```bash
python -m pytest backend/tests -v
```
**Result**:
- **150 passed in 1.33s** (100% pass rate).
- Test Suites:
  - `backend/tests/test_api.py` (API router, sessions, jobs endpoints)
  - `backend/tests/test_contract_alignment.py` (contract definitions)
  - `backend/tests/test_detection_pipeline.py` (tiling functions, global NMS)
  - `backend/tests/test_golden_fixtures.py` (showcase fixtures C03, C04, C06 readbacks)
  - `backend/tests/test_hardening_pack1.py` (storage, auth, job state machines)
  - `backend/tests/test_hardening_pack2.py` (media validation service, storage error semantics, upload flows)
  - `backend/tests/test_phase3_storage_and_upload.py` (upload intents, storage services)
  - `backend/tests/test_phase4a_dispatch.py` (dispatch repository, worker payloads, methodology gates)
  - `backend/tests/test_schemas.py` (Pydantic models, identity fail-closed withholding, video metadata)

---

## 3. Affected Modules & Existing Stubs

| Module Path | Pre-Change Status | Action in Phase 1 |
| :--- | :--- | :--- |
| `backend/app/schemas/canonical_vision.py` | Does not exist | **NEW_REQUIRED**: Implement framewise Vision contract (`SessionVisionResult`, `FrameVisionResult`, `TrackObservation`, `BoundingBox`). |
| `backend/app/schemas/manifest.py` | Does not exist | **NEW_REQUIRED**: Implement dynamic `JobExecutionManifest` schema. |
| `backend/app/adapters/common_adapter.py` | Does not exist | **NEW_REQUIRED**: Implement shared coordinate projections, clipping, empty-frame generator. |
| `backend/app/adapters/m1_adapter.py` | Does not exist | **NEW_REQUIRED**: Implement M1 adapter consuming native $1920 \times 1080$ outputs and projecting to source space. |
| `backend/app/adapters/m2_adapter.py` | Does not exist | **NEW_REQUIRED**: Implement M2 adapter consuming native $1920 \times 1080$ outputs and projecting to source space. |
| `backend/app/adapters/m3_adapter.py` | Does not exist | **NEW_REQUIRED**: Implement M3 adapter consuming native $1920 \times 1080$ outputs and projecting to source space. |
| `backend/app/services/identity_safety_service.py` | Does not exist | **NEW_REQUIRED**: Implement formal vs runtime identity separation and fail-closed withholding. |
| `backend/app/pipeline/identity.py` | Placeholder stub raising `NotImplementedError` | **REPLACE_STUB**: Adapt to dispatch to `IdentitySafetyService`. |
| `backend/app/services/calibration_service.py` | Does not exist | **NEW_REQUIRED**: Implement Calibration Permission Matrix and iPhone 16 research homography. |
| `backend/app/pipeline/calibration.py` | Placeholder stub raising `NotImplementedError` | **REPLACE_STUB**: Adapt to dispatch to `CalibrationService`. |
| `backend/app/services/kinematics_service.py` | Does not exist | **NEW_REQUIRED**: Implement 7-point median smoothing, $\Delta t > 0.50\text{s}$ continuity reset, $> 36\text{ km/h}$ outlier rejection. |
| `backend/app/pipeline/kinematics.py` | Placeholder stub raising `NotImplementedError` | **REPLACE_STUB**: Adapt to dispatch to `KinematicsService`. |
| `backend/app/core/config.py` | `MAX_VIDEO_DURATION_SECONDS = 300.0` | **EXISTING_ADAPT**: Update default ceiling to `360.0`. |
| `backend/app/schemas/video.py` | `duration_seconds: le=300.0` | **EXISTING_ADAPT**: Update constraint to `le=360.0`. |
| `backend/app/services/media_validation_service.py` | Uses `settings.MAX_VIDEO_DURATION_SECONDS` | **EXISTING_ADAPT**: Aligns with 360.0s ceiling. |

---

## 4. Current Registry & Execution Readiness State

- `backend/app/pipeline/registry.py`:
  - `MethodologyExecutorRegistry` maintains empty `_executors = {}`.
  - `is_ready_for_execution()` returns `False` for all methodologies.
  - Readiness gate: **STRICTLY FAIL-CLOSED** (`METHODOLOGY_EXECUTOR_NOT_READY`).
  - **Invariance Rule**: Registry must remain fail-closed in Phase 1. Adapters are translation interfaces and do NOT represent production execution readiness.

---

## 5. Media Duration Policy Baseline

- Current `Settings.MAX_VIDEO_DURATION_SECONDS = 300.0`.
- Current `VideoMetadata.duration_seconds` constraint: `le=300.0`.
- Approved Target Policy: Harmonize to `360.0` seconds to accept the $339.99\text{s}$ research match video while rejecting $> 360.0\text{s}$.
