# Coach study iterative design — Pass 02

**Disposition: `COACH_STUDY_ITERATION_PASS02_PASS_WITH_LIMITATIONS`**

This was a frontend presentation pass. The user-study theme was that coach reports should be readable and lead with plain language. The remaining inconsistency was observed during development after Pass 01: the full-session result used the rich `CoachReport` renderer, while `/showcase` still put the frozen combined Markdown report in a plain `<pre>`. The six original coach responses did not specifically identify the showcase renderer inconsistency.

## Changes

The shared `CoachReportPresentation` component now supplies the scope badge, Coach-Friendly Summary and unchanged rich Markdown report in both routes. `CoachReport` remains the single Markdown renderer, with GFM support and raw HTML skipped. The full-session detailed report appears immediately below its summary; the longer frozen showcase report remains available in an expandable section below the selected case summary. The showcase API supplies **one** frozen `full_coach_report_markdown` covering C03, C04 and C06, so the UI labels that combined scope explicitly and does not split or rewrite the source text.

The summary is a UI-only layer; it is not added to either report string or to the full-session Markdown download. No model, inference, research artifact, backend route, fixture, scientific status, metric or report content was changed.

## Summary grounding

| Report | Structured sources used | Display rule |
|---|---|---|
| Full session | `job_status`, `instruction_events.length`, `identity_evaluation.method_formal_identity_status`, `identity_evaluation.player_level_analysis_allowed`, `calibration_mode`, and count of `structured_evidence.evidence_items` with missing-visual-evidence limitation codes | Builds up to four short sentences. The formal-benchmark wording appears only for `FAIL_UNSAFE_MERGE` with player conclusions withheld; distance/speed suppression appears only for `NO_METRIC_CALIBRATION`; the missing-window count appears only when positive. |
| C03 | `card.id`, `card.title`, `card.response_summary`; frozen showcase manual-verification/disclaimer state | The plain-language zone sentence is shown only when the frozen response confirms entry and retention. Otherwise its recorded first sentence is displayed. No number is added. |
| C04 | Same card fields and frozen showcase provenance | The plain-language marking sentence is shown only when the frozen response confirms reduced ground-plane separation and lower follow-up median separation. Otherwise its recorded first sentence is displayed. No number is added. |
| C06 | Same card fields and frozen showcase provenance | The plain-language pressing sentence is shown only when the frozen response confirms reduced separation in both events. Otherwise its recorded first sentence is displayed. No number is added. |

The showcase summary reminds readers that manual verification does not certify automated persistent identity; this matches the frozen disclaimer and `scientific_automated_status`. Existing numeric case metrics remain in the case evidence and full Markdown report.

## Verification

| Check | Result |
|---|---|
| Full Phase 6 result | Coach-Friendly Summary precedes rich report; the exact persisted report is passed directly to the renderer. Technical details still show `COMPLETED_WITH_LIMITATIONS`, `FAIL_UNSAFE_MERGE`, `NO_METRIC_CALIBRATION`, `DETERMINISTIC_FALLBACK`, 13 events, 28 evidence items and `WITHHELD`. |
| C03 | Summary and rich combined report visible when expanded; C03 overlay video loaded (`readyState` 4); manual/oracle provenance visible. |
| C04 | Summary and rich combined report visible when expanded; contact sheet loaded (`naturalWidth` 2400); manual/oracle provenance visible. |
| C06 | Summary and rich combined report visible when expanded; C06 overlay video loaded (`readyState` 4); manual/oracle provenance visible. |
| Event → video regression | `evt_0` still opened the existing private 340 s player at 26.54 s with controls and paused playback. |
| Markdown download | Existing button remained present and was clicked. The browser did not expose a saved download path for byte comparison. Source still uses `result.report_markdown` directly. |
| Browser console | No error entries on the checked views. |
| `npm run build` | PASS, exit 0. |
| `npx tsc --noEmit` | PASS, exit 0. |
| Existing frontend tests | No test script or `src` test/spec files found. |

Screenshots are in `docs/evaluation/coach_study_iteration_pass02/`. The default narrow browser viewport was retained. The frozen showcase exposes one combined report for all three cases; this is a source-data boundary, not a generated per-case report. Download bytes remain unverified because the in-app browser did not provide a saved file path.
