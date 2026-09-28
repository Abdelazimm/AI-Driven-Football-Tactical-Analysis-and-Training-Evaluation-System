# P0 Contract Freeze Revision 2A (REV2A) Changelog

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 2A Final Consistency Hotfix)  
**Date**: 2026-09-26  
**Status**: `P0_CONTRACT_FREEZE_REV2A_READY_FOR_APPROVAL`

This changelog records the six specific consistency hotfixes applied to resolve all remaining internal contradictions between specification documents, contract test plans, and implementation file maps. No production pipeline code was modified, no research artifacts were altered, and no scientific evaluations were rerun.

---

## Master Consistency Hotfix Table

| # | Hotfix Focus Area | REV2 State / Inconsistency | REV2A Authoritative Resolution | Target Files / Contracts | Architectural Impact |
| :- | :--- | :--- | :--- | :--- | :--- |
| **01** | **M1 Baseline Parameters in Tests** | Tests referenced historical Stage 4B values (`detector_operating_point = 0.20`, `global_nms_iou = 0.70`). | Enforced exact frozen M1 two-tier thresholds: `tracker_input_candidate_confidence_floor = 0.05`, `standalone_qualification_confidence = 0.25`, `tile_nms_iou = 0.70`, `global_nms_iou = 0.50`. Tracker: `track_high_thresh = 0.35`, `track_low_thresh = 0.10`, `new_track_thresh = 0.35`, `track_buffer = 120`, `match_thresh = 0.85`, `gmc_method = none`, `proximity_thresh = 0.15`, `appearance_thresh = 0.88`, `with_reid = true`, `fuse_score = true`. | `backend/app/adapters/m1_adapter.py`, `P0_CONTRACT_TEST_PLAN_REV2A.md` (Test 01) | Eliminates Stage 4B leakage into frozen M1 test specifications; aligns tests with frozen baseline. |
| **02** | **Adapter Coordinate-Space Semantics & Anti-Double-Scaling** | Ambiguity regarding whether adapters should rescale from model tensor dimensions ($704 \times 704$ for M2, $1280 \times 1280$ for M3). | Established that runner outputs for M1, M2, and M3 are native in `VISION_WORKING_SPACE` ($1920 \times 1080$). Ultralytics unletterboxes M1 tiles to tile pixels before horizontal stitching; M2 RF-DETR postprocesses to $1920 \times 1080$; M3 SRITrack runs directly at $1920 \times 1080$. Production adapters MUST NOT apply internal tensor rescales ($704 \rightarrow 1920$ or $1280 \rightarrow 1920$). Adapters apply ONLY the verified source transform ($1920 \times 1080 \rightarrow \text{source resolution}$, e.g. $s_x = 2.0, s_y = 2.0$ for 4K). | `backend/app/adapters/m1_adapter.py`, `backend/app/adapters/m2_adapter.py`, `backend/app/adapters/m3_adapter.py`, `P0_CONTRACT_TEST_PLAN_REV2A.md` (Tests 01–03, 05) | Prevents disastrous double-scaling of player bounding boxes. |
| **03** | **Exact LLM Digest & System Prompt Hashes** | Truncated strings (`46e0c10c...`, `ab95a835...`) and outdated hashes appeared in several test and file map summaries. | Replaced all references with the exact 64-character SHA-256 hex strings everywhere: Model: `llama3.1:8b`, Digest: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`, Prompt SHA-256: `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`. Tests assert full strings. | `backend/app/services/llm_report_service.py`, `P0_CONTRACT_TEST_PLAN_REV2A.md` (Test 22), `P0_IMPLEMENTATION_FILE_MAP_REV2A.md` | Enforces exact cryptographic integrity checks without prefix truncation. |
| **04** | **Kinematics Velocity Continuity Semantics** | REV2 conflated `valid_delta_frames <= 120` with the `0.50s` time-based gap reset. | Disentangled frame buffer from time continuity. Kinematic continuity is strictly time-based: $\Delta t = (\text{frame}_i - \text{frame}_{i-1}) / \text{probed\_fps}$. If $\Delta t > 0.50\text{ s}$, velocity continuity resets and no interpolation occurs. Clarified that 120 frames is strictly the BoT-SORT track buffer, NOT a kinematics threshold. Preserved 7-point median and outlier rejection ($> 36\text{ km/h}$). | `backend/app/services/kinematics_service.py`, `P0_CONTRACT_TEST_PLAN_REV2A.md` (Test 15) | Prevents FPS-dependent velocity distortion on variable framerate videos. |
| **05** | **Exact ASR Tactical Category Schema** | Stale category names (`COVERAGE`, `TRANSITION`, `TACTICAL_DISCIPLINE`) leaked into test descriptions. | Enforced the exact five frozen tactical categories everywhere: `Defensive`, `Offensive`, `Pressing`, `Passing`, `Positioning / Hold Ground`. Dedicated test asserts exact category names and deterministic keyword extraction mapping. | `backend/app/services/asr_service.py`, `P0_CONTRACT_TEST_PLAN_REV2A.md` (Test 17) | Guarantees strict taxonomy alignment between ASR extraction and downstream fusion/LLM. |
| **06** | **LLM Timeout Setting Unification** | Contradiction between `PRODUCTION_LLM_TIMEOUT_SECONDS = 45` and `environment default = 120`. | Set initial production default to 120 seconds (`PRODUCTION_LLM_TIMEOUT_SECONDS = 120`), matching `FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120`, kept environment-configurable via `LLM_TIMEOUT_SECONDS`. Labeled 45s strictly as a historical/candidate policy awaiting E2E product benchmarking. Zero-retry and deterministic fallback preserved. | `backend/app/services/llm_report_service.py`, `backend/app/core/config.py`, `P0_CONTRACT_TEST_PLAN_REV2A.md` (Test 24) | Eliminates configuration ambiguity while preserving 100% reliable deterministic fallback. |

---

## Detailed Consistency Audit Rationale

### 1. M1 Final Baseline Invariants
In historical Stage 4B exploration, YOLO11m was run with a single confidence threshold of 0.20 and global NMS IoU of 0.70. However, the frozen M1 evaluation baseline established a superior two-tier confidence structure:
- **`tracker_input_candidate_confidence_floor = 0.05`**: Allows low-confidence detections into the candidate pool for BoT-SORT association.
- **`standalone_qualification_confidence = 0.25`**: Required for initial track creation.
- **`tile_nms_iou = 0.70`**: Intra-tile NMS.
- **`global_nms_iou = 0.50`**: Inter-tile seam suppression.
- **BoT-SORT Tracker**: `track_high_thresh = 0.35`, `track_low_thresh = 0.10`, `new_track_thresh = 0.35`, `track_buffer = 120`, `match_thresh = 0.85`, `gmc_method = "none"`, `proximity_thresh = 0.15`, `appearance_thresh = 0.88`, `with_reid = True`, `fuse_score = True`.

Test 01 in REV2A strictly verifies these frozen parameters and explicitly rejects the stale 0.20 / 0.70 values.

### 2. Coordinate Space Architecture & Double-Scale Prevention
Analysis of the frozen execution scripts confirmed the following coordinate lifecycles:
- **M1**: Tile crops are fed to YOLO11m at `imgsz=1280`. Ultralytics internal postprocessing scales predicted boxes back to the tile crop dimensions (e.g. $[0, W_{\text{tile}}]$). `remap_tile_bbox_to_full_frame` adds the tile x-offset and clips to $[0, 1920] \times [0, 1080]$. Global NMS operates on these full working frame boxes. BoT-SORT receives and emits tracks in $1920 \times 1080$.
- **M2**: RF-DETR postprocesses internal $704 \times 704$ representations directly to $1920 \times 1080$ before Deep-EIoU tracklet generation and GTA-Track association.
- **M3**: YOLO26 and SRITrack operate directly on $1920 \times 1080$ working frames.
Therefore, **all three vision pipelines return tracks in `VISION_WORKING_SPACE` ($1920 \times 1080$)**. Production adapters do NOT apply internal tensor rescales; they only project from $1920 \times 1080$ to `MEDIA_SOURCE_SPACE` ($3840 \times 2160$ for 4K video, $s_x = 2.0, s_y = 2.0$).

### 3. Complete LLM Digest and System Prompt Hash
REV2A replaces all truncated strings with full 64-character SHA-256 strings:
- **Model**: `llama3.1:8b`
- **Digest**: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`
- **Prompt Hash**: `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`

### 4. Kinematics Velocity Continuity
The kinematic continuity reset threshold is defined strictly in seconds:
$$\Delta t = \frac{\text{frame}_i - \text{frame}_{i-1}}{\text{fps}_{\text{probed}}}$$
$$\text{If } \Delta t > 0.50\text{ s} \implies \text{Reset velocity continuity, no interpolation across the gap.}$$
The quantity 120 frames is recorded strictly as the M1 BoT-SORT track buffer (`track_buffer = 120`), completely decoupled from kinematics continuity.

### 5. Frozen ASR Tactical Taxonomy
The schema strictly enforces the five frozen tactical categories:
1. `Defensive`
2. `Offensive`
3. `Pressing`
4. `Passing`
5. `Positioning / Hold Ground`

All references to `COVERAGE`, `TRANSITION`, and `TACTICAL_DISCIPLINE` are purged.

### 6. LLM Timeout Policy Alignment
- `FORMAL_LLM_BENCHMARK_TIMEOUT_SECONDS = 120` (formal scientific benchmark protocol).
- `PRODUCTION_LLM_TIMEOUT_SECONDS = 120` (initial frozen production default, configurable via `LLM_TIMEOUT_SECONDS`).
- 45s is documented strictly as a provisional candidate policy subject to future E2E product benchmarking.
- Generation parameters remain frozen: `temperature = 0.0`, `seed = 42`, `top_p = 1.0`, `num_ctx = 4096`, `retries = 0`.
