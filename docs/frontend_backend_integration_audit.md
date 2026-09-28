# Frontend → Backend Integration Readiness Audit

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Date**: 2026-09-22  
**Type**: READ-ONLY AUDIT — no source files modified  

---

## A. FRONTEND FRAMEWORK AND STRUCTURE

| Property | Value |
|---|---|
| **Framework** | React 19 + TanStack Start (SSR) + TanStack Router |
| **Build tool** | Vite 8.1.5 via `@lovable.dev/vite-tanstack-config` |
| **Styling** | Tailwind CSS 4.2 + tw-animate-css |
| **Component library** | shadcn/ui (Radix primitives) — 46 UI components |
| **State management** | Local `useState` only; no global store |
| **Data fetching** | `@tanstack/react-query` installed but **never used** |
| **Forms** | `react-hook-form` + `zod` installed but **unused** — analysis form uses raw `useState` |
| **Charts** | `recharts` installed but **unused** |
| **Package manager** | Bun (bun.lock present) |
| **SSR / Deploy target** | Nitro → Cloudflare (default from Lovable config) |

### Resolved Paths

| Area | Path |
|---|---|
| Frontend root | [`frontend/tactical-ai-insights-main/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main) |
| Frontend src | [`frontend/tactical-ai-insights-main/src/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src) |
| Backend root | [`backend/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend) |
| Backend app | [`backend/app/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app) |
| Shared contracts | [`shared/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/shared) |
| Golden showcase | [`golden/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/golden) |
| Modal worker | [`modal_app/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/modal_app) |

---

## B. PAGE / ROUTE INVENTORY

| Route | File | Purpose | Has Dynamic Params |
|---|---|---|---|
| `/` | [`index.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/index.tsx) | Dashboard / landing | No |
| `/analysis/new` | [`analysis.new.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.new.tsx) | New analysis creation form | No |
| `/analysis/processing` | [`analysis.processing.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.processing.tsx) | Processing/progress display | **No** ⚠️ |
| `/results` | [`results.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx) | Results viewer (7 tabs) | **No** ⚠️ |
| `/comparisons` | [`comparisons.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/comparisons.tsx) | Methodology comparison | No |
| `/showcase` | [`showcase.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/showcase.tsx) | Validated capability showcase | No |
| `/research` | [`research.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/research.tsx) | Research / methodology docs | No |

> [!CAUTION]
> **CRITICAL**: `/analysis/processing` and `/results` have **NO route parameters** (no `$jobId` or `$sessionId`). They are singleton static pages. A user cannot navigate to a specific job's progress or results by URL. This is a **P0 blocker**.

### Missing Routes (Recommended)

| Recommended Route | Purpose |
|---|---|
| `/analysis/$jobId` | Job-specific processing/progress view |
| `/analysis/$jobId/results` | Job-specific results view |

---

## C. COMPONENT INVENTORY

### Application Components

| Component | File | Purpose |
|---|---|---|
| `AppShell` | [`app-shell.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/app-shell.tsx) | Navigation header + footer shell |
| `PageIntro` | [`tactical-ui.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx) | Page header with eyebrow/title/description |
| `MetricCard` | [`tactical-ui.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx) | Single metric display card |
| `LimitationPanel` | [`tactical-ui.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx) | Identity withholding warning banner |
| `TacticalPitch` | [`tactical-ui.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx) | Decorative animated pitch SVG |
| `StatusBadge` | [`tactical-ui.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx) | Status indicator (success/warning/muted) |
| `PlaceholderNote` | [`tactical-ui.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx) | Info-level "not connected" note |
| `Panel` | [`results.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx) (inline) | Results section wrapper (inline, not reusable) |

### Data Files

| File | Purpose |
|---|---|
| [`tactical-data.ts`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts) | All methodology definitions, result metrics, and pipeline stages |

### shadcn/ui Library

46 standard Radix-based UI primitives in [`src/components/ui/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/ui). These are unmodified Lovable-generated components and do not require backend integration.

---

## D. CURRENT DATA FLOW

```
┌──────────────────────────────────────────────────────┐
│ tactical-data.ts (static TypeScript arrays/objects)  │
└────────┬─────────────────────────────────────────────┘
         │ imported directly
         ├──► index.tsx (dashboard stats — hardcoded)
         ├──► analysis.new.tsx (methodology list)
         ├──► analysis.processing.tsx (pipeline stages)
         ├──► results.tsx (resultMetrics)
         ├──► comparisons.tsx (methodology list)
         ├──► research.tsx (methodology list)
         └──► showcase.tsx (inline `cases` array)
```

> [!IMPORTANT]
> **There are ZERO network API calls in the entire frontend.** No `fetch()`, no `axios`, no `useQuery`, no Supabase client. TanStack React Query is installed but never imported in any route or component. Every page renders from static TypeScript data or inline JSX literals.

---

## E. MOCK / PLACEHOLDER DATA INVENTORY

| Location | What | Classification |
|---|---|---|
| [`tactical-data.ts:6-10`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts#L6-L10) | `methodologies` array — 3 methods with IDs, titles, stacks | **KEEP** — aligns with backend; wire to API for availability |
| [`tactical-data.ts:12-20`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts#L12-L20) | `resultMetrics` — 7 metrics all showing "Not available" | **REPLACE DURING INTEGRATION** |
| [`tactical-data.ts:22`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts#L22) | `pipeline` — 16 stage name strings | **KEEP** — matches `shared/constants/stages.ts` exactly (minus terminal states) |
| [`index.tsx:15-19`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/index.tsx#L15-L19) | Dashboard `stats` array — "—", "03", "Not evaluated", "03" | **REPLACE DURING INTEGRATION** |
| [`analysis.processing.tsx:7`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.processing.tsx#L7) | `const current=4` — hardcoded stage index | **REPLACE DURING INTEGRATION** |
| [`analysis.processing.tsx:7`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.processing.tsx#L7) | `w-[31%]` — hardcoded progress bar | **REPLACE DURING INTEGRATION** |
| [`analysis.processing.tsx:7`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/analysis.processing.tsx#L7) | Info cards: "Method 3 · Re-entry Focused", "00:42 · illustrative", "training-session.mp4" | **REPLACE DURING INTEGRATION** |
| [`results.tsx:10`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx#L10) | Status badge "COMPLETED WITH LIMITATIONS" + "IDENTITY_STATUS: NOT_EVALUATED" | **REPLACE DURING INTEGRATION** |
| [`results.tsx:10`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx#L10) | Coach audio tab: 2 hardcoded example instructions at 00:14 and 00:27, rendered at 45% opacity | **REPLACE DURING INTEGRATION** |
| [`results.tsx:10`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx#L10) | Evaluation tab: all metric values = "Not available — …" | **REPLACE DURING INTEGRATION** |
| [`results.tsx:10`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx#L10) | Report tab: 5 section headers with "Not available" placeholder text | **REPLACE DURING INTEGRATION** |
| [`results.tsx:10`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx#L10) | Technical tab: 8 hardcoded key-value pairs (Method 3 specific) | **REPLACE DURING INTEGRATION** |
| [`showcase.tsx:6`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/showcase.tsx#L6) | `cases` array — C06, C04, C03 with names and interpretations | **VALID FROZEN SHOWCASE DATA** — but skeletal; missing full ShowcaseCard fields |
| [`research.tsx:8`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/research.tsx#L8) | `states` array — 5 identity status strings | **KEEP FOR DESIGN PREVIEW** |
| [`tactical-ui.tsx:16`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/components/tactical-ui.tsx#L16) | `TacticalPitch` — hardcoded 8-player SVG coordinates | **KEEP FOR DESIGN PREVIEW** — decorative only |

> [!NOTE]
> No `setTimeout`, `setInterval`, or `Math.random` is used in any application component to simulate progress. The `Math.random` found in `sidebar.tsx` is in the unused shadcn sidebar skeleton width generator — irrelevant to application data flow.

---

## F. UPLOAD FLOW AUDIT

### Video Upload

| Aspect | Status | Details |
|---|---|---|
| Upload component | ✅ Present | `<input type="file" accept="video/mp4,video/quicktime">` |
| File type validation | ⚠️ PARTIAL | Accept attribute limits browser picker to MP4/MOV; no JS re-validation |
| Duration validation | ❌ MISSING | Text says "Maximum 5 minutes / 300 seconds" but **no client-side check** |
| Size validation | ❌ MISSING | No file size limit enforced |
| Preview | ⚠️ MINIMAL | Shows filename and size in MB; no video thumbnail or preview playback |
| Upload state | ❌ MISSING | No upload progress bar, no uploading/success/error states |
| Cancellation / retry | ❌ MISSING | No cancel button; no retry mechanism |
| Removal / replacement | ❌ MISSING | Selecting a new file replaces silently; no explicit remove button |
| Upload to backend | ❌ MISSING | File is stored only in `useState<File>()` — never uploaded anywhere |
| Persistence | ❌ NONE | Browser refresh loses the file reference completely |

### Coach Audio Upload

| Aspect | Status | Details |
|---|---|---|
| Three modes | ✅ Present | "Extract from video", "Upload separate", "No coach audio" — all 3 implemented |
| Separate audio input | ✅ Present | `<input type="file" accept="audio/*">` appears when "separate" selected |
| Audio type validation | ⚠️ PARTIAL | `accept="audio/*"` only; no specific format enforcement |
| Audio preview/player | ❌ MISSING | No audio playback preview |
| Upload to backend | ❌ MISSING | Stored only in `useState<File>()` |

---

## G. METHODOLOGY SELECTOR AUDIT

| Aspect | Status | Details |
|---|---|---|
| Three methods displayed | ✅ Yes | All 3 render with radio selection |
| Internal IDs | ✅ CORRECT | `METHOD_1_YOLO11_BOTSORT`, `METHOD_2_RFDETR_GTATRACK`, `METHOD_3_YOLO26_SRITRACK` |
| User-facing names | ✅ CORRECT | "Original Hybrid", "Global Association", "Re-entry Focused" |
| Pipeline stacks | ✅ CORRECT | Matches specification exactly |
| Selection persisted in state | ✅ Yes | `useState<MethodId>` with default `METHOD_1_YOLO11_BOTSORT` |
| Included in API payload | ❌ NO | No API payload exists — button is disabled with "Backend connection required" |
| Survives navigation/reload | ❌ NO | Component-local `useState` — lost on navigation or refresh |
| Incorrect "best" marking | ✅ CLEAN | No method is marked as best or recommended |
| Availability/unavailability | ❌ MISSING | No concept of a method being unavailable or disabled |

### ID Alignment with Backend

The frontend `MethodId` type in [`tactical-data.ts`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts#L1) defines:
```typescript
export type MethodId = "METHOD_1_YOLO11_BOTSORT" | "METHOD_2_RFDETR_GTATRACK" | "METHOD_3_YOLO26_SRITRACK";
```

The backend uses `ApplicationMode` enum: `AUTOMATED_ANALYSIS | VALIDATED_SHOWCASE | ANALYSIS_WITHOUT_METRICS`.

> [!WARNING]
> **Methodology ID has no backend equivalent.** The backend `ApplicationMode` describes *operating mode*, not *pipeline methodology*. There is no backend enum or field for method selection. This must be added to the shared contract and the `AnalysisJob` schema.

---

## H. CALIBRATION AUDIT

| Aspect | Status | Details |
|---|---|---|
| Three modes displayed | ✅ Yes | "Custom Pitch Calibration", "No Metric Calibration", "Validated Demo Calibration" |
| Demo safety warning | ✅ PRESENT | PlaceholderNote: "reserved for the frozen demonstration footage and cannot be applied to arbitrary uploads" |
| Internal IDs | ⚠️ MISMATCH | Frontend uses `"custom" | "none" | "demo"`; backend uses `CUSTOM_PITCH_CALIBRATION | NO_METRIC_CALIBRATION | DEMO_FIXED_CALIBRATION` |
| Default selection | `"none"` | Matches backend `NO_METRIC_CALIBRATION` semantically |
| Included in API payload | ❌ NO | Never transmitted; button is disabled |
| Custom calibration UI | ❌ MISSING | No 4-point landmark input, no pitch dimension form |

---

## I. ASYNC JOB / PROGRESS AUDIT

> [!CAUTION]
> **CRITICAL: The entire async job model is absent.** The processing page is a static UI mockup.

| Aspect | Status | Details |
|---|---|---|
| Job creation | ❌ MISSING | "Start Analysis" button is disabled; no API call |
| Job ID | ❌ MISSING | No `job_id` concept anywhere in frontend |
| Session ID | ❌ MISSING | No `session_id` concept anywhere in frontend |
| Route parameter | ❌ MISSING | `/analysis/processing` has no `$jobId` param |
| Status polling | ❌ MISSING | No `useQuery`, no polling, no SSE, no WebSocket |
| Server-Sent Events | ❌ MISSING | Not implemented |
| WebSocket | ❌ MISSING | Not implemented |
| React Query | ⚠️ INSTALLED BUT UNUSED | `QueryClientProvider` wraps the app but zero queries exist |
| Progress bar | ❌ HARDCODED | `w-[31%]` CSS width literal |
| Current stage | ❌ HARDCODED | `const current=4` (TRACKING) |
| Elapsed time | ❌ HARDCODED | "00:42 · illustrative" |
| Navigation to results | ❌ MISSING | No "View Results" link; no redirect on completion |
| Fake timers | ✅ NONE | No `setTimeout`/`setInterval` simulating progress |

### Pipeline Stage Alignment

Frontend [`pipeline`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts#L22) array vs backend [`AnalysisStage`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/shared/constants/stages.ts):

| Backend Stage | In Frontend Pipeline | Notes |
|---|---|---|
| UPLOADED | ✅ | |
| VALIDATING | ✅ | |
| PREPROCESSING | ✅ | |
| DETECTING | ✅ | |
| TRACKING | ✅ | |
| IDENTITY_EVALUATION | ✅ | |
| CALIBRATING | ✅ | |
| KINEMATICS | ✅ | |
| AUDIO_EXTRACTION | ✅ | |
| TRANSCRIBING | ✅ | |
| INSTRUCTION_PARSING | ✅ | |
| FUSION | ✅ | |
| GENERATING_EVIDENCE | ✅ | |
| GENERATING_REPORT | ✅ | |
| RENDERING | ✅ | |
| UPLOADING_RESULTS | ✅ | |
| COMPLETED | ❌ MISSING | Terminal state not in pipeline array |
| COMPLETED_WITH_LIMITATIONS | ❌ MISSING | Terminal state not in pipeline array |
| FAILED | ❌ MISSING | Terminal state not in pipeline array |

The frontend `pipeline` array contains exactly the 16 processing stages. Terminal states (COMPLETED, COMPLETED_WITH_LIMITATIONS, FAILED) are correctly omitted from the progress stepper but must be handled for result navigation.

---

## J. RESULTS PAGE AUDIT

The results page at [`results.tsx`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/routes/results.tsx) has **7 tabs**:

### Tab: Overview

| Field | Current Data | Status |
|---|---|---|
| Status badge | Hardcoded "COMPLETED WITH LIMITATIONS" | MOCK — needs `AnalysisResult.job_status` |
| Identity status | Hardcoded "IDENTITY_STATUS: NOT_EVALUATED" | MOCK — needs `IdentityEvaluation.identity_status` |
| 7 metric cards | All "Not available" from `resultMetrics` | MOCK — needs `AnalysisResult` fields |
| System summary | Hardcoded text | MOCK |
| LimitationPanel | Static component | PARTIAL — correct design but not data-driven |
| Limitation bullets | 3 hardcoded strings | MOCK |
| Loading state | ❌ MISSING | |
| Empty state | ❌ MISSING | |
| Error state | ❌ MISSING | |

### Tab: Video

| Field | Current Data | Status |
|---|---|---|
| Video player | `TacticalPitch` SVG with play button overlay | MOCK — no `<video>` element |
| Video URL | None | MISSING — needs Supabase Storage URL |
| Loading state | ❌ MISSING | |
| Unavailable state | ❌ MISSING | |

### Tab: Players

| Field | Current Data | Status |
|---|---|---|
| Content | `<LimitationPanel/>` only | ✅ GOOD — correctly shows withholding by default |
| Player cards | None rendered | ✅ SAFE — no unconditional player rendering |
| Gating logic | ❌ MISSING | No `player_level_analysis_allowed` check; static layout |
| Player list when allowed | ❌ MISSING | No component exists for when identity passes |

### Tab: Coach Audio

| Field | Current Data | Status |
|---|---|---|
| Placeholder note | ✅ Present | "No transcript is attached" |
| Example instructions | 2 hardcoded rows at 45% opacity | MOCK |
| Audio player | ❌ MISSING | No `<audio>` element |
| Timestamps | ✅ Layout present | "00:14", "00:27" hardcoded |
| Instruction category | ✅ Layout present | "Pressing cue", "Positional cue" hardcoded |
| No-audio state | ❌ MISSING | No conditional rendering for absent audio |

### Tab: Evaluation

| Field | Current Data | Status |
|---|---|---|
| Detection metrics | 4 items: Precision, Recall, mAP50, mAP50:95 | ✅ Labels correct, values "Not available" |
| Tracking metrics | 10 items including HOTA, DetA, AssA, IDF1, MOTA, ID switches | ✅ Labels correct, values "Not available" |
| Engineering metrics | 3 items: Runtime, Effective FPS, GPU Memory | ✅ Labels correct, values "Not available" |
| Null handling | ⚠️ CONCERN | Values are strings "Not available — ..." not `null`. No type-safe null representation |
| Zero fallback | ✅ SAFE | No metric currently falls back to 0 |
| GT-required marker | ✅ Present | "identity ground truth required" shown for tracking metrics |

### Tab: Report

| Field | Current Data | Status |
|---|---|---|
| Report sections | 5 headers: Session Summary, Movement Response, Coach Instructions, Observed Tactical Behaviour, Reliability/Limitations | MOCK — all say "Not available" |
| Markdown rendering | ❌ MISSING | No markdown parser — backend sends `report_markdown` |
| Download button | ✅ Present but disabled | Correctly disabled in preview |
| Real report injection | ⚠️ NEEDS WORK | Would need markdown renderer and section mapping |

### Tab: Technical

| Field | Current Data | Status |
|---|---|---|
| Provenance fields | 8 key-value pairs all hardcoded to Method 3 | MOCK |
| Player-level warning | ✅ Present | "Player-level analysis is not allowed in this state" |
| Missing fields | `run_id`, `artifact_version`, `checkpoint_metadata`, `model_sha256` | Partially represented |

---

## K. IDENTITY SAFETY AUDIT

> [!IMPORTANT]
> **HIGH PRIORITY ITEM** — Overall assessment: **PARTIAL — correctly designed but not data-driven.**

### What exists

1. **`LimitationPanel` component** — Hardcoded message: "Player-level analysis withheld. Persistent identity did not meet the required reliability threshold." with `NOT_EVALUATED · COMPLETED WITH LIMITATIONS`.
2. **Players tab** — Shows only `<LimitationPanel/>` — no player cards rendered.
3. **Technical tab** — Shows `Identity status: NOT_EVALUATED` and a warning "Player-level analysis is not allowed in this state."
4. **Research page** — Lists 5 identity states with icons; explains the safety gate concept.
5. **Results page header** — Shows `IDENTITY_STATUS: NOT_EVALUATED`.

### What is MISSING

| Gap | Severity |
|---|---|
| No `IdentityEvaluation` TypeScript type in frontend | P0 |
| No `player_level_analysis_allowed` boolean check | P0 |
| No `withholding_reason` dynamic display | P1 |
| `LimitationPanel` is hardcoded, not parameterized by backend state | P1 |
| No conditional rendering path for `PASS_RELIABLE` — what do players look like when allowed? | P1 |
| Frontend `IdentityStatus` type is missing `FAIL_INVALID_OUTPUT` compared to audit spec (but backend also lacks it) | P2 |
| Frontend `IdentityStatus` type is missing `EVALUATING` (backend has it in `confidence.ts`) | P2 |

### Frontend vs Backend Identity Status Comparison

| Status Value | Frontend `tactical-data.ts` | Backend `confidence.ts` | Shared `confidence.ts` |
|---|---|---|---|
| NOT_EVALUATED | ✅ | ✅ | ✅ |
| EVALUATING | ❌ | ✅ | ✅ |
| PASS_RELIABLE | ✅ | ✅ | ✅ |
| FAIL_HIGH_FRAGMENTATION | ✅ | ✅ | ✅ |
| FAIL_IDENTITY_CONFLICT | ✅ | ✅ | ✅ |
| FAIL_UNSAFE_MERGE | ✅ (research.tsx) | ❌ | ❌ |
| FAIL_INVALID_OUTPUT | ❌ | ❌ | ❌ |

> [!WARNING]
> `FAIL_UNSAFE_MERGE` appears in the frontend Research page's `states` array but is NOT in the shared `IDENTITY_STATUS` constant or backend enum. This needs reconciliation.

---

## L. COACH AUDIO AUDIT

| Aspect | Status | Details |
|---|---|---|
| Three audio modes in form | ✅ Present | "Extract from video" / "Upload separate" / "No coach audio" |
| Separate audio file picker | ✅ Present | Appears conditionally |
| Audio player (results) | ❌ MISSING | No `<audio>` element anywhere |
| Transcript timeline | ⚠️ SKELETAL | 2 hardcoded example rows |
| Instruction cards | ⚠️ SKELETAL | Format exists but data is inline JSX |
| Timestamp display | ✅ Layout exists | "00:14", "00:27" |
| Instruction category | ✅ Layout exists | "Pressing cue", "Positional cue" |
| Instruction target | ❌ MISSING | No player target displayed |
| Confidence | ❌ MISSING | No confidence indicator |
| No-audio behavior | ❌ MISSING | No conditional path when audio is absent in results |
| Raw transcript privacy | ✅ ACKNOWLEDGED | PlaceholderNote: "without unnecessary raw private transcript data" |

### Backend Schema Gap

The backend [`InstructionEvent`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/shared/schemas/instruction.ts) has rich fields (`start_s`, `end_s`, `raw_text`, `category`, `target_player_pseudonym`, `is_target_resolved`, `alignment_window_start_s`, `alignment_window_end_s`, `confidence`) — but the frontend instruction display is just `[timestamp, quote, label]` inline tuples. Complete redesign of the coach audio tab data binding is needed.

---

## M. EVALUATION METRICS AUDIT

| Metric Category | Frontend Labels | Backend Source | Zero-Fallback Risk |
|---|---|---|---|
| **Detection** | Precision, Recall, mAP50, mAP50:95 | Not in `AnalysisResult` schema directly | ❌ None (string "Not available") |
| **Tracking** | Raw IDs, Final Identities, Fragmentation Ratio, Re-entry Recovery, HOTA, DetA, AssA, IDF1, MOTA, ID switches | Partially in `IdentityEvaluation` | ❌ None |
| **Engineering** | Runtime, Effective FPS, GPU Memory | Not in `AnalysisResult` | ❌ None |

> [!WARNING]
> The backend `AnalysisResult` schema has `metrics: Dict[str, MovementMetric]` — this is a dictionary of movement metrics, NOT detection/tracking evaluation metrics. There is **no backend schema** for detection evaluation metrics (mAP, HOTA, etc.). These are GT-dependent and may need a separate `EvaluationMetrics` schema.

### Critical Rule: "UNAVAILABLE ≠ 0"

The current frontend correctly shows string "Not available" for all metrics. No zero fallback exists. This is safe. However, when real data integration occurs, the `Metric` type in [`tactical-data.ts`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts#L4) uses `value?: string` — the value is optional but when present is a string. There is no numeric type safety to prevent accidental "0" emission.

---

## N. REPORT AUDIT

| Aspect | Status | Details |
|---|---|---|
| Report sections | 5 section headers rendered | MOCK — all show "Not available" |
| Markdown support | ❌ MISSING | Backend sends `report_markdown` string; frontend has no markdown renderer |
| Download button | ✅ Present, disabled | Correctly disabled |
| `report_status` handling | ❌ MISSING | No distinction between `GROUNDED_LLM`, `DETERMINISTIC_FALLBACK`, `WITHHELD` |
| Grounding status indicator | ❌ MISSING | No badge showing whether report is LLM-grounded or deterministic |
| Real backend report injection | ⚠️ NEEDS MARKDOWN RENDERER | Would need `react-markdown` or equivalent |

---

## O. VALIDATED SHOWCASE AUDIT

| Aspect | Status | Details |
|---|---|---|
| Cases present | ✅ C06, C04, C03 | Correct IDs and names |
| Oracle-assisted disclaimer | ✅ PRESENT | "Player identity and coach-instruction targets were manually verified for this capability demonstration. Automated persistent identity is evaluated separately." |
| "FROZEN DEMO" badge | ✅ Present | StatusBadge on each card |
| Media | ❌ PLACEHOLDER | Uses `TacticalPitch` SVG — no real media |
| Data source | ❌ INLINE JSX | `cases` array in component file, not from backend/golden |
| Player field | ❌ MISSING | Backend `ShowcaseCard` has `player`, `instructions`, `time`, `response_summary`, `primary_metrics` — none present in frontend |
| Primary metrics | ❌ MISSING | Backend cards have metric values; frontend shows only "Validation: Manual oracle" and "Confidence: Case verified" |
| Coach report | ❌ MISSING | Backend has `full_coach_report_markdown` |
| Media resolution | ❌ MISSING | Backend has `ShowcaseResolvedMedia` — frontend has no media references |
| Limitations list | ❌ MISSING | Backend `ShowcaseResponse` has `limitations[]` |
| Methodology note | ❌ MISSING | Backend has `methodology_note` |
| Homography RMSE | ❌ MISSING | Backend has `homography_rmse` |

> [!WARNING]
> The frontend showcase is a **skeletal representation** of what the backend `ShowcaseResponse` provides. Of the ~12 fields in the response contract, only `id`, `name`, and the disclaimer text are present. Significant data binding work is needed.

---

## P. METHODOLOGY COMPARISON AUDIT

| Aspect | Status | Details |
|---|---|---|
| Three methods displayed | ✅ | Cards with titles and descriptions |
| "Whole-System Comparison" section | ✅ Present | Table with 16 metric rows × 3 methods |
| "Controlled Identity Comparison" section | ✅ Present | Separate table with same structure |
| Winner label | ✅ ABSENT | Correctly avoids declaring a winner |
| Metric values | All "Not available" | CORRECT for preview |
| Data source | ❌ STATIC | Hardcoded metric names; no backend data integration |
| GT metric availability | ❌ MISSING | No indicator of which metrics require ground truth |
| Methodology IDs | ✅ Correct | Uses `methodologies` from `tactical-data.ts` |
| Null handling | N/A | All cells are the string "Not available" |

---

## Q. FRONTEND TYPE / BACKEND SCHEMA COMPATIBILITY

### Type Systems Compared

The frontend defines its own types in [`tactical-data.ts`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/frontend/tactical-ai-insights-main/src/lib/tactical-data.ts). The shared contracts are in [`shared/`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/shared). The frontend **does not import from `shared/`**.

| Backend/Shared Type | Frontend Equivalent | Status |
|---|---|---|
| `AnalysisJob` | ❌ None | **MISSING_FRONTEND** |
| `AnalysisResult` | ❌ None | **MISSING_FRONTEND** |
| `IdentityEvaluation` | ❌ None | **MISSING_FRONTEND** |
| `IdentityStatus` (shared const) | `IdentityStatus` type in tactical-data.ts | **PARTIAL** — missing `EVALUATING`; has extra `FAIL_UNSAFE_MERGE` |
| `MethodId` (frontend-only) | ❌ None in backend | **MISSING_BACKEND** |
| `ApplicationMode` | ❌ None in frontend | **MISSING_FRONTEND** |
| `CalibrationMode` | Frontend uses `"custom" \| "none" \| "demo"` | **NAME_MISMATCH** |
| `AnalysisStage` | `pipeline` string array | **PARTIAL** — matches processing stages but is string[], not typed enum |
| `Methodology` | Frontend-only interface | **MOCK_ONLY** — not from shared |
| `Metric` | Frontend-only interface `{label, value?, reason?}` | **TYPE_MISMATCH** — vs `MovementMetric` with `value: number \| null`, `unit`, `confidence`, `display_value` |
| `InstructionEvent` | ❌ None | **MISSING_FRONTEND** |
| `TranscriptSegment` | ❌ None | **MISSING_FRONTEND** |
| `ShowcaseCard` (shared) | Inline `cases` array | **TYPE_MISMATCH** — frontend has `{id, name, icon, interpretation}`; shared has 11+ fields |
| `ShowcaseResponse` (shared) | ❌ None | **MISSING_FRONTEND** |
| `ArtifactReference` | ❌ None | **MISSING_FRONTEND** |
| `Calibration` | ❌ None | **MISSING_FRONTEND** |
| `VideoMetadata` | ❌ None | **MISSING_FRONTEND** |
| `Session` | ❌ None | **MISSING_FRONTEND** |
| `AnalysisLimitation` | ❌ None (hardcoded strings in JSX) | **MISSING_FRONTEND** |
| `MovementMetric` | ❌ None | **MISSING_FRONTEND** |

---

## R. API LAYER AUDIT

### Current State

| Search Pattern | Occurrences in Frontend |
|---|---|
| `fetch()` | 0 (only in server.ts SSR wrapper — not API calls) |
| `axios` | 0 |
| `useQuery` / `useMutation` | 0 |
| `supabase` | 0 |
| API service files | 0 |
| Custom data-fetching hooks | 0 |
| `import.meta.env` / `VITE_` | 0 |

> [!CAUTION]
> **There is no API layer whatsoever.** The frontend has zero backend communication. TanStack React Query is installed and the `QueryClientProvider` wraps the app, but no queries or mutations are defined.

### Backend API State

The FastAPI backend at [`main.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/main.py) has a single endpoint:

```
GET /health → {"status": "ok", "project": "...", "environment": "..."}
```

The [`api/__init__.py`](file:///d:/Final%20project%20videos%20transcripts/AI-Driven%20Football%20Tactical%20Analysis%20and%20Training%20Evaluation%20System/backend/app/api/__init__.py) is empty — no routers registered.

The backend has comprehensive **Pydantic schemas** and a **GoldenFixtureService** for showcase, but **no API route handlers** beyond health check.

---

## S. PROPOSED ENDPOINT MAP

| Frontend Action | Endpoint | Method | Status | Notes |
|---|---|---|---|---|
| Create analysis session | `POST /api/v1/sessions` | POST | **MISSING** | Returns `session_id` |
| Upload video | `POST /api/v1/sessions/{session_id}/video` or signed-upload | POST | **MISSING** | Multipart or signed URL |
| Upload audio | `POST /api/v1/sessions/{session_id}/audio` or signed-upload | POST | **MISSING** | Multipart or signed URL |
| Create analysis job | `POST /api/v1/analysis/jobs` | POST | **MISSING** | Accepts session_id, method, calibration |
| Start analysis job | `POST /api/v1/analysis/jobs/{job_id}/start` | POST | **MISSING** | Triggers Modal worker |
| Get job status | `GET /api/v1/analysis/jobs/{job_id}` | GET | **MISSING** | Returns `AnalysisJob` |
| Get job result | `GET /api/v1/analysis/jobs/{job_id}/result` | GET | **MISSING** | Returns `AnalysisResult` |
| Get showcase | `GET /api/v1/showcase` | GET | **MISSING** | `GoldenFixtureService.get_showcase_response()` exists but no route |
| List methodologies | `GET /api/v1/methodologies` | GET | **MISSING** | Returns availability/config |
| Get comparison data | `GET /api/v1/comparisons` | GET | **MISSING** | Scientific comparison results |
| Health check | `GET /health` | GET | **EXISTING** | Only existing endpoint |

---

## T. SUPABASE STORAGE / PERSISTENCE REQUIREMENTS

### Current Frontend Assumptions

| Media Type | Current Assumption | Required |
|---|---|---|
| Input video | Browser `File` object in `useState` | Supabase Storage signed upload URL |
| Input audio | Browser `File` object in `useState` | Supabase Storage signed upload URL |
| Annotated output video | `TacticalPitch` SVG placeholder | Supabase Storage signed read URL |
| Report file | Not implemented | Supabase Storage or inline markdown |
| Showcase media | `TacticalPitch` SVG placeholder | Supabase Storage from golden fixture upload |

### Environment Variables

| Variable | In `.env.example` | Used in Frontend | Used in Backend |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ | ❌ | ✅ (config.py) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | ❌ | ✅ (config.py) |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | ❌ | ✅ (config.py) |
| `BACKEND_API_URL` | ✅ | ❌ | N/A |
| `MODAL_TOKEN_ID` | ✅ | ❌ | N/A |
| `MODAL_TOKEN_SECRET` | ✅ | ❌ | N/A |

### Required Persistence Entities (from frontend needs)

| Entity | Backend Schema Exists | Supabase Table Needed |
|---|---|---|
| Session | ✅ `Session` | Yes |
| VideoMetadata | ✅ `VideoMetadata` | Yes |
| AnalysisJob | ✅ `AnalysisJob` | Yes |
| AnalysisResult | ✅ `AnalysisResult` | Yes |
| IdentityEvaluation | ✅ `IdentityEvaluation` | Yes (embedded in result or separate) |
| InstructionEvent | ✅ `InstructionEvent` | Yes |
| ArtifactReference | ✅ `ArtifactReference` | Yes |
| Calibration | ✅ `Calibration` | Yes |
| ShowcaseCard | ✅ `ShowcaseCard` | Yes (or served from golden fixtures) |
| MethodologySelection | ❌ Missing | Needs schema |

---

## U. ROUTING / STATE PERSISTENCE AUDIT

### Critical State Persistence Gaps

| State | Storage | Survives Refresh | Survives Navigation | Severity |
|---|---|---|---|---|
| Selected video `File` | `useState<File>` | ❌ | ❌ | P0 |
| Selected audio `File` | `useState<File>` | ❌ | ❌ | P0 |
| Audio mode | `useState("video")` | ❌ | ❌ | P1 |
| Method selection | `useState<MethodId>` | ❌ | ❌ | P1 |
| Calibration mode | `useState("none")` | ❌ | ❌ | P1 |
| Job ID | **Does not exist** | N/A | N/A | **P0** |
| Analysis result | **Does not exist** | N/A | N/A | **P0** |

### Route Recommendations

| Current Route | Problem | Recommended |
|---|---|---|
| `/analysis/processing` | No job ID — cannot identify which job | `/analysis/$jobId` |
| `/results` | No job ID — cannot identify which result | `/analysis/$jobId/results` |

---

## V. ERROR / EMPTY / LOADING STATE AUDIT

| Page/Component | Loading | Empty | Error | Not-Available | Completed-With-Limitations |
|---|---|---|---|---|---|
| Dashboard (`/`) | ❌ | ❌ | ❌ | ❌ | N/A |
| New Analysis (`/analysis/new`) | N/A | N/A | ❌ | ❌ | N/A |
| Processing (`/analysis/processing`) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Results (`/results`) | ❌ | ❌ | ❌ | ❌ | ⚠️ Static only |
| Comparisons (`/comparisons`) | ❌ | ❌ | ❌ | ✅ "Not available" cells | N/A |
| Showcase (`/showcase`) | ❌ | ❌ | ❌ | ❌ | N/A |
| Research (`/research`) | N/A | N/A | N/A | N/A | N/A |
| Root error boundary | ✅ | N/A | ✅ | N/A | N/A |
| 404 page | N/A | N/A | N/A | ✅ | N/A |

### Error Handling for Key Scenarios

| Scenario | Handled | UI |
|---|---|---|
| Invalid video | ❌ | No validation |
| Video > 5 minutes | ❌ | Text warning only, no enforcement |
| Unsupported format | ⚠️ | `accept` attribute only |
| Upload failure | ❌ | No upload exists |
| Backend unavailable | ❌ | No backend calls exist |
| GPU job failure | ❌ | No job management |
| Job timeout | ❌ | No timeout logic |
| Processing failure (FAILED stage) | ❌ | No terminal state handling |
| Partial result | ❌ | No partial result concept |
| Identity reliability failure | ⚠️ | Static `LimitationPanel` only |
| Result artifact unavailable | ❌ | No artifact loading |
| Network reconnect | ❌ | No connectivity awareness |
| **TECHNICAL FAILURE vs SCIENTIFIC LIMITATION** | ❌ | No distinction — same static treatment |

---

## W. SECURITY / ENVIRONMENT VARIABLE AUDIT

### Frontend Environment Variables Referenced: **ZERO**

No `import.meta.env` or `VITE_` references exist in any frontend source file.

### Security Findings

| Check | Status |
|---|---|
| API keys in frontend bundle | ✅ SAFE — none present |
| Supabase client in frontend | ✅ SAFE — not initialized |
| Service-role keys in frontend | ✅ SAFE — not referenced |
| Raw transcript exposure | ✅ SAFE — PlaceholderNote acknowledges privacy; hardcoded example instructions are generic |
| Public media URLs | ✅ SAFE — no URLs exist yet |
| Participant identity info | ✅ SAFE — no real data |

### Future Concerns

| Risk | Mitigation Needed |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` will be in frontend bundle | Acceptable — public anon key |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` will be in frontend bundle | Acceptable — anon key with RLS |
| `SUPABASE_SERVICE_ROLE_KEY` | Must NEVER be in frontend; backend-only |
| `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | Must NEVER be in frontend; backend-only |
| Signed upload URLs | Backend must generate; frontend must not have direct bucket write |

---

## X. COMPONENT → BACKEND DEPENDENCY MATRIX

| Page | Component | Source File | Current Data Source | Required Backend Data | API Dependency | Persistence | Readiness | Missing Work | Priority |
|---|---|---|---|---|---|---|---|---|---|
| Dashboard | Stats cards | `index.tsx` | Hardcoded array | Session count, method count, last identity status, showcase count | `GET /sessions/summary`, `GET /showcase` | Supabase | NOT READY | API client, query hooks | P1 |
| New Analysis | Video upload | `analysis.new.tsx` | `useState<File>` | Signed upload URL | `POST /uploads/video` | Supabase Storage | NOT READY | Upload service, progress, validation | P0 |
| New Analysis | Audio upload | `analysis.new.tsx` | `useState<File>` | Signed upload URL | `POST /uploads/audio` | Supabase Storage | NOT READY | Upload service | P1 |
| New Analysis | Method selector | `analysis.new.tsx` | `tactical-data.ts` | Method availability | `GET /methodologies` | None | PARTIAL | API availability check | P1 |
| New Analysis | Calibration selector | `analysis.new.tsx` | Inline tuples | Calibration modes | None (static for now) | None | PARTIAL | ID mapping to backend enum | P1 |
| New Analysis | Start Analysis | `analysis.new.tsx` | Disabled button | Job creation response | `POST /analysis/jobs` | Supabase | NOT READY | API call, navigation to job page | P0 |
| Processing | Progress bar | `analysis.processing.tsx` | `w-[31%]` hardcoded | `AnalysisJob.progress_percent` | `GET /analysis/jobs/{id}` | Supabase | NOT READY | Polling/SSE, dynamic progress | P0 |
| Processing | Stage stepper | `analysis.processing.tsx` | `const current=4` | `AnalysisJob.current_stage` | `GET /analysis/jobs/{id}` | Supabase | NOT READY | Stage mapping, dynamic index | P0 |
| Processing | Info cards | `analysis.processing.tsx` | Hardcoded strings | Job metadata | `GET /analysis/jobs/{id}` | Supabase | NOT READY | Dynamic binding | P0 |
| Results | Status badge | `results.tsx` | Hardcoded | `AnalysisResult.job_status` | `GET /analysis/jobs/{id}/result` | Supabase | NOT READY | Dynamic status | P0 |
| Results | Metric cards | `results.tsx` | `resultMetrics` static | `AnalysisResult` fields | `GET /analysis/jobs/{id}/result` | Supabase | NOT READY | Type-safe metric binding | P0 |
| Results | LimitationPanel | `tactical-ui.tsx` | Hardcoded | `IdentityEvaluation` | Embedded in result | Supabase | PARTIAL | Parameterize with real data | P0 |
| Results | Video player | `results.tsx` | SVG placeholder | Annotated video URL | `ArtifactReference` storage URL | Supabase Storage | NOT READY | `<video>` element, signed URL | P1 |
| Results | Players tab | `results.tsx` | `LimitationPanel` | Player data (if allowed) | `GET /result` | Supabase | PARTIAL | Conditional rendering, player component | P0 |
| Results | Coach Audio tab | `results.tsx` | 2 hardcoded rows | `InstructionEvent[]` | `GET /result` | Supabase | NOT READY | Instruction list, audio player | P1 |
| Results | Evaluation tab | `results.tsx` | "Not available" strings | Evaluation metrics | `GET /result` + GT metrics | Supabase | NOT READY | Metric type system | P1 |
| Results | Report tab | `results.tsx` | Placeholder text | `report_markdown` | `GET /result` | Supabase | NOT READY | Markdown renderer, download | P1 |
| Results | Technical tab | `results.tsx` | Hardcoded KV pairs | `AnalysisResult` + `AnalysisJob` metadata | `GET /result` | Supabase | NOT READY | Dynamic binding | P2 |
| Showcase | Case cards | `showcase.tsx` | Inline `cases` array | `ShowcaseResponse` | `GET /showcase` | Golden fixtures | NOT READY | Full card data, media, report | P1 |
| Comparisons | Metric tables | `comparisons.tsx` | "Not available" × 48 | Comparison dataset | `GET /comparisons` | Supabase | NOT READY | Data binding, null display | P2 |
| Research | Method cards | `research.tsx` | `tactical-data.ts` | Static (informational) | None | None | READY | None — informational page | P3 |
| Research | Safety gate | `research.tsx` | Hardcoded states | Static (informational) | None | None | READY | None — informational page | P3 |

---

## Y. INTEGRATION READINESS SCORECARD

| Category | Status | Rationale |
|---|---|---|
| **Upload readiness** | **NOT READY** | File picker exists but no upload logic, no progress, no validation, no backend endpoint |
| **Methodology selection readiness** | **PARTIAL** | Correct IDs exist; no backend enum for method; selection not persisted; no availability check |
| **Async-job readiness** | **NOT READY** | No job ID, no job creation, no polling, no SSE, static progress display |
| **Progress readiness** | **NOT READY** | Hardcoded stage index and percentage; correct stage names match backend |
| **Results schema readiness** | **NOT READY** | No frontend types for `AnalysisResult`; all data is static strings; tabs are correctly structured |
| **Identity safety readiness** | **PARTIAL** | `LimitationPanel` exists with correct messaging; Players tab correctly shows withholding; but no dynamic gating logic, no `player_level_analysis_allowed` check |
| **Audio readiness** | **NOT READY** | Three audio modes in form are correct; no audio player, no transcript binding, no `InstructionEvent` types |
| **Evaluation readiness** | **PARTIAL** | Correct metric labels; "Not available" strings are safe; no numeric type binding; GT distinction exists |
| **Report readiness** | **NOT READY** | Section headers exist; no markdown renderer; no `report_status` handling; download button present but disabled |
| **Showcase readiness** | **PARTIAL** | C03/C04/C06 cards present with correct disclaimer; skeletal data vs full `ShowcaseResponse`; no real media |
| **Comparison readiness** | **PARTIAL** | Both comparison types exist; correct metric labels; no data binding; no winner label (correct) |
| **API-layer readiness** | **NOT READY** | Zero API calls exist; React Query installed but unused; no service layer |
| **Persistence readiness** | **NOT READY** | All state is component-local `useState`; no URL params; refresh loses everything |
| **Error handling readiness** | **NOT READY** | Root error boundary exists; no per-component loading/error/empty states |
| **Security readiness** | **READY** | No secrets exposed; no API keys in bundle; clean environment |

---

## Z. CRITICAL BLOCKERS

1. **No persistent job ID** — Processing and Results pages are static singletons with no route parameters. A user cannot navigate to, bookmark, or share a specific job.

2. **No API service layer** — Zero network calls exist in the entire frontend. React Query is installed but completely unused.

3. **Simulated progress only** — Processing page has `const current=4` and `w-[31%]` hardcoded. No polling, SSE, or WebSocket.

4. **No result retrieval** — Results page renders entirely from static arrays in `tactical-data.ts`. No mechanism to fetch or display real `AnalysisResult` data.

5. **Upload never reaches backend** — `File` objects are stored in `useState` and never uploaded. No upload endpoint, no signed URL flow, no progress indicator.

6. **"Start Analysis" button does nothing** — Disabled with "Backend connection required". No `onClick` handler that would create a job.

7. **Identity safety gate is static** — `LimitationPanel` is hardcoded with `NOT_EVALUATED`. No `player_level_analysis_allowed` boolean drives conditional rendering. When identity passes, there is no player component to show.

8. **Frontend does not import shared contracts** — The comprehensive `shared/schemas/` and `shared/constants/` TypeScript types are not referenced by any frontend file. Types are duplicated/simplified in `tactical-data.ts`.

9. **Calibration IDs mismatch** — Frontend uses `"custom" | "none" | "demo"`; backend uses `CUSTOM_PITCH_CALIBRATION | NO_METRIC_CALIBRATION | DEMO_FIXED_CALIBRATION`.

10. **No methodology ID in backend** — Frontend has `MethodId` type but backend has no equivalent enum or field on `AnalysisJob`.

11. **No markdown renderer** — Backend sends `report_markdown`; frontend has no markdown rendering capability.

12. **Showcase data is skeletal** — Frontend showcase cards have 3 fields; backend `ShowcaseResponse` has ~12 fields including media, metrics, report, and limitations.

---

## AA. NON-BLOCKING IMPROVEMENTS

1. **Extract `Panel` to shared component** — Currently inline in `results.tsx`; reusable across pages.

2. **Add `react-markdown` dependency** — Needed for report tab and showcase coach report.

3. **Add video duration validation** — Client-side `HTMLVideoElement.duration` check before upload.

4. **Add Skeleton loading states** — shadcn `Skeleton` component is already available but unused.

5. **recharts integration** — Installed but unused; could visualize comparison metrics and timeline data.

6. **react-hook-form + zod for analysis form** — Both installed; could replace raw `useState` for better validation.

7. **Add `EVALUATING` to frontend identity states** — Present in shared constants but missing from frontend.

8. **Reconcile `FAIL_UNSAFE_MERGE`** — Present in frontend Research page but not in shared/backend enums.

---

## AB. RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: Shared Contracts (Foundation)
- Import `shared/` types into frontend (configure TypeScript path alias or package)
- Replace `tactical-data.ts` types with shared imports
- Map calibration frontend IDs to backend `CalibrationMode` enum
- Add methodology selection to shared contracts and backend `AnalysisJob`

### Phase 2: API Client Layer
- Create `src/lib/api-client.ts` with base URL configuration
- Create typed React Query hooks in `src/hooks/`
- Configure `VITE_API_BASE_URL` environment variable
- Wire `QueryClient` already present in router

### Phase 3: Media Upload
- Implement signed-upload flow (backend generates signed Supabase Storage URL)
- Add upload progress component
- Add client-side video duration validation
- Add file size validation

### Phase 4: Analysis Job Creation
- Wire "Start Analysis" button to `POST /api/v1/analysis/jobs`
- Navigate to `/analysis/$jobId` on creation
- Add `$jobId` route parameter to processing page

### Phase 5: Async Progress
- Implement status polling via React Query (`refetchInterval`)
- Bind `AnalysisJob.current_stage` and `progress_percent` to UI
- Add completion detection and redirect to results
- Add FAILED state handling

### Phase 6: Results Hydration
- Add `$jobId` route parameter to results page
- Fetch `AnalysisResult` via React Query
- Bind all tabs to real data
- Add loading/error/empty states per tab

### Phase 7: Identity Safety Gating
- Wire `IdentityEvaluation` into results page
- Make `LimitationPanel` data-driven (accept props)
- Implement conditional Players tab: show player data only when `player_level_analysis_allowed === true`
- Build player card component for the allowed case
- Handle `COMPLETED_WITH_LIMITATIONS` vs `COMPLETED` display

### Phase 8: Audio, Transcript & Report
- Build audio player component
- Bind `InstructionEvent[]` to Coach Audio tab
- Add `react-markdown` and render `report_markdown`
- Implement `report_status` badge (GROUNDED_LLM / DETERMINISTIC_FALLBACK / WITHHELD)
- Enable report download

### Phase 9: Showcase
- Wire `GET /api/v1/showcase` to Showcase page
- Bind full `ShowcaseResponse` data (cards, media, report, limitations)
- Resolve media URLs from Supabase Storage
- Add showcase coach report rendering

### Phase 10: Comparison
- Wire `GET /api/v1/comparisons` to Comparisons page
- Bind metric values to table cells
- Handle null/unavailable metrics without zero fallback
- Add GT-required indicators

### Phase 11: Error/Security Hardening
- Add per-component loading states (Skeleton)
- Add per-component error boundaries
- Distinguish TECHNICAL FAILURE from SCIENTIFIC LIMITATION in UI
- Add network reconnection awareness
- Validate no secrets leak into client bundle
- Configure CSP headers

---

## AC. FILES INSPECTED

### Frontend (all under `frontend/tactical-ai-insights-main/`)
- `package.json`, `vite.config.ts`, `tsconfig.json`
- `src/router.tsx`, `src/routeTree.gen.ts`, `src/server.ts`, `src/start.ts`, `src/styles.css`
- `src/routes/__root.tsx`, `index.tsx`, `analysis.new.tsx`, `analysis.processing.tsx`, `results.tsx`, `showcase.tsx`, `comparisons.tsx`, `research.tsx`
- `src/components/app-shell.tsx`, `src/components/tactical-ui.tsx`
- `src/lib/tactical-data.ts`, `utils.ts`, `error-capture.ts`, `error-page.ts`, `lovable-error-reporting.ts`
- `src/hooks/use-mobile.tsx`
- `src/assets/` (2 SVG asset JSON files)
- `src/components/ui/` (46 shadcn components — listed, select files inspected)
- `AGENTS.md`

### Backend (all under `backend/`)
- `app/main.py`, `app/__init__.py`
- `app/core/config.py`
- `app/api/__init__.py`
- `app/schemas/` — all 18 files: `__init__.py`, `job.py`, `result.py`, `identity.py`, `showcase.py`, `stages.py`, `modes.py`, `confidence.py`, `calibration.py`, `instruction.py`, `transcript.py`, `kinematics.py`, `limitation.py`, `artifact.py`, `session.py`, `video.py`, `detection.py`, `tracking.py`
- `app/services/golden.py`
- `app/pipeline/` (directory listing)

### Shared (all under `shared/`)
- `index.ts`
- `schemas/` — all 15 files
- `constants/` — all 4 files

### Other
- `.env.example`
- `golden/` (directory listing)
- `modal_app/` (directory listing)
- `docs/` (directory listing)
- Root `AGENTS.md`

---

## AD. COMMANDS / VALIDATIONS RUN

| Command | Purpose | Result |
|---|---|---|
| Directory listings (11) | Structure discovery | Completed |
| File views (40+) | Source inspection | Completed |
| grep: `fetch\|axios\|useQuery\|useMutation\|supabase` | API call search | **Zero results** in application code |
| grep: `setTimeout\|setInterval\|Math.random\|mock\|demo\|fake\|placeholder\|hardcoded` | Mock data search | Identified all occurrences (see Section E) |
| grep: `VITE_\|import.meta.env` | Environment variable search | **Zero results** in frontend application code |

No `npm install`, `npm run build`, `tsc`, or `lint` was executed (dependencies not installed; bun lockfile present, not npm).

---

## AE. QUESTIONS OR UNRESOLVED CONTRACTS

1. **Where should methodology ID live in the backend?** The `AnalysisJob` has `mode: ApplicationMode` (AUTOMATED_ANALYSIS, etc.) but no field for which detection/tracking pipeline to use. Should a `methodology_id` field be added to `AnalysisJob`?

2. **Evaluation metrics schema?** Detection evaluation metrics (mAP, HOTA, etc.) are not in `AnalysisResult`. Are these stored separately? Do they need a dedicated `EvaluationMetrics` interface? Are GT-dependent metrics (HOTA, MOTA, etc.) only available for the research comparison, not for user-uploaded video analysis?

3. **Frontend deploy target?** The Vite config uses Lovable's Cloudflare-targeting Nitro preset. Will the frontend continue to deploy to Cloudflare, or will it move to a different host?

4. **Signed URL strategy?** For media uploads and downloads — will the frontend call the FastAPI backend to get signed Supabase Storage URLs, or will it use the Supabase JS client directly with anon key + RLS policies?

5. **SSR implications?** The app uses TanStack Start with server-side rendering via Nitro. Data fetching hooks need to account for SSR hydration. Should initial data be loaded server-side or client-only?

6. **`FAIL_UNSAFE_MERGE` reconciliation** — This identity status appears in the frontend Research page but not in shared constants or backend enum. Is it a valid status that should be added to the shared contract, or should it be removed from the frontend?

---

## AF. FINAL BACKEND-INTEGRATION READINESS SUMMARY

The Lovable-generated frontend is a **well-designed, scientifically responsible UI shell** that correctly demonstrates the intended user experience, including:

- ✅ Correct methodology IDs and pipeline descriptions
- ✅ Correct pipeline stage names matching backend enums
- ✅ Identity safety messaging with appropriate withholding language
- ✅ Showcase disclaimer correctly separating oracle-assisted from automated results
- ✅ "Not available" rather than fabricated zeros for absent metrics
- ✅ No simulated progress using fake timers
- ✅ No secrets or API keys in the frontend bundle
- ✅ Clean "PLACEHOLDER DATA" labels on dashboard

However, **it is entirely disconnected from any backend**:

- ❌ Zero API calls
- ❌ Zero React Query usage (despite being installed)
- ❌ Zero shared type imports
- ❌ No route parameters for job/session identification
- ❌ No upload logic
- ❌ No async job management
- ❌ No loading, error, or empty states
- ❌ No markdown rendering for reports

**The frontend is ready to be CONNECTED to a backend, but cannot function as a real application without the 11-phase integration work described above.** The existing UI design, component architecture, and scientific safety messaging are strong foundations that should be preserved during integration.
