# Frontend Application (Reserved Workspace)

## 1. Stack Specifications

This directory is reserved for the future user interface of the **AI-Driven Football Tactical Analysis and Training Evaluation System**.

In subsequent integration prompts, this directory will host:
- **Framework**: [Next.js](https://nextjs.org/) (React 18+ / 19, TypeScript)
- **Routing**: Next.js App Router (`app/` directory)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **UI Components**: [Shadcn UI](https://ui.shadcn.com/) (Radix primitives)
- **Deployment**: [Vercel](https://vercel.com/)

---

## 2. Key Interface Modules To Be Built

1. **Dashboard & Upload Portal**:
   - Direct browser upload of football training footage ($\le 300\text{ s}$) to Supabase Storage via signed presigned URLs.
   - Operating mode selector (`AUTOMATED_ANALYSIS`, `VALIDATED_SHOWCASE`, `ANALYSIS_WITHOUT_METRICS`).
   - Pitch calibration selector (`DEMO_FIXED_CALIBRATION`, `CUSTOM_PITCH_CALIBRATION`, `NO_METRIC_CALIBRATION`).

2. **Job Progress Monitor**:
   - Real-time stage tracker observing asynchronous Modal execution (`VALIDATING` $\rightarrow$ `UPLOADING_RESULTS`).
   - Graceful status indicators for `COMPLETED` and `COMPLETED_WITH_LIMITATIONS`.

3. **Tactical Results & Visualizer**:
   - Interactive timeline aligning coach speech commands with detected player responses.
   - Metric cards displaying speed ($km/h$) and distance ($m$) only when validly calibrated.
   - Grounded coach tactical evaluation report with progressive disclosure of limitations.

4. **Validated Showcase Explorer**:
   - Zero-inference presentation layer for manually verified golden demonstration cases (**C03**, **C04**, **C06**).
   - Provenance badges highlighting `ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION`.

---

## 3. Shared Contracts Integration

The frontend imports data contracts and enums directly from the project's root `shared/` directory:
- `shared/constants/modes.ts`
- `shared/constants/stages.ts`
- `shared/constants/confidence.ts`
- `shared/schemas/*.ts`
