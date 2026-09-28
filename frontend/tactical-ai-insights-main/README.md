# Tactical AI Insights

Build a premium, modern, animated frontend for:

AI-Driven Football Tactical Analysis and Training Evaluation System

DESIGN DIRECTION:

Premium Tactical Command Center.

The interface should feel like an elite football performance lab combined with an AI tactical command center.

Avoid generic SaaS styling.

==================================================

VISUAL IDENTITY

==================================================

Theme:

- Dark navy / near-black background

- Neon football green as the primary accent

- Cyan / electric blue as a secondary AI accent

- High-contrast white typography

- Subtle glassmorphism

- Thin luminous borders

- Tactical pitch grids

- Animated player trajectory lines

- AI neural-network / tracking visual motifs

- Premium football analytics aesthetic

The branding should visually match a logo that combines:

football + artificial intelligence / neural brain imagery.

Animations must feel sophisticated and subtle:

- scanning lines

- moving player nodes

- trajectory paths

- hover glow

- animated processing states

- smooth card transitions

- tactical-map movement

Do not make the interface childish, game-like, or overly cyberpunk.

==================================================

TECH STACK

==================================================

Use:

- React

- TypeScript

- Tailwind CSS

- shadcn/ui where appropriate

The frontend will later connect to:

- Python FastAPI backend

- Modal serverless GPU workers

- Supabase PostgreSQL

- Supabase Storage

Keep API/data-access code modular and separate from UI components.

Do not hardcode fake backend behavior into the UI.

Use typed interfaces for backend data.

==================================================

PRIMARY NAVIGATION

==================================================

Create:

1. Dashboard

2. New Analysis

3. Comparisons

4. Validated Showcase

5. Research / Methodology

Use a premium top navigation or compact tactical sidebar depending on screen size.

==================================================

PAGE 1 — DASHBOARD

==================================================

Hero section:

"TACTICAL INTELLIGENCE

FOR A SMARTER TOMORROW"

Supporting text:

"Advanced AI analysis for modern football training."

Include an animated tactical football pitch visualization with:

- player nodes

- tracking paths

- detection overlays

- subtle AI network connections

Primary CTA:

"New Analysis"

Secondary CTA:

"View Validated Showcase"

Below, include compact system cards such as:

- Analysis Sessions

- Available Methodologies

- Identity Reliability

- Validated Showcase

These can use placeholder values until backend integration.

==================================================

PAGE 2 — NEW ANALYSIS

==================================================

This is the most important interaction page.

Use a step-based interface:

1. Upload

2. Configure

3. Analyse

4. Results

--------------------------------

VIDEO UPLOAD

--------------------------------

Large drag-and-drop card:

"Upload Training Session"

Support:

MP4

MOV

Maximum duration:

5 minutes / 300 seconds

Show uploaded video name, size and duration after selection.

--------------------------------

COACH AUDIO

--------------------------------

Provide three choices:

1. Use audio from uploaded video

2. Upload separate coach audio file

3. No coach audio available

If option 1 is selected:

show:

"Coach audio will be extracted automatically from the video."

If option 2:

show separate audio upload control.

--------------------------------

PROCESSING METHODOLOGY SELECTOR

--------------------------------

Create a premium segmented methodology selector inspired by model-selection controls.

Show three cards horizontally on desktop and vertically on mobile.

METHOD 1

Title:

Original Hybrid

Technical:

YOLO11m

+

BoT-SORT

+

Constrained Reconciliation

Badge:

Original Project Method

Description:

"Hybrid player detection, short-term tracking and constrained tracklet reconciliation."

Internal method ID:

METHOD_1_YOLO11_BOTSORT

METHOD 2

Title:

Global Association

Technical:

RF-DETR-L

+

Deep-EIoU

+

GTA

Badge:

Modified GTATrack-based

Description:

"Transformer-based detection with sports-oriented tracking and global tracklet association."

Internal method ID:

METHOD_2_RFDETR_GTATRACK

METHOD 3

Title:

Re-entry Focused

Technical:

YOLO26m

+

SRITrack

+

DINOv3 ReID

Badge:

Modified SRITrack-based

Description:

"Re-entry-focused sports tracking designed to improve player identity recovery after leaving and returning to the frame."

Internal method ID:

METHOD_3_YOLO26_SRITRACK

Selected methodology card should:

- glow subtly

- expand slightly

- show detailed description

- clearly indicate active selection

Do not imply that one method is "best".

Add an optional text link:

"Compare methodologies"

==================================================

CALIBRATION

==================================================

Under Advanced Settings include:

Metric Calibration

Options:

- Custom Pitch Calibration

- No Metric Calibration

Keep:

Validated Demo Calibration

available only as a clearly labelled demo-specific option.

Do not imply that the demo homography can be applied to arbitrary uploaded videos.

==================================================

START ANALYSIS

==================================================

Large premium neon-green CTA:

"Start Analysis →"

Show a summary immediately above it:

Video

Coach Audio

Selected Methodology

Calibration Mode

==================================================

PAGE 3 — PROCESSING

==================================================

Build an animated processing page.

Header:

"Analysing Training Session"

Show:

- methodology selected

- progress percentage

- elapsed time

- video thumbnail

Use pipeline stages such as:

UPLOADED

VALIDATING

PREPROCESSING

DETECTING

TRACKING

IDENTITY_EVALUATION

CALIBRATING

KINEMATICS

AUDIO_EXTRACTION

TRANSCRIBING

INSTRUCTION_PARSING

FUSION

GENERATING_EVIDENCE

GENERATING_REPORT

RENDERING

UPLOADING_RESULTS

Visualize stages using a vertical or horizontal animated pipeline.

Completed stages:

green check.

Current stage:

animated neon indicator.

Future stages:

muted.

Create an animated tactical pitch / tracking visualization beside the progress pipeline.

The real backend will eventually run asynchronously.

Design the UI so the user may leave the page and return later.

==================================================

PAGE 4 — RESULTS

==================================================

Header example:

Session Analysis

Method 3 — Re-entry Focused

Status badges:

COMPLETED

or

COMPLETED WITH LIMITATIONS

Create summary metric cards.

Possible cards:

Players Detected

Raw Track IDs

Final Identities

Fragmentation Ratio

Identity Reliability

Runtime

Effective FPS

Do not assume every metric exists.

Unavailable metrics should display:

"Not available"

with a reason.

Never convert unavailable metrics to zero.

==================================================

RESULT TABS

==================================================

Create:

Overview

Video

Players

Coach Audio

Evaluation

Report

Technical

--------------------------------

OVERVIEW

--------------------------------

Show:

- system summary

- identity status

- key metrics

- coach instruction count

- tactical response highlights

- limitations

--------------------------------

VIDEO

--------------------------------

Display annotated output video.

Future overlays may include:

- bounding boxes

- track IDs

- trajectory paths

- tactical overlays

--------------------------------

PLAYERS

--------------------------------

Critical safety rule:

If:

player_level_analysis_allowed = true

show player-level cards.

If false:

DO NOT show player-specific tactical conclusions.

Instead display a prominent limitation panel:

"Player-level analysis withheld"

"Persistent identity did not meet the required reliability threshold."

The rest of the valid non-player-specific analysis should remain available.

--------------------------------

COACH AUDIO

--------------------------------

Display timestamped coach instructions.

Example visual:

00:14

"Press him"

00:27

"Hold your position"

Include instruction categories and timing.

Do not expose unnecessary private/raw transcript data.

--------------------------------

EVALUATION

--------------------------------

Display metric sections:

Detection

Precision

Recall

mAP50

mAP50:95

Tracking / Identity

Raw IDs

Final Identities

Fragmentation Ratio

Re-entry Recovery

Where valid ground truth exists:

HOTA

DetA

AssA

IDF1

MOTA

ID switches

Engineering

Runtime

Effective FPS

GPU Memory

If GT does not exist for a metric display:

"Not available — identity ground truth required."

--------------------------------

REPORT

--------------------------------

Create a premium readable tactical report layout.

Sections:

Session Summary

Movement Response

Coach Instructions

Observed Tactical Behaviour

Reliability / Limitations

Include:

"Download Report"

button placeholder.

--------------------------------

TECHNICAL

--------------------------------

Show advanced information:

Methodology used

Detector

Tracker

Association method

Calibration mode

Identity status

Model/checkpoint metadata

Run ID

Limitations

==================================================

PAGE 5 — METHODOLOGY COMPARISON

==================================================

Create a research-oriented comparison page for:

Method 1

Method 2

Method 3

Present comparison tables and charts for metrics such as:

Detector Precision

Recall

mAP50

mAP50:95

Raw IDs

Final IDs

Fragmentation Ratio

Re-entry Recovery

HOTA

AssA

IDF1

MOTA

ID switches

Runtime

Effective FPS

GPU Memory

Only display metrics that exist.

Clearly distinguish:

Whole-System Comparison

from:

Controlled Identity Comparison

Do NOT automatically display:

"Winner"

"Best Method"

ranking scores.

The interface presents scientific evidence only.

==================================================

PAGE 6 — VALIDATED SHOWCASE

==================================================

Create a visually distinct page:

"Validated Capability Showcase"

Show frozen demonstration cases:

C06 — Pressing Response

C04 — Defensive Marking

C03 — Hold Position

Each case should have:

media

description

validated metrics

coach-facing interpretation

metric confidence labels

At the top display:

"Oracle-Assisted Capability Demonstration"

And clearly show this disclaimer:

"Player identity and coach-instruction targets were manually verified for this capability demonstration. Automated persistent identity is evaluated separately."

Do not visually imply that the showcase proves automatic persistent identity.

==================================================

SCIENTIFIC SAFETY UI

==================================================

The frontend must clearly support:

identity_status

player_level_analysis_allowed

withholding_reason

Possible states include:

PASS_RELIABLE

FAIL_HIGH_FRAGMENTATION

FAIL_IDENTITY_CONFLICT

FAIL_UNSAFE_MERGE

NOT_EVALUATED

A failed identity gate must not look like an application crash.

Instead:

COMPLETED WITH LIMITATIONS

should be treated as a legitimate successful system state.

==================================================

RESPONSIVENESS

==================================================

Desktop should feel like a professional tactical command center.

Tablet and mobile should remain fully usable.

Methodology cards should become vertically stacked on smaller screens.

Results tables should become responsive cards where necessary.

==================================================

IMPORTANT

==================================================

For this first frontend generation:

Focus on:

- visual design

- navigation

- layouts

- reusable components

- responsive behaviour

- animations

- realistic placeholder data

Do NOT:

- implement real AI inference

- attempt to run models

- connect Modal

- build the full production API

- invent scientific results

- invent player metrics

- hardcode fake successful identity results

Use clearly-labelled placeholder/mock data where backend integration is not yet available.

The final result should look like a polished university final-project product and a credible modern football analytics platform.

==================================================

OFFICIAL BRAND ASSETS

==================================================

Two official SVG logo assets are provided with this project.

1. Project logo:

   project-logo.svg

2. University logo:

   university-logo.svg

These are AUTHORITATIVE brand assets.

Do NOT:

- redraw either logo

- regenerate either logo

- alter their geometry

- replace them with AI-generated approximations

- change the text contained inside them

- stretch or distort them

- crop important parts of them

Preserve their original aspect ratios.

--------------------------------

PROJECT LOGO USAGE

--------------------------------

The project logo is the PRIMARY product identity.

Use it prominently in:

- the main navigation / sidebar header

- dashboard branding

- loading / analysis states where appropriate

- New Analysis page

- Results header where appropriate

- favicon/app-icon preparation if technically appropriate

- mobile navigation branding

The project logo should visually integrate with the Premium Tactical Command Center theme.

Use subtle green/cyan glow or surrounding UI effects if appropriate, but do NOT modify the SVG artwork itself.

Do not place effects directly inside the logo artwork.

--------------------------------

UNIVERSITY LOGO USAGE

--------------------------------

The university logo is an institutional attribution mark, NOT the primary application brand.

Use it more conservatively.

Appropriate locations:

- footer

- Research / Methodology page

- About / academic project information area

- optional dashboard footer attribution

Example presentation:

"Final Year Project"

[University Logo]

AI-Driven Football Tactical Analysis and Training Evaluation System

Do not make the university logo compete visually with the project logo.

Do not apply neon effects, recolouring, gradients, or visual distortion to the university logo.

Keep sufficient clear space around it.

--------------------------------

NAVIGATION BRANDING

--------------------------------

Desktop navigation should use:

[Project Logo]

Project/product name

Do NOT place the university logo directly beside the project logo in the main navigation as if they form one combined brand.

The university logo should remain secondary academic attribution.

--------------------------------

RESPONSIVE LOGO BEHAVIOUR

--------------------------------

Desktop:

Show the full project logo where space permits.

Tablet:

Maintain correct proportions with slightly reduced dimensions.

Mobile:

Use the project logo in a compact form while maintaining readability.

Never squash the SVG to fit a fixed square.

Use object-fit / intrinsic SVG dimensions correctly.

--------------------------------

ACCESSIBILITY

--------------------------------

Use descriptive alt text:

Project logo:

"AI-Driven Football Tactical Analysis and Training Evaluation System logo"

University logo:

"University logo"

The logos must remain readable against the dark interface.

If the supplied SVG already contains its intended colours/background treatment, preserve them exactly.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/a14a9863-07f3-4874-8b22-a2b62184155e).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
