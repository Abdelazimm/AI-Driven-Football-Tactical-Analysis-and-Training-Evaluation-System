# Coach study iteration 01 — traceability

Only the six anonymised responses supplied in the task brief informed this table.

| User-study observation | Design decision | Files changed | Verification evidence |
|---|---|---|---|
| P1: report should be readable and not look like code | Render the existing persisted Markdown with semantic, styled React Markdown and GFM; retain original download | `src/components/coach-report.tsx`, `src/routes/analysis.$jobId.results.tsx`, `package.json`, `package-lock.json` | `before_report.png`, `after_report.png`; browser DOM showed report headings/lists and no raw source wrapper; build and TypeScript passed |
| P2/P4/P6: technical terms difficult; main coaching information first | Add Coach Overview from persisted facts, plain identity and calibration explanation, expandable technical details | `src/routes/analysis.$jobId.results.tsx` | `before_summary.png`, `after_coach_overview.png`, `after_technical_details.png`; browser showed 13 events, 28 evidence items, exact technical codes and withholding |
| P1/P5: automated result and manually verified showcase need clearer separation | Label real result “Automated session analysis”; label showcase page, cards and case details “Manually verified capability demonstration” | `src/routes/analysis.$jobId.results.tsx`, `src/routes/showcase.tsx` | `after_coach_overview.png`, `after_showcase_c03.png`, `after_showcase_c04.png`, `after_showcase_c06.png`; all three cases loaded with original media |
| P3/P5: event timestamps should open the corresponding video moment | Add per-event accessible View in video button, controlled tab state and metadata-aware seek to persisted `start_s` | `src/routes/analysis.$jobId.results.tsx` | `before_events.png`, `after_events.png`, `after_video_early_26.54s.png`, `after_video_late_336.70s.png`; browser player times matched 26.54, 121.00 and 336.70 s |

Screenshot paths in this table are relative to `docs/evaluation/coach_study_iteration/`.
