# CM3070 P0 Architecture & Contract Freeze — Revision 1 (REV1)

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 1)  
**Status**: `P0_CONTRACT_FREEZE_REV1_READY_FOR_REVIEW`  
**Authoritative Reference**: `CM3070_CANONICAL_FINAL_REPORT_EVIDENCE_LOG_v88.md`, `M1_FINAL_EVALUATION_BASELINE.json`, `M2_FINAL_EVALUATION_BASELINE.json`, `M3_selected_identity_configuration.json`  
**Execution Mode**: `ARCHITECTURE_AND_CONTRACT_FREEZE_ONLY` (Implementation Frozen)

---

## 1. Product Execution Policy (Objective 1)

### 1.1 Methodology Hierarchy & Identifiers
The production system defines three selectable methodologies and one automatic resolution rule. No cross-methodology component mixing is permitted under any circumstance.

| User-Facing Label | Requested Methodology | Resolved ID (`MethodologyId`) | Scientific Methodology Definition | Operational Role |
| :--- | :--- | :--- | :--- | :--- |
| **Auto / Recommended** | `AUTO` | `METHOD_2_RFDETR_GTATRACK` | Deterministic alias resolving to M2 Global Association | **Default Production Pipeline** |
| **Method 2: Global Association** | `METHOD_2_RFDETR_GTATRACK` | `METHOD_2_RFDETR_GTATRACK` | Fine-tuned RF-DETR Large ($\text{conf} \ge 0.50$, no NMS) + Deep-EIoU (OSNet-x1.0) + GTA-Track Offline Global Association | Primary / Benchmark Winner |
| **Method 1: Original Hybrid** | `METHOD_1_YOLO11_BOTSORT` | `METHOD_1_YOLO11_BOTSORT` | Domain-adapted YOLO11m (`M1_FORMAL_003` epoch-28) + 3-Tile Global NMS + BoT-SORT ($0.35/0.10$, buffer 120, match 0.85) + FastReID SBS-50 | Comparative Baseline |
| **Method 3: Re-entry Focused** | `METHOD_3_YOLO26_SRITRACK` | `METHOD_3_YOLO26_SRITRACK` | YOLO26 End-to-End Detector ($\text{conf} \ge 0.30$) + SRITrack-v1 (`M3_SRC_DEFAULT` amended birth gate $0.30$) + DINOv3 ReID | Secondary Modern Baseline |

```typescript
export enum MethodologyId {
  METHOD_1_YOLO11_BOTSORT = "METHOD_1_YOLO11_BOTSORT",
  METHOD_2_RFDETR_GTATRACK = "METHOD_2_RFDETR_GTATRACK",
  METHOD_3_YOLO26_SRITRACK = "METHOD_3_YOLO26_SRITRACK",
}

export enum RequestedMethodology {
  AUTO = "AUTO",
  METHOD_1_YOLO11_BOTSORT = "METHOD_1_YOLO11_BOTSORT",
  METHOD_2_RFDETR_GTATRACK = "METHOD_2_RFDETR_GTATRACK",
  METHOD_3_YOLO26_SRITRACK = "METHOD_3_YOLO26_SRITRACK",
}

export enum IdentityEvidenceBasis {
  FORMAL_DENSE_GT = "FORMAL_DENSE_GT",
  HUMAN_ORACLE = "HUMAN_ORACLE",
  RUNTIME_HEURISTIC_ONLY = "RUNTIME_HEURISTIC_ONLY",
  NOT_AVAILABLE = "NOT_AVAILABLE",
}
```

### 1.2 Default Resolution Semantics
- When `AUTO` is submitted (via UI or API request omitted field), the backend dispatcher deterministically resolves the execution pipeline to `METHOD_2_RFDETR_GTATRACK`.
- Both `requested_methodology` and `resolved_methodology` are stored immutably in the job dispatch payload and the persistent database record.
- Any request for an unknown or unsupported methodology string is rejected immediately at API ingress with HTTP `422 Unprocessable Entity` (`INVALID_METHODOLOGY_IDENTIFIER`).

### 1.3 Exact Final Methodology Baseline Freezes (Correction 1)
Components must strictly adhere to the frozen formal evaluation baselines:

#### Method 1 Frozen Baseline (`M1_FINAL_EVALUATION_BASELINE.json`)
- **Detector**: YOLO11m domain-adapted checkpoint `runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt`
  - SHA-256: `ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b`
  - File Size: `104,950,959` bytes
  - Tiling: 3 horizontal windows at $1920 \times 1080$ ($[0, 712]$, $[605, 1317]$, $[1208, 1920]$)
  - Tile NMS IoU: $0.70$, Global NMS IoU: $0.50$, imgsz: $1280$, half: `true`
  - Standalone qualification confidence: $0.25$, tracker input floor: $0.05$
- **Tracker**: Ultralytics BoT-SORT with external ReID feature bridge
  - `track_high_thresh = 0.35`
  - `track_low_thresh = 0.10`
  - `new_track_thresh = 0.35`
  - `track_buffer = 120`
  - `match_thresh = 0.85`
  - `gmc_method = "none"`
  - `proximity_thresh = 0.15`
  - `appearance_thresh = 0.88`
  - `with_reid = true`
  - `fuse_score = true`

#### Method 2 Frozen Baseline (`M2_FINAL_EVALUATION_BASELINE.json`)
- **Detector**: RF-DETR Large checkpoint `runs/method_2/M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth`
  - SHA-256: `7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85`
  - Version: `rfdetr 1.10.1`, internal resolution $704$, native top queries $300$
  - Operating Point: **`selection_confidence_inclusive = 0.50`** (formal threshold $\ge 0.50$; 0.40 is superseded)
  - Score Semantics: Native sigmoid score; **`external_nms = false`** (no external NMS)
- **Local ReID**: OSNet-x1.0 checkpoint `runs/method_2/M2_P0_preflight/checkpoints/sports_model.pth.tar-60`
  - SHA-256: `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd`
  - Embedding Dimension: $512$, crop clamped to $1920 \times 1080$, resize $[256, 128]$
- **Local Tracker**: Deep-EIoU from GTATrack-STC2025 (`source_sha256 = 6caecd0f...`, `config_sha256 = a3b96034...`)
  - Parameters: `track_high_thresh = 0.70`, `track_low_thresh = 0.40`, `new_track_thresh = 0.70`, `track_buffer = 90`, `match_thresh = 0.80`, `proximity_thresh = 0.50`, `appearance_thresh = 0.25`, `with_reid = true`
- **Global Association**: GTA-Track Offline Global Association Graph Solver (`M2_GTA_BASELINE_REV1`)

#### Method 3-v1 Frozen Baseline (`M3_selected_identity_configuration.json` & `M3_score_compatibility_amendment.json`)
- **Detector**: YOLO26 custom domain-adapted checkpoint `M3_FORMAL_001_DOMAIN_ADAPTED`
  - Operating Point: **`confidence >= 0.30`** (0.25 is superseded)
- **Tracker**: SRITrack-v1 configuration `M3_SRC_DEFAULT` with P5A score compatibility amendment
  - `track_high_th = 0.60`
  - `track_low_th = 0.10`
  - `track_new_th = 0.30` (amended from source default 0.70 to align with 0.30 detector operating point)
  - `track_buffer = 1000`
  - `track_match_th = 0.80`
  - `track_p_th = 0.50`, `track_vc_th = 0.50`, `track_vf_th = 0.25`, `track_b_th = 0.70`
  - `with_reid = true`, `EIoU = true`, `vp_dga = true`, `ris = true`, `det_min_area = 10`
  - Resolved Config SHA-256: `feeeb76e365a7e2c255e5946e7f7e7c67162530ab06112b6a8b83fbd8403f8ed`
  - Shared Amendment SHA-256: `8f9080ecfa2ca4b264c00124cae91890b8de871162e001e7312b7a3bb04f51c6`

### 1.4 Forensic Status of Legacy Stage 4B
- `STAGE4B_IS_SUPERSEDED_LEGACY_IMPLEMENTATION`: The pilot checkpoint (`best.pt`, 40.5 MB, SHA-256 `f6b3fe6f...`) was an early pilot exploration. It is NOT the deployment detector for M1.
- `STAGE4B_TILING_UTILITY_MAY_BE_REUSED`: Slicing and offset-remapping functions in `backend/app/pipeline/detection.py` (`generate_horizontal_tiles`, `remap_tile_bbox_to_full_frame`, `apply_global_nms`) are verified algorithmically sound and may be used by the M1 adapter.

### 1.5 Decoupled Identity Assurance Architecture (Correction 4)
The system strictly distinguishes between formal research evaluation against dense ground truth and runtime execution on arbitrary uploads:
1. **Formal Evaluation Identity Status** (`FORMAL_EVALUATION_IDENTITY_STATUS`):
   Formal dense-GT whole-system challenge evaluation established that all three methods trigger:
   $$\text{IdentityStatus} = \text{FAIL\_UNSAFE\_MERGE}$$
2. **Production Runtime Identity Assurance** (`PRODUCTION_RUNTIME_IDENTITY_ASSURANCE`):
   Arbitrary production uploads do NOT possess dense physical-player ground truth. Runtime heuristics (fragmentation count, instantaneous track conflict checks) provide operational diagnostics only and **cannot elevate an automated run to trusted physical identity**.
3. **Mandatory Fail-Closed Policy**:
   $$\text{AUTOMATED\_PLAYER\_LEVEL\_ACCUMULATED\_ANALYTICS} = \text{DISABLED}$$
   For all M1, M2, and M3 automated production runs, trusted accumulated physical-player attribution is disabled. Individual distance, speed, sprint count, and individual coach compliance metrics are strictly WITHHELD.
   *Exception*: Mode `VALIDATED_SHOWCASE` with `HUMAN_VERIFIED / ORACLE` provenance.

---

## 2. Canonical Vision Result Contract (Objectives 2, 5, 6, 14)

### 2.1 Canonical Coordinate System & Bounding Box Normalization (Correction 6)
To eliminate array-ordering ambiguities between pixel and normalized coordinates, the contract specifies **one consistent canonical ordering** $[x_1, y_1, x_2, y_2]$ for both representations, accompanied by explicit named attributes:

$$\text{Canonical Box} = [x_1, y_1, x_2, y_2] \quad \text{where } x_1 < x_2 \text{ and } y_1 < y_2$$

```python
from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    # Source-pixel coordinates [x1, y1, x2, y2]
    x1: float = Field(..., description="Top-left x in source pixels")
    y1: float = Field(..., description="Top-left y in source pixels")
    x2: float = Field(..., description="Bottom-right x in source pixels")
    y2: float = Field(..., description="Bottom-right y in source pixels")
    
    # Normalized coordinates [x1_norm, y1_norm, x2_norm, y2_norm] matching exact [x1, y1, x2, y2] ordering
    x1_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized left [0..1]")
    y1_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized top [0..1]")
    x2_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized right [0..1]")
    y2_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom [0..1]")
```

### 2.2 Track Identifier Semantics (Correction 5)
Automated track IDs are strictly method-local trajectory indices, not physical player identities.
- Canonical Field: **`opaque_track_id`** (or `method_track_id`), defined as:
  *"Method-local trajectory identifier only; not a verified physical-player identity."*
- Optional Pseudonym Field: **`physical_player_pseudonym`**, optional string (`None` for all automated runs; populated strictly under `HUMAN_VERIFIED / ORACLE`).

### 2.3 Typed Common Vision Schema (Correction 14)

```python
class TrackObservation(BaseModel):
    opaque_track_id: int = Field(..., description="Method-local trajectory index; NOT verified physical identity")
    physical_player_pseudonym: Optional[str] = Field(None, description="Populated ONLY under HUMAN_VERIFIED / ORACLE")
    tracklet_id: Optional[int] = Field(None, description="Native sub-tracklet identifier prior to global association")
    box: BoundingBox = Field(..., description="Canonical source pixel and normalized bounding box [x1, y1, x2, y2]")
    class_id: int = Field(default=0, description="0: Player, 1: Ball, 2: Referee")
    class_name: str = Field(default="player", description="Class label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    visibility: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Occlusion/visibility score")
    raw_detection_box: Optional[List[float]] = Field(None, description="Pre-association native box for audit provenance")

class FrameVisionResult(BaseModel):
    source_frame_index: int = Field(..., ge=0, description="Source video 0-indexed frame number")
    source_timestamp_s: float = Field(..., ge=0.0, description="Timestamp derived as source_frame_index / source_fps")
    processed_frame_index: int = Field(..., ge=0, description="Inference pipeline sequence index")
    observations: List[TrackObservation] = Field(default_factory=list, description="All tracked objects in frame")
    is_empty_frame: bool = Field(default=False, description="True if zero players detected; fails safely")

class MethodProvenance(BaseModel):
    requested_methodology: str
    resolved_methodology: str
    detector_model: str
    detector_checkpoint_sha256: str
    tracker_name: str
    tracker_config_sha256: str
    reid_model: Optional[str] = None
    reid_checkpoint_sha256: Optional[str] = None
    tiling_enabled: bool = False
    tile_count: int = 1
    tile_overlap_pct: float = 0.0
    nms_iou_threshold: Optional[float] = None
    confidence_threshold: float
    source_to_inference_scale: List[float] = Field(..., description="[scale_x, scale_y]")
    inference_resolution: List[int] = Field(..., description="[width, height]")
    runtime_wall_s: float

class SessionVisionResult(BaseModel):
    session_id: str
    video_id: str
    source_width: int
    source_height: int
    source_fps: float
    total_source_frames: int
    duration_seconds: float
    requested_methodology: str
    resolved_methodology: str
    identity_evidence_basis: str = "RUNTIME_HEURISTIC_ONLY"
    provenance: MethodProvenance
    frames: List[FrameVisionResult]
    total_detections: int
    unique_track_ids: int
    partial_failure_state: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)
```

---

## 3. M1 / M2 / M3 Adapter Contracts (Objective 3)

### 3.1 Method 1 Adapter (`M1Yolo11BotSortAdapter`)
- **Native Input**:
  - Detections: YOLO11m `M1_FORMAL_003` epoch-28 on 3 tiles ($1280 \times 1280$, overlap 15%). Score floor: $0.05$ for tracking input, qualification $0.25$.
  - Tracker: BoT-SORT ($0.35/0.10$, buffer 120, match 0.85, GMC none) emitting `tlwh` in $1920 \times 1080$.
- **Adapter Transformation**:
  1. Remap tile horizontal offsets: $x_{\text{global}} = x_{\text{tile}} + \text{offset}_x$.
  2. Compute scaling: $s_x = W_{\text{source}} / 1920.0$, $s_y = H_{\text{source}} / 1080.0$.
  3. Transform coordinates to canonical $[x_1, y_1, x_2, y_2]$:
     $$x_1 = \text{tl\_x} \times s_x, \quad y_1 = \text{tl\_y} \times s_y, \quad x_2 = (\text{tl\_x} + w) \times s_x, \quad y_2 = (\text{tl\_y} + h) \times s_y$$
  4. Map BoT-SORT track integer to `opaque_track_id`. Leave `physical_player_pseudonym = None`.

### 3.2 Method 2 Adapter (`M2RfDetrGtaTrackAdapter`)
- **Native Input**:
  - Detections: RF-DETR Large checkpoint `checkpoint_best_total.pth` (SHA-256 `7539cfb3...`). Formal threshold: **$\text{conf} \ge 0.50$**, `external_nms = false`.
  - Tracklets: Deep-EIoU generates short tracklets with `last_tlwh` geometry in source resolution.
  - Global Association: GTA-Track offline graph solver assigns tracklets to global trajectory IDs.
- **Adapter Transformation**:
  1. Convert native `last_tlwh` to canonical $[x_1, y_1, x_2, y_2]$:
     $$x_1 = \text{tl\_x}, \quad y_1 = \text{tl\_y}, \quad x_2 = \text{tl\_x} + w, \quad y_2 = \text{tl\_y} + h$$
  2. Map Deep-EIoU sub-tracklet index to `tracklet_id`.
  3. Map GTA-Track assigned global trajectory ID to `opaque_track_id`. Leave `physical_player_pseudonym = None`.

### 3.3 Method 3 Adapter (`M3Yolo26SriTrackAdapter`)
- **Native Input**:
  - Detections: YOLO26 domain-adapted checkpoint. Formal threshold: **$\text{conf} \ge 0.30$**.
  - Tracker: SRITrack-v1 `M3_SRC_DEFAULT` with amended birth gate $0.30$ (`track_new_th = 0.30`, buffer 1000). Native boxes are $[x_1, y_1, x_2, y_2]$ in inference resolution ($1280 \times 720$).
- **Adapter Transformation**:
  1. Compute scaling: $s_x = W_{\text{source}} / 1280.0$, $s_y = H_{\text{source}} / 720.0$.
  2. Project boxes:
     $$x_1 = x_{1,\text{infer}} \times s_x, \quad y_1 = y_{1,\text{infer}} \times s_y, \quad x_2 = x_{2,\text{infer}} \times s_x, \quad y_2 = y_{2,\text{infer}} \times s_y$$
  3. Map SRITrack trajectory ID to `opaque_track_id`. Leave `physical_player_pseudonym = None`.

---

## 4. Identity Safety Contract (Objective 4 & Correction 4)

### 4.1 Production Identity Evaluation States & Evidence Basis
The identity gate produces a typed result binding the evaluation status to its evidence basis:

```typescript
export enum IdentityStatus {
  NOT_EVALUATED = "NOT_EVALUATED",
  PASS_RELIABLE = "PASS_RELIABLE",
  FAIL_HIGH_FRAGMENTATION = "FAIL_HIGH_FRAGMENTATION",
  FAIL_IDENTITY_CONFLICT = "FAIL_IDENTITY_CONFLICT",
  FAIL_UNSAFE_MERGE = "FAIL_UNSAFE_MERGE",
  FAIL_INVALID_OUTPUT = "FAIL_INVALID_OUTPUT",
}

export enum IdentityEvidenceBasis {
  FORMAL_DENSE_GT = "FORMAL_DENSE_GT",
  HUMAN_ORACLE = "HUMAN_ORACLE",
  RUNTIME_HEURISTIC_ONLY = "RUNTIME_HEURISTIC_ONLY",
  NOT_AVAILABLE = "NOT_AVAILABLE",
}
```

### 4.2 Production Invariants
1. **Automated Upload Guard**: For any automated analysis run (`identity_evidence_basis == RUNTIME_HEURISTIC_ONLY`), `player_level_analysis_allowed` is **strictly False**.
   - Runtime heuristics (e.g. fragmentation count, frame conflict checks) generate diagnostic warnings only.
   - Heuristics cannot grant `PASS_RELIABLE` or unlock trusted physical-player analytics.
2. **Withholding Policy**:
   - `player_level_analysis_allowed = false`
   - Withholding reason explicitly populated: *"Player-level tactical conclusions and physical metrics are withheld because automated persistent identity has not been validated as reliable without dense ground truth."*
   - All accumulated player metrics (`distance_covered_m`, `average_speed_kmh`, `sprint_count`) are set to `null` with display value `"Withheld (Identity Gate)"`.

---

## 5. Metric Calibration Contract (Objective 5 & Corrections 3, 7)

### 5.1 Operating Modes & Evidence Basis
Pitch homography mapping is camera-specific and geometry-specific. It must never silently be applied to arbitrary uploaded videos.

```python
class CalibrationMode(str, Enum):
    NO_METRIC_CALIBRATION = "NO_METRIC_CALIBRATION"
    CAMERA_SPECIFIC_METRIC_CALIBRATION = "CAMERA_SPECIFIC_METRIC_CALIBRATION"
    INVALID_CALIBRATION = "INVALID_CALIBRATION"

class CalibrationEvidenceBasis(str, Enum):
    CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED = "CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED"
    GEOMETRIC_SOLVE_ONLY = "GEOMETRIC_SOLVE_ONLY"
    NO_CALIBRATION = "NO_CALIBRATION"
    INVALID = "INVALID"
```

### 5.2 Research Homography Provenance (Correction 3)
- Authoritative Configuration File: `config/3v3_homography_measured_metric_corrected.json`
- Authoritative SHA-256:
  `d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507`
- Pitch Geometry: Length **$19.31 \text{ m}$**, Width **$19.88 \text{ m}$**
- Independent Landmark Validation: 4 independent points, RMSE $= \mathbf{0.6505 \text{ m}}$ ($\approx 0.651 \text{ m}$), max error $0.8409 \text{ m}$, median error $0.6277 \text{ m}$.
- Classification: `MODERATE_CONFIDENCE_MEASURED_METRIC_ESTIMATE`.
- Scope: Restricted exclusively to research iPhone16 tripod setup on the measured pitch.

### 5.3 Decoupling Homography Solve from Independent Validation (Correction 7)
- Solving a 4-point homography computes a planar transformation ($H_{3 \times 3}$) from 4 source points to 4 destination points with algebraic residual zero.
- It does **NOT** provide independent landmark validation. Claims of "RMSE $< 1.50\text{ m}$" based solely on the 4 solve points are scientifically invalid and strictly prohibited.
- For user-supplied 4-point inputs without separate ground-truth test landmarks:
  - Classification is `GEOMETRIC_SOLVE_ONLY`.
  - Transform may be used for bounded geometric visualization (e.g. 2D pitch radar), but research-level metric accuracy is not claimed.
- For all uncalibrated uploads: Default is `NO_METRIC_CALIBRATION`. Metres ($m$) and $km/h$ are strictly suppressed. Measurements remain in pixels ($px, px/s$).

---

## 6. Kinematics Contract (Objective 6 & Correction 8)

### 6.1 Scientific Smoothing & Outlier Rejection Invariants
Kinematic calculations must adhere to the frozen scientific filtering rules:
1. **Temporal Filtering**: Centred rolling median filter over **7 observations per raw track** to suppress bounding box edge jitter.
2. **Temporal Gap Policy**: Velocity is calculated only for valid frame gaps:
   $$0 < \Delta_{\text{frames}} \le 120 \quad (\le 2.0\text{ s at 60 FPS})$$
   No interpolation is permitted across missing tracking observations or identity gaps. Across temporal tracking gaps $> 0.50 \text{ s}$ ($30$ frames at 60 FPS), velocity resets to `null`.
3. **Outlier Rejection Semantics (Correction 8)**:
   Frozen strictly as **`REJECT_AND_EXCLUDE_OUTLIER`**:
   $$\text{speed} > 36.0 \text{ km/h} \implies \text{Outlier Rejected}$$
   Any calculated instantaneous speed exceeding $36.0 \text{ km/h}$ ($10.0 \text{ m/s}$) is rejected as an unphysical outlier (caused by boundary jumps or tracking switches) and **strictly excluded from accepted steps, cumulative distance covered, and mean/peak speed statistics**. It is never clamped.

---

## 7. ASR / Instruction Contract (Objective 7)

### 7.1 Production ASR Engine Specification
- Engine: `faster-whisper base.en` executed via `CTranslate2`.
- Runtime: CPU `int8`, 8 compute threads, 16 kHz mono audio channel, Silero VAD preprocessing.
- Tactical Categories: `Pressing`, `Defensive`, `Positioning / Hold Ground`, `Passing`, `Offensive`.

### 7.2 Strict Elimination of Research Fallback
- The historical research pipeline contained an unsafe fallback catching all exceptions and silently returning a hardcoded historical session transcript from `g:/My Drive/...`.
- **THIS BEHAVIOR IS ELIMINATED.**
- If audio extraction or ASR transcription fails:
  1. Emit typed `ASRFailure` with an explicit error code (`AUDIO_EXTRACTION_FAILED`, `FFMPEG_ERROR`, `TRANSCRIPTION_TIMEOUT`).
  2. Record limitation: `"Coaching audio transcription failed; tactical instruction compliance analysis withheld."`
  3. Pipeline transitions to Vision-only mode (`COMPLETED_WITH_LIMITATIONS`).
  4. Never substitute a canned, mock, or historical transcript.

---

## 8. Multimodal Fusion Contract (Objective 8 & Correction 2)

### 8.1 Validated Temporal Response Window (Correction 2)
The scientifically frozen multimodal response window evaluates player movement following the completion of coach speech:

$$\text{evaluation\_start} = t_{\text{instruction\_end}} + 2.0 \text{ seconds}$$
$$\text{evaluation\_end} = t_{\text{instruction\_end}} + 6.0 \text{ seconds}$$

$$\text{Evaluation Window} = [t_{\text{end}} + 2.0\text{s}, \; t_{\text{end}} + 6.0\text{s}]$$

*Historical Clarification*: Early research exploratory scripts (Notebook 3) utilized a $[-2.0\text{s}, +5.0\text{s}]$ pre-command window for exploratory visual alignment. The frozen formal decision rules establish $[+2.0\text{s}, +6.0\text{s}]$ as the validated post-command response evaluation window.

### 8.2 Clean Boundary Rules (No Research Constants)
The production Fusion engine is completely redesigned to eliminate research mocks:
- NO hardcoded `PLAYER_01`.
- NO fixed $339.87\text{s}$ duration assumption.
- NO fixed $2500$ observation row assumption.
- NO synthetic $4.5\text{ m}$ displacement or $8.2\text{ km/h}$ speed injection.

### 8.3 Evidence Scopes & Typed Payload
- Allowed Scopes: `TEAM`, `SPATIAL`, `EVENT`, `ANONYMOUS_TRACK`, `PLAYER`.
- **Player Scope Gate**: `scope = PLAYER` is **strictly prohibited** unless `identity_evidence_basis == HUMAN_ORACLE` or `ApplicationMode == VALIDATED_SHOWCASE`.
- Under automated modes, all coaching events retain `target_resolution_status = "UNRESOLVED_TARGET"` and emit evidence only under `EVENT`, `TEAM`, or `ANONYMOUS_TRACK`.

---

## 9. Oracle Mode Contract (Objective 9 & Correction 10)

### 9.1 Provenance Readback of Verified Showcase Cases (Correction 10)
Showcase cases **C03, C04, and C06** preserve their verified calculations without recomputation. The values below are read back directly from the authoritative evidence artifacts in `physical_metric_upgrade/experiments/capability_showcase/metric_extensions_corrected/`:

| Metric / Parameter | Showcase C04: Marking | Showcase C06: Pressing | Showcase C03: Hold Position |
| :--- | :--- | :--- | :--- |
| **Case Identifier** | `C04_DEFEND_167_174` | `C06_PRESS_272_277` | `C03_HOLD_78_90` |
| **Source Evidence Artifact** | `C04_marking_metric/C04_metric_evidence.json` | `C06_pressing_metric/C06_metric_evidence.json` | `C03_hold_position_metric/C03_metric_evidence.json` |
| **Target Player** | `BLACK_01` (Track 69, manual) | `RED_01` (Track 157, manual) | `RED_03` (Track 41, manual) |
| **Opponent / Zone** | Opponent `RED_03` (Track 41) | Opponents `BLACK_03` (T185$\rightarrow$193), `BLACK_01` (T155) | Right goal-side final third ($x \in [12.87, 19.31]\text{m}$) |
| **Pre-Command Baseline** | Median separation: **$14.30 \text{ m}$** (mean $14.47\text{m}$, min $13.95\text{m}$) | Ev1 onset sep: $1.97\text{m}$; Ev2 onset sep: $4.14\text{m}$ | Pre-command distance to zone: **$4.66 \text{ m}$** |
| **Response Metric** | Min separation: **$7.96 \text{ m}$** (closing dist: **$6.34 \text{ m}$**, $44.35\%$ reduction) | Ev1 min sep: **$0.70 \text{ m}$**; Ev2 min sep: **$0.49 \text{ m}$** ($86.40\%$ reduction) | Zone entry at **$81.20 \text{ s}$** (latency **$3.24 \text{ s}$**); Repositioning path: **$8.51 \text{ m}$** |
| **Speed / Kinematics** | Mean speed: **$5.76 \text{ km/h}$**; Distance: **$34.58 \text{ m}$** | Ev1 mean speed: $3.48\text{ km/h}$; Ev2 mean speed: **$9.12 \text{ km/h}$** | Repositioning speed: **$10.09 \text{ km/h}$**; Retention speed: $3.91\text{ km/h}$ |
| **Tactical Compliance** | Follow-up sep median: **$4.30 \text{ m}$** ($100\%$ below baseline) | Directional approach: Ev1 $0.77\text{m}$; Ev2 $4.02\text{m}$ | Zone retention: **$100.0\%$** ($5.00\text{s}$ inside, 0 exits, excursion $0.0\text{m}$) |
| **Independent RMSE** | $0.6505 \text{ m}$ ($\approx 0.651 \text{ m}$) | $0.6505 \text{ m}$ ($\approx 0.651 \text{ m}$) | $0.6505 \text{ m}$ ($\approx 0.651 \text{ m}$) |
| **Status / Sanity** | `PASS_C04_CORRECTED_METRIC_EXTENSION` | `PASS_C06_CORRECTED_METRIC_EXTENSION` | `PASS_C03_CORRECTED_METRIC_EXTENSION` |
| **Coach Summary Exclusions**| Peak speed $35.76\text{ km/h}$ (threshold-sensitive) | Peak speeds $35.59, 35.53\text{ km/h}$; Overall distance $17.64\text{m}$ | Retention path $5.43\text{m}$ (jitter-sensitive) |

---

## 10. LLM / Report Contract (Objective 10 & Correction 9)

### 10.1 Frozen LLM Model & Prompt Identity
- Model: `llama3.1:8b` via Ollama.
- Exact Model Digest:
  `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`
- System Prompt SHA-256:
  `ab95a8350208367aee29395866ece720c17c85c8d03a79b33b052e99442ae9ce`

### 10.2 Exact Frozen Patch 001 Validator Gates (Correction 9)
Every generated report is verified against the exact 8 gates of `LLM_GROUNDING_VALIDATOR_PATCH_001`:

1. **Gate 1: `IDENTITY_SAFETY_NEW_PLAYER_ID`**  
   If `player_level_reporting_enabled == False`, asserts that the generated text contains ZERO occurrences of player pseudonyms (`Player_XX`, `Player XX`, `PlayerXX`). Violation: `UNSUPPORTED_PLAYER_IDENTITY`.
2. **Gate 2: `PROHIBITED_PSYCHOLOGICAL_INFERENCE`**  
   Rejects speculative psychological, disciplinary, or motivational terms (`lazy`, `unmotivated`, `disciplined`, `focused`, `hesitant`, `distracted`). Violation: `OVERSTATED_CERTAINTY`.
3. **Gate 3: `PRIVACY_NAME_LEAK`**  
   Rejects occurrences of participant real names, asserting canonical pseudonymization compliance. Violation: `PRIVACY_POLICY_VIOLATION`.
4. **Gate 4: `UNSUPPORTED_NUMERIC_VALUES` (Patched)**  
   Extracts all numeric literals using `NUM_PAT = re.compile(r"(?<![A-Za-z_0-9\[])\d+(?:\.\d+)?(?![0-9])")` across all leaves of `evidence_dict` (including strings via `all_numbers_patched`). Asserts that every number in generated text exists in evidence within tolerance $10^{-4}$. Derivation/rounding of unlisted numbers is prohibited. Violation: `UNSUPPORTED_NUMERIC_CLAIM`.
5. **Gate 5: `UNRESOLVED_TARGET_BECAME_RESOLVED` (Patched)**  
   When all coaching events have `UNRESOLVED_TARGET`, evaluates target claims with negation awareness. Distinguishes safe negative limitations (*"was not attributed to a specific player"*) from contradictory affirmative resolutions (*"was attributed to Player 1"*). Violation: `CONTRADICTS_INPUT`.
6. **Gate 6: `MISSING_SPEED_INFERRED`**  
   If evidence limitations declare metric speed unavailable, rejects generated text claiming quantitative speed or velocity values. Violation: `MISSING_SPEED_INFERRED`.
7. **Gate 7: `UNSUPPORTED_EVENT_CATEGORY`**  
   Rejects tactical category terms present in text that do not exist in the evidence coaching events. Violation: `UNSUPPORTED_EVENT_CATEGORY`.
8. **Gate 8: `UNSUPPORTED_EVENT_ACTION`**  
   Rejects tactical action verbs not grounded in the source coaching transcript or evidence observations. Violation: `UNSUPPORTED_EVENT_ACTION`.

### 10.3 Safe Fallback Execution
On validation failure or Ollama timeout ($> 45\text{s}$), the pipeline automatically engages `ReportStatus.DETERMINISTIC_FALLBACK`, compiling a deterministic report directly from `StructuredEvidence`.

---

## 11. Final Analysis Result Contract (Objective 11)

### 11.1 Product `AnalysisResult` Mapping
The final analysis result matches `backend/app/schemas/result.py`:

```python
class AnalysisResult(BaseModel):
    id: str
    session_id: str
    job_id: str
    methodology_id: MethodologyId
    application_mode: ApplicationMode
    calibration_mode: CalibrationMode
    job_status: JobStatus  # COMPLETED | COMPLETED_WITH_LIMITATIONS | FAILED
    identity_evaluation: IdentityEvaluation
    evaluation_metrics: Optional[EvaluationMetrics] = None
    metrics: Dict[str, MovementMetric] = Field(default_factory=dict)
    instruction_events: List[InstructionEvent] = Field(default_factory=list)
    limitations: List[AnalysisLimitation] = Field(default_factory=list)
    artifact_references: List[ArtifactReference] = Field(default_factory=list)
    report_markdown: Optional[str] = None
    report_status: ReportStatus
    created_at: datetime
```

### 11.2 Frontend Transparent Rendering (`analysis.$jobId.results.tsx`)
- Status Badge: `COMPLETED_WITH_LIMITATIONS` rendered with amber styling.
- Persistent Limitation Banner:
  *"Scientific Limitation: Persistent player tracking failed the identity safety gate (FAIL_UNSAFE_MERGE). Accumulated player-level analytics are withheld. Team-level spatial metrics and uncalibrated tracklet dynamics remain available."*
- Player metric cards display `"— (Withheld)"` with informative tooltip.

---

## 12. Orchestration State Machine (Objective 12)

The execution sequence strictly executes 16 stages:
`UPLOADED` $\rightarrow$ `VALIDATING` $\rightarrow$ `PREPROCESSING` $\rightarrow$ `DETECTING` $\rightarrow$ `TRACKING` $\rightarrow$ `IDENTITY_EVALUATION` $\rightarrow$ `CALIBRATING` $\rightarrow$ `KINEMATICS` $\rightarrow$ `AUDIO_EXTRACTION` $\rightarrow$ `TRANSCRIBING` $\rightarrow$ `INSTRUCTION_PARSING` $\rightarrow$ `FUSION` $\rightarrow$ `GENERATING_EVIDENCE` $\rightarrow$ `GENERATING_REPORT` $\rightarrow$ `RENDERING` $\rightarrow$ `UPLOADING_RESULTS`.

- **Fatal Stages**: `VALIDATING`, `DETECTING`, `TRACKING`, `UPLOADING_RESULTS`.
- **Degradable Non-Fatal Stages**: `IDENTITY_EVALUATION`, `CALIBRATING`, `AUDIO_EXTRACTION`, `TRANSCRIBING`, `GENERATING_REPORT`.

---

## 13. Media Duration Policy (Objective 13 & Correction 11)

### 13.1 Proposed Bounded Product Policy: 360.0 Seconds
- **Current Product Limit**: $300.0 \text{ s}$.
- **Main Research Session Duration**: $339.99 \text{ s}$ ($20,391$ frames at $59.972$ FPS).
- **Proposed Ceiling**: **$360.0 \text{ seconds}$** ($6$ minutes).

### 13.2 Asynchronous Worker & Timeout Semantics (Correction 11)
- Speculative claims regarding GPU runtime (e.g. "~550s on T4/A10G") are **removed**.
- Worker timeout is classified as:
  $$\text{Worker Timeout} = \text{CONFIGURABLE / PROVISIONAL\_PENDING\_REAL\_E2E\_BENCHMARK}$$
- The execution architecture is strictly asynchronous: worker updates progress percentage ($0.0 \dots 100.0$) and emits stage heartbeats to Supabase, eliminating reliance on speculative completion timeouts.

---

## 14. Dependency Isolation & Packaging (Objective 14 & Correction 12)

### 14.1 Dependency Isolation Requirement (Correction 12)
Methodologies M1, M2, and M3 must remain strictly dependency-isolated and reproducible:
- Separate sub-packages: `backend/app/methodologies/m1/`, `.../m2/`, `.../m3/`.
- Lazy importing of methodology-specific weights and modules.

### 14.2 Packaging Strategy Status
- The proposal for a single unified Modal GPU image is labeled:
  $$\text{Packaging Strategy} = \text{PROVISIONAL\_PENDING\_DEPENDENCY\_SMOKE}$$
- A bounded dependency smoke test will verify library compatibility across PyTorch 2.4, Torchvision, Ultralytics, and CTranslate2 before the packaging design is finalized.
- Speculative VRAM numbers without measured execution evidence are removed.

---

## 15. Artifact & Provenance Contract (Objective 15)

Every job persists `analysis-artifacts/{job_id}/manifest.json` recording:
- `job_id`, `session_id`, `requested_methodology`, `resolved_methodology`
- `source_media`: filename, SHA-256, duration ($339.99\text{s}$), fps ($59.972$), resolution ($3840 \times 2160$)
- `models`: detector checkpoint SHA-256, tracker config SHA-256, ReID SHA-256, ASR model, LLM digest (`46e0c10c...`), prompt SHA-256 (`ab95a835...`), validator version (`LLM_GROUNDING_VALIDATOR_PATCH_001`)
- `identity_assurance`: `identity_status = FAIL_UNSAFE_MERGE`, `identity_evidence_basis = RUNTIME_HEURISTIC_ONLY`, `player_level_analysis_allowed = false`
- `calibration`: `mode`, `evidence_basis`, `homography_sha256` (`d0e9680f...`), `rmse_m` ($0.651\text{m}$)
- `artifacts_produced`: list of stored artifacts with storage paths and SHA-256 checksums.

---

## 16. Architecture & Contract Freeze Sign-Off

This document constitutes Revision 1 of the frozen specification for CM3070 application integration. All subsequent implementation must adhere to these contracts.

**Freeze Status**: `P0_CONTRACT_FREEZE_REV1_READY_FOR_REVIEW`
