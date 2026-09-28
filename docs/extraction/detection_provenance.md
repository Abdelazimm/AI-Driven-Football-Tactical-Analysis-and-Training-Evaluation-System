# Detection Pipeline Extraction & Provenance Audit

## 1. Source Context & Audited Artifacts

| Attribute | Research Source Provenance |
|---|---|
| **Authoritative Research Source** | `01_vision_pipeline_corrected.ipynb` (Local research root) & `/content/drive/MyDrive/Football_Training_Assistant_MVP/01_vision_pipeline.ipynb` |
| **Source Notebook Size** | 11,328,403 bytes |
| **Source Notebook SHA-256** | `7afe44d5a2de61c8553da122647f32bfcaec05965923c84e4e713e2aba2feb03` |
| **Stage Context** | Stage 4 ("Player Detection Experiments", Cells 67–81) & Stage 4B ("fine_tuning_pilot/yolo11m_pilot_memory_safe") |
| **Selected Deployment Detector** | Stage 4B fine-tuned YOLO11m (`best.pt`) |
| **Detector Checkpoint Path** | `/content/drive/MyDrive/Football_Training_Assistant_MVP/runs/vision_20260805T232509Z_d2f9bc0d/stage_4/fine_tuning_pilot/yolo11m_pilot_memory_safe/weights/best.pt` |
| **Detector File Size** | 40,539,756 bytes |
| **Detector Checkpoint SHA-256**| `f6b3fe6f21256c61083ccc6c6b96dffeb4490c65c3ce150c3924a0fa353e6f5e` |
| **Audit Handoff Reference** | `docs/research_handoff/integration_audit.md` (Sections 4 & 5), `docs/research_handoff/integration_audit.json` |

---

## 2. Research Source Behavior vs. Production Adaptation

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           RESEARCH SOURCE BEHAVIOR                                │
├───────────────────────────────────────────────────────────────────────────────────┤
│ • Hardcoded Colab / Google Drive paths (e.g. /content/drive/MyDrive/...)          │
│ • State coupled to notebook cells (successful_annotation_frame_ids, global vars)  │
│ • Fixed resolutions assumed in various baseline cells (3840x2160 or 1920x1080)    │
│ • In-cell execution of Ultralytics YOLO with direct matplotlib display calls     │
│ • GPU-dependent evaluation on Google Colab CUDA environment                       │
│ • Model loaded directly via global script scope                                   │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │  EXTRACTION & ADAPTATION
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION APPLICATION BEHAVIOR                           │
├───────────────────────────────────────────────────────────────────────────────────┤
│ • Zero hardcoded Drive or Windows paths; runtime configuration via DetectionConfig│
│ • Stateless pure Python functions & classes without notebook side-effects         │
│ • Dynamic resolution support via runtime frame.shape (H, W, C)                    │
│ • Clear decoupling between model loading (load_detector) and frame inference      │
│ • Pure Python/NumPy horizontal tile generator (3 tiles, 15% overlap, no gaps)     │
│ • Pure Python/NumPy tile-to-full-frame coordinate remapping & boundary clipping   │
│ • Pure Python/NumPy Global NMS (IoU 0.70) operating in full-frame coordinates     │
│ • Dynamic timestamp support (caller timestamp_s or derived from ffprobe FPS)      │
│ • Testable on CPU without GPU hardware or loading 40 MB model weights             │
│ • Emits typed Detection schema records with full coordinate provenance            │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Verified Parameter Audit

The deployment detection configuration verified from the research handoff and Stage 4/4B evidence consists of:

| Parameter | Audited Value | Role in Production Pipeline |
|---|---|---|
| **Model Framework** | Ultralytics YOLO | Execution engine for player detection |
| **Target Class ID** | `0` (`person`) | Filters detections exclusively to persons; suppresses balls, sports equipment, etc. |
| **Tile Count** | `3` horizontal tiles | Slices full video frame vertically across width to maximize small-object resolution |
| **Tile Overlap** | `15%` ($0.15$) | Ensures seamless boundary coverage without gaps between adjacent tiles |
| **Inference Image Size (`imgsz`)** | `1280` | Input dimension passed to YOLO network per tile |
| **Confidence Threshold** | `0.20` | Detection confidence cutoff accepted for Stage 4B deployment |
| **Global NMS IoU Threshold**| `0.70` | Inter-tile non-maximum suppression cutoff to merge duplicated players across overlapping seams |

---

## 4. Pipeline Geometry & Coordinate Math

### Horizontal Tile Generation
Given an arbitrary frame of width $W$ and height $H$, with tile count $n = 3$ and overlap fraction $o = 0.15$:
1. Tile width $w_{\text{tile}}$ is derived to span $W$ across $n$ tiles overlapping by $o$:
   $$w_{\text{tile}} = \left\lceil \frac{W}{1 + (n - 1)(1 - o)} \right\rceil = \left\lceil \frac{W}{2.70} \right\rceil$$
2. Tile step $\Delta x = \lfloor (1 - o) \cdot w_{\text{tile}} \rfloor = \lfloor 0.85 \cdot w_{\text{tile}} \rfloor$.
3. Offsets:
   - Tile 0: $x \in [0, w_{\text{tile}}]$, $y \in [0, H]$
   - Tile 1: $x \in [\Delta x, \Delta x + w_{\text{tile}}]$, $y \in [0, H]$
   - Tile 2: $x \in [W - w_{\text{tile}}, W]$, $y \in [0, H]$

### Remapping & Clipping
For a bounding box $[x_1, y_1, x_2, y_2]$ detected in Tile $i$ with origin $(x_{\text{offset}}, 0)$:
$$x_{1,\text{full}} = x_1 + x_{\text{offset}}, \quad x_{2,\text{full}} = x_2 + x_{\text{offset}}$$
$$y_{1,\text{full}} = y_1, \quad y_{2,\text{full}} = y_2$$
Coordinates are strictly clipped to $[0, W]$ and $[0, H]$.

### Global NMS
Merged candidates from all tiles are sorted by confidence descending. Candidates with $\text{IoU} \ge 0.70$ relative to higher-confidence candidates in full-frame coordinates are suppressed. All coordinates remain in **full-frame pixels**.
