# Final demo and visualization polish

**Disposition: `FINAL_DEMO_POLISH_PASS_OVERLAY_DEFERRED`.** The local presentation now navigates from Home to the persisted Phase 6 full-session result, the three frozen oracle-assisted cases, comparison, and research without an upload, Supabase write, Modal job, or LLM call.

## Verified presentation flow

- Home links directly to existing job `9b01f139-5411-4a6d-9f9b-85e6a6fb4cdc` and uses its persisted event/status fields rather than placeholder totals. New Analysis remains a separate action.
- Results has eight panels: Executive Summary, Tactical Events, Video / Media, Radar / Spatial View, Kinematics, Identity Safety, Full Coach Report, and Artifacts / Provenance. It displays the real `METHOD_2_RFDETR_GTATRACK` job, `COMPLETED_WITH_LIMITATIONS`, `DETERMINISTIC_FALLBACK`, `FAIL_UNSAFE_MERGE`, `NO_METRIC_CALIBRATION`, 13 events, and 28 evidence items. Six response windows explicitly say visual evidence is insufficient. The report download button now saves the persisted Markdown.
- The Video tab plays the validated private **Analyzed Session Video** through a short-lived signed read URL issued only for the configured local demo job to a loopback client. Browser metadata loaded: 340 s, 1920×1080. A refresh action renews the playback link. The tab states that no annotated output was generated.
- Showcase reads `GET /api/v1/showcase` from frozen fixtures. C06 Pressing Response and C03 Hold Position play their existing MP4 overlays; C04 Defensive Marking displays its actual PNG contact sheet. Cards select case details, verified instructions, frozen evidence, fixture SHA-256, and the full frozen coach interpretation. Browser media loaded: C06 7.515 s, C03 19.951 s, C04 2400×8520. The page labels these `ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION` and keeps automated identity failure separate.
- Comparison shows configured method stacks and clearly identifies the one persisted M2 product run. It does not derive cross-method rankings from that run. Research remains available. The legacy `/results` mock preview now links to the real persisted result.
- New Analysis keeps the 360 s duration rule and its production upload lifecycle. It removes the inaccurate “Up to 1 GB” claim, states the observed 48 MB accepted / 64 MiB rejected storage probes, and distinguishes backend reachability, upload intent, storage size rejection, transfer/network, validation, and job registration stages.

## Overlay decision

`FULL_SESSION_OVERLAY_RENDER_SOURCE=REQUIRES_INFERENCE_RERUN`. The persisted result has 28 event-level evidence items and video timestamps but no complete frame-indexed boxes, detections, tracklets, or observation parquet. Its artifact registry contains only result, report, metadata, and execution manifest; no `OVERLAY_VIDEO` exists. Offline annotation from the persisted artifacts is therefore unsupported. No 340-second M2 run was started.

## Verification and boundaries

The six requested routes `/`, `/analysis/new`, `/analysis/{job}/results`, `/showcase`, `/comparisons`, and `/research` opened in the local in-app browser. The showcase cases were clicked and their media loaded. Every result tab was activated; the spatial panel was corrected after browser testing found an attempt to render a structured object as text. A clean browser tab then showed no console errors across the demo routes. Broken remote development-logo references were replaced by a local text mark and accurate institutional text. The decorative pitch is static and explicitly labelled as a schematic, never as live tracking.

Final checks: `npm run build` passed, `npx tsc --noEmit` passed, and targeted backend showcase/media tests passed **12/12**. The signed full-session URL returned HTTP 206 for a byte-range request. No screenshots were saved. The local API and frontend must be running and Supabase must be reachable for the private full-session input; showcase media is served from verified local fixtures. No frozen research file, model, methodology, formal metric, oracle measurement, or Phase 6 result was changed.

See [source audit](FINAL_DEMO_SOURCE_AUDIT.md), [changed files](FINAL_DEMO_CHANGED_FILES.md), and [machine-readable verification](FINAL_DEMO_VERIFICATION.json).
