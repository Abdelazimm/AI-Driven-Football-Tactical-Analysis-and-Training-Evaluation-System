# Repository-wide integration audit

Audit date: 2026-09-21  
Scope: read-only inspection for application integration. No model, experiment, notebook, or frozen result was rerun or modified.

## 1. Executive state

The repository is a research prototype implemented mainly in four Google Colab notebooks plus deterministic Python audit/showcase scripts. It has no production API, job runner, Supabase integration, or suitable Next.js frontend.

Scientific state that integration must preserve:

- Automated persistent identity: `FAIL_HIGH_FRAGMENTATION`.
- Raw track IDs: 115; meaningful reconciled identities: 37.
- Fragmentation ratio: 6.1667; acceptance threshold: 1.5.
- Full-session automated player-level assessment: `WITHHELD`.
- Frozen showcase: `PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE`.
- Showcase mode: `ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION`.
- Showcase identities, targets, opponents, and zone meaning are manually verified, not automated.
- Corrected calibration: `MODERATE_CONFIDENCE_MEASURED_METRIC_ESTIMATE`.
- Measured pitch: 19.31 m x 19.88 m; independent landmark RMSE: 0.651 m (rounded from 0.6505057 m).

## 2. Logical project structure

```text
Football_Training_Assistant_MVP/
|-- 01_vision_pipeline.ipynb                 # Drive: full research vision notebook
|-- 02_audio_pipeline.ipynb                  # real/synthetic ASR pipeline
|-- 03_orchestrator_fusion.ipynb             # fail-closed audio/vision fusion
|-- 04_report_generation.ipynb               # inclusive reporting + Ollama/grounding
|-- Autonomus_scout.ipynb                    # capability-showcase research notebook
|-- config/
|   |-- frozen_splits.json
|   |-- selected_detection_config.json       # stale pre-Stage-4B selection; do not treat as final
|   |-- 3v3_homography.json                  # historical 20 x 20 research calibration
|   |-- 3v3_homography_measured_metric_corrected.json
|   `-- ollama_report.json
|-- configs/
|   `-- botsort_football_fallback_C.yaml      # Experiment C tracker configuration
|-- models/
|   |-- yolo_multi_domain_adapted.pt
|   |-- yolo11m.pt
|   |-- faster_whisper/
|   `-- prtreid/
|-- data/                                    # custom videos/audio/intermediate CSV/JSON
|-- experiments/
|   |-- vision_3v3_identity_repair/
|   |-- persistent_identity_prtreid/         # E0-E6 and frozen detections
|   |-- capability_showcase/
|   `-- ...                                  # historical run evidence
|-- predictions/ models/ runs/ figures/ tables/ reports/ outputs/
|-- selected_C_roster_assignments.csv        # 111,890-row Experiment C observation artifact
|-- tracking_3v3_dataset_b.csv                # large tracking artifact
|-- C03_hold_position_deterministic_response/
|-- c04_deterministic_response/
|-- C06_pressing_deterministic_response/
|-- physical_metric_upgrade/
|   |-- config/3v3_homography_measured_metric_corrected.json
|   `-- experiments/
|       |-- homography_validation_physical_corrected/
|       `-- capability_showcase/
|           |-- metric_extensions_corrected/
|           |-- metric_sanity_audit/
|           `-- 05_final_showcase/            # read-only golden data
|-- build_corrected_metric_showcase.py
|-- build_metric_sanity_audit.py
|-- build_final_oracle_showcase.py
|-- build_homography_validation.py
|-- physical_metric_upgrade.py
`-- .soccertrack-v2-reference/                # third-party/research reference, not app runtime
```

Local inventory at audit time: 542 files, 124 directories, approximately 0.611 GB, excluding Drive-only large models/videos. The working copy includes no application-level `package.json`, Next.js project, FastAPI package, Modal configuration, Supabase client, or production dependency lockfile.

## 3. Notebooks and responsibilities

| Notebook | Observed responsibility | Production extraction value |
|---|---|---|
| `01_vision_pipeline.ipynb` | detection, BoT-SORT, stitching/reliability research, homography, kinematics, Dataset B experiments | high, but code is notebook/path/state coupled |
| `02_audio_pipeline.ipynb` | ffmpeg extraction, CPU Faster-Whisper, word timestamps, deterministic instruction parsing | high |
| `03_orchestrator_fusion.ipynb` | pseudonymization, time-window alignment, fail-closed fusion | high |
| `04_report_generation.ipynb` | deterministic report, inclusive explanations, Ollama prompt/validator/fallback | high, except local Ollama transport |
| `Autonomus_scout.ipynb` | human-review and oracle showcase research | golden evidence/reference only, not automated runtime logic |

## 4. Model artifact audit

### Detector artifacts

| Path | Size | Type/framework | Evidence and use | Runtime assessment |
|---|---:|---|---|---|
| `/content/drive/MyDrive/Football_Training_Assistant_MVP/runs/vision_20260805T232509Z_d2f9bc0d/stage_4/fine_tuning_pilot/yolo11m_pilot_memory_safe/weights/best.pt` | 40,539,756 B | Ultralytics YOLO, fine-tuned from YOLO11m | accepted Stage 4B tiled detector; SHA-256 `f6b3fe6f21256c61083ccc6c6b96dffeb4490c65c3ce150c3924a0fa353e6f5e` | technically T4-compatible; intended app status is unresolved because Dataset B Experiment C used a different detector |
| `/content/drive/MyDrive/Football_Training_Assistant_MVP/models/yolo_multi_domain_adapted.pt` | 40,486,892 B | Ultralytics YOLO adaptation artifact | custom-domain adaptation/dry-run research | not established as the frozen Experiment C detector |
| `/content/drive/MyDrive/Football_Training_Assistant_MVP/models/yolo11m.pt` | 40,684,120 B | official YOLO11m | baseline/teacher | baseline/research unless explicitly selected later |
| `/content/drive/MyDrive/Football_Training_Assistant_MVP/experiments/persistent_identity_prtreid/E6_deep_eiou_gta/01_frozen_detections/yolov8m.pt` | 52,136,884 B | official Ultralytics YOLOv8m | exact Experiment C detector checkpoint reconstructed for the permanent frozen pre-tracker pass; SHA-256 `5d4a90cdc7a21786cc59cd19778e9eafff836df9e2da32524737c7ee6efe4fe5` | T4-compatible; strongest provenance for reproducing Dataset B Experiment C detections |

There is no single unambiguous application detector declaration. Stage 4B selected the fine-tuned YOLO11m tiled configuration, while the later Dataset B/Experiment C evidence used official YOLOv8m. The root `config/selected_detection_config.json` predates Stage 4B and explicitly represents an unselected baseline. Integration must resolve this with an explicit versioned deployment manifest; it must not infer from filename recency.

### ASR and ReID artifacts

- `models/faster_whisper/`: locally cached Faster-Whisper assets. Exact byte total was not established in repository summaries. The real pipeline specifies `base.en`, Faster-Whisper 1.2.1, CTranslate2 CPU `int8`.
- `models/prtreid/` and E0-E6 ReID/GTA/Deep-EIoU assets: research-only. They did not make automated persistent identity pass and must not be presented as a production identity solution.

## 5. Detection implementation

Two evidenced detection paths exist:

1. Accepted Stage 4B benchmark configuration:
   - fine-tuned `best.pt` above;
   - three horizontal tiles, 15% overlap;
   - `imgsz=1280`, global NMS IoU 0.70, person class only;
   - accepted confidence 0.20;
   - validation evidence on 100 frames: mAP50 0.51677, mAP50-95 0.19906, precision 0.4455, recall 0.5668, F1 0.4989, mean latency 246.95 ms.
2. Dataset B Experiment C/frozen-detection configuration:
   - official `yolov8m.pt`, Ultralytics 8.4.150;
   - source 3840x2160 resized with OpenCV `INTER_AREA` to 1920x1080;
   - `conf=0.05`, `imgsz=1280`, `classes=[0]`, `max_det=16`, default NMS IoU 0.70;
   - sequential frames, no frame skip;
   - frozen output: 317,402 detections across all 20,391 frames, mean 15.5658/frame.

Reusable concerns for `backend/pipeline/detection.py`: model loading, streaming decode, resize metadata, person filtering, tiling/global NMS where selected, normalized output schema, and provenance (weight hash, framework version, parameters, source dimensions, processed dimensions, frame index and timestamp). Notebook globals and Drive paths must be removed.

Recommended detection-row schema: `frame_index`, `timestamp_s`, `x1`, `y1`, `x2`, `y2`, `confidence`, `class_id`, `source_width`, `source_height`, `processing_width`, `processing_height`, `scale_x`, `scale_y`, `detector_manifest_id`.

## 6. Tracking versus persistent identity

### Short-term tracking

- Tracker: Ultralytics BoT-SORT.
- SoccerTrack validation research configuration: `track_high_thresh=0.13`, `track_low_thresh=0.03`, `new_track_thresh=0.12`, `track_buffer=120`, `match_thresh=0.95`, `gmc_method=none`, `with_reid=false`.
- Dataset B Experiment C configuration: `configs/botsort_football_fallback_C.yaml`: high 0.25, low 0.05, new 0.45, buffer 420, match 0.85, fuse score true, GMC none, proximity 0.15, appearance 0.88, ReID true/model auto.
- Expected input: ordered person detections per frame. Expected output: per-observation raw track ID, frame/timestamp, image bbox/centroid or footpoint, confidence, coordinate-space provenance.

These configurations are experimental and tied to different datasets. The deployment manifest must select one without relabeling its evidence.

### Persistent identity

Postprocessing/research components include micro-track filtering, multi-pass/global stitching, roster-aware constraints, appearance/ReID, GTA split/connect experiments, and Deep-EIoU research. Experiment C evaluation used a 30-frame micro-track threshold and a maximum stitch gap of 7 seconds, with motion/spatial/appearance/team costs and conflict safeguards.

The result remains failed:

```text
fragmentation_ratio = meaningful_final_ids / expected_active_players
                    = 37 / 6
                    = 6.1667
gate threshold      = 1.5
status              = FAIL_HIGH_FRAGMENTATION
```

The application may reuse the explicit gate, audit schema, conflict checks, and fail-closed behavior. It must not claim reliable persistent identity from the current tracker/stitcher/ReID/GTA stack. Player-level conclusions require a passed gate or an explicitly separate manual/oracle workflow with provenance. If identity, target, calibration, or speed is unresolved, corresponding conclusions remain withheld.

## 7. Homography and calibration

Authoritative corrected configuration:

`/content/drive/MyDrive/Football_Training_Assistant_MVP/config/3v3_homography_measured_metric_corrected.json`

Local audited copy:

`physical_metric_upgrade/config/3v3_homography_measured_metric_corrected.json`

Tracking-to-metric matrix:

```text
[[-0.012802040941679778, -0.03938196326742872, 24.416392327252076],
 [ 0.0003684827148920768, 0.03530078523580245, -32.538796529924724],
 [-0.000011678487000361972, -0.00363943658404158, 1.0]]
```

- Pitch metric coordinates: X 0..19.31 m (left to right goal), Y 0..19.88 m (near to far).
- Tracking coordinate space: 1920x1080. Source frame: 3840x2160. Source-to-tracking scale is 0.5 in both axes; tracking-to-source visualization scale is 2.0.
- Player mapping uses bbox bottom-center/footpoint, then planar perspective transformation.
- Independent corrected validation: RMSE 0.6505057 m, maximum error 0.84092 m; confidence is moderate, not GPS-grade.
- Historical `config/3v3_homography.json` and earlier measured calibration remain historical/frozen.

Reusable functions exist in `build_corrected_metric_showcase.py`: `project_xy`, `inverse_project_xy`, `line_array`, `intersect`; configuration/provenance is reusable. For arbitrary uploads, the app must implement three explicit modes: (A) frozen project demo calibration only for matching camera/geometry, (B) user-supplied/custom four-point or landmark calibration with validation and coordinate provenance, (C) no-metric mode that withholds metres/speed rather than applying the demo matrix.

## 8. Kinematics

The corrected deterministic implementation is in `build_corrected_metric_showcase.py::build_track_kinematics` and supporting event functions.

- Position: homography-projected footpoint.
- Smoothing: centered rolling median over 7 observations per raw track.
- Valid temporal gap: `0 < delta_frames <= 120`.
- Time delta: frame delta divided by the source video's FPS.
- Displacement: Euclidean distance between consecutive smoothed metric positions.
- Speed: `distance_m / delta_t_s * 3.6` km/h.
- Outlier rule: reject speed greater than 36 km/h.
- Missing/gap handling: no interpolation across missing observations or identity gaps; invalid speed remains unavailable; rejected/gap steps contribute zero accepted distance.
- Metric sanity audit recommends average and P95 estimated speed; threshold-sensitive maxima are not coach-facing headlines. C03 retention path is jitter-sensitive and the C06 overall path was not reproduced from exported timeseries coverage.

Production must read FPS/timestamps from each uploaded video. The research value near 59.972 FPS is video-specific and must never be a global constant.

## 9. Audio and ASR

Authoritative real-audio pipeline in `02_audio_pipeline.ipynb`:

- Source: `data/custom/audio/coach_commands.m4a`.
- ffmpeg extraction: 16 kHz, mono, PCM WAV.
- Faster-Whisper 1.2.1, model `base.en`, CPU int8, 4 CPU threads, 1 worker, beam size 5.
- English forced; word timestamps enabled; VAD enabled with 500 ms minimum silence; `condition_on_previous_text=false`.
- Observed real session: approximately 340.033 s, 27 ASR segments, 128 timestamped words, 14 structured events.
- Private raw transcript: `data/custom/audio/3v3_real_audio_whisper_raw.json`; do not expose publicly.
- Public/pseudonymized events: `data/custom/audio/3v3_real_audio_coaching_events.json`; unresolved names remain `UNRESOLVED_TARGET`.
- Summary: `experiments/3v3_real_audio_audio_summary.json`.

Reusable modules: `media/audio.py` (ffmpeg probe/extract), `pipeline/asr.py` (model lifecycle/streaming transcript), `pipeline/instructions.py` (deterministic phrase/category/profile parsing), and Pydantic schemas. `gTTS` belongs only to synthetic fixtures. The repository does not record a trustworthy exact base.en cache size; container/image planning must measure the pinned downloaded snapshot. Faster-Whisper/CTranslate2 can run CPU int8 as tested; T4 CUDA is optional and needs a compatible CUDA/CTranslate2 image.

## 10. Audio-vision fusion

`03_orchestrator_fusion.ipynb` consumes saved tracking/kinematics and coaching events, pseudonymizes identities, aligns windows, and emits fail-closed fused events.

- Typical response window: 2 seconds before instruction through 5 seconds after its end.
- Target resolution depends on roster/identity evidence.
- When target identity is unresolved or identity gate fails: kinematics are null/withheld and label is `PLAYER_LEVEL_ASSESSMENT_WITHHELD`.
- Authoritative real-session output: `data/custom/3v3_real_audio_fused_events.json`.
- Summary: `experiments/3v3_real_audio_fusion_summary.json`.
- Active states include `FAIL_HIGH_FRAGMENTATION`, `UNRESOLVED_TARGET`, and `PLAYER_LEVEL_ASSESSMENT_WITHHELD`.

Reusable concerns: loaders and schema validation, pseudonymization, interval alignment, gate composition, deterministic evidence provenance. Notebook-specific globals and file discovery should not move into production unchanged.

## 11. Reporting and Ollama

`04_report_generation.ipynb` contains:

- `TacticalReportGenerator` deterministic report path;
- `explain_status_for_coach`, `report_value`, and `selected_tracking_evidence` inclusive-report helpers;
- tests for failure preservation, unknown status fallback, missing data, technical evidence preservation, and privacy;
- structured Ollama input for `qwen3:8b`, temperature 0, `think=false`;
- `validate_response`-style grounding rules mirrored in `build_final_oracle_showcase.py`;
- deterministic fallback when the LLM is unavailable or invalid.

Reusable as-is conceptually: evidence schema, prompt contract, mandatory limitations, forbidden psychological labels, numeric grounding, validator, deterministic fallback, and inclusive progressive disclosure. Not reusable as transport: `http://localhost:11434`, the local Windows Ollama service, and local model lifecycle. Deployment needs a separately approved report-model adapter; no replacement is selected by this audit.

## 12. Final showcase (golden data)

Golden directory:

`physical_metric_upgrade/experiments/capability_showcase/05_final_showcase/`

It contains nine Markdown/JSON artifacts, including:

- `showcase_frontend_payload.json`: schema version 1.0; C06/C04/C03 cards, badges, report Markdown, limitations.
- `showcase_final_coach_report.md`: grounded coach-facing report.
- `showcase_grounding_validation.json`: report grounding evidence.
- `showcase_final_summary.json`: frozen final state.
- `showcase_grounded_evidence.json`, Ollama input/raw response, deterministic summary, completeness record.

The payload is not self-contained. It references media paths that do not match the current local/Drive directory names:

| Payload reference | Located artifact |
|---|---|
| `experiments/capability_showcase/C06_pressing_deterministic_response/C06_pressing_sequence_overlay.mp4` | `C06_pressing_deterministic_response/C06_pressing_sequence_overlay.mp4` |
| `experiments/capability_showcase/C04_marking/C04_black01_red03_response_contact_sheet.png` | `c04_deterministic_response/C04_black01_red03_response_contact_sheet.png` |
| `experiments/capability_showcase/C03_hold_position/C03_hold_position_overlay.mp4` | `C03_hold_position_deterministic_response/C03_hold_position_overlay.mp4` |

Do not edit the golden JSON. Add an integration-time immutable media manifest that maps frozen logical references to copied/served storage objects, preserving checksums and provenance.

## 13. Frontend state

No suitable frontend/application code exists. No root application `package.json`, App Router, React components, Tailwind/Shadcn setup, or Vercel configuration was found. The Next.js/React/TypeScript application should be a new integration layer. The frozen `showcase_frontend_payload.json` is a useful display contract, not a frontend implementation.

## 14. Modal/T4 readiness

- GPU-suitable: YOLO detection; optional CUDA ASR; possibly tracker/ReID if retained.
- CPU-suitable: video probing/ffmpeg orchestration, BoT-SORT association after detections, homography, kinematics, fusion, validation, deterministic report, JSON/DB operations; current ASR was tested CPU int8.
- Image/container must include pinned Python runtime, PyTorch/CUDA-compatible Ultralytics, OpenCV runtime, ffmpeg/ffprobe, Faster-Whisper/CTranslate2, model manifests, selected detector weights, tracker config, and extracted production modules.
- Cold start is dominated by image size and model load/download. Bake pinned weights in the image or a versioned Modal volume; never silently download latest weights per request.
- Load large GPU models sequentially unless measured concurrency proves safe on T4. Do not co-reside optional ReID/ASR GPU models by default.
- Long video jobs must be background jobs with persisted stage checkpoints and resumable artifacts. A single HTTP request must not own the processing lifetime.

## 15. Five-minute video readiness

The audited research video is approximately 340 seconds at 3840x2160 and produced 317,402 pre-tracker detections and more than 111,000 tracked observations. At the same bitrate, a 300-second upload could be on the order of 2 GB; this is an inference from the repository media, not a platform guarantee.

Risks and required design changes:

- Direct-to-Supabase upload with server-side duration/type/size validation; do not proxy multi-GB bodies through Next.js/FastAPI.
- Stream decode; do not hold full video/frame arrays in RAM.
- Explicit scratch-space budget for input, audio WAV, processed video, clips, detections, tracking tables, and render intermediates.
- Background Modal job, idempotent stage state, heartbeat/progress, cancellation, timeout, retry, and partial-failure handling.
- Persist outputs after probe, detection, tracking, ASR, fusion, and report stages.
- Encode processed video separately and clean temporary files only after durable upload.
- Enforce 300 seconds using ffprobe before GPU scheduling.

## 16. Supabase conceptual split

PostgreSQL/JSONB:

- `sessions`: owner, source metadata, consent/visibility, created time.
- `analysis_jobs`: session, immutable pipeline manifest, state, current stage, progress, Modal call ID, error code.
- `calibrations`: mode, source/processing resolution, points/matrix, geometry, validation metrics, confidence.
- `analysis_results`: quality gates, aggregate metrics, evidence JSON, report status, scientific limitations.
- `instruction_events`: timestamp interval, redacted text, category/profile, pseudonymous target status.
- `artifacts`: storage key, kind, checksum, size, MIME type, provenance, frozen flag.
- `showcase_cases`: immutable references to the three golden cases and their manual-verification provenance.

Supabase Storage:

- raw uploads, extracted audio, processed/annotated videos, clips, figures/contact sheets, CSV/Parquet observation tables, model-independent evidence bundles, final reports, and golden showcase media copies.

Use private buckets and signed URLs for participant media/raw transcripts. Apply row-level security and service-role separation. Never expose signed consent forms or raw participant names in public artifacts.

## 17. Frozen/read-only boundary

Never rewrite:

- all historical experiment outputs and frozen split manifests;
- E0-E6 identity/ReID/GTA/Deep-EIoU artifacts and frozen detections;
- original/historical homography files and validation packages;
- corrected homography validation and corrected metric extensions;
- metric sanity audit;
- `physical_metric_upgrade/experiments/capability_showcase/05_final_showcase/`;
- final reports, grounding evidence, Ollama raw response, frontend payload, and summary;
- C03, C04, and C06 deterministic response evidence/media;
- source notebooks when performing application integration; extract with provenance into new modules instead.

## 18. Verified gaps

- No FastAPI application, API schemas/routes, authentication/authorization, or OpenAPI contract.
- No Modal deployment image/app, GPU function, job state adapter, volume strategy, or secrets configuration.
- No Supabase schema/migrations/client, storage abstraction, RLS policies, or signed-upload flow.
- No Next.js frontend or Vercel deployment configuration.
- No durable background orchestration, progress events, cancellation, retry, or idempotency.
- No production-wide requirements/lockfile or container build.
- No authoritative single deployment model manifest resolving YOLO11m Stage4B versus YOLOv8m Experiment C.
- No arbitrary-video calibration workflow or no-metric UI mode.
- No immutable mapping from frozen showcase media references to real storage objects.
- No production privacy/retention/deletion workflow for participant media.

## 19. Conclusion

The deterministic evidence, safety gates, calibration provenance, ASR settings, fusion behavior, report grounding rules, and golden showcase are reusable. The notebooks are not deployable application code. Integration should create a new, versioned layer around frozen evidence and extracted pure functions, preserving the failed automated identity state and keeping manual oracle demonstrations visibly separate.
