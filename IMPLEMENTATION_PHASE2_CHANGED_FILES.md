# IMPLEMENTATION_PHASE2_CHANGED_FILES.md
# Implementation Phase 2 Changed Files Manifest

**Project**: AI-Driven Football Tactical Analysis and Training Evaluation System  
**Phase**: Implementation Phase 2 — Real Vision Execution Layer  
**Date**: 2026-09-26  

---

## 1. Created Files

| File Path | Purpose / Description |
| :--- | :--- |
| `IMPLEMENTATION_PHASE2_SOURCE_READBACK.md` | Source readback and line-by-line lineage audit of frozen runner scripts (`frozen_m1_clip_runner.py`, `frozen_m2_clip_runner.py`, `frozen_m3_clip_runner.py`). |
| `IMPLEMENTATION_PHASE2_DEPENDENCY_PREFLIGHT.md` | Matrix of installed package versions, hardware runtime detection, checkpoint verification hashes, and execution readiness classifications. |
| `backend/app/runners/__init__.py` | Package initialization exporting `BaseVisionRunner`, `verify_checkpoint_file`, `M1VisionRunner`, `M2VisionRunner`, and `M3VisionRunner`. |
| `backend/app/runners/base.py` | Abstract base class `BaseVisionRunner(MethodologyExecutor)` providing cryptographic checkpoint verification, hardware device resolution, dynamic container probing, and adapter pipeline integration. |
| `backend/app/runners/m1_runner.py` | Production execution runner for Method 1: 3-tile slicing (`(0, 712)`, `(605, 1317)`, `(1208, 1920)`), YOLO11m detector (`epoch28.pt`), global NMS (0.50), and fresh BoT-SORT instance with `yolo26n-reid.onnx`. |
| `backend/app/runners/m2_runner.py` | Production execution runner for Method 2: RF-DETR Large detector (`checkpoint_best_total.pth`, operating point $\ge 0.50$, no external NMS), OSNet x1_0 ReID (`sports_model.pth.tar-60`), fresh Deep-EIoU tracker, and in-memory Global Tracklet Association (GTA). |
| `backend/app/runners/m3_runner.py` | Production execution runner for Method 3: full-frame adapted YOLO26m (`M3_ADAPTED_YOLO26M.pt`, operating point $\ge 0.30$), DINOv3 feature extractor (`model.pth.tar-60`), and fresh SRITrack-v1 tracker with P5A score amendment (`track_new_th = 0.30`). |
| `backend/app/runners/shims/cython_bbox.py` | Exact pure-Python/NumPy drop-in replacement shim for cython_bbox v0.1.5 (`bbox_overlaps`), providing proven float64 numerical equivalence against Sergey Karayev Fast R-CNN reference C code. |
| `backend/tests/test_cython_bbox_equivalence.py` | Deterministic verification test suite proving float64 numerical equivalence between reference cython_bbox and production shim across 8,000 randomized boxes, identical boxes, edge-touching boxes, non-overlapping boxes, nested boxes, and 1-pixel boxes (`M2_CYTHON_BBOX_SHIM_EQUIVALENCE_VERIFIED`). |
| `IMPLEMENTATION_PHASE2_FINAL_VERIFICATION.md` | Final scientific execution verification report addressing all 5 bounded verification objectives. |
| `IMPLEMENTATION_PHASE2_REPORT.md` | Comprehensive report documenting the execution layer, verification outcomes, and scientific boundaries. |
| `IMPLEMENTATION_PHASE2_TEST_RESULTS.json` | JSON test execution records and checkpoint verification results. |
| `IMPLEMENTATION_PHASE2_CHANGED_FILES.md` | This manifest file. |

---

## 2. Modified Files

| File Path | Modification Summary |
| :--- | :--- |
| `backend/app/pipeline/registry.py` | Added `create_production_registry()` factory function with lazy imports to register `M1VisionRunner`, `M2VisionRunner`, and `M3VisionRunner` in `MethodologyExecutorRegistry` while keeping module imports decoupled. |

---

## 3. Files Left Strictly Read-Only & Untouched
- All original research notebooks (`01_vision_pipeline.ipynb`, `02_audio_pipeline.ipynb`, etc.)
- All research baseline and experiment checkpoints
- All ground truth annotations and evaluation results
- C03, C04, and C06 golden showcase evidence
