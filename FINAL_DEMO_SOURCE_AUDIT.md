# Final demo source audit

| Surface | Initial state | Evidence and action |
|---|---|---|
| Home `/` | WORKING_BUT_NEEDS_POLISH | Navigation works, but only offers new upload/showcase and uses placeholder telemetry; add existing Phase 6 result shortcut. |
| New Analysis `/analysis/new` | WORKING_BUT_NEEDS_POLISH | Real upload lifecycle exists; 1 GB frontend claim conflicts with observed Supabase HTTP 413 for 64 MiB; network failures lack stage context. Preserve 360 s duration rule. |
| Job telemetry `/analysis/$jobId` | READY | Real job status route and nested results outlet work. |
| Results `/analysis/$jobId/results` | WORKING_BUT_NEEDS_POLISH | Real Phase 6 result renders, but tabs omit event/evidence details and input playback; download button has no action; scientific limitations need clearer presentation. |
| Static `/results` preview | LEGACY | Contained illustrative metrics, coach phrases, a decorative video panel, and a broken remote logo; replace with a link to the persisted real job. |
| Showcase `/showcase` | LEGACY | Three static case cards and schematic pitch; no detail interaction or real media. GoldenFixtureService exists but no API route is registered. |
| Comparison `/comparisons` | WORKING_BUT_NEEDS_POLISH | Method descriptions render; metrics deliberately unavailable pending validated source binding. |
| Research `/research` | WORKING_BUT_NEEDS_POLISH | Method and identity explanations render; image assets may depend on a remote development path. |
| Golden fixtures | READY | C03/C06 MP4, C04 PNG, validated payload/report and SHA-256 manifest exist under `golden/`. These are frozen and read-only. |
| Full-session input media | READY | Validated private Supabase input `0ccfbb77-2d37-4e1e-a80a-90f6b9bd44ab`, linked to Phase 6 job, can be supplied through a short-lived signed read URL. |
| Full-session annotated overlay | MISSING_MEDIA | No `OVERLAY_VIDEO`, observation parquet, detections, tracklets, or per-frame coordinates were persisted. Result has 28 event evidence items and vision timestamps only. `FULL_SESSION_OVERLAY_RENDER_SOURCE=REQUIRES_INFERENCE_RERUN`; defer. |
| Frozen research and model settings | DO_NOT_TOUCH | No methodology, formal evaluation, golden measurement, or research artifact changes are required. |

Phase 6 source: `IMPLEMENTATION_PHASE6_FINAL_E2E_RESULT.json`, canonical job `9b01f139-5411-4a6d-9f9b-85e6a6fb4cdc`; live result API structure inspected without exporting raw transcripts or media.
