# Integration and runtime risks

## Critical

### C1. No authoritative deployment detector manifest

Stage 4B accepted a fine-tuned YOLO11m tiled detector, while Dataset B Experiment C and the E6 permanent detection artifact use official YOLOv8m with a different preprocessing/threshold configuration. `config/selected_detection_config.json` is stale and explicitly predates the accepted Stage 4B result.

Impact: the application could silently deploy a scientifically different pipeline.  
Control: require a human-approved immutable detector manifest before implementation; include path, SHA-256, Ultralytics version, preprocessing, confidence, NMS, class filter, tiling, and validation scope.

### C2. Automated persistent identity failed

The frozen result is 115 raw IDs, 37 meaningful IDs, fragmentation ratio 6.1667 against threshold 1.5. ReID, stitching, GTA, and Deep-EIoU experiments did not convert this into a reliable full-session identity solution.

Impact: player-level attribution can be wrong.  
Control: enforce the quality gate before player-level fusion/reporting; emit `WITHHELD` and retain observable team/anonymous evidence. Manual/oracle mode must be a separately authorized, prominently labeled demonstration path.

### C3. Participant media/privacy architecture is absent

Raw videos, real audio, raw ASR text, names, and consent-sensitive material currently exist as research files without production RLS, retention, deletion, audit logging, or signed URL policies.

Impact: unauthorized disclosure of personal data.  
Control: private Supabase buckets, least-privilege service role, per-owner RLS, short-lived signed URLs, deletion/retention workflow, redacted public artifacts, and no signed consent forms/names in public output.

## High

### H1. Frozen showcase media references are not resolvable as written

The golden frontend payload references three paths that do not match the current local/Drive directory layout, and the final showcase folder contains JSON/Markdown only.

Impact: broken showcase cards.  
Control: do not edit golden payload; create a checksum-backed integration media manifest mapping logical frozen references to immutable storage objects.

### H2. Notebook/Colab/Drive path coupling

Core logic depends on notebook globals, execution order, `/content/drive`, Colab APIs, and previously created variables.

Impact: non-reproducible jobs and NameErrors in serverless workers.  
Control: extract stateless functions, typed configuration, explicit inputs/outputs, stage manifests, unit tests, and no global runtime state.

### H3. Five-minute jobs cannot be synchronous requests

Research processing handled a ~340-second 4K video and large tabular artifacts. Detection/tracking/ASR/rendering can exceed web timeouts and scratch limits.

Impact: request timeout, duplicate jobs, partial outputs, excessive cost.  
Control: direct upload, queued Modal jobs, idempotency key, persisted checkpoints, progress events, cancellation/retry, explicit scratch quota, and durable artifact upload per stage.

### H4. Demo homography is camera-specific

The corrected matrix assumes a 1920x1080 tracking space derived from 3840x2160 source frames and the measured 19.31 x 19.88 m pitch/camera view.

Impact: invalid metre/speed values on arbitrary uploads.  
Control: calibration mode enum (`DEMO_FIXED`, `CUSTOM_VALIDATED`, `NO_METRIC`); fail closed when resolution/geometry/provenance do not match.

### H5. Local Ollama coupling

Report generation calls `http://localhost:11434` with `qwen3:8b` in the research environment.

Impact: unavailable report model in Modal/Vercel, large model/cold-start cost.  
Control: preserve evidence schema/validator/fallback behind an adapter; select deployment transport/model later through a separate decision.

### H6. Dependency/version drift

Notebook cells install packages dynamically and used mixed Python environments. There is no application lockfile/container.

Impact: changed inference, binary ABI failure, CUDA mismatch.  
Control: pin and test one image; record framework and model hashes; prohibit per-request package/model downloads.

## Medium

### M1. T4 memory and lifecycle contention

YOLO, optional ReID, and optional GPU ASR can contend for 16 GB T4 VRAM.

Control: start with sequential model stages, unload/synchronize between stages, keep verified ASR on CPU int8, and benchmark before concurrency.

### M2. Temporary disk amplification

A raw upload can coexist with decoded/processed video, WAV, clips, figures, detections, tracking tables, and output video. A 300-second upload at research bitrate may be about 2 GB, with intermediates significantly larger.

Control: stream frames, use compressed/columnar tables, upload checkpoints, delete only validated uploaded temporaries, and reserve several times the accepted upload limit.

### M3. Hardcoded video assumptions

Research logic contains 59.972 FPS, fixed resolutions, fixed 20,391-frame boundaries, fixed player counts, frame windows, and video-specific tracker/calibration parameters.

Control: probe every upload; carry timebase/FPS/dimensions/player expectation as immutable job metadata; validate every coordinate transform.

### M4. CSV scale and memory use

Research artifacts exceed 100,000 rows and frozen detections exceed 317,000 rows for one session.

Control: Parquet/Arrow or chunked processing for application intermediates; database stores aggregates/metadata, object storage stores large tables.

### M5. Tracker/ReID portability and licensing

Ultralytics BoT-SORT is straightforward, but PRTReID/GTA/Deep-EIoU research code has custom imports and extra dependencies.

Control: keep research identity stacks out of the first production image unless licenses, source pinning, tests, and value are approved.

### M6. Raw transcript leakage

The real raw ASR artifact is unredacted, while public events are pseudonymized.

Control: schema-level public/private separation, redaction tests, and storage policy; never serialize raw names into frontend payloads.

### M7. Grounding depends on exact schema

The report validator checks mandatory limitations, numbers, and forbidden terms. Schema drift can bypass or over-block reports.

Control: version evidence/report schemas and validator rules; deterministic fallback on unknown/invalid output; retain raw validation log.

## Low

### L1. Encoding issues in the frozen payload

Console inspection displayed mojibake for en dashes, quotes, and approximate symbols. The file may be valid UTF-8 but consumers must decode it explicitly.

Control: UTF-8 end-to-end tests; do not rewrite golden bytes merely to normalize display.

### L2. Visualization-only dependencies

Matplotlib/Supervision can enlarge the image and slow cold starts.

Control: isolate optional render worker/dependency group; evidence calculation must not depend on plotting.

### L3. Naming inconsistency

Examples: `Autonomus_scout.ipynb`, `c04_deterministic_response`, and multiple `config`/`configs` directories.

Control: leave research files untouched; use a clean logical naming layer and manifest in the new application.

## Required runtime gate order

1. Validate upload, ownership, consent/authorization metadata, MIME, duration <= 300 s, and probe metadata.
2. Validate selected immutable pipeline manifest and model checksums.
3. Detection and short-term tracking.
4. Persistent-identity attempt and quality gate.
5. Calibration mode/validation gate before metric units.
6. Kinematics with source timestamps and outlier/missing-data policy.
7. ASR/instruction extraction with private/public separation.
8. Fusion: unresolved target or failed identity => withhold player-level assessment.
9. Deterministic evidence and scientific-limitations assembly.
10. Optional report model, then grounding validator; deterministic fallback on failure.
11. Durable artifact upload and frontend result publication.
