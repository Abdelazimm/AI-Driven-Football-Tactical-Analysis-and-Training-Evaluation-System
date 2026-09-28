# Coach study iteration 01 — source-first audit

Audit performed before code edits on 27 September 2026. The six anonymised coach responses in the supplied brief are the design source. The authoritative verification target is the existing Phase 6 job `9b01f139-5411-4a6d-9f9b-85e6a6fb4cdc`.

| Surface | Pre-change implementation | Consequence for this iteration |
|---|---|---|
| Results route (`frontend/tactical-ai-insights-main/src/routes/analysis.$jobId.results.tsx`) | Renders persisted `AnalysisResult`; initial Executive Summary exposes technical status codes as the primary content. Eight Radix tabs use `defaultValue`. Tactical Events are static cards. The report is a `pre` containing raw `report_markdown`. Markdown download uses the same persisted string. | Add coach-first wording and disclosure, Markdown presentation, and controlled tabs for event navigation while preserving the result values and download. |
| Showcase route (`src/routes/showcase.tsx`) | Backend-backed C03/C04/C06 cards and media; top text says oracle-assisted, details say `MANUALLY VERIFIED`, and a boundary disclaimer is shown. | Make the manually verified provenance visually prominent across the page and cards. |
| Components (`src/components/`) | `tactical-ui.tsx` supplies `PageIntro` and `StatusBadge`; `ui/tabs.tsx` wraps Radix Tabs. No report, tactical-event, or video-player component is present. | Reuse existing panels, badges and tabs; add one focused report renderer. |
| API and types (`src/lib/api-client.ts`, `shared/schemas/result.ts`) | `getDemoInputVideo` returns the private signed input playback URL for the validated job. `AnalysisResult` contains `report_markdown`, instruction event `start_s`, identity and calibration fields, and evidence items. | Reuse the current signed URL and event timestamps. No backend or schema change is needed. |
| Frontend dependencies | No explicit Markdown rendering package or frontend test script is declared. | Add a maintained React Markdown renderer with GFM; render raw HTML as text/skip it, without `dangerouslySetInnerHTML`. Verify with build, TypeScript and browser. |

Pre-change browser observation for the Phase 6 job: Executive Summary displayed `COMPLETED_WITH_LIMITATIONS`, `DETERMINISTIC_FALLBACK`, `FAIL_UNSAFE_MERGE`, `NO_METRIC_CALIBRATION`, 13 events, 28 evidence items and player-level `WITHHELD`. Full Coach Report exposed literal Markdown syntax; Tactical Events had no video controls. Screenshots are in `docs/evaluation/coach_study_iteration/before_*.png`.

The research workspace on `G:` is read-only. No research artifact, backend path, inference run, persisted result, or scientific status is in edit scope.
