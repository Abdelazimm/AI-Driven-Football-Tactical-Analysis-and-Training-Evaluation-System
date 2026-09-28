# Phase 6 pre-run snapshot

Date: 2026-09-27. Captured before any Phase 6 full-session upload or execution.

## Repository and regression state

- Primary editable workspace: `D:\Final project videos transcripts\AI-Driven Football Tactical Analysis and Training Evaluation System`.
- Secondary research reference: `G:\My Drive\Football_Training_Assistant_MVP` (read only).
- This workspace has no `.git` directory, so a Git commit/status cannot be recorded. SHA-256 hashes of 11 application/configuration files were saved in `scratch/phase6_prerun_code_hashes.json` as the pre-run source snapshot.
- Backend: 271 tests collected. The Phase 5 full regression passed 271/271, with no application changes since then.
- Frontend: `npm run build` PASS; `npx tsc --noEmit` PASS in `frontend/tactical-ai-insights-main`.

## Product infrastructure

- Deployed Modal app: `football-tactical-analysis`; production function: `execute_analysis_worker`.
- Volume: `football-model-checkpoints`; remote paths `/data/models/m2/checkpoint_best_total.pth` and `/data/models/m2/sports_model.pth.tar-60`.
- Remote runtime preflight: PASS, Python 3.11.12, Tesla T4, CUDA available, PyTorch 2.14.0+cu130, torchvision 0.29.0+cu130, FFmpeg 5.1.9. Packaged M2 imports succeeded.
- Detector remote SHA-256: `7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85`, 134,747,227 bytes. ReID remote SHA-256: `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd`, 30,393,613 bytes.
- Supabase `analysis_jobs` connectivity: PASS. Private `analysis-inputs` bucket exists and has no bucket-specific `file_size_limit`; the project-wide limit has not been verified. The backend upload-intent default is 1 GiB, below the 2.39 GB source. The existing `MAX_UPLOAD_SIZE_BYTES` environment override will be set above the measured source size for this final validation; no scientific component will change.
- Backend result retrieval route: HTTP 200 for the real Phase 5 smoke job.
- Configured maximum video duration: 360.0 s. Production Modal worker timeout: 900 s. These are existing settings, unchanged for the first Phase 6 attempt.

## Original source verification

- Path: `G:\My Drive\Football_Training_Assistant_MVP\data\custom\3v3_match_iphone16.MOV`.
- File exists; size: **2,390,441,924 bytes**.
- ffprobe: MOV-family container, duration **340.010000 s**, HEVC video at **3840×2160**, average frame rate **3058650/51001 = 59.97235348326503 fps**, **20,391** video frames, and AAC audio streams.
- Required frozen source SHA-256: `0e676f4327d1e7e7ed458d619e5558f6630fc7efb0dda7bc608aec45cb9a5c71`.
- Actual source SHA-256: **`0e676f4327d1e7e7ed458d619e5558f6630fc7efb0dda7bc608aec45cb9a5c71` — MATCH**. Upload may proceed.

## Calibration decision for first run

The existing public job API rejects `DEMO_FIXED_CALIBRATION` for uploads. The orchestrator does not pass the uploaded source hash to `CalibrationService` for camera compatibility validation. The product calibration permission gate therefore does not approve fixed calibration through this lifecycle, even for the original file. The first run will use `NO_METRIC_CALIBRATION` and withhold metres/km/h. No calibration or scientific rule was changed.

No Phase 6 methodology, model, tracking, ASR, Fusion, calibration, identity, LLM, prompt, validator, or fallback code was modified before this snapshot.
