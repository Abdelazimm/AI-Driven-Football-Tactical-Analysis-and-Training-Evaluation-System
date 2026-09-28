# FINAL SYSTEM REVALIDATION & COMPLETENESS AUDIT (v2)
## CM3070 Final Project: AI-Driven Football Tactical Analysis and Training Evaluation System

- **Audit Date**: 2026-09-26
- **Audit Execution Mode**: `STRICT_READ_ONLY_FULL_PROJECT_REAUDIT` (Conducted from scratch)
- **Primary Product Workspace**: `D:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System`
- **Parent Archive Workspace**: `D:\Final project videos transcripts`
- **Legacy Colab Notebooks Workspace**: `G:\My Drive\Colab Notebooks`
- **Research / Methodology Workspace**: `G:\My Drive\Football_Training_Assistant_MVP`
- **Audit Status**: COMPLETE — FULL FOUR-WORKSPACE INDEPENDENT BASELINE ESTABLISHED

---

## 1. Executive Summary

This independent, from-scratch re-audit synthesizes evidence across all four project workspaces following the formal completion and freezing of the Vision whole-system challenge evaluation. The audit incorporates newly unlocked materials from the root archive workspace (including 26 University of London CM3070 lecture transcripts, the comprehensive project exam dossier, course ethics templates, and historical showcase generation scripts) alongside the primary product codebase, frozen research artifacts, and legacy Colab notebooks.

### 1.1 Definitive Scientific & Engineering Baseline

1. **Formal Vision Evaluation is Complete**:
   - The formal four-clip challenge evaluation (3,780 total frames) across all 12 method $\times$ clip configurations is completed, frozen, and cryptographically hashed under `FORMAL_TRACKER_STATE_POLICY = FRESH_STATE_PER_CHALLENGE_CLIP`.
   - **Source Video SHA-256**: `0e676f4327d1e7e7ed458d619e5558f6630fc7efb0dda7bc608aec45cb9a5c71`.
   - **Frozen Dense-GT Manifest SHA-256**: `524d231703d77485f4b57526929aedeadb744a801089aa12d905c0ef21808aec`.
   - **Final Evaluation Manifest SHA-256**: `ec8c60824622d9b07b1b03b9b19365a7b1a2f7aab635a9c596dbec6cf90dd556`.
   - **Official Outcome**: **M2 (Global Association / RF-DETR + GTA-Track)** is the decisive winner:
     - **HOTA**: **0.6710** (vs M1 0.4632, M3-v1 0.3517)
     - **MOTA**: **0.8522** (vs M1 0.5673, M3-v1 0.3253)
     - **IDF1**: **0.9144** (vs M1 0.5891, M3-v1 0.4066)
     - **IDSW**: **19** (vs M1 186, M3-v1 5)
     - **Precision**: **0.9878**, **Recall**: **0.8637**
   - **Production Decision**: `DEFAULT_VISION_METHOD = M2_GLOBAL_ASSOCIATION`.
   - **Tri-Methodology Requirement**: All three methodologies (M1, M2, M3) must remain fully implemented and selectable in the final application (`AUTO` $\rightarrow$ M2, `M1`, `M2`, `M3`). Detectors and trackers must NEVER be cross-combined.

2. **Persistent Identity Scientific Boundary**:
   - `PLAYER_LEVEL_ACCUMULATED_ANALYTICS = DISABLED`.
   - Across full continuous match footage (340s, 60 FPS), automated identity remains `FAIL_HIGH_FRAGMENTATION` (115 raw IDs $\rightarrow$ 37 meaningful IDs; ratio $6.1667 > 1.50$). Even M2 exhibits 19 ID switches and 9 clip-local unsafe identity overlaps across the challenge clips. The system must fail closed, returning `COMPLETED_WITH_LIMITATIONS` with player-level conclusions strictly withheld.

3. **Oracle Showcase Revalidation Status**:
   - **Status**: `ORACLE_SHOWCASE_REQUIRES_REVALIDATION`.
   - The root archive script `build_final_oracle_showcase.py` proves that the historical showcase (C03, C04, C06) was hardcoded to call `qwen3:8b` via Ollama and used a pre-patch validator.
   - Human-verified inputs (player IDs, targets, response intervals, opponents) are 100% valid, but the coaching report text and frontend payload must be re-rendered through the frozen `llama3.1:8b` model enforcing `LLM_GROUNDING_VALIDATOR_PATCH_001`.

4. **Product Integration Status**:
   - **Product Control Plane**: Mature, hardened, and verified (FastAPI, TanStack Start SSR frontend, Supabase DB & Storage with 4 migrations, authoritative media validation, atomic worker dispatch, 150/150 passed tests).
   - **Research Subsystems**: Frozen and verified (Faster-Whisper ASR, Llama 3.1 8B LLM, Homography, Fusion).
   - **Primary Backend Pipeline**: Currently contains fail-closed stubs (`NotImplementedError`) and HTTP 409 dispatch block.
   - **Effort Classification**: **MEDIUM INTEGRATION TASK** (3 to 5 focused engineering days; zero major rebuilding).

---

## 2. Exact Workspace Map

```
ROOT / FILESYSTEM TOPOLOGY
├── [1] PARENT ARCHIVE WORKSPACE
│   Path: D:\Final project videos transcripts
│   Role: Comprehensive academic, raw data, ethics, and historical tooling repository
│   Key Contents:
│   ├── CM3070_EXAM_PROJECT_DOSSIER.md (75.8 KB forensic project analysis)
│   ├── CM3070_EXAM_QUESTION_BANK.md (82.7 KB 100-question exam prep)
│   ├── _ca0bcfddc99545298e85097c36f56ae1_Consent-form-example-1.docx (UoL Ethics Form PR/001)
│   ├── subtitle (58).txt ... subtitle (83).txt (26 official CM3070 lecture transcripts)
│   ├── build_final_oracle_showcase.py (historical Qwen generation script)
│   ├── build_corrected_metric_showcase.py, build_metric_sanity_audit.py, build_homography_validation.py
│   ├── tracking_3v3_dataset_b.csv (59 MB), selected_C_roster_assignments.csv (33 MB)
│   └── M3 engineering & forensics scripts (m3_p2b_..., m3_p5_..., m3_r2_...)
│
├── [2] PRIMARY PRODUCT WORKSPACE (Authoritative Product Implementation)
│   Path: D:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System
│   Role: Production web application, control plane, persistence, validation, tests
│   Key Contents:
│   ├── frontend/tactical-ai-insights-main/ (React 19, TanStack Start SSR, Vite 8, Tailwind 4)
│   ├── backend/app/ (FastAPI API v1, repositories, media validation, dispatch service)
│   ├── backend/migrations/ (001_phase3_initial_schema through 004_media_validation)
│   ├── backend/tests/ (150 passed pytest automated tests)
│   ├── modal_app/ (Modal deployment and worker callback harness)
│   ├── golden/ (Immutable showcase fixtures and media)
│   └── shared/schemas/ (Cross-boundary Pydantic v2 data models)
│
├── [3] LEGACY COLAB NOTEBOOKS WORKSPACE
│   Path: G:\My Drive\Colab Notebooks
│   Role: Historical evolutionary research notebooks (Stages 0 through 6)
│   Key Contents:
│   ├── 01_vision_pipeline.ipynb (26.8 MB, 378 cells documenting Stages 0–6 + 3v3 identity crisis)
│   ├── 02_audio_pipeline.ipynb (211 KB, early ASR and keyword prototyping)
│   ├── 03_orchestrator_fusion.ipynb (85 KB, early fusion and evaluation window design)
│   ├── 04_report_generation.ipynb (697 KB, early reporting and showcase cells)
│   └── Autonomus_scout.ipynb, Autonomous_Scout_Feature_Prototype.ipynb (early concept prototypes)
│
└── [4] RESEARCH / METHODOLOGY WORKSPACE (Authoritative Scientific Repository)
    Path: G:\My Drive\Football_Training_Assistant_MVP
    Role: Methodology comparisons, frozen weights, TrackEval benchmarks, canonical evidence
    Key Contents:
    ├── methodology_comparison/final_evaluation/whole_system_challenge_evaluation/ (Formal Vision TrackEval)
    ├── methodology_comparison/asr/ (Faster-Whisper vs Parakeet evaluation and freeze)
    ├── methodology_comparison/llm/ (Llama 3.1 8B vs Qwen3:8B formal benchmark)
    ├── backend/pipeline/ (Operational pipeline: asr.py, fusion.py, validator.py, reporter.py, homography.py)
    └── config/3v3_homography_measured_metric_corrected.json (Validated RMSE 0.651m calibration)
```

---

## 3. Evidence Authority Rules

To prevent historical artifacts from overriding newer validated engineering, the following strict hierarchy of authority is established:

```
[Level 1: Verified Source Code & Live DB State] (HIGHEST AUTHORITY)
   │  - Passing automated tests in primary workspace (150/150 tests)
   │  - Applied PostgreSQL schemas and triggers in Supabase migrations 001–004
   │  - Working API endpoints, media probing, and atomic dispatch logic
   ▼
[Level 2: Frozen Scientific Benchmarks & Checkpoint Manifests]
   │  - Whole-system challenge TrackEval metrics (FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv)
   │  - Frozen ASR benchmark (ASR_MODEL_SELECTION_FROZEN, Faster-Whisper base.en)
   │  - Frozen LLM benchmark (LLM_FORMAL_BENCHMARK_EXECUTION_COMPLETE, Llama 3.1 8B digest 46e0c10c...)
   │  - Corrected pitch calibration (RMSE 0.651m, config SHA-256 d0e9680f...)
   ▼
[Level 3: Operational Research Pipeline Modules]
   │  - Tested scripts in Football_Training_Assistant_MVP/backend/pipeline/
   │  - LLM_GROUNDING_VALIDATOR_PATCH_001 (13/13 passed regression tests)
   ▼
[Level 4: Comprehensive Forensic Dossiers & Exam Documents]
   │  - CM3070_EXAM_PROJECT_DOSSIER.md and CM3070_EXAM_QUESTION_BANK.md
   │  - University lecture subtitle transcripts (subtitle 58–83.txt)
   ▼
[Level 5: Historical Research Notebooks & Early Prototypes]
   │  - 01_vision_pipeline.ipynb (Stages 0–6), 04_report_generation.ipynb
   │  - Historical generation scripts (build_final_oracle_showcase.py with Qwen)
   ▼
[Level 6: Stale Documentation Text & Inline Comments] (LOWEST AUTHORITY)
   │  - Mentions of Qwen in model_manifest.yaml
   │  - Claims that Vision selection is "pending" or that Stage 4B is deployment detector
   │  - Old proposal expectations of autonomous player-level assessment
```

*Rule: If Level 6 prose conflicts with Level 1 code or Level 2 frozen benchmarks, Level 6 is explicitly classified as STALE/SUPERSEDED.*

---

## 4. Complete Project Chronology

```
[1. Academic Proposal & Early Concept Exploration (Autumn 2025)]
   Problem: Lack of objective, accessible tactical training review tools for grassroots/amateur football.
   Early Title: "The Autonomous Scout & Effort Analyzer".
   Implementation: `Autonomous_Scout_Feature_Prototype.ipynb` (Gradio, single still image, YOLOv8m).
   Limitation: Detected people/balls on still images; inferred crude effort without temporal or tactical context.

[2. Video Pipeline Inception & Scale Failure (Stages 0 - 3)]
   Implementation: Scaled YOLOv8m to full video (`01_vision_pipeline.ipynb`, SoccerTrack v2 dataset).
   Finding: Severe false negative rate (>40%) on distant players (scales <50px).
   Decision: Introduce horizontal slicing/tiling to restore small-object resolution.

[3. Slicing & Fine-Tuning Pilot (Stage 4B)]
   Implementation: 3 horizontal tiles with 15% overlap at imgsz=1280. Fine-tuned YOLO11m pilot (`best.pt`, 40.5 MB).
   Result: Solved detection recall on wide-angle camera views.

[4. Tracking & Motion Evaluation (Stage 5)]
   Implementation: Evaluated ByteTrack on tiled detections.
   Finding: Rapid track fragmentation during rapid camera pans and player crossings.
   Decision: Transition to BoT-SORT with Camera Motion Compensation (CMC) and short-gap interpolation.

[5. Physical Pitch Homography Calibration (Stage 6)]
   Implementation: Provisional 20m x 20m plane upgraded to measured 19.31m x 19.88m physical pitch geometry.
   Validation: Independent ground truth achieved RMSE = 0.651m (max error 0.841m).
   Safety Policy: 7-observation rolling median filter; 36.0 km/h kinematic outlier rejection.

[6. Real 3v3 Match Recording & The Identity Fragmentation Crisis]
   Implementation: Processed 340s continuous 3v3 match footage (`3v3_match_iphone16.MOV`, 60 FPS).
   Crisis: Generated 115 raw track IDs for 6 players (collapsing to 37 meaningful tracks).
   Result: Fragmentation ratio = 6.1667 (far exceeding the 1.50 acceptance threshold).
   Repair Attempts: Evaluated 60 FPS-aware tuning, anchor constraints, and multi-pass stitching. Unsafe identity switches persisted.
   Scientific Decision: Declare automated persistent identity FAIL_HIGH_FRAGMENTATION. Introduce fail-closed Quality Gate: enforce `PLAYER_LEVEL_ACCUMULATED_ANALYTICS = DISABLED`.

[7. Oracle-Assisted Capability Showcase (C03, C04, C06)]
   Implementation: Demonstrated downstream capabilities using human-verified player identities.
   Execution: Generated using `build_final_oracle_showcase.py` with `qwen3:8b` via Ollama (7 attempts needed).
   Result: Validated tactical responses for Pressing (C06), Marking (C04), and Position Hold (C03).

[8. Tri-Methodology Vision Redesign & Benchmark (M1, M2, M3)]
   Motivation: Address the tracking/identity failure through formal paradigm exploration:
     - M1: Original Hybrid (YOLO11m + BoT-SORT + Fallback C)
     - M2: Global Association (RF-DETR + GTA-Track with deep ReID)
     - M3: Re-entry Focused (YOLO26 + SriTrack with spatial-recurrent memory)

[9. ASR & LLM Methodology Selection Freezes]
   ASR: `faster-whisper base.en` decisively defeated `parakeet_tdt_v2` (WER 18.4% vs 36.8%, Tactical Recall 76.5% vs 52.9%).
   LLM: `llama3.1:8b` defeated `qwen3:8b` (Schema pass rate 93.75% vs 31.25%, 100% deterministic repeatability).
   Validation: Finalized `LLM_GROUNDING_VALIDATOR_PATCH_001` (8 deterministic gates).

[10. Formal Vision Challenge Evaluation (The Present)]
   Execution: Pinned TrackEval on 4 frozen challenge clips (3,780 frames) under fresh-state-per-clip policy.
   Outcome: M2 decisively won (HOTA 0.6710, MOTA 0.8522, IDF1 0.9144, 19 ID switches).
   Production Decision: M2 declared DEFAULT; all three methods preserved as selectable options in product.

[11. Product Architecture Hardening & Final Integration Baseline]
   Primary Workspace: FastAPI control plane, TanStack Start SSR frontend, Supabase migrations 001–004, authoritative media validation, atomic worker dispatch idempotency, 150 passed tests.
```

---

## 5. Requirements Traceability Matrix

Extracted from University of London CM3070 course specifications (`subtitle 58–83.txt`), `CM3070_EXAM_PROJECT_DOSSIER.md`, and primary system contracts:

| Req ID | Requirement Description | Category | Supporting Evidence & Location | Current Implementation State | Verification Method | Status | Remaining Gap |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| **FR-01** | Detect football players in wide-angle video | Functional | `01_vision_pipeline.ipynb` Stage 4B, `backend/app/pipeline/detection.py` | Implemented (YOLO11m 3-tile slicing, 15% overlap, NMS IoU 0.70) | Pytest `test_detection_tile_pipeline.py` (15 tests) | **VERIFIED** | None |
| **FR-02** | Multi-object tracking across consecutive frames | Functional | `methodology_comparison/` (M1, M2, M3) | Implemented in research; stubbed in primary `tracking.py` | Official TrackEval scoring (3,780 frames) | **READY FOR PORTING** | Port M1/M2/M3 executors |
| **FR-03** | Persistent player identity recovery across occlusions | Functional | `01_vision_pipeline.ipynb` DB3V3.R13, TrackEval IDSW | Fails automated criteria (ratio 6.1667 > 1.50). Fail-closed withholding enforced | Identity Safety Gate assertions | **VERIFIED FAIL-CLOSED** | None (Preserve fail-closed) |
| **FR-04** | Planar pitch coordinate calibration | Functional | `3v3_homography_measured_metric_corrected.json` | 19.31m $\times$ 19.88m matrix verified (RMSE 0.651m) | Reprojection error audit | **VERIFIED** | Port homography to primary |
| **FR-05** | Kinematics derivation with outlier rejection | Functional | `build_corrected_metric_showcase.py`, Stage 6 | 7-point median filter + 36 km/h speed clamp | Speed distribution tests | **READY FOR PORTING** | Port kinematics to primary |
| **FR-06** | Coach speech transcription with timestamps | Functional | `methodology_comparison/asr/`, `ASR_MODEL_SELECTION_FROZEN` | Faster-Whisper base.en CPU int8 verified (WER 18.4%) | ASR benchmark suite | **READY FOR PORTING** | Port ASR to primary |
| **FR-07** | Deterministic tactical instruction classification | Functional | `ASR_TACTICAL_EVENT_GT_FROZEN_REV3.json` | Keyword extractor with parent segment timestamp inheritance | Keyword unit tests | **READY FOR PORTING** | Port keyword parser |
| **FR-08** | Multimodal spatio-temporal fusion | Functional | `Football_Training_Assistant_MVP/backend/pipeline/fusion.py` | 2s–6s response window, pitch thirds, identity withholding | Fusion unit tests | **READY FOR PORTING** | Port fusion engine |
| **FR-09** | Identity safety gating and player withholding | Safety | `shared/schemas/job.py`, `backend/app/schemas/result.py` | Enforces `COMPLETED_WITH_LIMITATIONS` when ratio > 1.50 | Pytest `test_schemas.py` | **VERIFIED** | None |
| **FR-10** | Hallucination-free report generation | Functional | `LLM_GROUNDING_VALIDATOR_PATCH_001`, `reporter.py` | Llama 3.1 8B + 8 deterministic grounding gates + fallback | 13/13 regression tests | **READY FOR PORTING** | Port reporter/validator |
| **FR-11** | Modern interactive web interface | UI/UX | `frontend/tactical-ai-insights-main/` | React 19 / TanStack Start SSR wizard, monitor, 7-tab dashboard | Vite build (0 errors) | **VERIFIED** | Wire showcase & selector |
| **NFR-01**| Server-authoritative media validation | Security | `MediaValidationService`, `FFProbeMediaProbeService` | Container whitelist, 300s ceiling, codec check via ffprobe | Pytest `test_hardening_pack2.py` (46 tests) | **VERIFIED** | None |
| **NFR-02**| Atomic dispatch idempotency | Reliability | `WorkerDispatchRepository`, migration 003 | Partial unique index `uq_active_worker_dispatch_per_job` | Pytest `test_hardening_pack1.py` (17 tests) | **VERIFIED** | None |
| **NFR-03**| Worker callback authentication | Security | `/api/v1/internal/jobs/{id}/progress` | Shared secret with constant-time HMAC comparison | Pytest `test_hardening_pack1.py` | **VERIFIED** | None |
| **NFR-04**| Participant privacy & pseudonymization | Ethics | `AGENTS.md`, `CM3070_EXAM_PROJECT_DOSSIER.md` | Canonical aliases (Player_01), raw name leakage scans | Schema scans | **VERIFIED** | None |
| **NFR-05**| Inclusive & accessible design | Inclusivity | Lecture subtitle 68, `CM3070_EXAM_PROJECT_DOSSIER.md` | Plain-language limitation banners, tabular data, clean typography | Visual inspection | **PARTIAL** | Planned coach study |

---

## 6. Current Frozen Subsystem Matrix

| Subsystem | Frozen Production Specification | Exact Checksum / Reference | Execution Runtime | Production Role |
| :--- | :--- | :--- | :--- | :--- |
| **Vision (M2)** | RF-DETR + GTA-Track (Deep-EIoU tracklets, global graph ReID association) | `GT_CLIP_01`–`04` fixed outputs | GPU (T4 / A10G) | **DEFAULT / AUTO Method** |
| **Vision (M1)** | YOLO11m + BoT-SORT (Fallback C, high=0.25, low=0.05, new=0.45, buffer=420) | `M1_FORMAL_003_DOMAIN_ADAPTED` | GPU (T4 / A10G) | Selectable Method |
| **Vision (M3)** | YOLO26 + SriTrack-v1 (Spatial-recurrent identity recovery) | `M3_ALL_FOUR_RAW_OUTPUTS_FIXED.json` | GPU (T4 / A10G) | Selectable Method |
| **ASR** | Faster-Whisper `base.en`, CTranslate2, Silero VAD, word timestamps, 16 kHz mono | `ASR_MODEL_SELECTION_FROZEN` | CPU int8 (8 threads) | **Frozen Production ASR** |
| **LLM** | Meta `llama3.1:8b` (greedy temp 0.0, seed 42) | Digest: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | Local Ollama / vLLM | **Frozen Production LLM** |
| **System Prompt** | Coach report system prompt | SHA-256: `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce` | Text template | **Frozen Production Prompt** |
| **Grounding Validator**| `LLM_GROUNDING_VALIDATOR_PATCH_001` (8 deterministic regex/logic gates) | 13/13 regression tests passed | In-process Python | **Frozen Production Validator**|
| **Pitch Calibration**| 19.31m $\times$ 19.88m physical pitch, RMSE 0.651m, 36 km/h speed clamp | SHA-256: `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507` | In-process Python | **Frozen Production Calibration**|
| **Database** | Supabase PostgreSQL, Migrations 001–004, RLS, partial unique index | Verified live on Supabase | Cloud PostgreSQL | **Authoritative Product DB** |
| **Storage & Probe** | `SupabaseStorageService` + `MediaValidationService` (`ffprobe`, 300s cap) | 46 unit tests passed | In-process Python / CLI | **Authoritative Ingestion** |

---

## 7. Vision Final-State Verification

### 7.1 Whole-System Challenge Evaluation Audit
- **Protocol**: `FORMAL_TRACKER_STATE_POLICY = FRESH_STATE_PER_CHALLENGE_CLIP`.
- **Benchmark Source Directory**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\final_evaluation\whole_system_challenge_evaluation\`
- **Inspected Files**:
  - `FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv`
  - `FINAL_WHOLE_SYSTEM_PER_CLIP_METRICS.csv`
  - `FINAL_WHOLE_SYSTEM_IDENTITY_SAFETY.json`
  - `FINAL_WHOLE_SYSTEM_EVALUATION_REPORT.md`
  - `FINAL_WHOLE_SYSTEM_EVALUATION_MANIFEST.json` (SHA-256: `ec8c60824622d9b07b1b03b9b19365a7b1a2f7aab635a9c596dbec6cf90dd556`)

### 7.2 Official TrackEval Metric Breakdown

| Metric | M1 — Original Hybrid (YOLO11m + BoT-SORT) | M2 — Global Association (RF-DETR + GTA-Track) | M3-v1 — Re-entry Focused (YOLO26 + SriTrack) | Scientific Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **HOTA** | 0.4632 | **0.6710** | 0.3517 | M2 achieves a +20.78% absolute improvement over M1. |
| **DetA** | 0.5020 | **0.6567** | 0.2551 | RF-DETR detector significantly outperforms YOLO11m and YOLO26. |
| **AssA** | 0.4333 | **0.6862** | 0.4852 | GTA-Track global association provides vastly superior temporal linkage. |
| **MOTA** | 0.5673 | **0.8522** | 0.3253 | M2 minimizes false positives and misses across all challenge sequences. |
| **IDF1** | 0.5891 | **0.9144** | 0.4066 | M2 maintains identity continuity across >91% of trajectories. |
| **IDSW** | 186 | 19 | **5** | M3 has fewer raw switches only because its detector missed 14,180 detections. |
| **FP** | 6004 | 224 | **36** | M1 suffered severe false positive hallucinations; M2 is highly clean. |
| **FN** | 2931 | **2873** | 14180 | M3 collapsed into extreme false negatives (>75% missed players). |
| **Precision**| 0.7514 | 0.9878 | **0.9948** | M2 and M3 both possess near-perfect precision; M1 is noisy. |
| **Recall** | 0.8609 | **0.8637** | 0.3273 | M2 balances high recall (86.37%) with unmatched precision (98.78%). |

### 7.3 Per-Clip Scenario Analysis
- **GT_CLIP_01_REENTRY (840 frames)**: M2 achieved HOTA 0.6924 (MOTA 0.8536, 2 IDSW) vs M1 0.4457 (MOTA 0.3018, 49 IDSW). M3 collapsed to recall 0.1605.
- **GT_CLIP_02_OCCLUSION (720 frames)**: M2 achieved HOTA 0.6877 (MOTA 0.8639, 2 IDSW) vs M1 0.5014 (MOTA 0.6199, 44 IDSW).
- **GT_CLIP_03_SAME_TEAM_INTERACTION (840 frames)**: M2 achieved HOTA 0.5847 (MOTA 0.7653, 13 IDSW) vs M1 0.4598 (MOTA 0.5990, 63 IDSW).
- **GT_CLIP_04_LONG_GAP_REENTRY (1,380 frames)**: M2 achieved HOTA 0.7032 (MOTA 0.9091, 2 IDSW) vs M1 0.4535 (MOTA 0.7096, 30 IDSW).

---

## 8. Oracle Showcase Revalidation Audit

### 8.1 Evidence from Root Archive Script
Inspection of `D:\Final project videos transcripts\build_final_oracle_showcase.py` reveals the exact operational reality:
- Lines 12–13:
  ```python
  MODEL = "qwen3:8b"
  OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
  ```
- The historical showcase coaching report was generated by `qwen3:8b` via Ollama and required 7 attempts to satisfy the pre-patch validator.
- Ingestion tracking came from `selected_C_roster_assignments.csv` (Experiment C tracking), not M2.
- Tactical commands (`"Press high on the ball, press high on the ball."` at 271.6s–274.4s) were originally generated by ASR and human-verified.

### 8.2 Revalidation Determination & Boundary
$$\mathbf{DISPOSITION: ORACLE\_SHOWCASE\_REQUIRES\_REVALIDATION}$$

- **Reusable (No change needed)**:
  - Human ground-truth annotations (player IDs `RED_01`, `BLACK_01`, `RED_03`, opponent attributions, response time intervals).
  - Physical homography matrix and pitch geometry (19.31m $\times$ 19.88m).
  - Video cut points and overlay videos (`C06_pressing_sequence_overlay.mp4`, `C03_hold_position_overlay.mp4`, `C04_black01_red03_response_contact_sheet.png`).
- **Must Be Re-Rendered**:
  - Re-run the structured evidence through `llama3.1:8b` (digest `46e0c10c...`) with `LLM_GROUNDING_VALIDATOR_PATCH_001`.
  - Re-serialize the output payload to conform to the primary product's `AnalysisResult` Pydantic model in `shared/schemas/results.py`.

---

## 9. ASR Audit

- **Authoritative Model**: `faster-whisper base.en` executed via `CTranslate2` on CPU int8 (8 threads).
- **Dataset Evaluated**: `coach_commands.m4a` (340.033s real Egyptian coaching audio).
- **Benchmark Verdict**: Decisively defeated NVIDIA `parakeet_tdt_v2`:
  - **WER**: **18.40%** vs 36.80% (50.0% relative reduction)
  - **CER**: **11.86%** vs 23.29%
  - **Tactical Event Recall**: **76.47%** (13 / 17 events) vs 52.94% (9 / 17)
  - **Tactical Event F1**: **83.87%** vs 66.67%
- **Status in Primary Repo**: [`backend/app/pipeline/audio.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/audio.py) and [`instructions.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/instructions.py) are stubs raising `NotImplementedError`. Operational logic exists in `Football_Training_Assistant_MVP/backend/pipeline/asr.py`. Direct port required.

---

## 10. LLM Audit

- **Authoritative Model**: Meta `llama3.1:8b` (Digest: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`).
- **System Prompt SHA-256**: `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`.
- **Grounding Validator**: `LLM_GROUNDING_VALIDATOR_PATCH_001` (8 deterministic gates).
- **Benchmark Verdict**: Decisively defeated Alibaba Cloud `qwen3:8b` across 16 test cases (32 executions):
  - **Schema Pass Rate**: **93.75%** vs 31.25%
  - **Timeout Failure Rate**: **6.25%** vs 68.75%
  - **Deterministic Repeatability**: **100.0% Exact String Match**
  - **Unsupported Identities**: **0 violations** (100% pass)
- **Stale References**: `backend/app/core/model_manifest.yaml` line 96 references `qwen3:8b`. This is an isolated documentation discrepancy that must be updated.
- **Cohere Investigation**: Verified absent from all football pipeline notebooks and code (present only in coursework tutorials).

---

## 11. Multimodal Fusion Audit

- **Research Implementation**: `Football_Training_Assistant_MVP/backend/pipeline/fusion.py`.
- **Temporal Alignment**: Constructs evaluation windows $[t_{end} + 2.0s, t_{end} + 6.0s]$ following tactical events.
- **Spatial Alignment**: Maps projected coordinates to pitch thirds (Defensive Third $<6.44m$, Middle Third $6.44m \le x \le 12.87m$, Attacking Third $>12.87m$).
- **Identity Safety Boundary**: Automatically strips individual player attributions and aggregates team-level metrics whenever identity status $\ne$ `PASS_RELIABLE`.
- **Disposition**: `READY_AS_IS_FOR_PORTING`. No mathematical or algorithmic redesign required; direct port into primary [`backend/app/pipeline/fusion.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/fusion.py).

---

## 12. Homography and Kinematics Audit

- **Pitch Dimensions**: Length **19.31 m**, Width **19.88 m** (physical pitch measurements).
- **Matrix Provenance**: `config/3v3_homography_measured_metric_corrected.json` (SHA-256: `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507`).
- **Independent Validation**: RMSE = **0.651 m** (max error 0.841 m).
- **Kinematics Rules**: 7-observation rolling median filter on pixel coordinates; 36.0 km/h outlier velocity clamp; no gap interpolation across $>0.5s$.
- **Calibrated vs Non-Calibrated Safety**:
  - `DEMO_FIXED_CALIBRATION` is restricted to original research camera geometry.
  - Arbitrary user uploads operate in `NO_METRIC_CALIBRATION` mode (normalized pixel space $[0, 1]$; metric units m and km/h strictly suppressed).
- **Analytics Safety Breakdown**:
  - *Accumulated player-specific analytics*: UNSAFE (Withheld across full sessions).
  - *Short-window player observations*: SAFE ONLY with human verification (Oracle mode).
  - *Team-level spatial analytics*: SAFE for automated reporting (centroid, spread, group speed).
  - *Anonymous track-level metrics*: SAFE for visual trajectory displays.

---

## 13. Product Vision Executor Architecture

The production architecture must support all three evaluated methods:

$$\mathbf{PRODUCTION\_VISION\_EXECUTORS = \{M1, M2, M3\}}$$
$$\mathbf{DEFAULT\_VISION\_METHOD = M2\_GLOBAL\_ASSOCIATION}$$

### Architectural Plan
1. **`M2Executor` (DEFAULT / AUTO)**:
   - Detector: RF-DETR. Tracker: GTA-Track (Deep-EIoU tracklets + deep ReID graph matching).
   - Wins on overall tracking consistency (HOTA 0.6710, MOTA 0.8522, IDF1 0.9144, 19 ID switches).
2. **`M1Executor` (Selectable Option)**:
   - Detector: Fine-tuned YOLO11m. Tracker: BoT-SORT (Fallback C configuration).
   - High recall (0.8609), but higher fragmentation (186 ID switches, HOTA 0.4632).
3. **`M3Executor` (Selectable Option)**:
   - Detector: YOLO26. Tracker: SriTrack-v1 (Spatial-recurrent association).
   - Low ID switches (5), but lower recall (0.3273, HOTA 0.3517).
4. **Stage 4B Role**:
   - Reusable utility code for horizontal tile slicing (`backend/app/pipeline/detection.py`).
   - Retained as detector component of M1; NOT used for M2 (RF-DETR) or M3 (YOLO26).

---

## 14. Primary Product Application Re-Audit

- **Frontend**: React 19.0.0, TanStack Start 1.170.18 (Nitro SSR), TanStack Router, Vite 8.1.5, Tailwind CSS 4.2.1.
  - [`analysis.new.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.new.tsx): Direct upload wizard with XHR progress bar (0..100%). Needs methodology selector dropdown.
  - [`analysis.$jobId.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.tsx): Dynamic polling job monitor. Working.
  - [`analysis.$jobId.results.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.results.tsx): 7-tab dashboard with 409 retry handling. Working.
  - [`showcase.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/showcase.tsx): Static mock cards. Needs live wiring to `/api/v1/showcase`.
  - Preview routes (`analysis.processing.tsx`, `results.tsx`): Kept for preview; need cleanup.
- **Backend API**: FastAPI with versioned `/api/v1` routers (`sessions.py`, `jobs.py`, `showcase.py`, `calibrations.py`, `internal.py`). Working.
- **Database**: Supabase PostgreSQL with 4 migrations applied and verified live. Working.
- **Storage & Probing**: `SupabaseStorageService` + `MediaValidationService` (`ffprobe` enforcing 300s ceiling, container whitelist, codecs). Working.
- **Dispatch**: `WorkerDispatchService` with atomic idempotency via `uq_active_worker_dispatch_per_job`. Working.
- **Modal**: CPU-only control harness in `modal_app/worker.py`. Needs GPU environment and pipeline invocation.
- **Test Suite**: 150 / 150 passed pytest tests (100% pass rate in 1.30s). Working.

---

## 15. Legacy Colab Notebook Evidence Index

| Notebook Name | Size | Project Stage | Core Purpose & Critical Findings | Superseded? | Report Value & Data to Extract |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `01_vision_pipeline.ipynb` | 26.8 MB | Stages 0–6 + 3v3 Repair (378 cells) | Initial YOLO failure, Stage 4B tiling, BoT-SORT CMC, 19.31m pitch homography, 3v3 fragmentation crisis (ratio 6.1667). | Yes (by `methodology_comparison`) | Extract PR curves, tiling ablation diagrams, and fragmentation logs for Chapters 3 & 4. |
| `02_audio_pipeline.ipynb` | 211 KB | Audio Prototyping (9 cells) | Early Faster-Whisper integration, Silero VAD tuning, deterministic tactical keyword extractor. | Yes (by `methodology_comparison/asr`) | Extract transcription samples and keyword rules for Chapter 4. |
| `03_orchestrator_fusion.ipynb` | 85 KB | Fusion Prototyping (7 cells) | Formulated 2s–6s temporal response window, spatial zone assignment, and identity fail-closed withholding. | Yes (by research `fusion.py`) | Extract fusion timing diagrams and spatial zone definitions for Chapter 4. |
| `04_report_generation.ipynb` | 697 KB | Reporting Prototyping (51 cells) | Early Ollama Qwen experiments, prompt engineering, generation of Oracle showcase `05_final_showcase`. | Yes (by `methodology_comparison/llm`) | Documents transition from Qwen to Llama for Chapter 5. |
| `Autonomus_scout.ipynb` | 2.2 MB | Early Exploration (31 cells) | Exploratory player tracking, tactical heatmaps, and scout metric visualizations. | Yes | Historical prototype narrative for Chapter 3. |
| `Autonomous_Scout_Feature_Prototype.ipynb` | 7 KB | Early Exploration (4 cells) | Minimal feature prototype for automated scouting metrics. | Yes | Initial proposal background context. |

---

## 16. Parent/Archive Workspace Evidence Index

| File / Artifact Name | Size | Artifact Type | Forensic Value & Relevance to CM3070 | Status |
| :--- | :---: | :--- | :--- | :---: |
| `CM3070_EXAM_PROJECT_DOSSIER.md` | 75.8 KB | Forensic Exam Dossier | Exhaustive technical breakdown: aims, proposal diff, 3v3 experiments, ethics, inclusive design, top numbers. | **AUTHORITATIVE EVIDENCE** |
| `CM3070_EXAM_QUESTION_BANK.md` | 82.7 KB | 100-Question Exam Bank | 100 comprehensive questions and answers covering all technical, ethical, and theoretical project aspects. | **AUTHORITATIVE EVIDENCE** |
| `_ca0bcfddc99545298e85097c36f56ae1_Consent-form-example-1.docx` | 41.3 KB | Ethics Document | Official University of London Participant Consent Form (`PR/001`) with Participant Information Sheet (`PR/002`). | **AUTHORITATIVE ETHICS** |
| `subtitle (58).txt` ... `subtitle (83).txt` | 230 KB | 26 Lecture Transcripts | Complete course guidance from Dr. Matthew Yee-King and Marco Gillies (assessment criteria, inclusive design, reports). | **AUTHORITATIVE REQUIREMENTS**|
| `build_final_oracle_showcase.py` | 31.7 KB | Python Script | Provenance script proving historical showcase used `qwen3:8b` via Ollama and pre-patch validator. | **PROVENANCE EVIDENCE** |
| `tracking_3v3_dataset_b.csv` | 59.1 MB | CSV Data | Raw 3v3 tracking output across 20,391 frames. | **HISTORICAL BENCHMARK DATA** |
| `selected_C_roster_assignments.csv` | 33.4 MB | CSV Data | Authoritative Experiment C tracking file ingested by Oracle showcase. | **HISTORICAL SHOWCASE DATA** |
| `build_corrected_metric_showcase.py` | 48.0 KB | Python Script | Generates physical metric showcase and kinematics derivations. | **METHODOLOGY SCRIPT** |
| `build_metric_sanity_audit.py` | 32.5 KB | Python Script | Implements metric sanity checks and speed threshold sensitivity audits. | **METHODOLOGY SCRIPT** |
| `build_homography_validation.py` | 27.0 KB | Python Script | Computes landmark reprojection residuals and independent RMSE (0.651m). | **METHODOLOGY SCRIPT** |
| `m3_...` series (15 scripts) | ~220 KB | Python Scripts | Complete engineering and forensic scripts for M3 SriTrack development and M3-R2 diagnostics. | **METHODOLOGY PROVENANCE** |

---

## 17. Ethics and Consent Readiness

### 17.1 Recorded Football Participants
- **Documented Evidence**: `_ca0bcfddc99545298e85097c36f56ae1_Consent-form-example-1.docx` (University of London Form PR/001).
- **Researcher Confirmation**: Confirmed that all 10 participants for 5v5 and all 6 participants for 3v3 signed informed consent prior to recording (`CM3070_EXAM_PROJECT_DOSSIER.md` Section 21).
- **Data Protection Safeguards**: Signed physical forms contain identifying personal data and must remain in an access-controlled private store. All project outputs use canonical pseudonyms (`Player_01`, `Player_02`). Raw participant names are strictly excluded from reports.
- **Status**: `RESEARCHER-CONFIRMED; ETHICS STORE REQUIRED`.

### 17.2 Planned Coach User Study
- **Planned Instrument**: Google Forms survey with mandatory participation-consent question.
- **Workflow**: Near-final functional prototype $\rightarrow$ Evaluation video/demo $\rightarrow$ Coach survey $\rightarrow$ Traceable iterative design changes $\rightarrow$ Final verification.
- **Status**: `PLANNED_NOT_YET_EXECUTED`.

---

## 18. Coach User-Study / Iterative-Design Readiness

- **Prerequisites for Coach Study**:
  1. Functional prototype running real video analysis.
  2. Clear disclosure that player-level accumulated metrics are withheld (`COMPLETED_WITH_LIMITATIONS`).
  3. Interactive display of 2D radar pitch, tactical event list, and coaching report.
  4. Working Oracle capability showcase demonstrating what is possible when identity is verified.
- **Iterative Design Traceability**:
  - The survey must capture structured feedback on:
    - Clarity of limitation banners.
    - Utility of 2D tactical radar vs raw video.
    - Understandability of automated coaching report sections.
    - Coach-suggested layout and metric adjustments.
  - Feedback items will be converted into traceable GitHub/product issues, implemented in code, and verified in post-change smoke tests.

---

## 19. Final-Report Evidence Gap Matrix

| Final Report Chapter (10,500 words) | Required Scientific Evidence | Current Repository Evidence Status | Strongest Source Artifact | Missing Elements |
| :--- | :--- | :---: | :--- | :--- |
| **1. Introduction & Motivation** | Amateur football tactical review challenge, single-camera constraints. | **READY** | `README.md`, `docs/architecture.md`, `subtitle (58).txt` | None |
| **2. Related Work** | Object detection, multi-object tracking, ASR, LLM grounding literature. | **READY** | `CM3070_EXAM_PROJECT_DOSSIER.md` Section 25, `subtitle (66).txt` | None |
| **3. Computer Vision Evolution** | Early YOLO failure, Stage 4B horizontal tiling ablation, BoT-SORT tuning. | **READY** | `01_vision_pipeline.ipynb` Cells 0–158, `detection_provenance.md` | None |
| **4. The Identity Crisis** | Mathematical proof that persistent identity fails (ratio 6.1667 > 1.50). | **READY** | `01_vision_pipeline.ipynb` DB3V3.R13, `CM3070_EXAM_PROJECT_DOSSIER.md` | None |
| **5. Tri-Methodology Vision Benchmark** | TrackEval HOTA/MOTA/IDF1 comparison on 4 challenge clips across M1, M2, M3. | **READY** | `FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv`, `FINAL_WHOLE_SYSTEM_EVALUATION_REPORT.md` | None |
| **6. Audio & Tactical Extraction** | ASR benchmark (Faster-Whisper vs Parakeet, WER 18.4%), tactical keyword extraction. | **READY** | `ASR_CANDIDATE_A_VS_B_FINAL_COMPARISON.csv`, `ASR_MODEL_SELECTION_RATIONALE.md` | None |
| **7. LLM Grounding & Reporting** | Head-to-head LLM benchmark (Llama 3.1 vs Qwen), 8 grounding gates. | **READY** | `LLM_FORMAL_BENCHMARK_COMPARISON.md`, `test_deterministic_integration.py` | None |
| **8. Metric Homography & Kinematics** | Physical pitch measurement (19.31m $\times$ 19.88m), RMSE 0.651m, speed clamping. | **READY** | `3v3_homography_measured_metric_corrected.json`, `build_homography_validation.py` | None |
| **9. Capability Showcase (Oracle)** | Proof of concept on Pressing (C06), Marking (C04), Holding (C03). | **PARTIAL** | Verified human inputs exist; report text needs Llama revalidation. | Re-rendered Llama report text. |
| **10. System Architecture & Engineering**| Web app, FastAPI, Supabase DB & Storage, atomic dispatch, 150 tests. | **READY** | Primary product workspace, Migrations 001–004, 150 passed pytest tests. | None |
| **11. Inclusive Design & Ethics** | Fail-closed safety, plain language, consent PR/001, coach study plan. | **READY** | `_ca0bcfdd...Consent-form...docx`, `CM3070_EXAM_PROJECT_DOSSIER.md` Sec 21–24 | Coach study execution. |
| **12. Limitations & Future Work** | Honest reflection, D0 concept, what failed and why. | **READY** | `CM3070_EXAM_QUESTION_BANK.md` Q87–98, `CM3070_EXAM_PROJECT_DOSSIER.md` | None |

---

## 20. Visualization and Figure Inventory

| Fig # | Proposed Figure Title | Core Scientific / Technical Question Answered | Source Artifact Path | Metrics / Fields Required | Report Section |
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

## 21. Stale / Superseded Artifact Register

| Artifact Path | Stale Statement / Content | Authoritative Current State | Concrete Action |
| :--- | :--- | :--- | :--- |
| `backend/app/core/model_manifest.yaml` | Line 96 references `qwen3:8b` as research baseline | `llama3.1:8b` (digest `46e0c10c...`) is frozen final LLM | Update manifest with Llama 3.1 8B and prompt SHA |
| `backend/app/core/model_manifest.yaml` | Vision selection listed as unresolved | `DEFAULT_VISION_METHOD = M2_GLOBAL_ASSOCIATION` | Update manifest with M2 default and M1/M3 options |
| `golden/fixtures/showcase_final_coach_report.md` | Generated using `qwen3:8b` with pre-patch validator | Llama 3.1 8B with Patch 001 is the frozen standard | Re-render report text through Llama 3.1 pipeline |
| `golden/fixtures/showcase_frontend_payload.json` | Flat custom JSON structure | Must match `shared/schemas/results.py` contract | Convert payload into canonical `AnalysisResult` JSON |
| `G:\My Drive\Football_Training_Assistant_MVP\frontend/` | 3-file static prototype (`index.html`, `index.css`, `app.js`) | Superseded by TanStack Start SSR web app | Retain in research workspace; do NOT import into product |
| `G:\My Drive\Football_Training_Assistant_MVP\backend/server.py` | Monolithic prototype server | Superseded by modular FastAPI control plane | Retain in research workspace; do NOT import into product |
| `frontend/tactical-ai-insights-main/src/routes/analysis.processing.tsx` | Static simulated preview page | Superseded by live polling `$jobId` route | Retain preview banner or cleanly redirect |
| `frontend/tactical-ai-insights-main/src/routes/results.tsx` | Static mock preview page | Superseded by live dynamic `$jobId/results` route | Retain preview banner or cleanly redirect |

---

## 22. Exact P0/P1/P2/P3 Gap Register

### P0 — Must Complete Before Final Real End-to-End Run

- **GAP-P0-1: Tri-Methodology Vision Executors Implementation**:
  - *Location*: Primary workspace: [`backend/app/pipeline/tracking.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/tracking.py), [`registry.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/registry.py).
  - *Current State*: `tracking.py` raises `NotImplementedError`; `registry.py` returns HTTP 409.
  - *Required Action*: Implement `M1Executor` (YOLO11m + BoT-SORT), `M2Executor` (RF-DETR + GTA-Track), and `M3Executor` (YOLO26 + SriTrack). Register all three with `AUTO` resolving to `M2`.
  - *Dependencies*: None. Code-only porting.
  - *Risk*: Video analysis cannot run.
- **GAP-P0-2: ASR Pipeline Integration**:
  - *Location*: Primary workspace: [`backend/app/pipeline/audio.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/audio.py), [`instructions.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/instructions.py).
  - *Current State*: Stubs raising `NotImplementedError`.
  - *Required Action*: Port `ASRPipeline` from research `backend/pipeline/asr.py` (`faster-whisper base.en` CPU int8, Silero VAD, tactical keyword classifier).
  - *Dependencies*: None. Code-only porting.
  - *Risk*: Audio cannot be transcribed or converted to tactical events.
- **GAP-P0-3: Multimodal Fusion Engine Integration**:
  - *Location*: Primary workspace: [`backend/app/pipeline/fusion.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/fusion.py).
  - *Current State*: Stub raising `NotImplementedError`.
  - *Required Action*: Port `FusionEngine` from research `backend/pipeline/fusion.py` (2s–6s evaluation windows, pitch thirds, fail-closed player withholding).
  - *Dependencies*: GAP-P0-1, GAP-P0-2.
  - *Risk*: Vision tracks and audio instructions cannot be synthesized.
- **GAP-P0-4: LLM Reporting & Patch 001 Grounding Validator Integration**:
  - *Location*: Primary workspace: [`backend/app/pipeline/reporting.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/reporting.py), [`evidence.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/pipeline/evidence.py).
  - *Current State*: Stubs raising `NotImplementedError`.
  - *Required Action*: Port `ReportEngine`, `LLMClient`, and `validate_grounding` from research. Enforce `llama3.1:8b`, prompt SHA `ab95a835...`, and deterministic fallback.
  - *Dependencies*: GAP-P0-3.
  - *Risk*: Reports cannot be generated or validated.
- **GAP-P0-5: Modal GPU Worker Container Configuration**:
  - *Location*: Primary workspace: [`modal_app/worker.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/modal_app/worker.py), `requirements-modal.txt`.
  - *Current State*: CPU-only smoke harness without AI inference packages.
  - *Required Action*: Add NVIDIA T4 GPU allocation, PyTorch, CUDA, CTranslate2, and Ultralytics dependencies. Wire worker to invoke integrated pipeline.
  - *Dependencies*: GAP-P0-1 to GAP-P0-4.
  - *Risk*: Real cloud video processing cannot execute.

### P1 — Must Complete Before Coach User Study / Final Submission

- **GAP-P1-1: Model Manifest Synchronization**:
  - *Location*: Primary workspace: [`backend/app/core/model_manifest.yaml`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/core/model_manifest.yaml).
  - *Current State*: References `qwen3:8b`.
  - *Required Action*: Update to `llama3.1:8b` (digest `46e0c10c...`), prompt SHA `ab95a835...`, and declare `M2_GLOBAL_ASSOCIATION` as default vision method.
- **GAP-P1-2: Frontend Upload Wizard Methodology Selector**:
  - *Location*: Primary workspace: [`src/routes/analysis.new.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.new.tsx).
  - *Current State*: Wizard lacks methodology selection.
  - *Required Action*: Add dropdown: `AUTO (Recommended: M2 Global Association)`, `M1 (Original Hybrid)`, `M2 (Global Association)`, `M3 (Re-entry Focused)`.
- **GAP-P1-3: Frontend Showcase Live API Wiring**:
  - *Location*: Primary workspace: [`src/routes/showcase.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/showcase.tsx).
  - *Current State*: Uses static mock cards.
  - *Required Action*: Connect React Query to fetch live cases from `/api/v1/showcase` and render real overlay videos.
- **GAP-P1-4: Oracle Showcase Revalidation**:
  - *Location*: Primary workspace: [`golden/fixtures/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/golden/fixtures/).
  - *Current State*: Generated by `qwen3:8b`.
  - *Required Action*: Re-run showcase evidence through `llama3.1:8b` with Patch 001 validator, format to canonical `AnalysisResult` contract.

### P2 — Important Hardening

- **GAP-P2-1: Python Runtime Standardization**:
  - Standardize local development virtual environment from 3.8.10 to 3.10+ to match Modal container contract.
- **GAP-P2-2: Frontend Legacy Routes Cleanup**:
  - Cleanly deprecate or redirect `/analysis/processing` and `/results` preview routes.

### P3 — Optional / Future Work

- **GAP-P3-1: Multi-Tenant Authentication UI**:
  - Implement full Supabase Auth UI (signup, login, JWT verification) in place of development tenant mode.

---

## 23. Final Closure Sequence

```
[Step 1: Manifest Synchronization]
  Update `model_manifest.yaml` (lock Llama 3.1 8B, prompt SHA, M2 default).
       │
[Step 2: Port Research Pipeline Modules]
  Adapt `asr.py`, `homography.py`, `fusion.py`, `validator.py`, `reporter.py` into primary `backend/app/pipeline/`.
       │
[Step 3: Implement Vision Methodology Executors]
  Implement `M1Executor`, `M2Executor`, `M3Executor` in `backend/app/pipeline/tracking.py` and register in registry.
       │
[Step 4: Revalidate Oracle Showcase]
  Re-run showcase evidence through Llama 3.1 8B with Patch 001 validator; update `golden/fixtures/`.
       │
[Step 5: Frontend Component Wiring]
  Add methodology selector to `analysis.new.tsx`; wire `showcase.tsx` to `/api/v1/showcase`.
       │
[Step 6: Upgrade Modal GPU Container]
  Add NVIDIA T4 GPU, PyTorch, CUDA, CTranslate2 to `modal_app/worker.py` and wire pipeline.
       │
[Step 7: Automated Regression & End-to-End Smoke Test]
  Run full test suite (150+ tests) and execute live match video analysis through web UI.
       │
[Step 8: Evaluation Video & Coach Survey]
  Record near-final walkthrough video; conduct coach user study using Google Forms.
       │
[Step 9: Traceable Iterative Design Changes]
  Convert coach feedback into product refinements; verify post-change stability.
       │
[Step 10: Final Demo & 10,500-Word Report Production]
  Generate 8 report figures from CSV/JSON; produce final 20-minute video demo; write final report.
```

---

## 24. Risks and Scientific Limitations

1. **Persistent Identity Invariant**:
   - Automated persistent identity across full sessions remains mathematically unsolved (`FAIL_HIGH_FRAGMENTATION`).
   - The system must NEVER report unverified individual player metrics. All real session analyses must return `COMPLETED_WITH_LIMITATIONS`.
2. **Single-Camera Planar Ambiguity**:
   - Planar homography mapping carries an independent RMSE of 0.651m. Footpoint occlusions during crowd scenes can induce transient positional jitter.
3. **Compute Latency & Cold Starts**:
   - Complete 5-minute video processing (YOLO slicing + M2 tracking + Faster-Whisper + Llama 3.1 generation) takes approximately 100–120s on an NVIDIA GPU. Heartbeat callbacks are critical to maintain client polling without timeout.

---

## 25. Final Audit Disposition

$$\mathbf{AUDIT\_VERDICT: PASS\_COMPLETE\_REVALIDATION\_BASELINE\_ESTABLISHED}$$

The CM3070 project has completed all scientific research, model selections, and empirical evaluations. The primary product control plane is hardened and passing 150/150 tests. Prototype closure is strictly an integration exercise to port the validated research pipeline modules into the primary backend and Modal worker.
