# Final demo changed files

## Read-only API and tests

- `backend/app/api/showcase.py`: frozen showcase metadata and verified, range-capable local media routes.
- `backend/app/api/router.py`: register showcase routes.
- `backend/app/services/golden.py`: per-case media SHA-256 verification before serving.
- `backend/app/api/jobs.py`: loopback-only signed input playback for the configured completed demo job.
- `backend/app/core/config.py`: configurable presentation job ID, defaulting to the existing Phase 6 job.
- `backend/tests/test_demo_routes.py`: frozen cases, media MIME/range, and invalid-case checks.

## Frontend

- `frontend/tactical-ai-insights-main/src/lib/demo.ts`: existing job link configuration.
- `frontend/tactical-ai-insights-main/src/lib/api-client.ts`: showcase/media and demo playback reads plus clearer transport errors.
- `frontend/tactical-ai-insights-main/src/components/app-shell.tsx`: working local text mark and accurate presentation status.
- `frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx`: static pitch illustration labelled as schematic rather than live tracking.
- `frontend/tactical-ai-insights-main/src/routes/index.tsx`: real-job shortcut and persisted home snapshot.
- `frontend/tactical-ai-insights-main/src/routes/analysis.new.tsx`: observed storage-limit wording and staged error descriptions.
- `frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.results.tsx`: real input video, event/evidence panels, safety wording, report download, artifact provenance.
- `frontend/tactical-ai-insights-main/src/routes/showcase.tsx`: backend-backed interactive C03/C04/C06 cases and real media.
- `frontend/tactical-ai-insights-main/src/routes/comparisons.tsx`: configured method comparison and single-run evidence context.
- `frontend/tactical-ai-insights-main/src/routes/research.tsx`: accurate local institutional attribution in place of an unavailable remote asset.
- `frontend/tactical-ai-insights-main/src/routes/results.tsx`: retire illustrative mock results and link to the real job.
- `frontend/tactical-ai-insights-main/src/routes/analysis.processing.tsx`: clarify the legacy preview and its schematic pitch.

## Evidence

- `FINAL_DEMO_SOURCE_AUDIT.md`, `FINAL_DEMO_POLISH_REPORT.md`, `FINAL_DEMO_VERIFICATION.json`, and this inventory.
- `scratch/final_demo_build.log`, `scratch/final_demo_tsc.log`, and `scratch/final_demo_backend_tests.log` contain final checks.

No golden fixture or frozen research artifact was edited.
