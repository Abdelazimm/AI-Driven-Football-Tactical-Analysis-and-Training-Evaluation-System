# CM3070 P0 Contract Test Plan

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze  
**Document**: Pre-Implementation Contract Test Specification  
**Status**: `P0_CONTRACT_FREEZE_READY_FOR_REVIEW`

This document defines the exact 20 contract test suites that must be implemented to validate all production contracts before end-to-end AI execution begins.

---

## Summary of Contract Test Suites

| # | Test Suite Identifier | Target Contract / Subsystem | Invariant Tested |
| :--- | :--- | :--- | :--- |
| **01** | `test_m1_adapter_to_canonical_vision_result` | M1 Adapter (`M1Yolo11BotSortAdapter`) | Converts tiled detections + BoT-SORT tracks to canonical `[x1, y1, x2, y2]` source pixels. |
| **02** | `test_m2_adapter_to_canonical_vision_result` | M2 Adapter (`M2RfDetrGtaTrackAdapter`) | Converts RF-DETR set predictions + Deep-EIoU tracklets + GTA-Track to canonical result. |
| **03** | `test_m3_adapter_to_canonical_vision_result` | M3 Adapter (`M3Yolo26SriTrackAdapter`) | Converts YOLO26 + SRITrack + DINOv3 to canonical result with correct scaling. |
| **04** | `test_bbox_and_timebase_normalization` | Common Vision Contract | Enforces $[x_1, y_1, x_2, y_2]$ ordering, $[0..1]$ normalized box, and $t = \text{frame} / \text{fps}$. |
| **05** | `test_empty_frame_handling` | Common Vision Contract | Zero-detection frames emit `is_empty_frame=True` without crashing the pipeline. |
| **06** | `test_fail_unsafe_merge_withholding` | Identity Safety Gate | `FAIL_UNSAFE_MERGE` forces `player_level_analysis_allowed=False` and withholds metrics. |
| **07** | `test_no_calibration_withholds_metric_units` | Calibration Contract | `NO_METRIC_CALIBRATION` suppresses metres, km/h, and m/s from all output fields. |
| **08** | `test_asr_explicit_failure_no_historical_fallback` | ASR Contract | Audio failure emits `ASRFailure`; NEVER substitutes historical transcript. |
| **09** | `test_vision_only_partial_completion_on_asr_failure` | Orchestrator & Job Lifecycle | When ASR fails, job completes as `COMPLETED_WITH_LIMITATIONS` with Vision metrics intact. |
| **10** | `test_fusion_consumes_real_evidence_only` | Multimodal Fusion Engine | Fusion output contains NO hardcoded `PLAYER_01`, 339.87s, 2500 rows, or 4.5m / 8.2km/h. |
| **11** | `test_fusion_forbids_player_scope_under_unsafe_identity` | Fusion Contract | Evidence items cannot have `scope=PLAYER` when identity gate has failed. |
| **12** | `test_oracle_mode_permits_bounded_player_evidence` | Oracle Showcase Contract | `VALIDATED_SHOWCASE` with `HUMAN_VERIFIED` permits verified player-level evidence. |
| **13** | `test_llama_model_digest_and_prompt_hash_enforcement` | LLM Reporting Contract | Strictly asserts digest `46e0c10c...` and prompt SHA-256 `ab95a835...`. |
| **14** | `test_grounding_validator_rejection_triggers_safe_fallback` | LLM Grounding Validator | Patch 001 violation automatically engages `DETERMINISTIC_FALLBACK`. |
| **15** | `test_job_manifest_provenance_completeness` | Provenance & Artifacts | Output manifest contains all model hashes, media hashes, and execution metadata. |
| **16** | `test_auto_methodology_resolves_to_m2` | Product Execution Policy | `AUTO` request resolves deterministically to `METHOD_2_RFDETR_GTATRACK`. |
| **17** | `test_manual_methodology_selection_executes_isolated_pipeline`| Product Execution Policy | Selecting M1, M2, or M3 runs its respective pipeline with zero cross-method component mixing. |
| **18** | `test_media_duration_policy_accepts_340s_session` | Media Validation & Ingest | Harmonized 360.0s ceiling accepts the 339.99s research match video without truncation. |
| **19** | `test_job_dispatch_idempotency_and_retry` | Orchestration & Dispatch | Unique index prevents duplicate dispatches; failed worker retries recover from checkpoint. |
| **20** | `test_analysis_result_transparent_limitation_rendering` | Result Schema & UI Contract | Frontend payload contains explicit limitation warnings and proper status badges. |

---

## Detailed Test Specifications

### Test 01: M1 Adapter to Canonical VisionResult
- **Target Module**: `backend/app/adapters/m1_adapter.py`
- **Fixture**: Synthetic YOLO11m tiled output (3 tiles of $1280 \times 1280$, overlap 15%) on $3840 \times 2160$ frame with BoT-SORT `tlwh` track IDs.
- **Invariants Asserted**:
  - Tile horizontal offsets correctly remapped into global image space.
  - Scale factor $2.0$ applied correctly ($1920 \times 1080 \rightarrow 3840 \times 2160$).
  - Native `tlwh` $[100, 200, 50, 100]$ transformed to canonical $[200.0, 400.0, 300.0, 600.0]$.
  - Provenance records `M1_FORMAL_003` checkpoint hash and BoT-SORT tracker configuration.

### Test 02: M2 Adapter to Canonical VisionResult
- **Target Module**: `backend/app/adapters/m2_adapter.py`
- **Fixture**: Native RF-DETR Hungarian set predictions (boxes, class 0, sigmoid scores) + Deep-EIoU tracklets + GTA-Track global identity matrix.
- **Invariants Asserted**:
  - No external NMS applied; transformer scores directly filtered by floor $0.40$.
  - Native `last_tlwh` transformed to canonical $[x_1, y_1, x_2, y_2]$.
  - Deep-EIoU sub-tracklet ID preserved in `tracklet_id`.
  - GTA-Track final trajectory ID mapped to `track_id`.

### Test 03: M3 Adapter to Canonical VisionResult
- **Target Module**: `backend/app/adapters/m3_adapter.py`
- **Fixture**: YOLO26 end-to-end detections ($1280 \times 720$) + SRITrack state + DINOv3 feature vectors.
- **Invariants Asserted**:
  - Test-time confidence floor $0.25$ verified.
  - Scaling factors $(W / 1280, H / 720)$ correctly applied to canonical coordinates.
  - SRITrack spatial-reliability re-entry ID mapped to canonical `track_id`.

### Test 04: Bounding Box and Timebase Normalization
- **Target Module**: `backend/app/schemas/canonical_vision.py`
- **Fixture**: Framewise observations with varying resolutions ($3840 \times 2160$, $1920 \times 1080$) and frame rates ($59.972$, $30.0$, $25.0$).
- **Invariants Asserted**:
  - $x_1 < x_2$ and $y_1 < y_2$ strictly enforced.
  - Normalized coordinates satisfy $0.0 \le \text{norm\_ymin} \le \text{norm\_ymax} \le 1.0$.
  - Timestamp calculated exactly as $\text{timestamp\_s} = \text{frame\_index} / \text{source\_fps}$.
  - Any box violating frame boundaries is clamped or rejected with validation error.

### Test 05: Empty Frame Handling
- **Target Module**: `backend/app/adapters/common_adapter.py`
- **Fixture**: Sequence of 100 frames where frames 40–45 contain 0 player detections.
- **Invariants Asserted**:
  - Frames 40–45 produce valid `FrameVisionResult` with `is_empty_frame = True`.
  - `observations = []` handled gracefully without `IndexError` or pipeline termination.
  - Downstream kinematics resets velocity tracking across the gap.

### Test 06: Fail Unsafe Merge Withholding
- **Target Module**: `backend/app/services/identity_safety_service.py`
- **Fixture**: Evaluation result containing 2 unsafe merges (swapped track IDs between opposing players).
- **Invariants Asserted**:
  - `identity_status` evaluates to `FAIL_UNSAFE_MERGE`.
  - `player_level_analysis_allowed` is `False`.
  - `withholding_reason` is non-empty and cites unsafe merge count.
  - Accumulated player metrics (`distance_covered_m`, `average_speed_kmh`) are `null`.

### Test 07: No-Calibration Metric Suppression
- **Target Module**: `backend/app/services/kinematics_service.py`
- **Fixture**: Valid tracking observations under `CalibrationMode.NO_METRIC_CALIBRATION`.
- **Invariants Asserted**:
  - Calculated movement metrics have unit `"px"` or `"px/s"`, never `"m"` or `"km/h"`.
  - Physical distance displays `"Uncalibrated Pitch"`.
  - No homography matrix is applied; raw pixel velocities are emitted.

### Test 08: ASR Explicit Failure with No Historical Fallback
- **Target Module**: `backend/app/services/asr_service.py`
- **Fixture**: Video file with corrupt audio track or missing AAC stream.
- **Invariants Asserted**:
  - Service emits `AudioProcessingResult(status="FAILED", error="AUDIO_EXTRACTION_FAILED")`.
  - Zero transcript segments and zero coaching events emitted.
  - System does NOT attempt to read `g:/My Drive/.../match_session_transcript.json`.

### Test 09: Vision-Only Partial Completion on ASR Failure
- **Target Module**: `backend/app/orchestrator/analysis_orchestrator.py`
- **Fixture**: End-to-end execution where Vision succeeds but ASR fails.
- **Invariants Asserted**:
  - Pipeline transitions through `TRANSCRIBING` $\rightarrow$ skips `INSTRUCTION_PARSING` $\rightarrow$ executes `FUSION` with `None` ASR.
  - Overall `JobStatus` finalizes as `COMPLETED_WITH_LIMITATIONS`.
  - `limitations` includes `"Coaching audio transcription failed..."`.
  - Vision tracking and spatial heatmaps are preserved and persisted.

### Test 10: Fusion Consumes Real Evidence Only
- **Target Module**: `backend/app/pipeline/fusion.py`
- **Fixture**: Real ASR events and Vision tracks from 60-second test clip.
- **Invariants Asserted**:
  - Output contains zero occurrences of literal string `"PLAYER_01"`.
  - Session duration is derived from video probe ($60.0 \text{ s}$), NOT $339.87 \text{ s}$.
  - Observation row count matches actual frame count, NOT $2500$.
  - Metric displacement and speed are calculated from real coordinates, NOT $4.5 \text{ m}$ / $8.2 \text{ km/h}$.

### Test 11: Fusion Forbids Player Scope Under Unsafe Identity
- **Target Module**: `backend/app/pipeline/fusion.py`
- **Fixture**: Multimodal fusion execution with `IdentityStatus.FAIL_UNSAFE_MERGE`.
- **Invariants Asserted**:
  - All emitted `EvidenceItem` objects have `scope` in `[TEAM, SPATIAL, EVENT, ANONYMOUS_TRACK]`.
  - Zero `EvidenceItem` objects have `scope = PLAYER`.
  - All coaching events have `target_resolution_status = "UNRESOLVED_TARGET"`.

### Test 12: Oracle Mode Permits Bounded Player Evidence
- **Target Module**: `backend/app/pipeline/fusion.py`
- **Fixture**: Execution with `ApplicationMode.VALIDATED_SHOWCASE` and pre-verified showcase case `C06`.
- **Invariants Asserted**:
  - `identity_source` records `"HUMAN_VERIFIED / ORACLE"`.
  - Emitted evidence includes `scope = PLAYER` with pseudonym `"Black01"`.
  - Verified showcase metrics ($18.4 \text{ km/h}$ max speed, $1.15 \text{ s}$ reaction latency) preserved unchanged.

### Test 13: Llama Model Digest and Prompt Hash Enforcement
- **Target Module**: `backend/app/services/llm_report_service.py`
- **Fixture**: Client invocation verifying Ollama configuration.
- **Invariants Asserted**:
  - Service queries `/api/show` and asserts digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`.
  - System prompt file SHA-256 equals `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`.
  - Mismatched digest or modified prompt raises fatal configuration error before execution.

### Test 14: Grounding Validator Rejection Triggers Safe Fallback
- **Target Module**: `backend/app/services/llm_report_service.py`
- **Fixture**: LLM response containing hallucinated metric ($25.4 \text{ km/h}$) not present in `StructuredEvidence`.
- **Invariants Asserted**:
  - `LLM_GROUNDING_VALIDATOR_PATCH_001` rejects response on Gate 3 (Metric Grounding).
  - Service catches validation error and switches to `ReportStatus.DETERMINISTIC_FALLBACK`.
  - Output report is generated from deterministic markdown template.
  - Pipeline completes without exception.

### Test 15: Artifact Provenance Completeness
- **Target Module**: `backend/app/services/artifact_service.py`
- **Fixture**: Completed analysis job execution.
- **Invariants Asserted**:
  - `manifest.json` contains valid SHA-256 for all produced artifacts.
  - Checkpoint hashes for detector, tracker, ASR, and LLM are present.
  - Manifest is serialized and persisted to Supabase storage `analysis-artifacts`.

### Test 16: AUTO Methodology Resolves to M2
- **Target Module**: `backend/app/api/jobs.py`
- **Fixture**: POST `/api/v1/jobs` request with `methodology_id = "AUTO"`.
- **Invariants Asserted**:
  - Stored job record has `methodology_id = "METHOD_2_RFDETR_GTATRACK"`.
  - Response payload confirms M2 Global Association pipeline configured.

### Test 17: Manual Methodology Selection Runs Isolated Pipeline
- **Target Module**: `backend/app/pipeline/registry.py`
- **Fixture**: Jobs submitted with explicit `METHOD_1_YOLO11_BOTSORT`, `METHOD_2_RFDETR_GTATRACK`, `METHOD_3_YOLO26_SRITRACK`.
- **Invariants Asserted**:
  - M1 job loads ONLY YOLO11 + BoT-SORT; does not import RF-DETR or SRITrack.
  - M2 job loads ONLY RF-DETR + GTA-Track; does not import YOLO11 or BoT-SORT.
  - M3 job loads ONLY YOLO26 + SRITrack; does not import RF-DETR or BoT-SORT.

### Test 18: Media Duration Policy Accepts 340s Match Session
- **Target Module**: `backend/app/services/media_validation_service.py`
- **Fixture**: Synthetic media asset probe with `duration_seconds = 339.99` and `fps = 59.972`.
- **Invariants Asserted**:
  - Probe passes duration validation ($339.99 \le 360.0$).
  - Status transitions to `UploadStatus.VALIDATED`.
  - Video with duration $360.1 \text{ s}$ is rejected with `DURATION_EXCEEDS_MAXIMUM`.

### Test 19: Job Dispatch Idempotency and Retry
- **Target Module**: `backend/app/services/job_dispatch_service.py`
- **Fixture**: Concurrent dispatch requests for the same job ID.
- **Invariants Asserted**:
  - Second concurrent dispatch is rejected by database constraint `uq_active_worker_dispatch_per_job`.
  - Interrupted job resumes from last completed stage checkpoint.

### Test 20: AnalysisResult Transparent Limitation Rendering
- **Target Module**: `backend/app/schemas/result.py` & Frontend Contract
- **Fixture**: Finalized result under `FAIL_UNSAFE_MERGE` and `NO_METRIC_CALIBRATION`.
- **Invariants Asserted**:
  - `job_status` is `COMPLETED_WITH_LIMITATIONS`.
  - `limitations` contains at least 2 entries (`IDENTITY` and `CALIBRATION`).
  - Serialized JSON matches frontend TypeScript `AnalysisResult` interface without missing keys.
