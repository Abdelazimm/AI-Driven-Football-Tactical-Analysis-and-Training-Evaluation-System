# Golden Artifacts & Showcase Provenance Registry

## 1. Purpose & Provenance

This package manages the immutable fixtures and verified demonstration media for the **Validated Showcase** (`ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION`).

The golden showcase contains frozen evidence for three capability demonstrations:
- **C03**: Hold Position / Tactical-Zone Retention
- **C04**: Defensive Marking / Close-Down
- **C06**: Pressing Response

These demonstrations were verified through expert manual review and hold the official status:
`PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE`.

---

## 2. Directory Layout

```text
golden/
├── README.md                      # This document
├── manifest.json                  # Manifest recording verified source paths, fixture paths, sizes, and SHA-256 hashes
├── media_map.json                 # Application mapping layer resolving frozen research paths to local fixtures & storage keys
│
├── fixtures/                      # Copied frozen JSON & Markdown payloads (byte-identical)
│   ├── showcase_frontend_payload.json       # 8,556 bytes, sha256: 20e0a6f0f8a537a8ce00567ffd136044231faa88c21446d1e82180751ce9c830
│   ├── showcase_final_coach_report.md       # 3,672 bytes, sha256: d491814396302018b3efd2ded3d68937ad0a6378c022ac8f317597c48bc8793d
│   ├── showcase_grounding_validation.json   # 3,757 bytes, sha256: a300006b13f0985e85c89075bf2654ff780429e05fb8f7fe4f7f5b9a39b1a4dd
│   └── showcase_final_summary.json          # 1,284 bytes, sha256: 3752c872d4cc3710fdb7c8f2fbf375269a6fb89dcc839f0c9f08cee72547e0e5
│
└── media/                         # Copied frozen demonstration media (byte-identical)
    ├── c06/
    │   └── C06_pressing_sequence_overlay.mp4          # 10,726,375 bytes, sha256: 6d8d8eea0f6a65c014228d1481f821742a2b2f4e6fb6db154a1e3ae1f39bfb05
    ├── c04/
    │   └── C04_black01_red03_response_contact_sheet.png  # 18,927,018 bytes, sha256: 73d47fab27089d5de39302e90244f235969dec5d058efed4510a92f25f378a50
    └── c03/
        └── C03_hold_position_overlay.mp4              # 20,281,548 bytes, sha256: b34a274a80952a770b9125414f07d5881904c3849dac95d2366fd968c5ab0f2e
```

---

## 3. Media Path Resolution Architecture (`media_map.json`)

The frozen `showcase_frontend_payload.json` contains research-relative paths that do not match the local directory structure (e.g. `experiments/capability_showcase/C06_...` vs local `C06_pressing_deterministic_response/...`).

**Rule**: The frozen payload JSON must **never** be edited to fix these paths.
Instead, the application uses `golden/media_map.json` and the backend `GoldenFixtureService` (`backend/app/services/golden.py`) to map frozen payload references to local fixture files and future Supabase Storage keys:

| Case | Original Frozen Payload Reference | Local Fixture Path | Future Supabase Storage Key | Checksum (SHA-256) | Status |
|---|---|---|---|---|---|
| **C06** | `experiments/capability_showcase/C06_pressing_deterministic_response/C06_pressing_sequence_overlay.mp4` | `golden/media/c06/C06_pressing_sequence_overlay.mp4` | `c06/C06_pressing_sequence_overlay.mp4` | `6d8d8eea...` | `RESOLVED` |
| **C04** | `experiments/capability_showcase/C04_marking/C04_black01_red03_response_contact_sheet.png` | `golden/media/c04/C04_black01_red03_response_contact_sheet.png` | `c04/C04_black01_red03_response_contact_sheet.png` | `73d47fab...` | `RESOLVED` |
| **C03** | `experiments/capability_showcase/C03_hold_position/C03_hold_position_overlay.mp4` | `golden/media/c03/C03_hold_position_overlay.mp4` | `c03/C03_hold_position_overlay.mp4` | `b34a274a...` | `RESOLVED` |

---

## 4. Scientific Disclaimer & Boundaries

- **Zero-Inference Presentation**: Loading and displaying showcase cases does not invoke YOLO, BoT-SORT, Whisper, or LLM inference.
- **Manual Verification Scope**: Player identities, coach-instruction targets, opponent relationships, and tactical zones in C03, C04, and C06 were manually verified by human review.
- **Persistent Identity Separation**: The showcase status (`PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE`) does **not** validate automated persistent identity, which definitively remains `FAIL_HIGH_FRAGMENTATION` ($6.1667 > 1.5$).
- **Metric Estimates**: Metre-based values are approximate measured metric estimates based on physically measured pitch dimensions ($19.31\text{ m} \times 19.88\text{ m}$) and planar homography with an independent landmark RMSE of $0.651\text{ m}$.
