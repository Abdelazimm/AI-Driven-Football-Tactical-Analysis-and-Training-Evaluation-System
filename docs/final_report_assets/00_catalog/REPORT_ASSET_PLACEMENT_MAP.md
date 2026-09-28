# Placement map

Use high-priority assets first; avoid repeating adjacent views of the same data.

## Introduction / system overview

- `01_introduction/system_overview.svg` — System overview (Priority A; essential). Supports: The integrated product processes private media through Vision, ASR, fusion, safety gates and reporting. The completed full-session run withheld player-level conclusions.

## Design / safety architecture

- `02_design_architecture/fail_closed_identity_gate.svg` — Fail-closed identity gate (Priority A; essential). Supports: All three formal methods failed the identity-safety gate. The Phase 6 run returned scoped non-player evidence while withholding player-level analytics.

## Methodology / Vision

- `03_methodology/vision/methodology_stacks.svg` — Vision method stacks (Priority A; essential). Supports: The formal comparison evaluates complete detector-and-tracker methodologies. M2 is selected for the product, subject to a failed identity-safety gate.
- `tables/formal_clip_protocol.md` — Frozen independent Vision challenge protocol (Priority B; optional/appendix). Supports: Each method ran on four independent fresh-state clips, totaling 3,780 scored frames per method.
- `tables/vision_checkpoint_provenance.md` — Frozen Vision checkpoint provenance (Priority C; optional/appendix). Supports: The formal comparison used specific frozen model artifacts; these hashes identify their checkpoint provenance.

## Methodology / Fusion

- `03_methodology/fusion/response_window_contract.svg` — Fusion response window (Priority A; essential). Supports: Fusion inspects visual evidence from two to six seconds after an instruction ends and explicitly records unavailable responses.

## Methodology / Calibration

- `03_methodology/calibration/calibration_permission_boundary.svg` — Calibration permission boundary (Priority A; essential). Supports: The research homography was denied for the derived transport input; the full-session product result used no metric calibration.

## Methodology / Reporting

- `03_methodology/llm/grounded_reporting_flow.svg` — Report grounding flow (Priority B; optional/appendix). Supports: Structured evidence passes through the frozen Llama 3.1/Patch-001 reporting path; the full-session result used deterministic fallback.
- `tables/grounding_gates.md` — Eight deterministic report-grounding gates (Priority B; optional/appendix). Supports: Patch-001 preserves eight checks for identity, privacy, missing data and unsupported claims.

## Evaluation / Vision

- `tables/vision_formal_aggregate.md` — Official four-clip complete-system Vision evaluation (Priority A; essential). Supports: Official TrackEval aggregate over four independent frozen challenge clips; unsafe shared-track IDs are a separate descriptive audit.
- `05_evaluation/vision/hota_deta_assa.svg` — Official HOTA, DetA and AssA (Priority A; essential). Supports: M2 achieved the highest aggregate HOTA, DetA and AssA across the frozen four-clip complete-system evaluation.
- `05_evaluation/vision/precision_recall.svg` — Precision and recall by complete Vision method (Priority B; optional/appendix). Supports: M3-v1's low IDSW count accompanies very low recall (0.3273); coverage must be considered when interpreting identity diagnostics.
- `05_evaluation/vision/identity_diagnostics.svg` — Distinct identity diagnostics (Priority A; essential). Supports: TrackEval ID switches and the separate one-to-one IoU shared-track audit are different measures; every method retained a failed identity gate.
- `tables/vision_formal_per_clip.md` — Official Vision metrics by frozen challenge clip (Priority C; optional/appendix). Supports: M2 achieved the highest HOTA and IDF1 in each of the four independent challenge clips.
- `05_evaluation/vision/per_clip_idf1.svg` — Per-clip Vision IDF1 (Priority B; optional/appendix). Supports: M2 had the highest IDF1 in all four frozen challenge clips, but failed the separate identity-safety gate.

## Evaluation / ASR

- `tables/asr_frozen_benchmark.md` — Frozen ASR lexical and tactical-event comparison (Priority B; optional/appendix). Supports: Candidate A was selected on the project's coaching audio under the corrected frozen tactical-event protocol.
- `05_evaluation/asr/asr_comparison.svg` — Frozen ASR candidate comparison (Priority A; essential). Supports: Selected Candidate A had 18.4% WER and 83.871% tactical-event F1, versus Candidate B's 36.8% and 66.667% on this project audio.

## Evaluation / LLM

- `tables/llm_formal_selection.md` — LLM frozen formal selection evidence (Priority A; essential). Supports: Both candidates avoided unsupported player identity and unavailable-evidence misuse. Llama 3.1 was selected after 15/16 schema-valid runs versus Qwen3's 5/16.
- `05_evaluation/llm/llm_schema_delivery.svg` — LLM formal schema delivery (Priority B; optional/appendix). Supports: The selected Llama 3.1 candidate completed and schema-validated 15/16 frozen cases, while Qwen3 did so for 5/16.

## Evaluation / Calibration

- `05_evaluation/calibration/corrected_landmark_errors.svg` — Independent calibration residuals (Priority A; essential). Supports: Four independent landmarks support a corrected research-camera RMSE of approximately 0.651 m, with maximum error 0.841 m.

## Implementation / Phase 6

- `tables/phase6_media_provenance.md` — Phase 6 source and transport provenance (Priority B; optional/appendix). Supports: The accepted product input was a downscaled, nontrimmed derived copy with 20,391 frames; it is distinct from the research source.
- `04_implementation/phase6_transport_provenance.svg` — Phase 6 transport provenance (Priority A; essential). Supports: The 2.390 GB original could not be uploaded; the 44.0 MB nontrimmed downscaled copy was accepted and used for the 340-second M2 E2E run.

## Evaluation / E2E

- `tables/phase6_measured_timings.md` — Measured Phase 6 worker timings (Priority C; optional/appendix). Supports: The worker total was 2,032.682 s (33 min 52.682 s); the pipeline aggregate dominated.
- `05_evaluation/end_to_end/worker_timing.svg` — Measured Phase 6 worker components (Priority A; essential). Supports: The measured pipeline aggregate was 2,012.314 s of a 2,032.682 s worker run. Individual Vision/ASR/fusion/report durations are unavailable.
- `05_evaluation/end_to_end/event_categories.svg` — Phase 6 tactical event categories (Priority B; optional/appendix). Supports: The full-session run yielded 13 tactical events: six pressing, four positioning and three defensive.
- `05_evaluation/end_to_end/missing_response_windows.svg` — Phase 6 unavailable response windows (Priority B; optional/appendix). Supports: Six response windows lacked tracking or visual observations; some extend beyond the 340-second media boundary.
- `tables/phase6_e2e_summary.md` — Phase 6 full-session result (Priority A; essential). Supports: The accepted derived transport copy completed the full product path with explicit identity, calibration and report limitations.

## Evaluation / user study

- `tables/coach_study_likert.md` — Coach-study descriptive Likert summary (n=6) (Priority C; optional/appendix). Supports: Six respondents rated 16 prototype statements/items on a 1–5 scale; all means and response counts derive from the hash-matched CSV.
- `05_evaluation/user_study/study_item_means.svg` — Coach-study item means (Priority A; essential). Supports: Withholding explanation was the lowest-rated item (3.83/5), informing the subsequent coach-facing design iterations.
- `tables/coach_study_future_preferences.md` — Future-capability selections (n=6) (Priority B; optional/appendix). Supports: Four of six respondents selected comparison between players as a desired capability for a reliable future version.
- `05_evaluation/user_study/future_capabilities.svg` — Coach-study future-capability preferences (Priority B; optional/appendix). Supports: Player comparison was the most selected future capability (4/6), but requires safe persistent identity before implementation.
- `tables/coach_study_profile.md` — Coach-study participant profile (Priority B; optional/appendix). Supports: The six participants included head coaches, assistant coaches, an analyst and a former player.

## Iterative design

- `screenshots/before_report.png` — Pass 01 before: report (Priority B; optional/appendix). Supports: Pass 01 before: report from the recorded iterative-design evidence.
- `screenshots/after_report.png` — Pass 01 after: coach report (Priority B; optional/appendix). Supports: Pass 01 after: coach report from the recorded iterative-design evidence.
- `screenshots/before_showcase_plain_report.png` — Pass 02 before: plain showcase report (Priority B; optional/appendix). Supports: Pass 02 before: plain showcase report from the recorded iterative-design evidence.
- `screenshots/after_full_session_summary_rich_report.png` — Pass 02 after: full-session rich report (Priority B; optional/appendix). Supports: Pass 02 after: full-session rich report from the recorded iterative-design evidence.
- `screenshots/after_c04_summary_rich_report.png` — Pass 02 after: C04 rich report (Priority B; optional/appendix). Supports: Pass 02 after: C04 rich report from the recorded iterative-design evidence.
- `screenshots/after_coach_overview.png` — Pass 01 after: coach overview (Priority B; optional/appendix). Supports: Pass 01 after: coach overview from the recorded iterative-design evidence.
- `06_iterative_design/feedback_to_ui_iterations.svg` — Iterative design rationale (Priority A; essential). Supports: The lowest-rated explanation item and qualitative readability feedback informed coach-first summaries and richer report presentation across two recorded passes.

## Limitations / future work

- `tables/limitations_matrix.md` — Evidence and reporting limitations (Priority A; essential). Supports: The result is useful when evidence scope, missing data and failed safety gates remain visible.

## Evaluation / showcase

- `tables/oracle_showcase_scope.md` — Three frozen oracle-assisted showcase cases (Priority A; essential). Supports: C06 pressing, C04 defensive marking and C03 hold position demonstrate manually verified capabilities.

# Completion pass placements

- **Requirements and Design / detailed architecture** — `02_design_architecture/detailed_product_architecture.svg` (Priority A; essential). Supports: The final React/TanStack frontend uses a FastAPI control plane, private Supabase persistence and a Modal compute worker; results return through durable job state and scoped evidence.
- **Requirements and Design / research boundary** — `02_design_architecture/product_research_boundary.svg` (Priority A; essential). Supports: The D: workspace owns product code and contracts, while the mounted G: workspace supplies frozen Vision, ASR, LLM, homography and formal-evaluation evidence through controlled read-only adaptation.
- **Methodology / calibration** — `03_methodology/calibration/coordinate_space_flow.svg` (Priority B; optional). Supports: Vision operates in a 1920×1080 working plane. Its working-space footpoints enter an approved homography for metric projection; adapters separately return bounding boxes to the dynamically probed source space.
- **Methodology / ASR** — `03_methodology/asr/asr_pipeline.svg` (Priority B; optional). Supports: Coach audio is normalized to 16 kHz mono, transcribed with frozen faster-whisper base.en, and mapped deterministically into the five frozen tactical-event categories.
- **Methodology / calibration** — `03_methodology/calibration/kinematics_pipeline.svg` (Priority B; optional). Supports: Metric movement derives from validated footpoints and approved homography, using seven-observation smoothing and actual probed FPS; gaps and implausible speeds are excluded.
- **Implementation / job lifecycle** — `04_implementation/product_job_lifecycle.svg` (Priority B; optional). Supports: Validated private media enters a session/job, is dispatched idempotently to Modal, and returns authenticated progress plus persisted results for review.
- **Evaluation / Vision** — `05_evaluation/vision/key_outcome_metrics.svg` (Priority B; optional). Supports: M2 led the frozen four-clip complete-system comparison on HOTA, MOTA and IDF1; all three methods nevertheless failed the formal identity-safety gate.
- **Methodology / Vision** — `03_methodology/vision/formal_clip_timeline.svg` (Priority B; optional). Supports: The four formal challenge clips occupy distinct positions in the research session and were evaluated with fresh tracker state for 3,780 frames per method.
- **User Study / response detail** — `05_evaluation/user_study/key_likert_distribution.svg` (Priority B; optional). Supports: Five report-relevant items show their full six-response distributions, including the two neutral ratings for the withholding explanation.
- **Implementation / UI capture** — `screenshots/completion_home_current.png` (Priority B; optional). Supports: Current homepage shows the official project title and navigation to the validated full-session result and showcase.
- **Implementation / final UI** — `04_implementation/final_ui_workflow.png` (Priority A; essential). Supports: Actual current homepage and recorded final coach-overview/event captures show navigation from entry to scoped full-session evidence.
- **Implementation / final UI** — `04_implementation/final_ui_evidence_review.png` (Priority B; optional). Supports: Recorded final UI shows event-to-video navigation, explicit identity withholding and report/provenance presentation.
- **Evaluation / showcase** — `05_evaluation/showcase/showcase_cases.png` (Priority A; essential). Supports: The frozen C03, C04 and C06 showcase cases use manually verified identity, targets and tactical meaning; the panels are real recorded UI captures.
