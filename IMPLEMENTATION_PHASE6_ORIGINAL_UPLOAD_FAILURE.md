# Phase 6 final full-session end-to-end validation

**Current disposition: `PHASE6_FINAL_FULL_E2E_FAILED` at the product upload gate.** No full-session analysis was run, and no production runtime or scientific output is claimed. The blocker is Supabase's project-wide Storage upload size cap, which rejected the authoritative 2,390,441,924-byte original source before any bytes transferred.

## Pre-run verification

The original iPhone 16 MOV exists in the read-only research reference and its actual SHA-256 is `0e676f4327d1e7e7ed458d619e5558f6630fc7efb0dda7bc608aec45cb9a5c71`, exactly matching the frozen authoritative hash. ffprobe measured 340.010000 s, 59.97235348326503 fps, 3840×2160 HEVC, 20,391 video frames, and AAC audio streams; size is 2,390,441,924 bytes. The pre-run snapshot records repository, frontend, Supabase, Modal, GPU, and exact remote M2 checkpoint checks.

The product maximum duration remains 360 s. The existing job API rejects `DEMO_FIXED_CALIBRATION` for uploads; the orchestrator does not pass a verified source hash into the calibration permission service. This run therefore selected `NO_METRIC_CALIBRATION` and would suppress metres/km/h. No calibration rule or other frozen methodology component was altered.

## Real product attempt and blocker

The backend API created session `b7a81465-4262-4ae4-b6b5-4d1679967818` and issued HTTP 201 for a video upload intent. The resulting media asset `6591dcf9-2691-4d95-b1dd-2ecfd6545e80` remains `PENDING`. The original source was targeted to the private `analysis-inputs` bucket at `b7a81465-4262-4ae4-b6b5-4d1679967818/video/6591dcf9-2691-4d95-b1dd-2ecfd6545e80_3v3_match_iphone16.MOV`.

The backend's default 1 GiB upload-intent ceiling was raised only through its existing `MAX_UPLOAD_SIZE_BYTES` environment setting for this one-off process. Supabase then rejected the resumable upload creation with **HTTP 413, “Maximum size exceeded.”** A separate **64 MiB** creation probe also returned HTTP 413. The bucket has no bucket-specific file limit, so the observed constraint is project-wide. The exact project limit and billing plan could not be read; the signed-in dashboard was unavailable. The product Storage object was verified absent and zero media bytes transferred. Supabase [documents plan-level global Storage limits](https://supabase.com/docs/guides/storage/uploads/file-limits), with Free projects capped at 50 MB; this project's plan was not verified.

No full-session AnalysisJob was created, so there is no dispatch ID, Modal call ID, worker stage log, ASR/Fusion result, report, callback, frontend real-result page, or final API result. These are explicitly null or `NOT_STARTED` in the Phase 6 machine-readable artifacts. The earlier bounded Phase 5 remote smoke remains valid but cannot stand in for the requested full-session measurement.

## Regression and scientific boundaries

Frontend `npm run build` and `npx tsc --noEmit` passed in the pre-run snapshot. Backend `pytest backend/tests -q --disable-warnings --basetemp scratch/pytest_phase6_final` passed **271/271 tests, 0 failures, 0 skips, in 282.95 s**. No application code, model weights, tracking/ASR/Fusion parameters, calibration, identity rules, LLM prompt/model, or deterministic fallback semantics were changed. No research experiment, Oracle rerender, coach study, or academic report writing was started.

## Required external action

Raise the current Supabase project's global Storage file-size limit above **2,390,441,924 bytes** (3 GiB provides margin), and verify the plan permits that value. A billing change, if required, must be handled by the account owner. Once the limit is raised, resume the existing upload intent/session for the same hash-verified original source, complete media validation, create one `AUTO` job, and perform the requested single full-session run. The existing 900 s Modal worker timeout remains unchanged for the first attempt; if it later fails, that outcome must be measured and documented before any minimal infrastructure correction.
