# Phase 6 changed files and external state

## Product integration changes

- `backend/app/schemas/dispatch.py` and `backend/app/schemas/manifest.py`: optional source/copy SHA-256 and derived-input role fields for worker dispatch and final execution manifest.
- `backend/app/services/dispatch_service.py`: forwards the provenance fields with the single remote dispatch.
- `backend/app/pipeline/orchestrator.py`: records source/copy provenance in the execution manifest and identifies the actual probed input as the verified transport copy.
- `modal_app/worker.py`: verifies downloaded transport-copy SHA-256 before processing, carries provenance into the result, and sets a full-session worker timeout of 10,800 seconds. M2, tracking, ASR, Fusion, calibration, and identity parameters were not changed.
- `frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.tsx`: renders the nested result route through its parent outlet, allowing real persisted results to appear at the results URL.
- `frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.results.tsx`: shows an explicit unavailable state when no overlay video artifact exists, instead of presenting a decorative pitch animation as an annotated result.

## Phase 6 evidence and one-off helpers

- `IMPLEMENTATION_PHASE6_ORIGINAL_UPLOAD_FAILURE.md`, `IMPLEMENTATION_PHASE6_ORIGINAL_UPLOAD_FAILURE_EVIDENCE.json`, and `scratch/phase6_original_failure_timings.json` preserve the failed original upload attempt before updating final artifacts.
- `scratch/phase6_probe_48mb.py`, `scratch/phase6_transport_manifest.py`, `scratch/phase6_transport_vision_check.py`, `scratch/phase6_transport_asr_check.py`, and `scratch/phase6_calibration_gate.py` support the bounded transport gate.
- `scratch/phase6_transport_upload.py`, `scratch/phase6_transport_dispatch.py`, `scratch/phase6_watch_job.py`, `scratch/phase6_collect_final.py`, `scratch/phase6_build_timings.py`, `scratch/phase6_verify_outputs.py`, and `scratch/phase6_artifact_manifest.py` support one real product run and its evidence collection. These scripts are not runtime production dependencies.
- `IMPLEMENTATION_PHASE6_TRANSPORT_COPY_MANIFEST.json`, `IMPLEMENTATION_PHASE6_TRANSPORT_VISION_CHECK.json`, `IMPLEMENTATION_PHASE6_TRANSPORT_ASR_CHECK.json`, and `IMPLEMENTATION_PHASE6_CALIBRATION_GATE.json` record the derived copy, suitability check, and fail-closed metric permission.
- `IMPLEMENTATION_PHASE6_FINAL_E2E_REPORT.md`, `IMPLEMENTATION_PHASE6_FINAL_E2E_RESULT.json`, `IMPLEMENTATION_PHASE6_STAGE_TIMINGS.json`, `IMPLEMENTATION_PHASE6_ARTIFACT_MANIFEST.json`, and this inventory are the final Phase 6 outputs. They record the completed single remote job and its limitations.
- `scratch/phase6_transport/3v3_match_iphone16_PHASE6_TRANSPORT.mp4` is the complete, derived 43,997,249-byte private product input, not the authoritative research source.

## External state

- Supabase accepted the private 43,997,249-byte transport copy and validated media `0ccfbb77-2d37-4e1e-a80a-90f6b9bd44ab` in session `b7a81465-4262-4ae4-b6b5-4d1679967818`.
- Modal app `football-tactical-analysis` was redeployed with provenance verification and the full-session timeout. One job `9b01f139-5411-4a6d-9f9b-85e6a6fb4cdc` was submitted as call `fc-01M3H776A65X2P2VCCATB57FND`.
- The original 2.39 GB upload remains rejected before transfer, with its pending media record preserved. No billing setting was changed.

No G: research artifact, frozen notebook, experiment, benchmark, golden showcase, model checkpoint, or scientific configuration was modified.
