# Homepage branding polish

- Added the supplied project and university SVGs to `frontend/tactical-ai-insights-main/public/branding/` and placed them side-by-side in the shared header, in that order, with descriptive alt text. The original files in Downloads were not edited.
- Removed white logo tiles. The frontend copy of the university SVG had a solid white background path; it was removed so the logo is transparent. The project logo uses a contrast adjustment against the dark header.
- Updated the shared header, homepage heading, and homepage/root page titles to **AI-Driven Football Tactical Analysis and Training Evaluation System**. The descriptive subtitle remains.
- Changed files: `frontend/tactical-ai-insights-main/src/components/app-shell.tsx`, `frontend/tactical-ai-insights-main/src/routes/index.tsx`, `frontend/tactical-ai-insights-main/src/routes/__root.tsx`, both new `public/branding/*.svg` files, and this note.
- Verified in the local browser at 1440px and 375px: both logos load, remain horizontally aligned, and do not overlap the title or navigation; no horizontal overflow. `npm run build` and `npx tsc --noEmit` both passed.

Frontend branding only. Backend and scientific behavior were unchanged.
