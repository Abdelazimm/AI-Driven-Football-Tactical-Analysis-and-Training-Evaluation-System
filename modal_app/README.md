# Modal Serverless Compute Worker (Reserved)

## 1. Role & Infrastructure

This directory is reserved for the asynchronous serverless execution definitions on [Modal](https://modal.com/).

- **Target Hardware**: NVIDIA T4 GPU (16 GB VRAM) on demand for GPU inference; dynamically scheduled CPU tasks for non-GPU stages.
- **Trigger**: Asynchronous invocation dispatched by the FastAPI control plane upon video upload completion.
- **Maximum Execution Duration**: Sized for videos up to 300 seconds (5 minutes).

---

## 2. Planned Pipeline Execution Stages

The worker will execute the following modular pipeline stages:
1. `VALIDATING` & `PREPROCESSING`: `ffprobe` duration and format verification ($\le 300\text{ s}$).
2. `DETECTING`: Stage 4B fine-tuned YOLO11m on NVIDIA T4 (3 horizontal tiles, global NMS 0.70).
3. `TRACKING`: BoT-SORT short-term tracking association.
4. `IDENTITY_EVALUATION`: Scientific identity gate check (acceptance threshold $\le 1.5$).
5. `CALIBRATING`: Planar homography mapping (if calibrated).
6. `KINEMATICS`: 7-frame median smoothing, outlier rejection ($> 36\text{ km/h}$).
7. `AUDIO_EXTRACTION` & `TRANSCRIBING`: `ffmpeg` 16 kHz WAV + Faster-Whisper `base.en`.
8. `INSTRUCTION_PARSING`: Tactical instruction event extraction.
9. `FUSION`: Multimodal time-window alignment and fail-closed gate enforcement.
10. `GENERATING_EVIDENCE` & `GENERATING_REPORT`: Deterministic evidence compilation and grounded reporting.
11. `RENDERING` & `UPLOADING_RESULTS`: Storage persistence and database status update.
