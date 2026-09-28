# Phase 5 remote product closure

**Disposition: `IMPLEMENTATION_PHASE5_FINAL_VERIFICATION_PASS` / `IMPLEMENTATION_PHASE5 = APPROVED` (2026-09-27).** One genuine bounded Modal and Supabase lifecycle completed. The machine-readable evidence is `IMPLEMENTATION_PHASE5_REAL_CLOUD_SMOKE.json`.

## Product lifecycle observed

An actual C04 video excerpt (source 167–179 s, encoded as a 11.983333 s, 1920×1080, 60 fps MP4) and the real 7.04 s C04 coach audio were uploaded to the private `analysis-inputs` bucket. The video passed `MediaValidationService` using a signed URL and authoritative ffprobe metadata. The backend API created a job with `methodology_id=AUTO`, which resolved to `METHOD_2_RFDETR_GTATRACK` before persistence. `AnalysisDispatchService` submitted `execute_analysis_worker` through `ProductionModalClient`; the provider returned a real call ID.

| Identifier | Value |
|---|---|
| Session | `b028dbcf-3a09-4923-8fe6-f57b1697b627` |
| Job | `0b4bdb05-1abf-41ac-b172-eed27a9ebc80` |
| Dispatch | `fbe30031-79ab-46e3-b34e-f55601042e6c` |
| Modal call | `fc-01M3GNVRA9KTWF3P7Q78A1WNY4` |
| Deployed app/function | `football-tactical-analysis / execute_analysis_worker` |
| Model volume | `football-model-checkpoints` |

The worker downloaded both objects from private Storage, verified the mounted frozen detector and ReID checkpoint hashes, executed four M2 Vision frames beginning at clip frame 400, ran real faster-whisper ASR, Fusion, structured evidence, and deterministic report fallback. It uploaded four job-scoped artifacts to private `analysis-outputs`, read the canonical result back from a fresh Supabase repository instance, and only then sent an authenticated `SUCCEEDED` callback. The callback transitioned the persisted job to `COMPLETED_WITH_LIMITATIONS` and dispatch to `SUCCEEDED`. The actual backend `GET /api/v1/analysis/jobs/{job_id}/result` returned HTTP 200; each artifact was downloaded and checked nonempty.

## Remote scientific readback

The first remote ASR event ended at source time **171.65 s**, yielding window **[173.65, 177.65] s**. Vision timestamps were **173.6667, 173.6833, 173.7000, 173.7167 s**; all four overlap the window. Five structured evidence items had positive observations. The clip encoding changed the frame rate from the original 59.97235 fps to 60 fps; its explicit 167.0 s source offset preserves the common source-session timeline. No metric calibration was applied, and metric values remained unavailable.

The persisted result reports `FAIL_UNSAFE_MERGE` under `FORMAL_DENSE_GT`, runtime basis `RUNTIME_HEURISTIC_ONLY`, `player_level_analysis_allowed=false`, and an explicit withholding reason. The current clip's runtime fragmentation ratio of 1.0 did not override the formal safety gate. The historical 6.1667 Configuration C ratio was not used as a production attribution. Report status is `DETERMINISTIC_FALLBACK`, with an explicit fallback limitation; no alternate LLM was substituted. The 120 s LLM default was unchanged.

## Infrastructure and persistence closure

- The deployed Python 3.11.12 image passed a remote import preflight for M2, RF-DETR, Deep-EIoU/OSNet/GTA packaged source, Whisper/CTranslate2, OpenCV, scientific libraries, FFmpeg, and Supabase. Modal provided a Tesla T4 and CUDA-enabled PyTorch 2.14.0. The remote volume and worker each verified detector SHA-256 `7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85` (134,747,227 bytes) and ReID SHA-256 `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd` (30,393,613 bytes).
- The four deployed SQL migrations define `analysis_jobs` and private `analysis-outputs` Storage, but no `analysis_results` table. The former `analysis_results` access caused PGRST205. `SupabaseAnalysisJobRepository` now stores immutable job-scoped report, metadata, manifest, and canonical result JSON in private Storage. The result JSON is uploaded last as the readback marker. A table migration was unnecessary.
- `ProductionModalClient` now spawns `execute_analysis_worker`; the legacy placeholder is excluded from the production path. The worker receives Storage references, frame bounds, source offsets, callback URL, and operating modes. The callback-only Modal ASGI endpoint applies the existing constant-time shared-secret check, ownership validation, monotonic progress, state guards, and persisted-result gate. An unauthenticated remote request returned HTTP 401.
- The worker returned timings of 9.702 s media acquisition, 0.849 s model verification, 35.822 s pipeline, 1.825 s persistence, and 49.259 s total. This was a bounded four-frame run, not the 340 s final session.

## Verification and boundaries

Backend and frontend regression results are recorded in `IMPLEMENTATION_PHASE5_TEST_RESULTS.json`. The local C04 smoke and invalidated earlier cloud claim remain historical records; the new cloud JSON is the only remote success evidence. No research source, experiment, frozen evidence, or model weights under `G:\My Drive\Football_Training_Assistant_MVP` were modified. The copied M2 tracking source matches the frozen reference hashes. No full-session run, Oracle rerender, coach study, or final academic report was started.

The results page was not manually populated or used as evidence; the production result API and artifact retrieval were verified directly for this job.
