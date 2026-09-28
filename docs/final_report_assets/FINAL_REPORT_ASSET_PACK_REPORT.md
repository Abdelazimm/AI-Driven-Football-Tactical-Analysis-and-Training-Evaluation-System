# Final report visual asset pack

**Disposition:** `FINAL_REPORT_ASSET_PACK_COMPLETION_PASS`  
**Project:** AI-Driven Football Tactical Analysis and Training Evaluation System  
**Scope:** Report assets only; no dissertation prose or product/research changes.

## Audit and evidence

The audit began with the canonical v89 evidence log supplied in Downloads, then reconciled the frozen Vision aggregate and per-clip results, identity-safety record, formal clip protocol, ASR comparison, LLM selection/freeze and model provenance against direct **read-only G:** research files after the drive was mounted. Direct D: artifacts supplied the Phase 6 result, measured timings, transport/calibration gates, corrected independent landmark records, frozen showcase scope and iterative-design screenshots. The original coach-study CSV was read in memory from the Downloads ZIP; its uncompressed SHA-256 exactly matches the hash in v89. Only aggregate study outputs were exported.

Every catalog entry lists source paths and SHA-256 hashes, fields, derivations, caption, guardrail, priority and intended report placement. Numeric graphs have CSV extracts in `source_data/`. The [catalog](00_catalog/REPORT_ASSET_CATALOG.md), [captions](00_catalog/REPORT_ASSET_CAPTIONS.md), [placement map](00_catalog/REPORT_ASSET_PLACEMENT_MAP.md), and [machine-readable manifest](FINAL_REPORT_ASSET_PACK_MANIFEST.json) are the entry points for report assembly.

## Baseline inventory before the completion pass

| Asset class | Count | Format |
|---|---:|---|
| Diagrams | 8 | SVG + PNG |
| Quantitative graphs | 12 | SVG + PNG at 300 DPI |
| Report-ready tables | 15 | Markdown + CSV |
| Preserved UI screenshots | 6 | PNG |
| Chart source-data extracts | 11 | CSV |
| Catalog entries | **41** | One entry per figure, table, or screenshot |

**Priority A (main report, select without duplicating adjacent evidence):** system overview; fail-closed identity gate; Vision method stacks; fusion response-window contract; calibration permission boundary; formal Vision aggregate table and HOTA/DetA/AssA graph; distinct identity diagnostics; ASR comparison; LLM selection table; corrected calibration residuals; Phase 6 transport provenance and worker timing; Phase 6 result table; coach-study means; iterative-design rationale; limitations matrix; oracle-assisted showcase scope table.

**Priority B (space permitting):** grounded-report flow; Vision precision/recall and per-clip IDF1; ASR and LLM supporting tables/graph; eight grounding gates; Phase 6 provenance and event/window details; coach-study future preferences and participant profile; six recorded before/after UI screenshots; formal clip protocol.

**Priority C (appendix candidates):** full per-clip Vision table; frozen Vision checkpoint hashes; full 16-item coach-study Likert table; exact measured Phase 6 worker component table. Priority is also recorded per item in the catalog and placement map.

## Additional assets discovered during audit

- The hash-matched study ZIP made all 16 item means and rating distributions directly reproducible while keeping participant rows private.
- The four independent Vision clip records supported a per-clip IDF1 view and table, separating frozen challenge performance from full-session identity safety.
- The separate unsafe shared-track audit was paired with official TrackEval IDSW in a two-panel figure so the measures cannot be conflated.
- The Phase 6 record supported an event-category chart and six missing-response-window segments, including windows beyond media end.
- The G: LLM selection decision supported a schema-delivery chart with the pre-patch grounding false-positive caveat.
- Direct checkpoint and protocol manifests supported provenance and appendix tables.

## Scientific guardrails embedded in the assets

- M2 has the strongest observed aggregate complete-system Vision metrics in the frozen four-clip comparison, yet **all three methods fail** the formal identity-safety gate. Player-level accumulated analytics remain withheld. Historical full-session fragmentation 6.1667 is kept separate from the final dense-GT comparison.
- M3-v1's low IDSW is shown alongside its low recall and high FN. Shared-track audit counts are never relabeled as TrackEval IDSW. The methodology diagram identifies modified GTA and SRITrack-v1 rather than implying vanilla implementations.
- The corrected 0.651 m RMSE belongs only to the research camera. The Phase 6 derived transport input used `NO_METRIC_CALIBRATION`; no metres, km/h, zero movement, or player-specific metric claims are inferred.
- The original media, its derived copy and the accepted product run have distinct provenance. The rejected original and 64 MiB probe do not establish an exact storage limit.
- The full-session run completed with limitations in 2,032.682 measured worker seconds. Separate Vision/ASR/fusion/report runtimes were unavailable. It used a deterministic report fallback and produced no full-session overlay.
- The three showcase cases are explicitly oracle-assisted with manual verification; they are not evidence that automated persistent identity passed.
- The six-person coach study is descriptive. No population inference, significance testing, fabricated theme frequency, or measured post-iteration improvement is claimed.

## Assets deliberately omitted

No metric speed/distance plot was created for the uncalibrated Phase 6 run; no full-session overlay was fabricated; no cross-method runtime ranking was made from noncontrolled logs; no exact Supabase limit was inferred; no test-count progression chart was made from incomparable stage snapshots; no training curves or new research results were generated; and no raw survey responses, participant timestamps or private transcripts were copied into the pack. Showcase cases were not ranked against one another using unlike metrics.

## Validation and reproducibility

The initial 41-entry pack was produced by `provenance/generate_assets.py`. The completion pass did not rerun that generator. Run `python docs/final_report_assets/provenance/validate_assets.py` to validate the current pack. The validator checks all catalogued SVG/PNG files, 300 DPI metadata for figures and composites, table Markdown/CSV readability, asset hashes, and every recorded source hash. The [validation result](provenance/VALIDATION_RESULT.json) records the final pass.

The generator writes only within `docs/final_report_assets/`. It reads G:, the D: source artifacts and the Downloads files without modifying them. All research experiments, GT, frozen outputs, product logic and study responses remain untouched.

## Completion pass — `FINAL_REPORT_ASSET_PACK_COMPLETION_PASS`

The completion pass added **13 catalog entries** to the validated baseline: nine SVG/PNG figures, three screenshot composites, and one real current-homepage screenshot. It also added one CSV extract for the formal clip timeline. The existing 41 catalogued assets were checked by SHA-256 before and after the append and were not regenerated.

| Asset class | Added | Final total |
|---|---:|---:|
| Diagrams | 6 | 14 |
| Quantitative graphs and timelines | 3 | 15 |
| Report-ready tables | 0 | 15 |
| Preserved UI screenshots | 1 | 7 |
| UI screenshot composites | 3 | 3 |
| Chart source-data extracts | 1 | 12 |
| Catalog entries | **13** | **54** |

**Added figures:** detailed product architecture; product versus frozen research boundary; coordinate-space and homography flow; frozen ASR pipeline; conditional metric kinematics; product job lifecycle; key HOTA/MOTA/IDF1 outcomes; formal challenge-clip timeline; selected coach-study Likert distributions.

**Added UI evidence:** live local homepage capture; home → coach overview → tactical events composite; event navigation, identity withholding and report composite; C03/C04/C06 manually verified, oracle-assisted showcase composite. The composites only crop and arrange real recorded UI pixels; they do not depict a newly executed backend run.

**Updated Priority A (22 entries):**

- **Design and methodology:** system overview; detailed final product architecture; product versus frozen research boundary; fail-closed identity gate; Vision method stacks; fusion response-window contract; calibration permission boundary.
- **Evaluation:** official four-clip Vision aggregate table; HOTA/DetA/AssA graph; distinct identity diagnostics; frozen ASR comparison; LLM formal selection table; corrected independent calibration residuals; Phase 6 transport provenance; measured Phase 6 worker timing; Phase 6 full-session result; coach-study item means; iterative-design rationale; evidence and reporting limitations matrix.
- **Product and showcase:** final UI workflow composite; frozen oracle-assisted showcase scope table; C03/C04/C06 showcase composite.

The completion pass added four Priority A entries and nine Priority B entries, giving **22 A, 28 B, and 4 C** overall. The key Vision metric graph complements the existing HOTA/DetA/AssA decomposition; it does not replace the aggregate table. The selected Likert distribution exposes six-person response counts hidden by item means and makes no inferential claim.

**Candidates skipped as redundant:** none of the ten requested candidate groups. Each supplied a distinct design, implementation or evidence view. The final placement-map review found no additional major prose-only section requiring an evidence-backed visual, so no filler asset was added.

**Remaining presentation limits:** the homepage is a live local capture; the other UI panels are recorded final-iteration screenshots rather than a fresh full-session backend capture. Their narrow original screenshot width limits how large their text can appear in print. The Phase 6 run had no metric calibration or full-session overlay, and persistent identity did not pass; the pack does not substitute showcase evidence for either. These limits are stated in the captions and guardrails.

The completion scripts are `provenance/completion_pass.py` (one-time append) and `provenance/refine_completion_assets.py` (visual refinements to completion-only assets). The final validator passed **54/54 entries**, **29/29 SVG/PNG pairs**, PNG integrity and DPI checks, table checks, and all recorded asset/source SHA-256 checks. No research, source evidence, product logic, or file from the original 41-entry asset set was modified.
