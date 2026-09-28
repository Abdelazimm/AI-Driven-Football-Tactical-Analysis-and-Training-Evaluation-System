# AGENTS.md — System Rules & Scientific Boundaries

## 1. Project Context & Purpose

This workspace hosts the application-integration phase of the University of London / Goldsmiths final-year Computer Science project:
**AI-Driven Football Tactical Analysis and Training Evaluation System**.

This is **APPLICATION INTEGRATION** work, not a new research experiment. All research notebooks, historical runs, and experiments are frozen and read-only.

---

## 2. Absolute Research Safety Rules

All future coding agents must strictly obey the following rules:

1. **Original Research is Read-Only**:
   - Do NOT modify existing research notebooks (`01_vision_pipeline.ipynb`, `02_audio_pipeline.ipynb`, `03_orchestrator_fusion.ipynb`, `04_report_generation.ipynb`, `Autonomus_scout.ipynb`).
   - Do NOT modify E0–E6 experiments or frozen split configurations.
   - Do NOT modify frozen detections, persistent-identity outputs, or historical/corrected homography validation files.
   - Do NOT modify C03, C04, or C06 showcase evidence or final capability-showcase artifacts.
   - Do NOT delete, move, rename, or overwrite research artifacts.

2. **No Automatic Research Reruns**:
   - Do NOT rerun research experiments.
   - Do NOT retrain models.
   - Do NOT rerun YOLO, tracking (BoT-SORT), ReID (PRTReID), GTA, ASR (Whisper), homography fitting, kinematics, or Ollama.
   - Any integration code must extract clean, modular, tested copies of logic into application packages, leaving research code untouched.

3. **Never Fabricate Data**:
   - Never fabricate player identities.
   - Never fabricate coach-instruction tactical targets.
   - Never fabricate metric distances, speeds, or coordinates.
   - If an observation, target, or speed is unavailable or invalid, report it explicitly as unavailable or withheld. Never emit an invented zero.

4. **No Path Dependencies on Research Environments**:
   - No Google Colab paths (`/content/drive/...`) may become runtime production dependencies.
   - No Windows absolute paths (`D:\...`, `C:\...`) may become runtime production dependencies.
   - All runtime file operations must use relative paths, environment-configured directories, or cloud object storage (Supabase Storage).

5. **Secrets & Security**:
   - Never expose API keys, database credentials, service-role keys, or OAuth secrets in frontend bundles or client-facing code.
   - Raw participant media and unredacted ASR transcripts must remain private.

---

## 3. Project Scientific State & Identity Safety Gate

### Persistent Identity Reality
Automated persistent identity in the research pipeline remains:
```
status:               FAIL_HIGH_FRAGMENTATION
raw_track_ids:        115
meaningful_ids:       37
fragmentation_ratio:  6.1667
acceptance_threshold: 1.5
```
This result is definitive and must **NEVER** be reinterpreted as successful automated persistent identity. ReID, micro-track stitching, GTA, and Deep-EIoU research did not solve identity fragmentation for full sessions.

### Mandatory Identity Gate Behavior
- Automated player-specific tactical assessment requires a **passed** identity safety gate.
- When `fragmentation_ratio > 1.5`, player-level conclusions must be **WITHHELD**.
- An identity failure **must NOT crash the application**.
- The application must fail safely and return `COMPLETED_WITH_LIMITATIONS` with `player_level_analysis_allowed = false` and an explicit `withholding_reason`.
- Anonymous, team-level, and observable spatial evidence may still be reported.

---

## 4. Validated Capability Showcase (Oracle-Assisted)

The golden capability showcase holds the status:
```
status: PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE
mode:   ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION
```
Included use cases:
- **C06**: Pressing Response
- **C04**: Defensive Marking / Close-Down
- **C03**: Hold Position / Tactical-Zone Retention

For all showcase cases:
- Player identity was **manually verified**.
- Coach-instruction target was **manually verified**.
- Opponent relationships were **manually verified**.
- Tactical-zone meaning was **manually verified** where applicable.

**Rule**: The application must NEVER present these showcase examples as evidence that automated persistent identity succeeded. Frozen golden showcase evidence must never be regenerated automatically.

---

## 5. Metric Calibration & Kinematics Rules

### Pitch Calibration
- Corrected physical research pitch dimensions: Length **19.31 m**, Width **19.88 m**.
- Calibration classification: `MODERATE_CONFIDENCE_MEASURED_METRIC_ESTIMATE`.
- Independent corrected homography RMSE: **0.651 m** (max error 0.841 m).
- The fixed research homography matrix is **CAMERA-SPECIFIC** and geometry-specific.
- It must **NEVER** silently be applied to arbitrary uploaded videos.

### Required Calibration Modes
1. `DEMO_FIXED_CALIBRATION`: Only valid for the original research camera setup and pitch.
2. `CUSTOM_PITCH_CALIBRATION`: For user-provided 4-point/landmark calibration with geometry validation.
3. `NO_METRIC_CALIBRATION`: For analysis without pitch calibration.

### Rules for Non-Metric Mode & Arbitrary Videos
- In `NO_METRIC_CALIBRATION` (or `ANALYSIS_WITHOUT_METRICS` mode), the application must **NEVER** present metres, km/h, metric distance covered, or metric separation. Pixel measurements must never be labelled metres.
- Uploaded-video FPS must be extracted dynamically from video metadata via `ffprobe`/container header. Never hardcode 59.972 FPS.
- Uploaded-video resolution must be detected dynamically. Never assume 3840x2160 or 1920x1080.
- Kinematics outlier rejection: speeds exceeding **36 km/h** must be rejected.
- Never interpolate speed or distance across tracking or temporal gaps.

---

## 6. Official Deployment Detector Decision

The deployment detector is explicitly selected as:
- **Model**: Stage 4B fine-tuned YOLO11m (`best.pt`)
- **Framework**: Ultralytics
- **Runtime Role**: Player detection
- **Status**: `SELECTED_FOR_DEPLOYMENT`
- **Audited Source Artifact**: `/content/drive/MyDrive/Football_Training_Assistant_MVP/runs/vision_20260805T232509Z_d2f9bc0d/stage_4/fine_tuning_pilot/yolo11m_pilot_memory_safe/weights/best.pt`
- **SHA-256**: `f6b3fe6f21256c61083ccc6c6b96dffeb4490c65c3ce150c3924a0fa353e6f5e`
- **Size**: 40,539,756 bytes
- **Tiling**: 3 horizontal tiles, 15% overlap, `imgsz=1280`, person class (`classes=[0]`), global NMS IoU 0.70, confidence threshold 0.20.

*Note*: The Experiment C YOLOv8m artifact is a frozen research/reproducibility artifact and is **NOT** the default deployment detector.
