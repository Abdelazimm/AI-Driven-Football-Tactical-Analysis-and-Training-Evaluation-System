# AI-Driven Football Tactical Analysis and Training Evaluation System

**Author:** Aly Mohamed Aly Abdelazim  
**Degree:** BSc Computer Science, University of London / Goldsmiths  
**Module:** CM3070 Final Project  
**Project template:** CM3020 Artificial Intelligence, Template 4.1, Project Idea 1 — “Orchestrating AI models to achieve a goal”

## Project overview and research question

This project investigates whether computer vision, coach-speech recognition and grounded language-model reporting can be orchestrated to support post-training football tactical review. It connects timestamped coaching instructions with available visual evidence and gives coaches a scoped account of what the system observed.

**Research question:** Can a multimodal AI pipeline combine football video and timestamped coaching instructions to support evidence-based tactical training review while withholding conclusions when persistent identity, metric calibration or visual evidence are insufficient?

Movement is treated as observable evidence, not a diagnosis of motivation or effort. The application is a research prototype and local presentation, not a production-ready player assessment service.

## Main system components and architecture

The React/TypeScript frontend uses TanStack Start. FastAPI provides the API and validates jobs and media. Supabase PostgreSQL and private Storage hold application records and media. Modal runs on-demand analysis workers. The processing path is Vision → ASR → temporal fusion → evidence validation → report → persisted result → coach-facing interface. The frontend reads an existing persisted result for the final local presentation; opening that result does not launch inference.

- **Vision methodologies:** Three complete methods were evaluated. M1 combines YOLO11m, BoT-SORT, external ReID and reconciliation. M2 combines RF-DETR-L, Deep-EIoU, ReID and modified GTA. M3 combines YOLO26m, modified SRITrack and DINOv3-based appearance evidence. M2 was selected for the AUTO complete-method runner on the frozen formal evaluation. Separately, the Stage 4B fine-tuned YOLO11m checkpoint is the designated deployment *detector* artifact (`SELECTED_FOR_DEPLOYMENT`). These roles must not be conflated.
- **ASR:** The selected transcription stack uses faster-whisper `base.en`; the comparison included NVIDIA Parakeet-TDT 0.6B v2. Tactical events are derived using deterministic categories and triggers.
- **Multimodal fusion:** A coach event ending at `t_end` is evaluated over the frozen response window `[t_end + 2 s, t_end + 6 s]`. Event, team, spatial and anonymous-track evidence remain distinct.
- **Grounded reporting:** Llama 3.1 8B was selected for structured report generation with deterministic grounding validation and a deterministic fallback. The full-session Phase 6 result used the fallback.
- **Fail-closed evidence design:** Unsafe persistent identity withholds player-level accumulated analytics. Unavailable calibration withholds metres and km/h. Missing visual observations are reported as insufficient evidence, never as zero movement. Invalid language-model output falls back to deterministic reporting.
- **Calibration:** Metric reporting requires valid camera-specific or user-supplied calibration. Arbitrary uploads never inherit the research-camera homography.

## Evaluation summary and key limitations

Formal Vision evaluation compared the three complete methods on four dense-ground-truth clips. M2 had the strongest observed complete-system benchmark performance, but **none of the methods passed the persistent physical-player identity safety requirement**. The historical identity study recorded `FAIL_HIGH_FRAGMENTATION`; the formal complete-method gate recorded `FAIL_UNSAFE_MERGE`. The integrated Phase 6 run processed a 340-second derived transport input (20,391 frames), recorded 13 tactical events and 28 structured evidence items, and ended `COMPLETED_WITH_LIMITATIONS`. Player-level analysis was withheld; the transport input used `NO_METRIC_CALIBRATION`; six response windows lacked sufficient visual observations. These are limitations, not evidence of non-response by players.

The C03, C04 and C06 capability showcase (`PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE`) uses manually verified identities, targets and tactical context. It does **not** demonstrate successful automated persistent identity. A six-participant formative coach study informed two interface iterations; there was no second post-iteration user study. Further limitations include camera-specific calibration, long full-session inference time, missing observations and no full-session overlay for Phase 6. Focused tests pass, but the historical broad test suite had environment-dependent failures; this README makes no claim that every test passes.

## Repository structure

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI routes, schemas, repositories, application services and focused tests |
| `frontend/tactical-ai-insights-main/` | TanStack Start frontend and local presentation |
| `modal_app/` | Worker orchestration and cloud runtime integration |
| `shared/` | Shared TypeScript contracts |
| `config/` | Application configuration templates |
| `golden/` | Safe showcase manifests and structured fixtures; private media is excluded |
| `docs/` | Architecture, evaluation, report drafts and safe figures |
| `scripts/` | Lightweight validation utilities |

One dated research audit remains under `docs/research_handoff/` because the golden manifest cites it; its earlier integration status does not describe the final product. Frozen research experiments remain outside this application workspace and were not rerun for publication.

## Final evidence and reproducibility

- [Phase 6 full-session evaluation](docs/phase6/IMPLEMENTATION_PHASE6_FINAL_E2E_REPORT.md) and [persisted result](docs/phase6/IMPLEMENTATION_PHASE6_FINAL_E2E_RESULT.json)
- [Final software verification](docs/evaluation/software_verification/IMPLEMENTATION_PHASE5_FINAL_VERIFICATION.md) and [remote lifecycle evidence](docs/evaluation/software_verification/IMPLEMENTATION_PHASE5_REMOTE_CLOSURE.md)
- [Coach-study iteration 1](docs/user-study/COACH_STUDY_ITERATION_REPORT.md) and [iteration 2](docs/user-study/COACH_STUDY_ITERATION_PASS02_REPORT.md)
- [Frozen integration contract](docs/reproducibility/P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md) and [final report figures](docs/final_report_assets/)

The figure provenance manifests retain the original source paths and SHA-256 values recorded when the figures were made. Some source files have since been relocated into `docs/` without changing their evidence content.

## Local setup

Use Python 3.10 or later and a current Node.js/npm installation. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Fill `.env` with your own Supabase and Modal configuration as needed. It is intentionally ignored by Git. Supabase service-role and worker callback credentials belong on the server only; never add them to browser code or commit them. Private media, checkpoint files and hosted persistence are not included, so cloning this repository alone does not reproduce the original Phase 6 job or its video.

Start FastAPI from the repository root:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, start the frontend:

```powershell
cd frontend\tactical-ai-insights-main
npm ci
npm run dev
```

Open the local URL printed by Vite. During local development, the frontend proxies `/api/v1` to loopback FastAPI. For a separately hosted API, configure `VITE_API_BASE_URL` in the frontend environment; do not place secrets in that variable.

## Fast verification

```powershell
cd frontend\tactical-ai-insights-main
npx tsc --noEmit
npm run build
```

From the repository root, run the focused backend checks:

```powershell
python -m pytest backend/tests/test_api.py backend/tests/test_phase3_storage_and_upload.py -q
```

The tests above do not launch the Vision, ASR or LLM pipeline.

## Privacy and data availability

Raw research footage, participant audio, the private Phase 6 transport copy, signed consent forms, participant signatures, private Supabase exports, model checkpoints and local credentials are intentionally excluded from this public repository. Structured evidence and diagrams included here must be interpreted with their documented safety gates. Access to private media or the persisted live result requires separate authorization and infrastructure.
