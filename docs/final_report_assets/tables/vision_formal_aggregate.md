# Official four-clip complete-system Vision evaluation

Official TrackEval aggregate over four independent frozen challenge clips; unsafe shared-track IDs are a separate descriptive audit.

| method | clip | HOTA | DetA | AssA | MOTA | IDF1 | IDSW | FP | FN | precision | recall | unsafe_shared_track_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | COMBINED_SEQ | 0.4632074630706638 | 0.502034899617084 | 0.4333140413339255 | 0.5672739349084354 | 0.5890910698887881 | 186 | 6004 | 2931 | 0.7513974576622086 | 0.8609450612012525 | 21 |
| M2 | COMBINED_SEQ | 0.6709604685660026 | 0.6566577888131803 | 0.6862317759504855 | 0.8521681373944398 | 0.9144202293264484 | 19 | 224 | 2873 | 0.9878452439090564 | 0.8636967454217668 | 9 |
| M3-v1 | COMBINED_SEQ | 0.3517226912390671 | 0.2550707045624534 | 0.4852102737574569 | 0.3253154948287314 | 0.4066114522347565 | 5 | 36 | 14180 | 0.9948081915200462 | 0.3272606509156466 | 9 |

**Guardrail:** All methods fail identity safety. M3's five IDSW must be read beside its 0.3273 recall and 14,180 FN.

**Sources:** G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\final_evaluation\whole_system_challenge_evaluation\FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv; G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\final_evaluation\whole_system_challenge_evaluation\FINAL_WHOLE_SYSTEM_IDENTITY_SAFETY.json; C:\Users\Abdelazim\Downloads\CM3070_CANONICAL_FINAL_REPORT_EVIDENCE_LOG_v89.md; D:\Final project videos transcripts\final_vision_evaluation\FORMAL_EXECUTION_PROTOCOL.json
