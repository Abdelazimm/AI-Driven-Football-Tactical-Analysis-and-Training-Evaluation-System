# FINAL SYSTEM REVALIDATION & COMPLETENESS AUDIT
## CM3070 Final Project: AI-Driven Football Tactical Analysis and Training Evaluation System

- **Audit Date**: 2026-09-26
- **Audit Type**: Strict Read-Only Cross-Workspace System Revalidation & Completeness Audit
- **Workspaces Audited**:
  1. **Primary Product Workspace**: `d:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System`
  2. **Secondary Research Workspace**: `G:\My Drive\Football_Training_Assistant_MVP`
  3. **Legacy Colab Notebooks Workspace**: `G:\My Drive\Colab Notebooks`
- **Audit Status**: COMPLETE — FINAL PRE-INTEGRATION BASELINE ESTABLISHED

---

## 1. Executive Summary

This audit establishes the comprehensive, unvarnished state of the entire CM3070 project following the completion of the formal Vision whole-system challenge evaluation. The audit synthesizes evidence across all three project workspaces without modifying any code, configuration, or frozen research artifacts.

### 1.1 Core Audit Conclusions

1. **Formal Vision Evaluation is Complete**:
   - The formal four-clip whole-system evaluation across all 12 method $\times$ clip configurations is finished, frozen, and hashed.
   - All runs strictly adhered to `FORMAL_TRACKER_STATE_POLICY = FRESH_STATE_PER_CHALLENGE_CLIP` with zero intra-clip resets.
   - Source video SHA-256: `0e676f4327d1e7e7ed458d619e5558f6630fc7efb0dda7bc608aec45cb9a5c71`.
   - Frozen dense-GT manifest SHA-256: `524d231703d77485f4b57526929aedeadb744a801089aa12d905c0ef21808aec`.
   - Final evaluation manifest SHA-256: `ec8c60824622d9b07b1b03b9b19365a7b1a2f7aab635a9c596dbec6cf90dd556`.

2. **Official Vision Outcome & Production Role**:
   - **M2 (Global Association / RF-DETR + GTA-Track)** is the decisive winner:
     - **HOTA**: **0.6710** (vs M1 0.4632, M3-v1 0.3517)
     - **MOTA**: **0.8522** (vs M1 0.5673, M3-v1 0.3253)
     - **IDF1**: **0.9144** (vs M1 0.5891, M3-v1 0.4066)
     - **IDSW**: **19** (vs M1 186, M3-v1 5)
     - **Precision**: **0.9878**, **Recall**: **0.8637**
   - **Production Decision**: `DEFAULT_VISION_METHOD = M2_GLOBAL_ASSOCIATION`.
   - **Architectural Requirement**: All three methodologies (M1, M2, M3) must remain fully implemented and selectable in the final product (`AUTO` $\rightarrow$ M2, `M1`, `M2`, `M3`). Detectors and trackers must NEVER be cross-combined.

3. **Definitive Scientific Boundary**:
   - `PLAYER_LEVEL_ACCUMULATED_ANALYTICS = DISABLED`.
   - Even the winning M2 exhibits 19 ID switches and 9 clip-local unsafe identity overlaps across the challenge clips. Automated persistent identity across full sessions remains mathematically unproven (`FAIL_HIGH_FRAGMENTATION`).
   - The product must continue to fail closed, reporting `COMPLETED_WITH_LIMITATIONS` with player-level conclusions strictly withheld.

4. **Oracle Showcase Revalidation Verdict**:
   - **Status**: `ORACLE_SHOWCASE_REQUIRES_REVALIDATION`.
   - The historical capability showcase (C03, C04, C06) generated in `05_final_showcase` was produced using the superseded `qwen3:8b` model (requiring 7 attempts) and an older pre-Patch 001 grounding validator, prior to the selection of `llama3.1:8b` and `LLM_GROUNDING_VALIDATOR_PATCH_001`.
   - Human-verified inputs (targets, player IDs, response intervals, opponents) remain 100% valid, but the coaching report text and frontend payload must be re-rendered through the frozen Llama 3.1 pipeline.

5. **Subsystem Integration Gap**:
   - **Product Control Plane**: 100% genuine and verified (FastAPI, TanStack Start SSR frontend, Supabase DB & Storage with 4 migrations, authoritative media validation, atomic worker dispatch, 150/150 passed tests).
   - **Research Methodology**: 100% frozen and verified (Faster-Whisper int8 ASR, Llama 3.1 8B LLM, 19.31m $\times$ 19.88m Homography, M1/M2/M3 TrackEval results).
   - **Primary Backend Pipeline**: Currently contains **fail-closed stubs** (`NotImplementedError`) and HTTP 409 dispatch block.
   - **Effort Classification**: **MEDIUM INTEGRATION TASK** (3 to 5 focused engineering days; zero major rebuilding).

---

## 2. Workspace Authority Map

| Domain / Subsystem | Primary Product Workspace (`D:\...`) | Secondary Research Workspace (`G:\My Drive\Football_Training_Assistant_MVP`) | Legacy Colab Workspace (`G:\My Drive\Colab Notebooks`) | Sole Authoritative Source |
| :--- | :--- | :--- | :--- | :--- |
| **Product Web Frontend** | TanStack Start SSR + React 19 + Vite + Tailwind CSS | 3-file static prototype (`index.html`, `index.css`, `app.js`) | None | **Primary Product Workspace** |
| **Backend API & Routing** | FastAPI (`/api/v1`), Pydantic v2, dependency injection | Monolithic `server.py` | None | **Primary Product Workspace** |
| **Database & Migrations** | Supabase PostgreSQL, Migrations 001–004, RLS | None | None | **Primary Product Workspace** |
| **Storage & Media Probing** | `SupabaseStorageService`, `ffprobe` media validation | Local file paths (`data/custom/`) | None | **Primary Product Workspace** |
| **Worker Dispatch & Idempotency** | Atomic `WorkerDispatchRepository`, partial unique index | In-memory local scripts | None | **Primary Product Workspace** |
| **Worker Callback Security** | `/api/v1/internal/jobs/{id}/progress`, HMAC-SHA256 | Direct in-process calls | None | **Primary Product Workspace** |
| **Modal Deployment Harness** | `modal_app/worker.py` control harness | None | None | **Primary Product Workspace** |
| **Vision M1/M2/M3 Methods** | Stubs (`NotImplementedError`), Stage 4B detector | Checkpoints, TrackEval harnesses, configs | Historical prototype code in `01_vision_pipeline.ipynb` | **Secondary Research Workspace** |
| **Final Vision Evaluation** | None | Whole-system challenge evaluation (TrackEval, GT, logs) | None | **Secondary Research Workspace** |
| **ASR Methodology** | Stubs (`audio.py`, `instructions.py`) | Frozen `backend/pipeline/asr.py`, Faster-Whisper int8 | `02_audio_pipeline.ipynb` | **Secondary Research Workspace** |
| **LLM Methodology & Grounding**| Stubs (`evidence.py`, `reporting.py`), stale manifest | Frozen `llama3.1:8b`, prompt SHA, Patch 001 validator | `04_report_generation.ipynb` | **Secondary Research Workspace** |
| **Homography Calibration** | Stubs (`calibration.py`, `kinematics.py`), calibration guards | Verified 3v3 matrix, RMSE 0.651m, 19.31m $\times$ 19.88m | Stage 6 calibration code | **Secondary Research Workspace** |
| **Capability Showcase** | `golden/` immutable fixtures and media | `05_final_showcase/` research generation source | Showcase prototyping cells | **Primary** (for app) / **Secondary** (origin) |
| **Project Chronological History**| Integration handoffs, audit manifests | Benchmark logs, freeze manifests | 378 cells of evolutionary history (Stages 0–6) | **Colab Notebooks** (History) / **Secondary** (Data) |

---

## 3. Full Project Chronological Evolution

Reconstructing the project chronologically reveals how technical obstacles forced disciplined scientific pivots:

```
[Phase 1: Early Vision Prototyping (Stages 0 - 3)]
  │  - Naive full-frame YOLOv8 on 4K/1080p footage.
  │  - Issue: Tiny player scales (~40-60px height) resulted in severe missed detections (>40% false negatives).
  ▼
[Phase 2: Slicing & Fine-Tuning Pilot (Stage 4B)]
  │  - Introduced 3-tile horizontal slicing with 15% overlap at imgsz=1280.
  │  - Fine-tuned YOLO11m pilot (`best.pt`, 40.5 MB, SHA-256 `f6b3fe6f...`).
  │  - Drastic recall recovery on distant pitch areas.
  ▼
[Phase 3: Tracking & Motion Evaluation (Stage 5)]
  │  - Evaluated ByteTrack on tiled detections.
  │  - Found severe track fragmentation under camera pan and player occlusions.
  │  - Transitioned to BoT-SORT with Camera Motion Compensation (CMC) and internal short-gap interpolation.
  ▼
[Phase 4: Physical Metric Grounding (Stage 6)]
  │  - Provisional 20m x 20m homography upgraded to physical field measurements: 19.31m x 19.88m.
  │  - Independent validation achieved RMSE = 0.651m.
  │  - Introduced 7-observation rolling median filter and 36.0 km/h kinematic outlier clamp.
  ▼
[Phase 5: Real 3v3 Match & Identity Fragmentation Crisis]
  │  - Applied pipeline to 340s continuous match footage (`3v3_match_iphone16.MOV`, 60 FPS).
  │  - Result: 115 raw track IDs generated for 6 players (37 meaningful tracks).
  │  - Fragmentation ratio = 6.1667 (far exceeding safety threshold 1.50).
  │  - Extensive repair attempts (Hungarian matching, anchor constraints, multi-pass stitching) failed to eliminate identity switches.
  │  - Scientific Decision: Declare automated persistent identity FAIL_HIGH_FRAGMENTATION. Enforce fail-closed withholding of player-level accumulated metrics.
  ▼
[Phase 6: Oracle-Assisted Capability Showcase (C03, C04, C06)]
  │  - Created proof-of-concept demonstrating downstream tactical capabilities using human-verified player identities.
  │  - Generated reports using local Ollama `qwen3:8b` (7 attempts required to pass validation).
  │  - Grounded tactical responses for Pressing (C06), Marking (C04), and Position Hold (C03).
  ▼
[Phase 7: Tri-Methodology Vision Redesign (M1, M2, M3)]
  │  - To formally benchmark alternative paradigm solutions:
  │    * M1: Original Hybrid (YOLO11m + BoT-SORT + Fallback C).
  │    * M2: Global Association (RF-DETR + GTA-Track with deep ReID).
  │    * M3: Re-entry Focused (YOLO26 + SriTrack with spatial-recurrent memory).
  ▼
[Phase 8: ASR & LLM Methodology Freezes]
  │  - ASR Benchmark: `faster-whisper base.en` decisively defeated `parakeet_tdt_v2` (WER 18.4% vs 36.8%, Tactical Recall 76.5% vs 52.9%).
  │  - LLM Benchmark: `llama3.1:8b` defeated `qwen3:8b` (Schema pass rate 93.75% vs 31.25%, 100% deterministic repeatability).
  │  - Finalized `LLM_GROUNDING_VALIDATOR_PATCH_001` with 8 deterministic gates.
  ▼
[Phase 9: Whole-System Challenge Evaluation (The Present)]
  │  - 4 challenge clips (3780 frames total) evaluated under TrackEval.
  │  - M2 achieved decisive victory (HOTA 0.6710 vs M1 0.4632 vs M3 0.3517).
  │  - All methods confirmed unsafe for autonomous accumulated identity.
  │  - M2 selected as DEFAULT; all 3 methods preserved as selectable options.
  ▼
[Phase 10: Product Architecture Hardening & Final Integration]
     - Primary workspace hardened with Supabase migrations 001–004, authoritative ffprobe probing, atomic dispatch idempotency, and 150 passed tests.
     - Ready for pipeline integration.
```

---

## 4. Current Frozen Subsystem Matrix

| Subsystem | Frozen Technical Specification | Verification Artifact / Digest | Runtime Target | Production Role |
| :--- | :--- | :--- | :--- | :--- |
| **Vision (M1)** | YOLO11m + BoT-SORT (Fallback C, high=0.25, low=0.05, new=0.45, buffer=420) | `M1_FORMAL_003_DOMAIN_ADAPTED` | GPU (T4/A10G) | Selectable Method |
| **Vision (M2)** | RF-DETR + GTA-Track (Deep-EIoU tracklets, global graph ReID association) | `GT_CLIP_01`–`04` final predictions fixed | GPU (T4/A10G) | **DEFAULT / AUTO Method** |
| **Vision (M3)** | YOLO26 + SriTrack-v1 (Spatial-recurrent identity recovery) | `M3_ALL_FOUR_RAW_OUTPUTS_FIXED.json` | GPU (T4/A10G) | Selectable Method |
| **ASR** | Faster-Whisper `base.en`, CTranslate2, Silero VAD, word timestamps, 16 kHz mono | `ASR_MODEL_SELECTION_FROZEN` | CPU int8, 8 threads | **Frozen Production ASR** |
| **LLM** | Meta `llama3.1:8b` (greedy temp 0.0, seed 42) | Digest: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | Local Ollama / vLLM | **Frozen Production LLM** |
| **System Prompt** | Structured coach reporting prompt | SHA-256: `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce` | Text template | **Frozen Production Prompt** |
| **Grounding Validator**| `LLM_GROUNDING_VALIDATOR_PATCH_001` (8 deterministic regex/logic gates) | 13/13 regression tests passed | In-process Python | **Frozen Production Validator**|
| **Homography** | 19.31m $\times$ 19.88m corrected 3v3 matrix, RMSE 0.651m, 36 km/h speed clamp | SHA-256: `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507` | In-process Python | **Frozen Production Calibration**|
| **Database** | Supabase PostgreSQL + Migrations 001–004, RLS, partial unique index | Verified live on Supabase | Cloud PostgreSQL | **Authoritative Product DB** |
| **Storage & Probe** | `SupabaseStorageService` + `MediaValidationService` (`ffprobe`, 300s limit) | 46 unit tests passed | In-process Python / CLI | **Authoritative Ingestion** |

---

## 5. Oracle Showcase Revalidation Analysis

### 5.1 Historical Provenance Audit
- **Directory**: `G:\My Drive\Football_Training_Assistant_MVP\experiments\capability_showcase\05_final_showcase\`
- **Inspected Files**:
  - `showcase_final_summary.json`
  - `showcase_ollama_input.json`
  - `showcase_ollama_raw_response.json`
  - `showcase_grounding_validation.json`
  - `showcase_final_coach_report.md`
  - `showcase_frontend_payload.json`
  - `showcase_artifact_completeness.json`

### 5.2 Key Audit Discoveries
1. **Model Used**: The showcase was generated using **`qwen3:8b`** via Ollama (`"ollama_model": "qwen3:8b"` in `showcase_final_summary.json`). It required **7 generation attempts** before passing validation (`"attempt_count": 7, "accepted_attempt": 7` in `showcase_grounding_validation.json`).
2. **Grounding Validator**: It used the pre-patch validator. It did NOT use `LLM_GROUNDING_VALIDATOR_PATCH_001`.
3. **Tracking Source**: Ingested tracking from `selected_C_roster_assignments.csv` (Experiment C), an earlier tracking run, rather than M2.
4. **Human Verification Inputs**:
   - Tactical commands were extracted from ASR (`"Press high on the ball, press high on the ball."` at 271.6s–274.4s) and human-verified.
   - Player identities (`RED_01`, `BLACK_01`, `RED_03`), opponents (`BLACK_03`, `BLACK_01`), response intervals, and tactical zone meanings were manually verified by human review (`C06_identity_mapping_review.json`).
5. **Payload Contract**: `showcase_frontend_payload.json` uses a legacy flat format that does not match the primary product's `AnalysisResult` schema in `shared/schemas/results.py`.

### 5.3 Formal Revalidation Determination
$$\mathbf{DISPOSITION: ORACLE\_SHOWCASE\_REQUIRES\_REVALIDATION}$$

### 5.4 Revalidation Specifications
- **What Can Be Reused Unchanged (100% Valid)**:
  - All human-verified oracle annotations (ground truth target mappings, player aliases, opponent attributions, evaluation time intervals, and tactical zone semantics).
  - The physical pitch homography matrix and dimensions (19.31m $\times$ 19.88m, RMSE 0.651m).
  - The video cut points, contact sheet images (`C04`), and overlay videos (`C03`, `C06`).
- **What Must Be Regenerated / Adapted**:
  - Re-run the structured evidence through the frozen **`llama3.1:8b`** using the frozen prompt (`ab95a835...`) and validate with **`LLM_GROUNDING_VALIDATOR_PATCH_001`**.
  - Transform the resulting report and metrics into the canonical **`AnalysisResult`** Pydantic contract.

---

## 6. ASR Final-State Audit

### 6.1 Authoritative Specification
- **Selected Model**: `faster-whisper base.en` executed via `CTranslate2` on CPU int8 (8 threads).
- **Audio Conditioning**: 16 kHz mono PCM, `task="transcribe"`, `language="en"`, `beam_size=5`, `word_timestamps=True`, `vad_filter=True`, `min_silence_duration_ms=500`, `condition_on_previous_text=False`.
- **Text Normalization**: Deterministic lowercase, punctuation stripping, football vocabulary mapping (e.g., "press", "hold", "mark", "drop").
- **Tactical Event Extraction**: Deterministic keyword matching with parent-segment timestamp inheritance.

### 6.2 Empirical Benchmark Evidence
- In formal head-to-head testing on real coaching audio (`coach_commands.m4a`, 340.033s):
  - **Word Error Rate (WER)**: **18.40%** (vs Parakeet TDT v2 36.80% — 50.0% relative error reduction).
  - **Character Error Rate (CER)**: **11.86%** (vs Parakeet 23.29%).
  - **Tactical Event Recall**: **76.47%** (13 / 17 GT events vs Parakeet 52.94% [9 / 17]).
  - **Tactical Event F1**: **83.87%** (vs Parakeet 66.67%).

### 6.3 Product Workspace Status & Extraction Plan
- Primary repo files [`backend/app/pipeline/audio.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/audio.py) and [`instructions.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/instructions.py) are currently stubs raising `NotImplementedError`.
- Operational logic exists in `Football_Training_Assistant_MVP/backend/pipeline/asr.py`.
- **Extraction Work**: Adapt `ASRPipeline` from research into `backend/app/pipeline/audio.py` and `instructions.py` with zero logic changes.

---

## 7. LLM Final-State Audit

### 7.1 Authoritative Specification
- **Selected Model**: Meta `llama3.1:8b` via Ollama / vLLM.
- **Authoritative Digest**: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`.
- **System Prompt SHA-256**: `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`.
- **Decoding Configuration**: Greedy decoding (`temperature=0.0`, `seed=42`, `top_p=1.0`), deployment timeout 120.0s.
- **Grounding Validator**: `LLM_GROUNDING_VALIDATOR_PATCH_001` (8 deterministic gates).

### 7.2 Empirical Benchmark Evidence
- In formal head-to-head testing across 16 common evaluation cases (32 executions):
  - **Schema Validation Pass Rate**: **93.75%** (15 / 16 cases) vs Qwen3:8B **31.25%** (5 / 16).
  - **Timeout Failure Rate**: **6.25%** (1 / 16) vs Qwen3:8B **68.75%** (11 / 16).
  - **Deterministic Repeatability**: **100.0% Exact String Match** across identical prompts.
  - **Hallucinations / Unsupported Identities**: **0 violations** (100% pass across both models).

### 7.3 Superseded Paths & Discrepancies
- **Cohere**: Audited and confirmed completely absent from the football pipeline (only referenced in coursework exercises).
- **Qwen**: Fully superseded by Llama 3.1 8B. Stale reference in `backend/app/core/model_manifest.yaml` (line 96) must be corrected.
- **Primary Repo Status**: [`backend/app/pipeline/evidence.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/evidence.py) and [`reporting.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/reporting.py) are stubs. Research backend `validator.py`, `llm_client.py`, and `reporter.py` contain the production-ready code.

---

## 8. Multimodal Fusion Audit

### 8.1 Fusion Engine Logic & Rules
- Resides in `Football_Training_Assistant_MVP/backend/pipeline/fusion.py`.
- **Temporal Alignment**:
  - Receives ASR tactical events with interval $[t_{start}, t_{end}]$.
  - Constructs post-instruction evaluation window: $[t_{end} + 2.0s, t_{end} + 6.0s]$.
- **Spatial Alignment**:
  - Projects player footpoint coordinates into pitch metric space $(x_m, y_m)$.
  - Assigns spatial thirds: Defensive Third ($x < 6.44m$), Middle Third ($6.44m \le x \le 12.87m$), Attacking Third ($x > 12.87m$).
- **Identity Safety Boundary Enforcement**:
  - Checks identity gate status.
  - If status $\ne$ `PASS_RELIABLE` (which is true for all real sessions), the fusion engine **strips all individual player attributions** and computes team-level spatial metrics only (team centroid displacement, spread, group speed).
  - Emits explicit limitation: `"Player-specific response withheld due to tracking fragmentation"`.

### 8.2 Compatibility Verdict
- The fusion logic is **mathematically sound and fully compatible** with M1, M2, and M3 track outputs, Faster-Whisper ASR events, and Llama 3.1 evidence contracts.
- **Work Required**: Pure product adaptation from research `fusion.py` into primary `backend/app/pipeline/fusion.py`. Zero redesign needed.

---

## 9. Homography and Kinematics Audit

### 9.1 Pitch Geometry and Transformation Matrix
- **Field Dimensions**: Length **19.31 m**, Width **19.88 m** (corrected physical field).
- **Homography Matrix**: `config/3v3_homography_measured_metric_corrected.json` (SHA-256 `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507`).
- **Independent Validation RMSE**: **0.651 m** (max residual error 0.841 m).
- **Confidence Rating**: `MODERATE_CONFIDENCE_MEASURED_METRIC_ESTIMATE`.

### 9.2 Kinematics Safety Invariants
1. **Coordinate Smoothing**: 7-observation rolling median filter on pixel coordinates prior to homography projection.
2. **Velocity Derivation**: Computed from consecutive smoothed metric points divided by $\Delta t$.
3. **Outlier Velocity Rejection**: Speeds exceeding **36.0 km/h** are clamped or flagged as tracking noise.
4. **Gap Handling**: Kinematics are NEVER interpolated across tracking gaps $> 0.5s$.
5. **Metric vs Non-Metric Safety Gate**:
   - `DEMO_FIXED_CALIBRATION` is restricted to original research geometry.
   - For arbitrary user-uploaded videos without custom landmarks, the system strictly operates in `NO_METRIC_CALIBRATION` mode. Pixel coordinates are normalized $[0, 1]$; metric units (m, km/h) are completely suppressed.

---

## 10. Vision Production Integration Audit

### 10.1 Required Production Architecture
The production architecture must support all three evaluated methods:

$$\mathbf{PRODUCTION\_VISION\_EXECUTORS = \{M1, M2, M3\}}$$
$$\mathbf{DEFAULT\_VISION\_METHOD = M2\_GLOBAL\_ASSOCIATION}$$

### 10.2 Methodology Executor Specifications

```
                       ┌───────────────────────────────────────────┐
                       │        MethodologyExecutorRegistry        │
                       └─────────────────────┬─────────────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             │                               │                               │
             ▼                               ▼                               ▼
  ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
  │     M1Executor      │         │     M2Executor      │         │     M3Executor      │
  │  (Original Hybrid)  │         │(Global Association) │         │ (Re-entry Focused)  │
  ├─────────────────────┤         ├─────────────────────┤         ├─────────────────────┤
  │ Detector: YOLO11m   │         │ Detector: RF-DETR   │         │ Detector: YOLO26    │
  │ Tracker:  BoT-SORT  │         │ Tracker:  GTA-Track │         │ Tracker:  SriTrack  │
  │ Fallback: Option C  │         │ (Deep-EIoU + ReID)  │         │ (Spatial-Recurrent) │
  └──────────┬──────────┘         └──────────┬──────────┘         └──────────┬──────────┘
             │                               │                               │
             └───────────────────────────────┼───────────────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   Canonical VisionResult  │
                               │  - Bounding boxes [x,y,w,h│
                               │  - Track IDs (raw)        │
                               │  - Confidence scores      │
                               │  - Provenance & Config    │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │    Identity Safety Gate   │
                               │  - Fragmentation Ratio    │
                               │  - Conflict Analysis      │
                               │  - FAIL_HIGH_FRAGMENTATION│
                               └───────────────────────────┘
```

1. **`M2Executor` (DEFAULT / AUTO)**:
   - Uses RF-DETR detector and GTA-Track with deep ReID tracklet stitching.
   - Wins on overall tracking consistency (HOTA 0.6710, MOTA 0.8522, IDF1 0.9144, 19 ID switches).
2. **`M1Executor` (Selectable Option)**:
   - Uses fine-tuned YOLO11m detector and BoT-SORT with CMC and Fallback C configuration.
   - High recall (0.8609), but prone to fragmentation (186 ID switches, HOTA 0.4632).
3. **`M3Executor` (Selectable Option)**:
   - Uses YOLO26 detector and SriTrack spatial-recurrent association.
   - Extremely low ID switches (5), but lower recall (0.3273, HOTA 0.3517).
4. **Role of Stage 4B YOLO11m**:
   - Stage 4B is the historical detector pilot.
   - It forms the detector component of M1 and provides reusable utility code for horizontal tile slicing (`backend/app/pipeline/detection.py`).
   - It is NOT the deployment detector for M2 (which uses RF-DETR) or M3 (which uses YOLO26).

---

## 11. Product Architecture Delta Since Previous Audit

| Architectural Area | State in Previous Audit (`2026-09-26T07:04Z`) | State in Current Revalidation Audit | Concrete Remediation Required |
| :--- | :--- | :--- | :--- |
| **Vision Selection Status** | `VISION_METHOD_PENDING_FINAL_EVALUATION_SELECTION` | **EVALUATION COMPLETE**: `M2` selected as default; all 3 methods selectable. | Update schemas and registry to support M1, M2, and M3. |
| **Methodology Registry** | Single executor expected; dispatch returns HTTP 409 | 3 executors required: `M1Executor`, `M2Executor`, `M3Executor`. | Implement multi-executor registry in `backend/app/pipeline/registry.py`. |
| **Frontend Upload Wizard** | Generic upload wizard without methodology options | User must select `AUTO (M2)`, `M1`, `M2`, or `M3`. | Add methodology dropdown to `src/routes/analysis.new.tsx`. |
| **Frontend Showcase View** | Static mock cards for C03, C04, C06 | Revalidation required before wiring live data. | Revalidate showcase with Llama 3.1, then wire to `/api/v1/showcase`. |
| **Model Manifest** | Line 96 lists `qwen3:8b` as research reference | `llama3.1:8b` (digest `46e0c10c...`) is frozen final LLM. | Update `backend/app/core/model_manifest.yaml`. |
| **Modal Container** | CPU-only control smoke harness | Must host GPU inference for M1/M2/M3 + Faster-Whisper. | Add GPU and model weights to `modal_app/worker.py`. |

---

## 12. Legacy Notebook Evidence Index

This index inventories the 6 historical notebooks in `G:\My Drive\Colab Notebooks` to preserve evidence provenance for the 10,500-word final report:

| Notebook Name | Size | Project Stage | Core Purpose & Critical Findings | Superseded? | Report Value & Data to Extract |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `01_vision_pipeline.ipynb` | 26.8 MB | Stages 0–6 + 3v3 Repair (378 cells) | Documents initial YOLO failure, Stage 4B tiling, BoT-SORT CMC, 19.31m pitch homography, and the 3v3 fragmentation crisis (ratio 6.1667). | Yes (by `methodology_comparison`) | **Crucial Historical Core**: Extract detection PR curves, tiling ablation figures, and fragmentation logs for Chapters 3 & 4. |
| `02_audio_pipeline.ipynb` | 211 KB | Audio Track Prototyping (9 cells) | Early Faster-Whisper integration, Silero VAD parameter tuning, deterministic keyword extractor design. | Yes (by `methodology_comparison/asr`) | Extract ASR transcription examples and keyword rule definitions for Chapter 4. |
| `03_orchestrator_fusion.ipynb` | 85 KB | Fusion Prototyping (7 cells) | Formulated 2s–6s temporal evaluation window, spatial zone assignment, and identity fail-closed withholding. | Yes (by research `fusion.py`) | Extract fusion timing diagrams and spatial zone definitions for Chapter 4. |
| `04_report_generation.ipynb` | 697 KB | Reporting Prototyping (51 cells) | Early Ollama Qwen experiments, prompt engineering, generation of Oracle showcase `05_final_showcase`. | Yes (by `methodology_comparison/llm`) | Documents the transition from Qwen to Llama and early grounding gate attempts for Chapter 5. |
| `Autonomus_scout.ipynb` | 2.2 MB | Early Concept Exploration (31 cells) | Exploratory player tracking, tactical heatmaps, and scout metric visualizations. | Yes | Historical prototype narrative for Chapter 3. |
| `Autonomous_Scout_Feature_Prototype.ipynb` | 7 KB | Early Concept Exploration (4 cells) | Minimal feature prototype for automated scouting metrics. | Yes | Background context only. |

---

## 13. Final-Report Evidence Readiness Audit

| Final Report Chapter / Topic | Required Scientific Evidence | Current Repository Evidence Status | Exact Evidence Location / Artifact | Missing Elements |
| :--- | :--- | :---: | :--- | :--- |
| **1. Introduction & Motivation** | Problem definition, amateur football filming constraints, single-camera challenge. | **READY** | `README.md`, `docs/architecture.md`, `01_vision_pipeline.ipynb` | None |
| **2. Related Work** | Object detection, multi-object tracking, ASR, LLM grounding literature. | **READY** | Research notebooks and literature citations in repo docs. | None |
| **3. Computer Vision Evolution** | Early YOLO failures, Stage 4B tiling ablation, BoT-SORT tuning. | **READY** | `01_vision_pipeline.ipynb` (Cells 0–158), `detection_provenance.md` | None |
| **4. The Identity Crisis** | Mathematical proof that persistent identity fails on 3v3 match footage. | **READY** | `01_vision_pipeline.ipynb` (Cells DB3V3.1–R13), fragmentation ratio 6.1667. | None |
| **5. Tri-Methodology Vision Evaluation** | TrackEval HOTA/MOTA/IDF1 benchmark on 4 challenge clips across M1, M2, M3. | **READY** | `FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv`, `FINAL_WHOLE_SYSTEM_EVALUATION_REPORT.md` | None |
| **6. Audio & Tactical Extraction** | ASR benchmark (Faster-Whisper vs Parakeet), tactical event extraction. | **READY** | `ASR_CANDIDATE_A_VS_B_FINAL_COMPARISON.csv`, `ASR_MODEL_SELECTION_RATIONALE.md` | None |
| **7. LLM Grounding & Reporting** | Head-to-head LLM benchmark (Llama 3.1 vs Qwen), 8 grounding gates. | **READY** | `LLM_FORMAL_BENCHMARK_COMPARISON.md`, `test_deterministic_integration.py` | None |
| **8. Metric Homography & Kinematics** | Physical pitch measurement (19.31m $\times$ 19.88m), RMSE 0.651m, speed clamping. | **READY** | `3v3_homography_measured_metric_corrected.json`, `metric_sanity_report.md` | None |
| **9. Capability Showcase (Oracle)** | Proof of concept on Pressing (C06), Marking (C04), Holding (C03). | **PARTIAL** | Verified human inputs and overlays exist; report text needs Llama revalidation. | Re-rendered Llama report text. |
| **10. System Integration & Architecture**| Modern web app, FastAPI, Supabase DB & Storage, atomic dispatch, tests. | **READY** | Primary product workspace, Migrations 001–004, 150 passed pytest tests. | None |
| **11. Limitations & Ethics** | Fail-closed safety, privacy pseudonymization, amateur coaching ethics. | **READY** | `AGENTS.md`, `research.tsx`, identity withholding contracts. | None |

---

## 14. Visualization and Graph Inventory

The following 8 figures should be plotted for the final report from verified CSV/JSON data:

| Fig # | Proposed Figure Title | Core Scientific Question Answered | Source Artifact Path | Metrics / Fields Required | Report Section |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | **Overall Vision Benchmark Performance** | How do M1, M2, and M3 compare across standardized tracking metrics? | `methodology_comparison/final_evaluation/whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv` | HOTA, DetA, AssA, MOTA, IDF1, Precision, Recall | Chapter 5 |
| **2** | **Per-Clip HOTA Across Challenge Scenarios** | How does tracking robustness vary across Re-entry, Occlusion, Interaction, and Long Gaps? | `.../whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_PER_CLIP_METRICS.csv` | Per-clip HOTA and MOTA across 4 sequences | Chapter 5 |
| **3** | **Identity Switches and Error Types** | Why does M2 achieve superior identity consistency compared to M1? | `.../whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_IDENTITY_SAFETY.json` | IDSW, FP, FN counts | Chapter 5 |
| **4** | **ASR Model Comparison: Error Rates & Event Recall** | Why was Faster-Whisper base.en selected over Parakeet TDT v2? | `methodology_comparison/asr/model_selection/ASR_CANDIDATE_A_VS_B_FINAL_COMPARISON.csv` | WER, CER, Tactical Event Recall, F1 score | Chapter 6 |
| **5** | **LLM Benchmark: Schema Compliance & Repeatability** | Why did Llama 3.1 8B decisively win over Qwen3:8B? | `methodology_comparison/llm/LLM_FORMAL_BENCHMARK_COMPARISON.md` | Schema pass rate, timeout rate, repeatability % | Chapter 7 |
| **6** | **Camera Homography Reprojection Accuracy** | What is the metric uncertainty of the single-camera homography? | `config/3v3_homography_measured_metric_corrected.json` | Landmark residual error (m), RMSE = 0.651m | Chapter 8 |
| **7** | **C06 Pressing Response Kinematics** | How did player RED_01 close down opponent BLACK_03? | `experiments/capability_showcase/metric_extensions_corrected/C06_pressing_metric/C06_metric_evidence.json` | Timestamp vs distance (m) and closing speed (km/h) | Chapter 9 |
| **8** | **System Architecture & Dataflow Diagram** | How does media flow from browser upload to grounded report? | `FINAL_ARCHITECTURE_PRE_INTEGRATION_AUDIT.md` (ASCII Diagram) | Architectural blocks and security gates | Chapter 10 |

---

## 15. Stale / Superseded Artifact List

1. **Obsolete Research Frontend (`G:\My Drive\Football_Training_Assistant_MVP\frontend/`)**:
   - Contains `index.html`, `index.css`, `app.js`. Obsolete vanilla JS prototype. Must NEVER overwrite primary product frontend.
2. **Obsolete Research Server (`G:\My Drive\Football_Training_Assistant_MVP\backend/server.py`)**:
   - Monolithic prototype script. Superseded by primary `backend/app/main.py`.
3. **Stale Model Manifest Reference (`backend/app/core/model_manifest.yaml`, Line 96)**:
   - Lists `qwen3:8b`. Must be updated to `llama3.1:8b` (digest `46e0c10c...`).
4. **Historical Showcase Generation Artifacts (`05_final_showcase/`)**:
   - `showcase_final_coach_report.md` and `showcase_grounding_validation.json` reflect `qwen3:8b` generation. Must be revalidated with Llama 3.1.
5. **Primary Backend Stubs (`backend/app/pipeline/*.py`)**:
   - All modules except `detection.py` raise `NotImplementedError`. Must be replaced with adapted research logic.
6. **Frontend Preview Routes (`analysis.processing.tsx`, `results.tsx`)**:
   - Static preview mock pages. Must be cleaned up or redirected.

---

## 16. Exact Final Integration Gap List

### P0 — Must Complete Before Final End-to-End System Test

- **GAP-P0-1: Tri-Methodology Vision Executors Implementation**:
  - *Location*: Primary workspace: [`backend/app/pipeline/tracking.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/tracking.py), [`registry.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/registry.py).
  - *Current State*: `tracking.py` raises `NotImplementedError`; `registry.py` returns HTTP 409.
  - *Required Change*: Implement `M1Executor` (YOLO11m + BoT-SORT), `M2Executor` (RF-DETR + GTA-Track), and `M3Executor` (YOLO26 + SriTrack) adapting code from research workspace. Set `DEFAULT_VISION_METHOD = M2_GLOBAL_ASSOCIATION`.
  - *Risk*: Without this, no vision analysis can execute.
- **GAP-P0-2: ASR Pipeline Adaptation**:
  - *Location*: Primary workspace: [`backend/app/pipeline/audio.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/audio.py), [`instructions.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/instructions.py).
  - *Current State*: Stubs raising `NotImplementedError`.
  - *Required Change*: Port `ASRPipeline` from `Football_Training_Assistant_MVP/backend/pipeline/asr.py` (`faster-whisper base.en` CPU int8, Silero VAD, tactical keyword classifier).
  - *Risk*: Without this, coach audio cannot be transcribed or converted to tactical events.
- **GAP-P0-3: Multimodal Fusion Engine Adaptation**:
  - *Location*: Primary workspace: [`backend/app/pipeline/fusion.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/fusion.py).
  - *Current State*: Stub raising `NotImplementedError`.
  - *Required Change*: Port `FusionEngine` from research `fusion.py` (spatio-temporal evaluation windows, spatial zone assignment, fail-closed withholding of individual player analytics).
  - *Risk*: Without this, vision and audio cannot be linked.
- **GAP-P0-4: LLM Reporting & Patch 001 Grounding Validator Adaptation**:
  - *Location*: Primary workspace: [`backend/app/pipeline/reporting.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/reporting.py), [`evidence.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/evidence.py).
  - *Current State*: Stubs raising `NotImplementedError`.
  - *Required Change*: Port `ReportEngine`, `LLMClient`, and `validate_grounding` from research `reporter.py`, `llm_client.py`, `validator.py`. Enforce `llama3.1:8b`, prompt SHA `ab95a835...`, and deterministic markdown fallback.
  - *Risk*: Without this, coaching reports cannot be generated or validated.
- **GAP-P0-5: Modal GPU Worker Container Configuration**:
  - *Location*: Primary workspace: [`modal_app/worker.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/modal_app/worker.py), `requirements-modal.txt`.
  - *Current State*: CPU-only smoke harness without AI inference packages.
  - *Required Change*: Add NVIDIA T4 GPU specification, PyTorch/CUDA, CTranslate2, Faster-Whisper, and Ultralytics dependencies. Wire worker to invoke the integrated pipeline.
  - *Risk*: Jobs cannot be executed in the cloud.

### P1 — Must Complete Before Final Submission

- **GAP-P1-1: Model Manifest Synchronization**:
  - *Location*: Primary workspace: [`backend/app/core/model_manifest.yaml`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/core/model_manifest.yaml).
  - *Current State*: Line 96 references `qwen3:8b`.
  - *Required Change*: Update to `llama3.1:8b` (digest `46e0c10c...`), prompt SHA `ab95a835...`, and declare `M2_GLOBAL_ASSOCIATION` as default vision method.
- **GAP-P1-2: Frontend Upload Wizard Methodology Selector**:
  - *Location*: Primary workspace: [`src/routes/analysis.new.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.new.tsx).
  - *Current State*: Upload wizard has no methodology choice.
  - *Required Change*: Add selectable dropdown: `AUTO (Recommended: M2 Global Association)`, `M1 (Original Hybrid)`, `M2 (Global Association)`, `M3 (Re-entry Focused)`. Pass selection to `/api/v1/jobs`.
- **GAP-P1-3: Frontend Showcase Live API Wiring**:
  - *Location*: Primary workspace: [`src/routes/showcase.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/showcase.tsx).
  - *Current State*: Uses hardcoded mock cards.
  - *Required Change*: Connect React Query to fetch live cases from `/api/v1/showcase` and display verified overlay videos.
- **GAP-P1-4: Oracle Showcase Revalidation**:
  - *Location*: Primary workspace: [`golden/fixtures/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/golden/fixtures/).
  - *Current State*: Generated by `qwen3:8b`.
  - *Required Change*: Re-render report text through `llama3.1:8b` with Patch 001 validator, format into canonical `AnalysisResult` schema, and update fixture JSON.

### P2 — Important Hardening

- **GAP-P2-1: Python Runtime Standardization**:
  - Standardize local development virtual environment from 3.8.10 to 3.10+ to match Modal and backend contracts.
- **GAP-P2-2: Frontend Legacy Routes Cleanup**:
  - Deprecate or remove `/analysis/processing` and `/results` preview routes.

### P3 — Optional / Future Work

- **GAP-P3-1: Multi-Tenant Authentication UI**:
  - Implement full Supabase Auth UI (signup, login, JWT verification) in place of development tenant mode.

---

## 17. Proposed Revalidation Sequence

1. **Step 1: Synchronize Model Manifest**: Update `backend/app/core/model_manifest.yaml` to lock `llama3.1:8b` and declare `DEFAULT_VISION_METHOD = M2_GLOBAL_ASSOCIATION`.
2. **Step 2: Port Research Pipeline Modules**: Adapt `asr.py`, `homography.py`, `fusion.py`, `validator.py`, and `reporter.py` into primary `backend/app/pipeline/`.
3. **Step 3: Implement Vision Methodology Executors**: Implement `M1Executor`, `M2Executor`, and `M3Executor` in `backend/app/pipeline/tracking.py` and register them in `MethodologyExecutorRegistry`.
4. **Step 4: Revalidate Oracle Showcase**: Re-run showcase evidence through Llama 3.1 8B with Patch 001 validator, update `golden/fixtures/` with canonical `AnalysisResult` JSON.
5. **Step 5: Wire Frontend Components**:
   - Add methodology selector to `src/routes/analysis.new.tsx`.
   - Wire `src/routes/showcase.tsx` to `/api/v1/showcase`.
6. **Step 6: Upgrade Modal Worker**: Add GPU environment and pipeline execution to `modal_app/worker.py`.
7. **Step 7: Execute End-to-End System Smoke Test**: Run a complete match video through the browser UI, confirming direct upload, ffprobe validation, atomic dispatch, worker execution, fail-closed identity withholding, and live UI dashboard rendering.

---

## 18. Exact Next Engineering Action

$$\mathbf{NEXT\_ACTION: UPDATE\_MODEL\_MANIFEST\_AND\_PORT\_PIPELINE\_MODULES}$$

The immediate next step is to update `backend/app/core/model_manifest.yaml` with the frozen Llama 3.1 8B digest and prompt hash, followed by porting the tested research pipeline modules (`asr.py`, `homography.py`, `fusion.py`, `validator.py`, `reporter.py`) into the primary `backend/app/pipeline/` package.

---

## 19. Risks and Scientific Limitations

1. **Scientific Boundary Invariant**:
   - Automated persistent identity across full sessions remains mathematically unsolved (`FAIL_HIGH_FRAGMENTATION`).
   - The system must NEVER emit invented or ungrounded individual player metrics. All real session analyses must return `COMPLETED_WITH_LIMITATIONS`.
2. **Single-Camera Perspective Ambiguity**:
   - Planar homography mapping carries an independent RMSE of 0.651m. Footpoint occlusions during crowd scenes can induce transient positional jitter.
3. **Compute Cold Start & Latency**:
   - A complete 5-minute video processing run (YOLO slicing + M2 tracking + Faster-Whisper + Llama 3.1 generation) takes approximately 100–120s on an NVIDIA GPU. Progress heartbeat callbacks are essential to prevent HTTP gateway timeouts.

---

## 20. Final Audit Disposition

$$\mathbf{AUDIT\_VERDICT: PASS\_COMPLETE\_REVALIDATION\_BASELINE\_ESTABLISHED}$$

The CM3070 project has completed all research and evaluation phases. The vision benchmark is definitively concluded with M2 as the default winner. The primary product workspace's control plane is mature, hardened, and verified with 150 passed tests. Final prototype closure requires only the controlled porting of the frozen research pipeline modules into the primary backend and Modal worker.
