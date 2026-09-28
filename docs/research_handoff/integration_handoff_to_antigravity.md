# Antigravity implementation handoff

## 1. What this project does

The research prototype analyzes football training video and coach audio. Its intended flow is upload/probe, player detection, short-term tracking, persistent-identity attempt, identity reliability gate, optional calibrated pitch mapping, kinematics, Faster-Whisper transcription, instruction extraction, audio/vision fusion, fail-closed deterministic evidence, grounded report generation, and frontend presentation.

The planned application stack is a new Next.js/React/TypeScript App Router frontend on Vercel, Supabase PostgreSQL/Storage, and FastAPI jobs on Modal with an NVIDIA T4. Maximum accepted video duration is 300 seconds.

## 2. Non-negotiable scientific constraints

- Automated identity is `FAIL_HIGH_FRAGMENTATION`: 115 raw IDs -> 37 meaningful IDs; ratio 6.1667 > 1.5.
- Full-session automated player-level assessment is `WITHHELD`.
- Do not use ReID/stitching/GTA/Deep-EIoU research as proof of reliable identity.
- Frozen showcase status `PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE` applies only to mode `ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION`.
- Showcase player identities, instruction targets, opponents, and zone semantics were manually verified.
- Metric values use `MODERATE_CONFIDENCE_MEASURED_METRIC_ESTIMATE`, 19.31 x 19.88 m geometry, independent RMSE 0.651 m. They are not GPS-grade ground truth.
- Do not generate player-to-ball distance: there are no saved ball detections.
- Avoid psychological/disciplinary labels. Report observable evidence and uncertainty only.

## 3. Golden artifacts

Treat all files under this directory as immutable:

`physical_metric_upgrade/experiments/capability_showcase/05_final_showcase/`

Primary files:

- `showcase_frontend_payload.json`
- `showcase_final_coach_report.md`
- `showcase_grounding_validation.json`
- `showcase_final_summary.json`
- `showcase_grounded_evidence.json`
- `showcase_deterministic_summary.md`
- `showcase_ollama_input.json`
- `showcase_ollama_raw_response.json`
- `showcase_artifact_completeness.json`

The payload is not media-self-contained. Build a separate immutable storage manifest (do not edit the golden JSON):

- C06 logical media -> `C06_pressing_deterministic_response/C06_pressing_sequence_overlay.mp4`
- C04 logical media -> `c04_deterministic_response/C04_black01_red03_response_contact_sheet.png`
- C03 logical media -> `C03_hold_position_deterministic_response/C03_hold_position_overlay.mp4`

Copy these into private/public-as-approved Supabase Storage objects, record checksums, and map frozen logical references to signed/CDN URLs.

## 4. Exact model and configuration paths

### Detector candidates — decision required

Stage 4B accepted detector:

`/content/drive/MyDrive/Football_Training_Assistant_MVP/runs/vision_20260805T232509Z_d2f9bc0d/stage_4/fine_tuning_pilot/yolo11m_pilot_memory_safe/weights/best.pt`

- 40,539,756 bytes
- SHA-256 `f6b3fe6f21256c61083ccc6c6b96dffeb4490c65c3ce150c3924a0fa353e6f5e`
- 3 horizontal tiles, 15% overlap, imgsz 1280, person class, global NMS 0.70, accepted confidence 0.20.

Dataset B/Experiment C exact frozen detector:

`/content/drive/MyDrive/Football_Training_Assistant_MVP/experiments/persistent_identity_prtreid/E6_deep_eiou_gta/01_frozen_detections/yolov8m.pt`

- 52,136,884 bytes
- SHA-256 `5d4a90cdc7a21786cc59cd19778e9eafff836df9e2da32524737c7ee6efe4fe5`
- Ultralytics 8.4.150
- 3840x2160 source -> 1920x1080 `INTER_AREA`; conf 0.05; imgsz 1280; person class; max_det 16; NMS IoU 0.70.

Do not use `config/selected_detection_config.json` as final: it is a stale, pre-Stage-4B baseline. Product/science owner must choose a deployment detector and validation scope, then create one immutable deployment manifest.

Experiment C tracker config:

- `/content/drive/MyDrive/Football_Training_Assistant_MVP/configs/botsort_football_fallback_C.yaml`
- `/content/drive/MyDrive/Football_Training_Assistant_MVP/experiments/vision_3v3_identity_repair/selected_tracking_config.json`
- high 0.25; low 0.05; new 0.45; buffer 420; match 0.85; fuse score true; GMC none; proximity 0.15; appearance 0.88; ReID true/auto.

Corrected demo calibration:

`/content/drive/MyDrive/Football_Training_Assistant_MVP/config/3v3_homography_measured_metric_corrected.json`

Local audited copy: `physical_metric_upgrade/config/3v3_homography_measured_metric_corrected.json`.

## 5. Code to extract

Create new production modules; never import notebooks at runtime.

| Current source | Extract into | Key behavior |
|---|---|---|
| `01_vision_pipeline.ipynb` | `backend/pipeline/detection.py` | streaming inference, coordinate provenance, detector manifest |
| same | `backend/pipeline/tracking.py` | short-term tracking only |
| same | `backend/pipeline/identity_gate.py` | fragmentation/conflict metrics and fail-closed states |
| `build_corrected_metric_showcase.py::project_xy`, `inverse_project_xy` | `backend/pipeline/calibration.py` | perspective mapping plus resolution validation |
| `build_corrected_metric_showcase.py::build_track_kinematics` | `backend/pipeline/kinematics.py` | 7-observation median, timestamp deltas, 36 km/h rejection, no gap interpolation |
| `build_metric_sanity_audit.py::prepare_case`, `summarize_case` | `backend/pipeline/metric_validation.py` | reproducibility, sensitivity, safe metric policy |
| `02_audio_pipeline.ipynb` | `backend/media/audio.py`, `backend/pipeline/asr.py`, `backend/pipeline/instructions.py` | ffmpeg extraction, Faster-Whisper base.en CPU int8, timestamps, deterministic events |
| `03_orchestrator_fusion.ipynb` | `backend/pipeline/fusion.py`, `backend/pipeline/gates.py` | pseudonymization, windows, unresolved-target withholding |
| `04_report_generation.ipynb` | `backend/pipeline/reporting.py`, `backend/pipeline/grounding.py` | inclusive deterministic report, validator, fallback |
| `build_final_oracle_showcase.py::validate_response`, `flatten_strings` | `backend/pipeline/grounding.py` | forbidden claims, mandatory limitations, numeric grounding |

Every module must accept explicit typed inputs/configuration and return typed results with provenance. No `/content/drive`, Windows path, notebook variable, display call, or hidden global state.

## 6. Deployment dependencies

- Pin one Python version and tested compatible set of PyTorch/CUDA, torchvision, Ultralytics, OpenCV headless, NumPy, Pandas/Arrow, SciPy, Pydantic, PyYAML, Faster-Whisper 1.2.1, CTranslate2, and ffmpeg-python 0.2.0.
- Install OS `ffmpeg` and `ffprobe`.
- Experiment C historical evidence used Ultralytics 8.4.150, PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, CUDA 12.8 on T4. Treat this as evidence, not a ready lockfile.
- Keep PRTReID/GTA/Deep-EIoU out of the initial runtime unless separately approved.
- Cache/bake exact detector and Faster-Whisper assets with hashes; no per-request latest downloads.
- Existing `qwen3:8b`/Ollama localhost transport is not deployment-ready. Preserve the structured evidence, prompt contract, validator, and deterministic fallback behind an adapter. Model/provider decision is unresolved.

## 7. Required application architecture

1. Next.js app: authenticated upload/session/results/showcase/calibration UI; direct signed Supabase upload.
2. Supabase: session/job/calibration/result/artifact metadata in PostgreSQL/JSONB; large/private media and tables in Storage; RLS and signed URLs.
3. FastAPI control plane: create job, validate metadata, return status/results; it must not proxy multi-GB uploads or hold long requests.
4. Modal background worker: probe -> detection -> tracking -> identity gate -> calibration/kinematics -> ASR -> fusion -> evidence/report -> artifact upload.
5. Persist a stage manifest/checkpoint after each stage. Jobs must be idempotent, cancellable, resumable, and observable.

## 8. Safety/gate behavior to implement first

- Upload gate: ownership/authorization, MIME, duration <= 300 s, size policy, ffprobe success.
- Identity gate: ratio > 1.5 => `FAIL_HIGH_FRAGMENTATION` and player-level assessment withheld.
- Calibration gate: use metric units only for matching demo calibration or independently validated custom calibration; otherwise `NO_METRIC`.
- Target gate: unresolved target => no player-response judgment.
- Missing speed/insufficient data => explicit unavailable value, never an invented zero.
- Report gate: validator failure or unavailable LLM => deterministic fallback, never ungrounded prose.
- Privacy gate: raw media/raw ASR private; pseudonyms in public report; signed forms and participant names never public.

## 9. Supabase conceptual entities

`sessions`, `analysis_jobs`, `calibrations`, `instruction_events`, `analysis_results`, `artifacts`, `showcase_cases`.

Store metadata, statuses, gates, and compact evidence in Postgres/JSONB. Store videos, audio, clips, figures, large CSV/Parquet, reports, and golden copies in Storage. All artifact records need checksum, MIME, byte size, provenance, owner/session, and frozen flag.

## 10. Known limitations

- No reliable automated persistent identity.
- Detector intended for production is unresolved between two evidenced paths.
- Demo homography is fixed-camera/pitch-specific.
- No ball detector/evidence.
- Metric estimates have moderate calibration confidence; maximum speed is threshold-sensitive.
- Research notebooks use hardcoded paths/FPS/resolution and mixed environments.
- Local Ollama is not portable.
- No API, queue, database, storage policy, frontend, deployment config, or production tests exist.

## 11. Proposed integration order

1. Freeze/copy golden artifacts and create checksum/media manifest.
2. Obtain detector-selection decision; write immutable pipeline/model manifest.
3. Define versioned Pydantic/TypeScript schemas and gate state machine.
4. Extract probe/detection/tracking modules with golden-fixture tests.
5. Implement identity quality gate before any player-level consumer.
6. Extract calibration/kinematics with `DEMO_FIXED`, `CUSTOM_VALIDATED`, `NO_METRIC` modes.
7. Extract audio/ASR/instruction modules with privacy split.
8. Extract fusion and deterministic evidence/report/grounding fallback.
9. Implement Supabase migrations/RLS/storage and direct upload.
10. Implement Modal background stages/checkpoints/progress/cancellation.
11. Implement FastAPI control/status/result endpoints.
12. Implement Next.js upload/progress/results/calibration/showcase UI.
13. Run fixture-based integration tests; only then run a separately approved end-to-end sample.

## 12. Decisions Antigravity must not guess

1. Which detector path is the application default: Stage4B fine-tuned tiled YOLO11m or Experiment C YOLOv8m?
2. Is automated tracking offered only as anonymous/team-level output while identity fails, or is manual roster review an explicit product feature?
3. Which deployment-compatible report model/provider, if any, replaces local Ollama?
4. Upload byte limit, retention duration, deletion policy, and who may access participant media/raw transcripts.
5. Modal timeout/retry/concurrency/scratch-volume budgets and cost ceiling.
6. Custom calibration UX and minimum validation criteria.
7. Whether large observation tables use Parquet in Storage or normalized database rows.

Until these are decided, implement interfaces and fail-closed states, not silent defaults.
