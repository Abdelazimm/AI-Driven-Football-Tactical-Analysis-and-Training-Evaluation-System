# Coach user-study iterative design — pass 01

**Disposition: `COACH_STUDY_ITERATION_PASS_WITH_LIMITATIONS`**

This post-user-study design pass used six anonymised coach responses. It changed frontend presentation and navigation only. Scientific methodology, persisted Phase 6 findings, identity and calibration states, report text, showcase evidence and research artifacts were not edited. No inference was launched.

## Implemented feedback themes

1. **Report looked like code.** The persisted Markdown is now displayed with headings, lists, emphasis, tables, quotes, separators and readable spacing. Raw HTML is skipped. The original Markdown download action remains connected to the unmodified persisted string.
2. **Main information should come first.** A Coach Overview now leads the real result with the persisted count of 13 events, the formal identity withholding boundary and the non-metric calibration boundary. Technical codes remain available in an expandable details section and the existing technical tabs. The result is labelled automated; C03/C04/C06 showcase cards and details are labelled manually verified.
3. **Event timestamps should open video.** Every event on the validated full-session result has an accessible button. It selects the existing private video tab, waits for metadata, seeks to the persisted event `start_s`, and scrolls the player into view. The player remains paused with controls available. The existing signed URL refresh is reused.

## Verification

| Check | Result |
|---|---|
| `npm run build` in `frontend/tactical-ai-insights-main` | PASS, exit 0 (client, SSR and Nitro builds) |
| `npx tsc --noEmit` | PASS, exit 0 |
| Existing frontend tests | No test script in `package.json` and no `src` test/spec files found |
| Real Phase 6 result, job `9b01f139-5411-4a6d-9f9b-85e6a6fb4cdc` | Loaded; 13 events and 28 evidence items still displayed; `COMPLETED_WITH_LIMITATIONS`, `FAIL_UNSAFE_MERGE`, `NO_METRIC_CALIBRATION`, `DETERMINISTIC_FALLBACK` and player-level `WITHHELD` remained in the technical view |
| Markdown report | Rendered as document structure in the browser; no raw source `pre` wrapper; download button present and clickable |
| Early event `evt_0` | Source 26.54 s; player `currentTime` 26.54 s, duration 340 s, `readyState` 4 |
| Mid event `evt_7` | Source 121.00 s; player `currentTime` 121.00 s, duration 340 s |
| Late event `evt_12` | Source 336.70 s; player `currentTime` 336.70 s, duration 340 s, `readyState` 4 |
| Showcase | C06 and C03 videos, C04 image, manual-verification wording and frozen evidence displayed |
| Browser fatal errors | No console error entries on the checked result and showcase views |

The browser did not expose a saved file path for the Blob-based Markdown download, so downloaded bytes could not be compared with the persisted source. The download action still uses the unmodified persisted report string; its control was clicked in the browser. Expiry recovery for a signed URL was not forced because it would require waiting for a real expiry; the existing refresh path remains connected. Seek verification measures the HTML video `currentTime`, not frame-exact codec presentation.

Before/after screenshots are in `docs/evaluation/coach_study_iteration/`. The browser's default narrow viewport was retained. Screenshots contain no study participant identifiers.

## Future Work retained from study feedback

Automatic event clips, event-category filtering, repeated-session or player progress tracking, player comparison, new physical workload/high-speed/acceleration metrics, and team compactness or line-spacing analysis were not implemented in this bounded pass.
