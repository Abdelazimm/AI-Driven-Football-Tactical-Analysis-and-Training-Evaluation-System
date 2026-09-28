# Deployment dependency audit

No production `requirements.txt`, `pyproject.toml`, lockfile, Dockerfile, Modal app, or root `package.json` exists. The `.soccertrack-v2-reference/pyproject.toml` belongs to third-party/reference research code and is not an application manifest.

## Core API

| Dependency | Observed version | Requirement | Deployment note |
|---|---|---|---|
| FastAPI | not present | future API | Add and pin in the new backend package; do not infer version from environment |
| Uvicorn | not present | future ASGI serving/local test | Add and pin if used; Modal may invoke ASGI directly |
| Pydantic | 2.13.4 observed in audio runtime | schemas/validation | Align FastAPI and Pydantic versions; migrate notebook models into a shared schema package |

## Vision

| Dependency | Observed version | CUDA/system needs | Modal/T4 note |
|---|---|---|---|
| PyTorch | 2.11.0+cu128 observed | CUDA-compatible wheel/driver for GPU | Pin a T4-compatible CUDA image; do not blindly reuse Colab runtime |
| torchvision | 0.26.0+cu128 observed | must match PyTorch | Required by vision/ReID research paths; verify only selected production path |
| Ultralytics | 8.4.150 recovered for Experiment C; other notebook cells may have later installs | PyTorch; CUDA optional | Pin 8.4.150 only for exact Experiment C reproduction; a Stage4B deployment also needs compatibility verification |
| OpenCV (`cv2`) | version not reliably frozen | system video/image codecs; headless preferred | Use `opencv-python-headless`; video encode/decode should rely on ffmpeg where practical |
| NumPy | version not reliably frozen | ABI compatibility with OpenCV/Pandas/SciPy | Pin as a tested set |
| Pillow | version not reliably frozen | none | report/showcase image rendering |

## Tracking and persistent-identity research

| Dependency | Observed use | Runtime decision |
|---|---|---|
| Ultralytics BoT-SORT | short-term tracker | candidate runtime component; extract configuration and test independently |
| `lap` | assignment solver in research cells | needed only by selected tracker implementation; pin if required |
| SciPy | Hungarian assignment, distances/filtering | likely required by stitching/evaluation; pin |
| scikit-learn | research metrics/analysis | omit unless extracted runtime code imports it |
| supervision | visualization/utility experiments | optional; avoid production dependency if simple drawing/schema code replaces it |
| PRTReID / torchreid | E0-E6 appearance research | research-only until separately approved; did not pass identity gate |
| GTA Tracklet code | identity split/connect research | research-only |
| custom Deep-EIoU tracker | E6 research | research-only |
| yacs, gdown, loguru, joblib | research/ReID tooling | exclude unless selected runtime module proves necessary |

## Audio

| Dependency | Observed version/config | System/model needs | Modal note |
|---|---|---|---|
| Faster-Whisper | 1.2.1 | CTranslate2; `base.en` model snapshot | CPU int8 is the verified path; bake/cache model rather than download on every request |
| CTranslate2 | installed transitively; exact version not preserved in audited summary | CPU instruction set or compatible CUDA/cuDNN for GPU | Keep CPU path initially unless GPU ASR is benchmarked with detector lifecycle |
| ffmpeg-python | 0.2.0 observed | `ffmpeg` and `ffprobe` OS binaries | Python package alone is insufficient; install binaries in image |
| gTTS | 2.5.4 observed | network for synthesis | synthetic test fixture only; not required for real production analysis |

## Geometry and data

| Dependency | Purpose | Note |
|---|---|---|
| OpenCV | perspective transform, frame I/O, drawing | calibration must retain coordinate-space metadata |
| NumPy | matrix/kinematics operations | validate finite values and dtype boundaries |
| Pandas | notebook CSV/event processing | acceptable for prototypes; use streaming/Parquet for large observations where possible |
| SciPy | assignment/statistics | only include selected functions |
| PyYAML | tracker configuration | validate configuration against an application schema |
| ijson | memory-safe large JSON parsing | useful for research annotation imports; not necessarily upload runtime |

## Reporting

| Dependency | Current use | Deployment note |
|---|---|---|
| Ollama 0.34.1 + `qwen3:8b` | local structured report generation | local Windows/localhost dependency; cannot be assumed on Modal/Vercel |
| Python JSON/Pydantic | deterministic evidence and validator | reusable and should remain authoritative |
| Matplotlib | audit figures | CPU-only; separate optional render layer from core evidence |

## Video/system packages

- Required: `ffmpeg`, `ffprobe`, video codecs needed for input probe/audio extraction/output rendering.
- Likely runtime: OpenCV headless; fonts for deterministic labels; temporary filesystem with an explicit quota.
- Avoid relying on Colab Drive FUSE, `/content/drive`, notebook display libraries, Google Colab APIs, Windows drive letters, or `localhost:11434`.

## Model build/download policy

1. Create a deployment manifest containing logical name, source, exact byte size, SHA-256, framework/version, license, and intended stage.
2. Resolve the detector ambiguity before building an image.
3. Bake small/critical weights in a versioned image or populate a read-only Modal volume during a controlled build step.
4. Pin Faster-Whisper model revision and record its measured cache size/checksums.
5. Never use an unpinned `pip install` or implicit model download in a user request.

## Environment evidence, not a production lock

- Vision/E6 runtime evidence: Python 3.13.15, PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, CUDA 12.8, Tesla T4.
- Audio runtime evidence: Python 3.12.13, PyTorch 2.11.0+cu128, Faster-Whisper 1.2.1, gTTS 2.5.4, ffmpeg-python 0.2.0, Pydantic 2.13.4.

These mixed notebook environments demonstrate feasibility but are not a reproducible deployable environment.
