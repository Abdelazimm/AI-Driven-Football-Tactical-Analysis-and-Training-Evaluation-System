"""
Method 2 (M2) Production Vision Execution Runner: RF-DETR-L + Deep-EIoU + OSNet + GTA.
Executes real frozen M2 model inference on input video frames and transforms observations
through M2VisionAdapter into canonical SessionVisionResult.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 2.3)
M2_FINAL_EVALUATION_BASELINE.json
frozen_m2_clip_runner.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# NumPy 2.x compatibility shim for Deep-EIoU tracker
if not hasattr(np, "float"):
    np.float = np.float64

from backend.app.adapters.m2_adapter import (
    M2Adapter,
    M2_DEEPEIOU_CONFIG,
    M2_DETECTOR_PROVENANCE,
    M2_GTA_CONFIG,
    M2_OPERATING_POINT,
    M2_REID_PROVENANCE,
)
from backend.app.runners.base import (
    BaseVisionRunner,
    resolve_candidate_path,
    verify_checkpoint_file,
)
from backend.app.schemas.methodology import MethodologyId


class M2VisionRunner(BaseVisionRunner):
    """
    Real execution runner for Method 2:
    - Full-frame 1920x1080 -> RF-DETR-L (checkpoint_best_total.pth)
    - 704x704 resize, 300 queries, class person (0), operating point >= 0.50
    - NO external NMS
    - OSNet x1_0 ReID feature extraction (sports_model.pth.tar-60)
    - Fresh Deep-EIoU online tracker instance per execution job
    - Global Tracklet Association (GTA) offline merge across sequence
    """

    def __init__(
        self,
        detector_path: Optional[Path] = None,
        reid_path: Optional[Path] = None,
        device: Optional[str] = None,
    ):
        super().__init__(device=device)
        self._detector_path_override = detector_path
        self._reid_path_override = reid_path
        self._detector = None
        self._reid_net = None
        self._verified_detector_path = None
        self._verified_reid_path = None
        self.last_gta_stats: Optional[Dict[str, Any]] = None

    @property
    def methodology_id(self) -> MethodologyId:
        return MethodologyId.METHOD_2_RFDETR_GTATRACK

    def get_adapter(self) -> M2Adapter:
        return M2Adapter()

    def _resolve_checkpoints(self) -> Tuple[Path, Path]:
        """Resolve and cryptographically verify M2 detector and ReID checkpoints."""
        if self._verified_detector_path is None:
            if self._detector_path_override:
                self._verified_detector_path = verify_checkpoint_file(
                    self._detector_path_override,
                    expected_sha256=M2_DETECTOR_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M2_DETECTOR_PROVENANCE.checkpoint_size_bytes,
                    component_name="M2 Detector (checkpoint_best_total.pth)",
                )
            else:
                model_root = Path(os.getenv("M2_MODEL_ROOT", "models/m2"))
                candidates = [
                    Path(p) for p in [
                        os.getenv("M2_DETECTOR_PATH", ""),
                        str(model_root / "checkpoint_best_total.pth"),
                    ] if p and str(p).strip() not in ("", ".")
                ]
                self._verified_detector_path = resolve_candidate_path(
                    candidates,
                    expected_sha256=M2_DETECTOR_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M2_DETECTOR_PROVENANCE.checkpoint_size_bytes,
                    component_name="M2 Detector (checkpoint_best_total.pth)",
                )

        if self._verified_reid_path is None:
            if self._reid_path_override:
                self._verified_reid_path = verify_checkpoint_file(
                    self._reid_path_override,
                    expected_sha256=M2_REID_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M2_REID_PROVENANCE.checkpoint_size_bytes,
                    component_name="M2 ReID (sports_model.pth.tar-60)",
                )
            else:
                model_root = Path(os.getenv("M2_MODEL_ROOT", "models/m2"))
                candidates = [
                    Path(p) for p in [
                        os.getenv("M2_REID_PATH", ""),
                        str(model_root / "sports_model.pth.tar-60"),
                    ] if p and str(p).strip() not in ("", ".")
                ]
                self._verified_reid_path = resolve_candidate_path(
                    candidates,
                    expected_sha256=M2_REID_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M2_REID_PROVENANCE.checkpoint_size_bytes,
                    component_name="M2 ReID (sports_model.pth.tar-60)",
                )

        return self._verified_detector_path, self._verified_reid_path

    def _setup_m2_imports(self) -> Tuple[Any, Any, Any, Any]:
        """Import frozen Deep-EIoU, OSNet, and GTA modules lazily."""
        vendored = Path(__file__).resolve().parent / "vendor" / "m2"
        deep_source = vendored / "deep_eiou"
        osnet_source = deep_source / "reid/torchreid/models/osnet.py"
        gta_source = vendored / "gta"
        for required in (deep_source / "tracker/Deep_EIoU.py", osnet_source, gta_source / "refine_tracklets.py"):
            if not required.is_file():
                raise FileNotFoundError(f"M2_PACKAGED_SOURCE_MISSING: {required}")

        # Frozen tracker source expects cython_bbox as a top-level module.
        # Install the already verified numerical shim without changing its semantics.
        from backend.app.runners.shims import cython_bbox as bbox_shim
        sys.modules["cython_bbox"] = bbox_shim

        if str(deep_source) not in sys.path:
            sys.path.insert(0, str(deep_source))
        if str(deep_source / "reid") not in sys.path:
            sys.path.insert(0, str(deep_source / "reid"))
        if str(gta_source) not in sys.path:
            sys.path.insert(0, str(gta_source))

        from tracker.Deep_EIoU import Deep_EIoU
        from Tracklet import Tracklet
        import refine_tracklets as gta

        # Load OSNet factory module dynamically
        spec = importlib.util.spec_from_file_location("m2_frozen_osnet", str(osnet_source))
        osnet_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(osnet_mod)

        return Deep_EIoU, Tracklet, gta, osnet_mod

    def _get_models(self):
        """Lazy load RF-DETR detector and OSNet ReID model."""
        import torch
        from rfdetr import RFDETRLarge
        from torchvision import transforms as T

        det_path, reid_path = self._resolve_checkpoints()
        Deep_EIoU, Tracklet, gta, osnet_mod = self._setup_m2_imports()

        if self._detector is None:
            self._detector = RFDETRLarge.from_checkpoint(str(det_path))

        if self._reid_net is None:
            state = torch.load(reid_path, map_location="cpu", weights_only=False)["state_dict"]
            net = osnet_mod.osnet_x1_0(num_classes=616, pretrained=False)
            net.load_state_dict(state, strict=True)
            net.eval().to(self.device)
            self._reid_net = net

        transform = T.Compose([
            T.ToPILImage(),
            T.Resize((256, 128)),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        return self._detector, self._reid_net, transform, Deep_EIoU, Tracklet, gta

    def _extract_osnet_features(
        self,
        net,
        transform,
        bgr_frame: np.ndarray,
        boxes: np.ndarray,
    ) -> np.ndarray:
        """Extract 512-dim OSNet embeddings for bounding box crops in batches of 32."""
        import torch

        tensors = []
        for x1, y1, x2, y2 in boxes:
            a, b = max(0, int(x1)), max(0, int(y1))
            c, d = min(1920, int(x2)), min(1080, int(y2))
            if c <= a or d <= b:
                tensors.append(transform(np.zeros((128, 64, 3), dtype=np.uint8)))
            else:
                tensors.append(transform(bgr_frame[b:d, a:c].copy()))

        if not tensors:
            return np.empty((0, 512), dtype=np.float32)

        blocks = []
        with torch.inference_mode():
            for off in range(0, len(tensors), 32):
                batch = torch.stack(tensors[off : off + 32]).to(self.device)
                feat = net(batch).detach().cpu().numpy().astype(np.float32)
                blocks.append(feat)

        all_feats = np.concatenate(blocks, axis=0)
        return all_feats

    def run_inference_and_tracking(
        self,
        video_path: Path,
        start_frame: int = 0,
        max_frames: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int, float, int]:
        """
        Execute real M2 inference with RF-DETR-L, Deep-EIoU online tracker,
        and offline GTA global tracklet association.
        """
        import cv2
        from PIL import Image

        detector, reid_net, transform, Deep_EIoU, Tracklet, gta = self._get_models()

        # Instantiate fresh Deep-EIoU tracker per run
        tracker_params = {
            "with_reid": True,
            "new_track_thresh": M2_DEEPEIOU_CONFIG["new_track_thresh"],
            "track_high_thresh": M2_DEEPEIOU_CONFIG["track_high_thresh"],
            "track_low_thresh": M2_DEEPEIOU_CONFIG["track_low_thresh"],
            "track_buffer": M2_DEEPEIOU_CONFIG["track_buffer"],
            "match_thresh": M2_DEEPEIOU_CONFIG["match_thresh"],
            "proximity_thresh": M2_DEEPEIOU_CONFIG["proximity_thresh"],
            "appearance_thresh": M2_DEEPEIOU_CONFIG["appearance_thresh"],
            "min_box_area": M2_DEEPEIOU_CONFIG["min_box_area"],
            "occ_iou_thresh": M2_DEEPEIOU_CONFIG["occ_iou_thresh"],
            "occ_sim_thresh": M2_DEEPEIOU_CONFIG["occ_sim_thresh"],
            "occ_buffer_frames": M2_DEEPEIOU_CONFIG["occ_buffer_frames"],
        }
        tracker = Deep_EIoU(SimpleNamespace(**tracker_params), frame_rate=30)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"CANNOT_OPEN_VIDEO: Failed to open '{video_path}'")

        try:
            source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            source_fps = float(cap.get(cv2.CAP_PROP_FPS))
            total_container_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if start_frame > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            end_frame = (
                start_frame + max_frames - 1
                if max_frames is not None
                else total_container_frames - 1
            )
            end_frame = min(end_frame, total_container_frames - 1)

            # Stage 1: Online local detection and tracking
            local_tracklets: Dict[int, Any] = {}
            frame_records: Dict[int, List[Dict[str, Any]]] = {}

            for current_frame_idx in range(start_frame, end_frame + 1):
                ok, image = cap.read()
                if not ok or image is None:
                    break

                # Resize to VISION_WORKING_SPACE (1920x1080)
                frame_1080p = cv2.resize(
                    image, (1920, 1080), interpolation=cv2.INTER_AREA
                )
                pil_image = Image.fromarray(cv2.cvtColor(frame_1080p, cv2.COLOR_BGR2RGB))

                # RF-DETR inference on full 1920x1080 canvas
                prediction = detector.predict(pil_image, threshold=0.0)
                boxes = np.asarray(prediction.xyxy)
                scores = np.asarray(prediction.confidence)
                classes = np.asarray(prediction.class_id)

                # Filter strictly at operating point >= 0.50, class person (0), NO external NMS
                keep = (classes == 0) & (scores >= M2_OPERATING_POINT)
                xy = boxes[keep].astype(np.float32)
                sc = scores[keep].astype(np.float32)
                n = len(sc)

                if n > 0:
                    features = self._extract_osnet_features(reid_net, transform, frame_1080p, xy)
                    detector_rows = np.column_stack((xy, sc)).astype(np.float32)
                    online_tracks = tracker.update(detector_rows, features)
                else:
                    online_tracks = []

                frame_observations: List[Dict[str, Any]] = []
                for track in online_tracks:
                    tid = int(track.track_id)
                    tlwh = np.asarray(track.last_tlwh, dtype=float)
                    if tlwh[2] <= 0 or tlwh[3] <= 0:
                        continue
                    x, y, w, h = tlwh.tolist()
                    box_working = [float(x), float(y), float(x + w), float(y + h)]
                    confidence = float(track.score)

                    obs = {
                        "track_id": tid,
                        "box_working": box_working,
                        "confidence": confidence,
                        "class_id": 0,
                    }
                    frame_observations.append(obs)

                    # Build in-memory tracklet for GTA
                    if tid not in local_tracklets:
                        local_tracklets[tid] = Tracklet(track_id=tid)
                    feat = track.smooth_feat if hasattr(track, "smooth_feat") and track.smooth_feat is not None else np.zeros(512, dtype=np.float32)
                    local_tracklets[tid].append_det(current_frame_idx, confidence, [x, y, w, h])
                    local_tracklets[tid].append_feat(feat)

                frame_records[current_frame_idx] = frame_observations

            # Stage 2: Offline GTA association across sequence
            gta_stats: Dict[str, Any] = {
                "frames_processed": len(frame_records),
                "local_tracklets_before_gta": len(local_tracklets),
                "tracklet_lengths": {int(tid): len(tr.bboxes) for tid, tr in local_tracklets.items()},
                "gta_input_count": len(local_tracklets),
                "split_invoked": False,
                "distance_matrix_invoked": False,
                "spatial_constraints_invoked": False,
                "merge_invoked": False,
                "gta_output_count": len(local_tracklets),
            }
            if local_tracklets:
                try:
                    gta_stats["split_invoked"] = True
                    post_split = gta.split_tracklets(
                        local_tracklets,
                        eps=M2_GTA_CONFIG["eps"],
                        max_k=M2_GTA_CONFIG["max_k"],
                        min_samples=M2_GTA_CONFIG["min_samples"],
                        len_thres=M2_GTA_CONFIG["min_len"],
                    )
                    gta_stats["distance_matrix_invoked"] = True
                    distance = gta.get_distance_matrix(post_split)
                    gta_stats["spatial_constraints_invoked"] = True
                    max_x, max_y = gta.get_spatial_constraints(
                        post_split, M2_GTA_CONFIG["spatial_factor"]
                    )
                    gta_stats["merge_invoked"] = True
                    merged_tracklets = gta.merge_tracklets(
                        post_split,
                        {},
                        distance,
                        seq_name="m2_run",
                        max_x_range=max_x,
                        max_y_range=max_y,
                        merge_dist_thres=M2_GTA_CONFIG["merge_dist_thres"],
                    )
                    gta_stats["gta_output_count"] = len(merged_tracklets)

                    # Remap frame records to global merged IDs
                    merged_frame_records: Dict[int, List[Dict[str, Any]]] = {
                        fid: [] for fid in frame_records.keys()
                    }
                    for global_id, internal_id in enumerate(sorted(merged_tracklets.keys()), 1):
                        tr = merged_tracklets[internal_id]
                        for gta_frame, box, score in zip(tr.times, tr.bboxes, tr.scores):
                            gta_fid = int(gta_frame)
                            if gta_fid in merged_frame_records:
                                x, y, w, h = box
                                merged_frame_records[gta_fid].append({
                                    "track_id": int(global_id),
                                    "box_working": [float(x), float(y), float(x + w), float(y + h)],
                                    "confidence": float(score),
                                    "class_id": 0,
                                })
                    frame_records = merged_frame_records
                except Exception as e:
                    # If GTA graph merge has insufficient observations for clustering,
                    # keep robust local tracklet outputs without crashing
                    gta_stats["gta_exception"] = str(e)

            self.last_gta_stats = gta_stats

            frames_data = [
                {"frame_index": fid, "tracks": frame_records.get(fid, [])}
                for fid in sorted(frame_records.keys())
            ]
            actual_total_frames = len(frames_data)
            return frames_data, source_width, source_height, source_fps, actual_total_frames

        finally:
            cap.release()
