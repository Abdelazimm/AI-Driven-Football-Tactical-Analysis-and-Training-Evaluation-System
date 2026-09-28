# Phase 2 Source-First Execution Audit

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Document**: `IMPLEMENTATION_PHASE2_SOURCE_READBACK.md`  
**Purpose**: Comprehensive audit and classification of the exact frozen research execution implementations used in the formal Vision evaluation before implementation of production runners.

---

## 1. Methodology 1 (M1): YOLO11m + BoT-SORT + ONNX ReID

### 1.1 Lineage & Source Provenance
- **Primary Source Runner**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\final_vision_evaluation\formal_fresh_state_per_clip\frozen_m1_clip_runner.py`
- **Baseline Configuration**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_1\M1_FINAL_EVALUATION_BASELINE\M1_FINAL_EVALUATION_BASELINE.json`
- **Detector Checkpoint**: `runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt` (SHA: `ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b`, Size: `104,950,959` bytes)
- **ReID Checkpoint**: `runs/method_1/M1_FINAL_EVALUATION_BASELINE/checkpoints/yolo26n-reid.onnx` (SHA: `8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb`, Size: `9,873,245` bytes)

### 1.2 Execution Mechanics
- **Video Input & Resolution**: Input source video (3840x2160) is resized to working resolution (1920x1080) using `cv2.resize(image, (1920, 1080), interpolation=cv2.INTER_AREA)`.
- **Tiling**: 3 horizontal tiles:
  - Tile 1: `(0, 712)`
  - Tile 2: `(605, 1317)`
  - Tile 3: `(1208, 1920)`
  - Overlap: 15% (107 px between tiles 1 & 2; 109 px between tiles 2 & 3).
- **Inference**: `model.predict([frame[:, a:b] for a, b in tiles], imgsz=1280, conf=0.05, iou=0.70, classes=[0], max_det=300, device=..., half=..., verbose=False)`.
- **Tile Remap & Normalization**: Detections remapped by `xy[:, (0, 2)] += float(a)` and clamped to `[0, 1920] x [0, 1080]`. Degenerate boxes removed (`x2 > x1`, `y2 > y1`, `conf >= 0.05`).
- **Global NMS**: Global `nms(xy, conf, 0.50)` applied across remapped tiled detections. Deterministic tie-breaking via `np.lexsort((xy[:, 3], xy[:, 2], xy[:, 1], xy[:, 0], -sc))`.
- **ReID Embedding Extraction**: Crops passed to `ultralytics.trackers.utils.reid.ReID(checkpoint_path, imgsz=448, device=...)`. Feature shape: `(N, 512)`.
- **Tracking Algorithm**: `ultralytics.trackers.bot_sort.BOTSORT(SimpleNamespace(**tracker_cfg))`.
  - Parameters: `track_high_thresh=0.35`, `track_low_thresh=0.05`, `new_track_thresh=0.25`, `track_buffer=60`, `match_thresh=0.70`, `fuse_score=True`, `gmc_method="sparseOptFlow"`, `proximity_thresh=0.50`, `appearance_thresh=0.25`, `with_reid=True`.
- **Reset Policy**: Strict instantiation of a new `BOTSORT` instance per job/session (`tracker_state: FRESH_AT_FIRST_FRAME`).
- **Adapter Integration**: Emits track tuples `(x1, y1, x2, y2, track_id, conf)` in 1920x1080 working space, which feed directly into `M1Adapter.adapt_framewise_tracks(...)`.

### 1.3 Component Reusability Classification
| Source Component | Action | Classification | Notes |
|---|---|---|---|
| Tile Slicing & Remapping | Extract clean helper | **`COPY_ADAPT`** | Preserves exact tile ranges `(0, 712)`, `(605, 1317)`, `(1208, 1920)`. |
| Global NMS (0.50) & Lexsort | Extract clean helper | **`COPY_ADAPT`** | Deterministic coordinate ordering and IoU 0.50 threshold. |
| YOLO11m Detector | Ultralytics invocation | **`WRAP`** | Wrapped in lazy executor loading. |
| ONNX ReID Bridge | Ultralytics ReID loader | **`WRAP`** | Wrapped with ONNX Runtime session. |
| BoT-SORT Tracker | Ultralytics BOTSORT class | **`WRAP`** | Strict fresh instance per execution job. |
| CSV/Partial File Writer | Remove filesystem dependency | **`REDESIGN_INTERFACE_ONLY`** | Adapts memory track observations directly to `SessionVisionResult`. |
| TrackEval / GT Comparison | Scientific benchmarking | **`DO_NOT_USE`** | Production runtime does not score against GT. |

---

## 2. Methodology 2 (M2): RF-DETR-L + Deep-EIoU + OSNet + GTA

### 2.1 Lineage & Source Provenance
- **Primary Source Runner**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\final_vision_evaluation\formal_fresh_state_per_clip\frozen_m2_clip_runner.py`
- **Baseline Configuration**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_2\M2_FINAL_EVALUATION_BASELINE\M2_FINAL_EVALUATION_BASELINE.json`
- **Detector Checkpoint**: `runs/method_2/M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth` (SHA: `7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85`, Size: `134,747,227` bytes)
- **ReID Checkpoint**: `runs/method_2/M2_P0_preflight/checkpoints/sports_model.pth.tar-60` (SHA: `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd`, Size: `30,393,613` bytes)
- **Tracker Source**: `runs/method_2/M2_P4_detector_to_deepeiou_contract/source/GTATrack-STC2025/Deep-EIoU/Deep-EIoU/tracker/Deep_EIoU.py`
- **GTA Source**: `runs/method_2/M2_FINAL_EVALUATION_BASELINE/source_snapshots/gta-link-lf/refine_tracklets.py`

### 2.2 Execution Mechanics
- **Video Input & Resolution**: Input source video (3840x2160) resized to working resolution (1920x1080) using `cv2.resize(image, (1920, 1080), interpolation=cv2.INTER_AREA)`.
- **Detector**: `rfdetr.RFDETRLarge.from_checkpoint(...)`. Resolution 704x704 square resize, 300 queries, 1 class (`person`).
- **Postprocessing & Confidence Filtering**: Detections filtered at `(classes == 0) & (scores >= 0.50)`. **NO external NMS** applied per contract REV2A.
- **Local ReID Model**: OSNet x1_0 architecture (`num_classes=616`) loaded from state dict `sports_model.pth.tar-60`. Crops transformed with `Resize((256, 128))` and ImageNet normalization. 512-dim feature embeddings extracted in batches of 32.
- **Local Online Tracker**: `Deep_EIoU` instance initialized with `new_track_thresh=0.7`, `track_high_thresh=0.7`. Emits local tracklets.
- **Offline Global Association (GTA)**:
  - Local tracklets partitioned and features organized into `Tracklet` objects.
  - Tracklet splitting: `gta.split_tracklets(tracklets, eps=0.65, max_k=2, min_samples=15, len_thres=50)`.
  - Spatial constraints and distance matrix: `gta.get_spatial_constraints(...)` with `spatial_factor=1.5`.
  - Global graph merge: `gta.merge_tracklets(..., merge_dist_thres=0.35)`.
  - Remapping: Generates global merged track IDs while preserving original local track scores.
- **Reset Policy**: Fresh `Deep_EIoU` and fresh GTA graph instance per execution job (`tracker_state: FRESH_AT_FIRST_FRAME`).
- **Adapter Integration**: Global tracks feed into `M2Adapter.adapt_framewise_tracks(...)`.

### 2.3 Component Reusability Classification
| Source Component | Action | Classification | Notes |
|---|---|---|---|
| RF-DETR Model Loader | `RFDETRLarge.from_checkpoint` | **`WRAP`** | Loads native checkpoint and returns raw 1920x1080 detections. |
| OSNet x1_0 ReID Model | Dynamic module load | **`WRAP`** | Clean wrapper loading `sports_model.pth.tar-60`. |
| Deep-EIoU Online Tracker | Pure tracking loop | **`COPY_ADAPT`** | Wrapped with pure Python IoU shim (`cython_bbox`). |
| GTA Offline Association | Whole-job association | **`WRAP`** | Wrapped as stage 2 of M2 execution. |
| MOT file intermediate generation | Streamlined memory tracklets | **`REDESIGN_INTERFACE_ONLY`** | Replaced file writes with in-memory tracklet generation where appropriate. |
| TrackEval scoring | Scientific benchmark | **`DO_NOT_USE`** | Production runtime does not score against GT. |

---

## 3. Methodology 3 (M3): YOLO26m + SRITrack-v1 + DINOv3

### 3.1 Lineage & Source Provenance
- **Primary Source Runner**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\final_vision_evaluation\formal_fresh_state_per_clip\frozen_m3_clip_runner.py`
- **Baseline Configuration**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_3\M3_P5_identity_calibration\M3_selected_identity_configuration.json`
- **Detector Checkpoint**: `methodology_comparison/runs/method_3/M3_FORMAL_001_DOMAIN_ADAPTED/checkpoints/M3_ADAPTED_YOLO26M.pt` (SHA: `ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf`, Size: `44,081,689` bytes)
- **ReID Checkpoint**: `methodology_comparison/checkpoints/method_3/model.pth.tar-60` (SHA: `5f4f1fa2226680c26458872f6241b9a5355d6e29a405fda1acdbcb11874b32f8`, Size: `1,104,745,338` bytes)
- **ReID Source Bundle**: `runs/method_3/M3_P4_detection_reid_cache/source_bundle`
- **Tracker Source**: `runs/method_3/M3_P5_identity_calibration/source_pinned`

### 3.2 Execution Mechanics
- **Video Input & Resolution**: Input source video (3840x2160) resized to working resolution (1920x1080) using `cv2.resize(image, (1920, 1080), interpolation=cv2.INTER_AREA)`.
- **Detector**: `ultralytics.YOLO(str(DET), task='detect')`. Full 1920x1080 image inference:
  `model.predict(source=frame, conf=0.30, iou=0.7, max_det=300, classes=[0], imgsz=1280, device=..., agnostic_nms=False, augment=False, verbose=False)`.
- **Feature Extractor**: `FeatureExtractor(logger, model_name='dinov3_vit_b_16', weight_path=..., device=...)`.
  - Backbone: `vit_base_patch16_dinov3.lvd1689m` initialized with weights from `model.pth.tar-60`.
  - Crops transformed and fed in batches of 16 to extract 512-dim embeddings.
- **Tracker**: `Tracker(SimpleNamespace(**params), (1080, 1920), frame_rate=fps)` from `sri_track.Kfree_tracker_main`.
  - P5A Amended Parameters: `track_high_th=0.6`, `track_low_th=0.1`, `track_new_th=0.3` (amended from 0.7), `track_buffer=1000`, `track_match_th=0.8`, `track_p_th=0.5`, `track_vc_th=0.5`, `track_vf_th=0.25`, `track_b_th=0.7`, `with_reid=True`, `EIoU=True`, `vp_dga=True`, `ris=True`, `det_min_area=10`.
- **Filtering**: Tracks with bounding box area `<= 10 px` rejected (`det_min_area`).
- **Reset Policy**: Fresh `Tracker` instance per execution job (`tracker_state: FRESH_AT_FIRST_FRAME`).
- **Adapter Integration**: Tracklet observations feed into `M3Adapter.adapt_framewise_tracks(...)`.

### 3.3 Component Reusability Classification
| Source Component | Action | Classification | Notes |
|---|---|---|---|
| Adapted YOLO26m Inference | Ultralytics invocation | **`WRAP`** | Native inference at `imgsz=1280, conf=0.30, iou=0.70`. |
| DINOv3 FeatureExtractor | ReID extraction module | **`WRAP`** | Wrapped with local model path resolution. |
| SRITrack Tracker | Pure tracking engine | **`WRAP`** | Pinned implementation with P5A amendment parameters. |
| CSV export & logging | In-memory tracklet mapping | **`REDESIGN_INTERFACE_ONLY`** | Maps tracker outputs directly to `SessionVisionResult`. |
| M3-R2 / Post-tuning | Disqualified variant | **`DO_NOT_USE`** | Strictly excluded per frozen contract. |
