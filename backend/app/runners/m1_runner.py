"""
Method 1 (M1) Production Vision Execution Runner: YOLO11m + Tiled NMS + BoT-SORT.
Executes real frozen M1 model inference on input video frames and transforms observations
through M1VisionAdapter into canonical SessionVisionResult.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 2.2)
M1_FINAL_EVALUATION_BASELINE.json
frozen_m1_clip_runner.py
"""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.adapters.m1_adapter import (
    M1Adapter,
    M1_BOTSORT_CONFIG,
    M1_DETECTOR_PROVENANCE,
    M1_REID_PROVENANCE,
    M1_THRESHOLDS,
)
from backend.app.runners.base import (
    BaseVisionRunner,
    resolve_candidate_path,
    verify_checkpoint_file,
)
from backend.app.schemas.methodology import MethodologyId


class M1VisionRunner(BaseVisionRunner):
    """
    Real execution runner for Method 1:
    - 3-tile slicing across 1920x1080 working resolution: (0, 712), (605, 1317), (1208, 1920)
    - YOLO11m domain-adapted detector (epoch28.pt)
    - Candidate floor 0.05, tile NMS IoU 0.70, global NMS IoU 0.50
    - Fresh BoT-SORT instance with yolo26n-reid.onnx per execution
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
        self._verified_detector_path = None
        self._verified_reid_path = None

    @property
    def methodology_id(self) -> MethodologyId:
        return MethodologyId.METHOD_1_YOLO11_BOTSORT

    def get_adapter(self) -> M1Adapter:
        return M1Adapter()

    def _resolve_checkpoints(self) -> Tuple[Path, Path]:
        """Resolve and cryptographically verify M1 detector and ReID checkpoints."""
        if self._verified_detector_path is None:
            if self._detector_path_override:
                self._verified_detector_path = verify_checkpoint_file(
                    self._detector_path_override,
                    expected_sha256=M1_DETECTOR_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M1_DETECTOR_PROVENANCE.checkpoint_size_bytes,
                    component_name="M1 Detector (epoch28.pt)",
                )
            else:
                candidates = [
                    Path(os.getenv("M1_DETECTOR_PATH", "")),
                    Path("G:/My Drive/Football_Training_Assistant_MVP/methodology_comparison/runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt"),
                    Path("D:/checkpoints/method_1/epoch28.pt"),
                    Path(M1_DETECTOR_PROVENANCE.checkpoint_path),
                ]
                self._verified_detector_path = resolve_candidate_path(
                    candidates,
                    expected_sha256=M1_DETECTOR_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M1_DETECTOR_PROVENANCE.checkpoint_size_bytes,
                    component_name="M1 Detector (epoch28.pt)",
                )

        if self._verified_reid_path is None:
            if self._reid_path_override:
                self._verified_reid_path = verify_checkpoint_file(
                    self._reid_path_override,
                    expected_sha256=M1_REID_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M1_REID_PROVENANCE.checkpoint_size_bytes,
                    component_name="M1 ReID (yolo26n-reid.onnx)",
                )
            else:
                candidates = [
                    Path(os.getenv("M1_REID_PATH", "")),
                    Path("G:/My Drive/Football_Training_Assistant_MVP/methodology_comparison/runs/method_1/M1_FINAL_EVALUATION_BASELINE/checkpoints/yolo26n-reid.onnx"),
                    Path("runs/method_1/M1_FINAL_EVALUATION_BASELINE/checkpoints/yolo26n-reid.onnx"),
                    Path("D:/checkpoints/method_1/yolo26n-reid.onnx"),
                    Path(M1_REID_PROVENANCE.checkpoint_path),
                ]
                self._verified_reid_path = resolve_candidate_path(
                    candidates,
                    expected_sha256=M1_REID_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M1_REID_PROVENANCE.checkpoint_size_bytes,
                    component_name="M1 ReID (yolo26n-reid.onnx)",
                )

        return self._verified_detector_path, self._verified_reid_path

    def _get_detector(self):
        """Lazy load detector model."""
        if self._detector is None:
            from ultralytics import YOLO
            det_path, _ = self._resolve_checkpoints()
            self._detector = YOLO(str(det_path))
        return self._detector

    def _detect_tiled(
        self,
        frame_1080p: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute 3-tile detection with overlap and global NMS at 0.50.
        Exact logic from frozen_m1_clip_runner.py.
        """
        import torch
        from torchvision.ops import nms

        detector = self._get_detector()
        tiles = ((0, 712), (605, 1317), (1208, 1920))
        tile_crops = [frame_1080p[:, a:b] for a, b in tiles]

        results = detector.predict(
            tile_crops,
            imgsz=1280,
            conf=M1_THRESHOLDS["tracker_input_candidate_confidence_floor"],
            iou=M1_THRESHOLDS["tile_nms_iou"],
            classes=[0],
            max_det=300,
            device=self.device,
            verbose=False,
        )

        chunks: List[np.ndarray] = []
        scores: List[np.ndarray] = []

        for (a, _), result in zip(tiles, results):
            if result.boxes is None or len(result.boxes) == 0:
                continue
            xy = result.boxes.xyxy.detach().cpu().numpy().astype(np.float32)
            sc = result.boxes.conf.detach().cpu().numpy().astype(np.float32)
            xy[:, (0, 2)] += float(a)
            chunks.append(xy)
            scores.append(sc)

        if not chunks:
            return np.empty((0, 4), dtype=np.float32), np.empty((0,), dtype=np.float32)

        xy = np.concatenate(chunks, axis=0)
        sc = np.concatenate(scores, axis=0)

        valid = np.isfinite(xy).all(axis=1) & np.isfinite(sc)
        xy, sc = xy[valid], sc[valid]

        xy[:, (0, 2)] = np.clip(xy[:, (0, 2)], 0, 1920)
        xy[:, (1, 3)] = np.clip(xy[:, (1, 3)], 0, 1080)

        box_valid = (
            (xy[:, 2] > xy[:, 0])
            & (xy[:, 3] > xy[:, 1])
            & (sc >= M1_THRESHOLDS["tracker_input_candidate_confidence_floor"])
        )
        xy, sc = xy[box_valid], sc[box_valid]

        if len(xy) > 0:
            keep = (
                nms(
                    torch.from_numpy(xy),
                    torch.from_numpy(sc),
                    M1_THRESHOLDS["global_nms_iou"],
                )
                .cpu()
                .numpy()
            )
            xy, sc = xy[keep], sc[keep]
            order = np.lexsort((xy[:, 3], xy[:, 2], xy[:, 1], xy[:, 0], -sc))
            xy, sc = xy[order], sc[order]

        return xy, sc

    def run_inference_and_tracking(
        self,
        video_path: Path,
        start_frame: int = 0,
        max_frames: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int, float, int]:
        """
        Execute real M1 tiled detection and BoT-SORT tracking.
        Enforces fresh tracker instance per execution job.
        """
        import cv2
        from ultralytics.engine.results import Boxes
        from ultralytics.trackers.bot_sort import BOTSORT

        _, reid_path = self._resolve_checkpoints()

        # Instantiate fresh BoT-SORT tracker per run (no cross-job state)
        tracker_cfg = {
            "tracker_type": "botsort",
            "track_high_thresh": M1_BOTSORT_CONFIG["track_high_thresh"],
            "track_low_thresh": M1_BOTSORT_CONFIG["track_low_thresh"],
            "new_track_thresh": M1_BOTSORT_CONFIG["new_track_thresh"],
            "track_buffer": M1_BOTSORT_CONFIG["track_buffer"],
            "match_thresh": M1_BOTSORT_CONFIG["match_thresh"],
            "gmc_method": M1_BOTSORT_CONFIG["gmc_method"],
            "proximity_thresh": M1_BOTSORT_CONFIG["proximity_thresh"],
            "appearance_thresh": M1_BOTSORT_CONFIG["appearance_thresh"],
            "with_reid": M1_BOTSORT_CONFIG["with_reid"],
            "model": str(reid_path),
            "fuse_score": M1_BOTSORT_CONFIG["fuse_score"],
        }
        tracker = BOTSORT(SimpleNamespace(**tracker_cfg))

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

            frames_data: List[Dict[str, Any]] = []

            for current_frame_idx in range(start_frame, end_frame + 1):
                ok, image = cap.read()
                if not ok or image is None:
                    break

                # Resize to VISION_WORKING_SPACE (1920x1080)
                frame_1080p = cv2.resize(
                    image, (1920, 1080), interpolation=cv2.INTER_AREA
                )

                xy, sc = self._detect_tiled(frame_1080p)
                n = len(sc)

                frame_tracks: List[Dict[str, Any]] = []
                if n > 0:
                    six = np.column_stack((xy, sc, np.zeros(n, dtype=np.float32))).astype(np.float32)
                    out = tracker.update(Boxes(six, (1080, 1920)), img=frame_1080p)

                    for pred in out:
                        det_row = int(round(float(pred[7]))) if len(pred) > 7 else 0
                        box = np.asarray(pred[:4], dtype=float)
                        box[[0, 2]] = np.clip(box[[0, 2]], 0, 1920)
                        box[[1, 3]] = np.clip(box[[1, 3]], 0, 1080)
                        if box[2] <= box[0] or box[3] <= box[1]:
                            continue

                        track_id = int(round(float(pred[4])))
                        conf = float(pred[5])
                        class_id = int(round(float(pred[6]))) if len(pred) > 6 else 0

                        frame_tracks.append({
                            "track_id": track_id,
                            "box_working": [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                            "confidence": conf,
                            "class_id": class_id,
                            "source_detection_id": f"f{current_frame_idx:06d}_d{det_row:03d}",
                        })

                frames_data.append({
                    "frame_index": current_frame_idx,
                    "tracks": frame_tracks,
                })

            actual_total_frames = len(frames_data)
            return frames_data, source_width, source_height, source_fps, actual_total_frames

        finally:
            cap.release()
