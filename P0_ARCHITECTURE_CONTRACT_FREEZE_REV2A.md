# CM3070 P0 Architecture & Contract Freeze — Revision 2A (REV2A)

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 2A Final Consistency Hotfix)  
**Date**: 2026-09-26  
**Status**: `P0_CONTRACT_FREEZE_REV2A_READY_FOR_APPROVAL`  
**Authoritative References**: `CM3070_CANONICAL_FINAL_REPORT_EVIDENCE_LOG_v88.md`, `M1_FINAL_EVALUATION_BASELINE.json`, `M2_FINAL_EVALUATION_BASELINE.json`, `M3_selected_identity_configuration.json`, `M3_detection_reid_cache_prelaunch.json`, `ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json`, `LLM_FINAL_INTEGRATION_FREEZE.json`, `C03/C04/C06_metric_evidence.json`  

---

## 1. Executive Summary & REV2A Scope

This document represents the definitive, frozen architectural and contract specification for the AI integration phase of the CM3070 project. It resolves all remaining internal inconsistencies from REV2, establishing exact coordinate-space lifecycles, rigorous anti-double-scaling rules, full cryptographic hashes for LLM verification, time-based kinematics continuity, and exact ASR taxonomy schemas.

### Core Scientific Invariants
1. **Original Research Remains Frozen & Read-Only**: Research notebooks, historical splits, and benchmark runs are immutable.
2. **Explicit Methodology Selection & Component Isolation**: Production executes only the selected vision methodology (M1, M2, or M3). Zero cross-contamination, zero silent fallbacks.
3. **Decoupled Identity Assurance**:
   - `method_formal_identity_status = FAIL_UNSAFE_MERGE` (proven under `FORMAL_DENSE_GT`).
   - Ordinary uploads evaluate `runtime_identity_evidence_basis = RUNTIME_HEURISTIC_ONLY`.
   - Runtime heuristics must **never** claim formal unsafe merge.
   - Accumulated player-level analytics remain **strictly withheld** (`player_level_analysis_allowed = false`).
4. **Coordinate Space Separation**:
   - `MEDIA_SOURCE_SPACE`: Native probed video container resolution ($3840 \times 2160$ for iPhone 16). Canonical `BoundingBox` is strictly in this space.
   - `VISION_WORKING_SPACE`: Fixed $1920 \times 1080$ tracking and homography plane.
   - `MODEL_INFERENCE_SPACE`: Internal tensor dimensions ($1280 \times 1280$ for M1 tiles, $704 \times 704$ for M2, $1280$ imgsz for M3).
   - **Anti-Double-Scaling Guarantee**: All three frozen runners (M1, M2, M3) output boxes natively in `VISION_WORKING_SPACE` ($1920 \times 1080$). Adapters apply ONLY the verified source transform ($1920 \times 1080 \rightarrow \text{source resolution}$, e.g. $s_x = 2.0, s_y = 2.0$ for 4K video).

---

## 2. Vision Pipeline & Adapter Contracts

### 2.1 Coordinate Space Lifecycle

```
[MODEL_INFERENCE_SPACE]
   M1: 1280x1280 tile tensor | M2: 704x704 tensor | M3: 1280 tensor
           │                            │                     │
   (Ultralytics unletterbox)    (RF-DETR postprocess) (SRITrack working)
           ▼                            ▼                     ▼
   tile pixels (W_tile, H_tile)         │                     │
           │                            │                     │
   (offset + clip to frame)             │                     │
           │                            │                     │
   (Global NMS IoU=0.50)                │                     │
           │                            │                     │
   (BoT-SORT tracking)                  │                     │
           │                            │                     │
           └────────────────────────────┼─────────────────────┘
                                        ▼
                           [VISION_WORKING_SPACE]
                           Fixed 1920x1080 Pixels
                                        │
                         (Adapter Source Projection)
                         s_x = W_source / 1920.0
                         s_y = H_source / 1080.0
                                        │
                                        ▼
                            [MEDIA_SOURCE_SPACE]
                 Canonical BoundingBox [x1, y1, x2, y2]
```

### 2.2 Method 1 (M1) — Fine-Tuned YOLO11m + Tiled NMS + BoT-SORT
- **Role**: Secondary baseline & research comparison detector.
- **Detector Checkpoint**:
  - Path: `runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt`
  - Filename: `epoch28.pt`
  - Architecture: `YOLO11m custom-domain-adapted`
  - SHA-256: `ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b`
  - Size: 104,950,959 bytes
- **ReID Model**:
  - Path: `runs/method_1/M1_FINAL_EVALUATION_BASELINE/checkpoints/yolo26n-reid.onnx`
  - Architecture: `official Ultralytics yolo26n-reid.onnx`
  - SHA-256: `8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb`
  - Size: 9,873,245 bytes
- **Tiling Architecture**:
  - 3 horizontal tiles covering full width with $15\%$ overlap.
  - Per-tile inference at `imgsz=1280`, class 0 (person).
- **Frozen Detection & NMS Operating Points**:
  - **`tracker_input_candidate_confidence_floor`**: `0.05` (candidate admission threshold).
  - **`standalone_qualification_confidence`**: `0.25` (track creation qualification threshold).
  - **`tile_nms_iou`**: `0.70` (intra-tile suppression).
  - **`global_nms_iou`**: `0.50` (inter-tile seam suppression).
  *(Note: Historical Stage 4B single threshold of 0.20 and global NMS of 0.70 are historical only and are NOT the frozen M1 baseline).*
- **BoT-SORT Tracker Parameters**:
  - `track_high_thresh = 0.35`
  - `track_low_thresh = 0.10`
  - `new_track_thresh = 0.35`
  - `track_buffer = 120` (tracker frame buffer; distinct from kinematics continuity)
  - `match_thresh = 0.85`
  - `gmc_method = "none"`
  - `proximity_thresh = 0.15`
  - `appearance_thresh = 0.88`
  - `with_reid = True`
  - `fuse_score = True`
- **Adapter Transform**:
  - Runner outputs tracks directly in `VISION_WORKING_SPACE` ($1920 \times 1080$).
  - Adapter projects to `MEDIA_SOURCE_SPACE`:
    $$x_{\text{source}} = x_{\text{working}} \times \left(\frac{W_{\text{source}}}{1920.0}\right), \quad y_{\text{source}} = y_{\text{working}} \times \left(\frac{H_{\text{source}}}{1080.0}\right)$$

### 2.3 Method 2 (M2) — RF-DETR-L + Deep-EIoU + GTA-Track
- **Role**: Default recommended automated tracking methodology (`AUTO` target).
- **Detector Checkpoint**:
  - Path: `runs/method_2/M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth`
  - Filename: `checkpoint_best_total.pth`
  - Architecture: `RF-DETR-L`
  - SHA-256: `7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85`
  - Size: 134,747,227 bytes
  - Operating Point: Score threshold $\ge 0.50$ (external NMS is False; native bipartite Hungarian matching).
- **ReID Model**:
  - Path: `runs/method_2/M2_P0_preflight/checkpoints/sports_model.pth.tar-60`
  - Filename: `sports_model.pth.tar-60`
  - Architecture: `OSNet-x1.0` (sports_model)
  - SHA-256: `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd`
  - Size: 30,393,613 bytes
- **Adapter Transform**:
  - Runner RF-DETR postprocessing emits boxes directly in `VISION_WORKING_SPACE` ($1920 \times 1080$) before Deep-EIoU association.
  - Adapter MUST NOT apply $704 \rightarrow 1920$ scaling.
  - Adapter applies ONLY source projection: $s_x = W_{\text{source}} / 1920.0, s_y = H_{\text{source}} / 1080.0$.

### 2.4 Method 3 (M3) — YOLO26m + SRITrack-v1 + DINOv3
- **Role**: Advanced experimental comparison methodology.
- **Detector Checkpoint**:
  - Path: `methodology_comparison/runs/method_3/M3_FORMAL_001_DOMAIN_ADAPTED/checkpoints/M3_ADAPTED_YOLO26M.pt`
  - SHA-256: `ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf`
  - Size: 44,081,689 bytes
  - Operating Point: Confidence $\ge 0.30$.
- **SRITrack Parameters (P5A Amended)**:
  - `track_new_th = 0.30` (amended from source-default 0.70 via P5A score compatibility amendment)
  - `track_high_th = 0.60`
  - `track_buffer = 1000`
- **Adapter Transform**:
  - Runner operates directly on $1920 \times 1080$ working frames.
  - Adapter applies ONLY source projection: $s_x = W_{\text{source}} / 1920.0, s_y = H_{\text{source}} / 1080.0$.

---

## 3. Kinematics & Calibration Safety Matrix

### 3.1 Kinematics Continuity & Outlier Rejection
- **Time-Based Continuity Rule**:
  $$\Delta t = \frac{\text{frame}_i - \text{frame}_{i-1}}{\text{fps}_{\text{probed}}}$$
  $$\text{if } \Delta t > 0.50\text{ s}: \quad \text{reset velocity continuity; do NOT interpolate across gap.}$$
  *(The 120-frame quantity belongs strictly to BoT-SORT's track buffer and is NOT used as a kinematics continuity threshold).*
- **Velocity Estimation**: 7-observation rolling median filter on planar pitch coordinates.
- **Outlier Rejection**:
  $$\text{speed} > 36.0\text{ km/h} \implies \mathbf{REJECT\_AND\_EXCLUDE\_OUTLIER}$$
  Rejected velocity steps are excluded from accepted distance and velocity calculations; never clamped.

### 3.2 Calibration Permission Matrix
| Calibration Mode | Description | Metric Permissions | Visualization Permissions |
| :--- | :--- | :--- | :--- |
| **`CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED`** | Fixed research homography (`d0e9680fdcdf...`, RMSE $0.6505\text{ m}$) on original camera geometry. | Metres ($m$), speed ($km/h$), and physical distance allowed. | 2D radar pitch visualization allowed. |
| **`GEOMETRIC_SOLVE_ONLY`** | User-supplied 4-point pitch corner solve without ground-truth landmark validation. | **Strictly suppressed** (`null`). Never emit $m$ or $km/h$. | Bounded 2D top-down pitch visualization allowed without metric labels. |
| **`NO_METRIC_CALIBRATION` / `INVALID`** | Uncalibrated video or mathematically degenerated homography. | **Strictly suppressed** (`null`). | Suppressed. |

---

## 4. Audio Pipeline & Tactical ASR Contract

### 4.1 Frozen Runtime Parameters
- **Engine**: `faster-whisper==1.2.1` with CTranslate2.
- **Model**: `base.en`, `compute_type="int8"`, `device="cpu"`, `cpu_threads=8`.
- **Audio Preprocessing**: Authoritative 16,000 Hz, single channel (mono), 16-bit PCM WAV.
- **Decoding Options**:
  - `task = "transcribe"`
  - `language = "en"`
  - `beam_size = 5`
  - `word_timestamps = True`
  - `vad_filter = True`
  - `vad_parameters = {"min_silence_duration_ms": 500}`
  - `condition_on_previous_text = False`

### 4.2 Text Normalization & Tactical Taxonomy
- **Text Normalization (6 Rules)**: Lowercase, apostrophe contraction expansion, hyphen/underscore to space, punctuation stripping, digits 0–10 to words, whitespace trim.
- **Exact Five Schema Categories & Keyword Mappings**:
  1. **`Defensive`**: `"defend"`, `"defence"`, `"defense"`, `"drop back"`, `"mark"`, `"cover"`.
  2. **`Offensive`**: `"attack"`, `"shoot"`, `"go forward"`, `"make a run"`, `"run forward"`.
  3. **`Pressing`**: `"press"`, `"close down"`, `"pressure"`, `"sprint"`.
  4. **`Passing`**: `"pass"`, `"play the ball"`, `"switch the ball"`.
  5. **`Positioning / Hold Ground`**: `"hold your position"`, `"hold position"`, `"hold your ground"`, `"stay in position"`, `"stick to your zone"`, `"stay in your zone"`, `"keep your shape"`.
  *(Categories `COVERAGE`, `TRANSITION`, and `TACTICAL_DISCIPLINE` are purged).*
- **Failure Semantics**: Audio extraction or transcription failure emits typed `ASRFailure` and transitions the pipeline to Vision-only mode (`COMPLETED_WITH_LIMITATIONS`). Zero historical transcript fallbacks.

---

## 5. Multimodal Fusion Engine

- **Validated Post-Command Response Window**:
  $$t_{\text{eval\_start}} = t_{\text{end}} + 2.0\text{s}, \quad t_{\text{eval\_end}} = t_{\text{end}} + 6.0\text{s}$$
  Legacy exploratory $[-2\text{s}, +5\text{s}]$ window is strictly rejected.
- **Evidence Scopes**: Emitted items under automated mode must be typed as `TEAM`, `SPATIAL`, `EVENT`, or `ANONYMOUS_TRACK`. Emitting `scope = PLAYER` raises validation error.
- **Readback Preservation (Oracle Mode)**: Preserves verified metrics without recomputation:
  - C04: $14.30\text{m} \rightarrow 7.96\text{m}$ separation reduction.
  - C06: $0.70\text{m}$ (t=275.9s) and $0.49\text{m}$ (t=279.7s) minimum separation.
  - C03: entry at $81.20\text{s}$, $100\%$ zone retention over $6.0\text{s}$.

---

## 6. LLM Report Service & Patch 001 Governance

### 6.1 Cryptographic Identity & Frozen Generation Configuration
- **Model**: `llama3.1:8b` via local Ollama.
- **Exact Digest**:
  `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`
- **System Prompt SHA-256**:
  `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`
- **Frozen Generation Parameters**:
  - `temperature = 0.0`
  - `seed = 42`
  - `top_p = 1.0`
  - `num_ctx = 4096`
  - `retries = 0` (zero retry policy)

### 6.2 Timeout Governance
- **Formal Scientific Benchmark Protocol**:
  $$\mathbf{FORMAL\_LLM\_BENCHMARK\_TIMEOUT\_SECONDS} = \mathbf{120}$$
- **Initial Production Default**:
  $$\mathbf{PRODUCTION\_LLM\_TIMEOUT\_SECONDS} = \mathbf{120}$$
  Configurable via environment variable `LLM_TIMEOUT_SECONDS`. A 45-second cutoff is documented strictly as a provisional candidate policy awaiting real product E2E benchmarking.
- **Fallback Execution**: Timeout or Patch 001 rejection automatically engages `ReportStatus.DETERMINISTIC_FALLBACK` from `StructuredEvidence` without failing the job.

### 6.3 Patch 001 Exact 8 Validation Gates
1. **Gate 1 (Identity Safety)**: Rejects individual player attribution unless Oracle mode.
2. **Gate 2 (Psychological Neutrality)**: Rejects disciplinary language (`lazy`, `blame`).
3. **Gate 3 (Privacy Policy)**: Rejects participant real names.
4. **Gate 4 (Numeric Grounding)**: Traverses all evidence string leaves (`all_numbers_patched`); rejects ungrounded numbers.
5. **Gate 5 (Negation-Aware Attribution)**: Permits negative attribution; rejects affirmative attribution of unresolved targets.
6. **Gate 6 (Missing Speed Safety)**: Rejects asserted speeds when kinematics speed is unavailable.
7. **Gate 7 (Tactical Taxonomy)**: Rejects categories not in evidence events.
8. **Gate 8 (Action Grounding)**: Rejects verbs not present in structured evidence.

---

## 7. Dynamic Job Execution Manifest

The manifest records actual per-job runtime values probed from the uploaded media container:
```json
{
  "job_id": "uuid",
  "media_metadata": {
    "duration_s": 142.5,
    "fps": 29.97,
    "resolution_width": 1920,
    "resolution_height": 1080
  },
  "methodology": {
    "requested": "AUTO",
    "resolved": "METHOD_2_RFDETR_GTATRACK",
    "method_formal_identity_status": "FAIL_UNSAFE_MERGE",
    "method_formal_identity_evidence_basis": "FORMAL_DENSE_GT"
  },
  "calibration_metadata": {
    "mode": "GEOMETRIC_SOLVE_ONLY",
    "homography_sha256": "3a8f...",
    "rmse_m": null
  },
  "runtime_diagnostics": {
    "runtime_identity_status": "UNVERIFIED_HEURISTIC_PASS",
    "runtime_identity_evidence_basis": "RUNTIME_HEURISTIC_ONLY",
    "player_level_analysis_allowed": false,
    "withholding_reason": "Automated tracking methodology has not demonstrated sufficiently safe persistent physical-player identity under formal benchmark evaluation."
  }
}
```
*(All calibration and RMSE fields are nullable and conditional).*
