# P0 REV2A — Final Vision Provenance Correction

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: P0 — Architecture & Contract Freeze (Revision 2A Final Vision Provenance Correction)  
**Date**: 2026-09-26  
**Status**: `P0_REV2A_VISION_PROVENANCE_VERIFIED`  
**Authoritative Baselines Read Back**:
- M1: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_1\M1_FINAL_EVALUATION_BASELINE\M1_FINAL_EVALUATION_BASELINE.json`
- M2: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_2\M2_FINAL_EVALUATION_BASELINE\M2_FINAL_EVALUATION_BASELINE.json`
- M3: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_3\M3_P5A_score_compatibility_amendment.json`

---

## 1. Provenance Reconciliation Table

| Method | Component | Previous REV2A Value | Verified Final Value | Authoritative Baseline Artifact | Physical File Verification | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M1** | Detector Checkpoint Path | `weights/best.pt` | `runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt` | `M1_FINAL_EVALUATION_BASELINE.json` (`detector.checkpoint_relative_to_methodology_comparison`) | Path verified on disk. Size: `104,950,959` bytes. SHA-256: `ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b`. | Replaces mixed Stage 4B pilot record (`best.pt`, 40.5MB, SHA `f6b3fe...`) with actual frozen M1 baseline artifact. |
| **M1** | Detector Filename | `best.pt` | `epoch28.pt` | `M1_FINAL_EVALUATION_BASELINE.json` | Filename confirmed on disk. | `epoch28.pt` is the exact trained weight file selected for formal M1 evaluation. |
| **M1** | Detector Size | `40,539,756 bytes` | `104,950,959 bytes` | `M1_FINAL_EVALUATION_BASELINE.json` (`detector.checkpoint_bytes`) | Size verified via `os.path.getsize` / `Get-Item`. | 40.5MB was the historical Stage 4B pilot weight size, not the fine-tuned domain-adapted M1 baseline. |
| **M1** | ReID Model | None / unspecified | `official Ultralytics yolo26n-reid.onnx` (`checkpoints/yolo26n-reid.onnx`) | `M1_FINAL_EVALUATION_BASELINE.json` (`reid.model`) | File verified on disk. Size: `9,873,245` bytes. SHA-256: `8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb`. | Documents exact row-aligned ReID feature bridge used by BoT-SORT in M1 evaluation. |
| **M2** | RF-DETR Checkpoint Path | `checkpoint_best_regular.pth` | `runs/method_2/M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth` | `M2_FINAL_EVALUATION_BASELINE.json` (`detector.checkpoint_project_relative`) | Path verified on disk. Size: `134,747,227` bytes. SHA-256: `7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85`. | Resolves checkpoint name ambiguity: `checkpoint_best_total.pth` was the actual checkpoint evaluated in the formal 12-run challenge. |
| **M2** | ReID Checkpoint Path | `osnet_x1_0_msmt17.pt` | `runs/method_2/M2_P0_preflight/checkpoints/sports_model.pth.tar-60` | `M2_FINAL_EVALUATION_BASELINE.json` (`local_reid.checkpoint_project_relative`) | Path verified on disk. Size: `30,393,613` bytes. SHA-256: `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd`. | `sports_model.pth.tar-60` is the actual sports-adapted OSNet-x1.0 model used for Deep-EIoU and GTA; `osnet_x1_0_msmt17.pt` was an unadapted general ReID candidate. |
| **M2** | ReID SHA-256 | `a937a0c8411d3d0f0c058c672be3f5ea0d995ffcaea146ad205d9e5beeed3058` | `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd` | `M2_FINAL_EVALUATION_BASELINE.json` (`local_reid.checkpoint_sha256`) | SHA-256 verified on physical file via `hashlib.sha256`. | Matches authoritative baseline and physical checkpoint on disk. |
| **M3** | Birth Gate Provenance Wording | `"replaces default 0.60"` | `"amended from source-default 0.70 to 0.30"` | `M3_P5A_score_compatibility_amendment.json` | Amendment record verified: `original_birth_gate.value = 0.70`, `amended_birth_gate.value = 0.30`. | Source SRI-Track `Kfree_tracker_main.py` default birth gate was 0.70 (`track_new_th`). `track_high_th` remained unchanged at 0.60. |

---

## 2. Verified Physical Checkpoint Readbacks

### Method 1 (M1) — Fine-Tuned YOLO11m
- **Detector File**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_1\M1_FORMAL_003_DOMAIN_ADAPTED\training\yolo11m_domain_adapted\weights\epoch28.pt`
- **Filename**: `epoch28.pt`
- **Architecture**: `YOLO11m custom-domain-adapted`
- **Byte Size**: `104,950,959 bytes`
- **SHA-256**: `ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b`
- **ReID File**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_1\M1_FINAL_EVALUATION_BASELINE\checkpoints\yolo26n-reid.onnx`
- **ReID SHA-256**: `8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb`
- **ReID Size**: `9,873,245 bytes`

### Method 2 (M2) — RF-DETR-L + Deep-EIoU + GTA-Track
- **Detector File**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_2\M2_FORMAL_001_DOMAIN_ADAPTED\checkpoint_best_total.pth`
- **Filename**: `checkpoint_best_total.pth`
- **Architecture**: `RF-DETR-L`
- **Byte Size**: `134,747,227 bytes`
- **SHA-256**: `7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85`
- **ReID File**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_2\M2_P0_preflight\checkpoints\sports_model.pth.tar-60`
- **Filename**: `sports_model.pth.tar-60`
- **Architecture**: `OSNet-x1.0` (sports_model)
- **Byte Size**: `30,393,613 bytes`
- **SHA-256**: `8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd`

### Method 3 (M3) — Domain-Adapted YOLO26m + SRITrack-v1
- **Detector File**: `G:\My Drive\Football_Training_Assistant_MVP\methodology_comparison\runs\method_3\M3_FORMAL_001_DOMAIN_ADAPTED\checkpoints\M3_ADAPTED_YOLO26M.pt`
- **Filename**: `M3_ADAPTED_YOLO26M.pt`
- **Byte Size**: `44,081,689 bytes`
- **SHA-256**: `ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf`
- **SRITrack Parameters**:
  - `track_high_th = 0.60` (unchanged high-stage gate)
  - `track_low_th = 0.10`
  - `track_new_th = 0.30` (amended from source-default `0.70` via P5A score compatibility amendment)
  - `track_buffer = 1000`
