# Deployment Targets & Infrastructure Specifications

## 1. Target Infrastructure Overview

The production deployment architecture is distributed across serverless cloud platforms to balance developer agility, GPU cost efficiency, and low-latency client experiences.

| Component | Target Platform | Runtime / Specifications | Purpose |
|---|---|---|---|
| **Frontend** | Vercel | Next.js (App Router), React, TypeScript | User dashboard, upload interface, results visualizer, golden showcase |
| **Relational Database** | Supabase Cloud | Managed PostgreSQL 15+ with JSONB | Application state, session metadata, job checkpoints, tactical events |
| **Object Storage** | Supabase Cloud | S3-compatible Object Storage | Raw video uploads, extracted audio, rendered clips, Parquet tables, golden media |
| **API Control Plane** | Modal / Cloud Container | Python 3.10+, FastAPI | Session creation, presigned upload URLs, job dispatch, status polling |
| **Heavy Inference Worker** | Modal Serverless Compute | Linux container with NVIDIA T4 GPU (16 GB VRAM) | On-demand video decoding, YOLO11m, BoT-SORT, Faster-Whisper, kinematics |

---

## 2. Ingestion Constraints & Policies

- **Maximum Upload Duration**: **300 seconds** (5 minutes).
- **Format Support**: Standard MP4 / MOV formats encoded with H.264 / AAC.
- **Probe Validation**: An initial lightweight validation step runs `ffprobe` on the uploaded container before any GPU hardware is allocated. If the video duration exceeds 300.0 seconds or lacks required streams, the job fails immediately at the `VALIDATING` stage without incurring GPU compute costs.

---

## 3. Asynchronous Background Job Pattern

Long-running video inference over footage up to 300 seconds requires background execution:

1. **Immediate Job Acknowledgment**:
   - When the user confirms video upload, the API control plane records a new `analysis_jobs` entry with status `UPLOADED` and returns immediately with a unique `job_id`.
   - The browser HTTP request terminates in $< 500\text{ ms}$. No client request is ever kept waiting or blocked for video processing.

2. **Decoupled Job Dispatch**:
   - The API triggers an asynchronous Modal serverless function (`spawn` or webhook queue).
   - Modal dynamically provisions container instances.

3. **On-Demand GPU Utilization**:
   - The NVIDIA T4 GPU container is spun up **on demand** and terminated as soon as GPU-intensive tasks (detection, optional GPU ASR) complete.
   - It does **not** remain permanently active or idle, preventing unnecessary operational costs.
   - CPU-only stages (probing, tracking association, homography mapping, kinematics smoothing, report generation) execute within CPU-optimized task boundaries.

4. **Progress Observation**:
   - The background worker updates the database row at every stage transition with `current_stage` and `progress_percent` (0.0% to 100.0%).
   - The Next.js frontend observes job progression via Supabase Realtime subscriptions or lightweight interval polling ($2\text{ s}$ to $5\text{ s}$).

---

## 4. Storage & Bandwidth Optimization

- **Direct Browser Uploads**: Video bytes flow directly from the user's browser to Supabase Storage via signed presigned URLs. Video files never traverse the Next.js server or the FastAPI gateway.
- **Private vs. Public Storage Separation**:
  - `raw-video` and `raw-audio` buckets are strictly private with Row-Level Security (RLS) and signed URL access only.
  - Golden showcase media assets and pseudonymized evaluation summaries are stored in access-controlled public/read-only buckets.
