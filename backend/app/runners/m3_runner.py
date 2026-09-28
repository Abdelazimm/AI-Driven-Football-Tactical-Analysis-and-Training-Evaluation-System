"""
Method 3 (M3) Production Vision Execution Runner: YOLO26m + SRITrack-v1 + DINOv3.
Executes real frozen M3 model inference on input video frames and transforms observations
through M3VisionAdapter into canonical SessionVisionResult.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 2.4)
M3_score_compatibility_amendment.json
frozen_m3_clip_runner.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.adapters.m3_adapter import (
    M3Adapter,
    M3_DETECTOR_PROVENANCE,
    M3_OPERATING_POINT,
    M3_SRITRACK_CONFIG,
)
from backend.app.runners.base import (
    BaseVisionRunner,
    resolve_candidate_path,
    verify_checkpoint_file,
)
from backend.app.schemas.methodology import MethodologyId

M3_REID_SHA256 = "5f4f1fa2226680c26458872f6241b9a5355d6e29a405fda1acdbcb11874b32f8"
M3_REID_SIZE_BYTES = 1104745338


class M3VisionRunner(BaseVisionRunner):
    """
    Real execution runner for Method 3:
    - Full-frame 1920x1080 -> adapted YOLO26m (M3_ADAPTED_YOLO26M.pt)
    - Full image inference, imgsz=1280, conf=0.30, iou=0.70
    - DINOv3 feature extractor (model.pth.tar-60)
    - Fresh SRITrack-v1 tracker instance with P5A amendment (track_new_th=0.30)
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
        self._feature_extractor = None
        self._verified_detector_path = None
        self._verified_reid_path = None

    @property
    def methodology_id(self) -> MethodologyId:
        return MethodologyId.METHOD_3_YOLO26_SRITRACK

    def get_adapter(self) -> M3Adapter:
        return M3Adapter()

    def _resolve_checkpoints(self) -> Tuple[Path, Path]:
        """Resolve and cryptographically verify M3 detector and DINOv3 ReID checkpoints."""
        if self._verified_detector_path is None:
            if self._detector_path_override:
                self._verified_detector_path = verify_checkpoint_file(
                    self._detector_path_override,
                    expected_sha256=M3_DETECTOR_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M3_DETECTOR_PROVENANCE.checkpoint_size_bytes,
                    component_name="M3 Detector (M3_ADAPTED_YOLO26M.pt)",
                )
            else:
                candidates = [
                    Path(os.getenv("M3_DETECTOR_PATH", "")),
                    Path("G:/My Drive/Football_Training_Assistant_MVP/methodology_comparison/runs/method_3/M3_FORMAL_001_DOMAIN_ADAPTED/checkpoints/M3_ADAPTED_YOLO26M.pt"),
                    Path("D:/checkpoints/method_3/M3_ADAPTED_YOLO26M.pt"),
                    Path(M3_DETECTOR_PROVENANCE.checkpoint_path),
                ]
                self._verified_detector_path = resolve_candidate_path(
                    candidates,
                    expected_sha256=M3_DETECTOR_PROVENANCE.checkpoint_sha256,
                    expected_size_bytes=M3_DETECTOR_PROVENANCE.checkpoint_size_bytes,
                    component_name="M3 Detector (M3_ADAPTED_YOLO26M.pt)",
                )

        if self._verified_reid_path is None:
            if self._reid_path_override:
                self._verified_reid_path = verify_checkpoint_file(
                    self._reid_path_override,
                    expected_sha256=M3_REID_SHA256,
                    expected_size_bytes=M3_REID_SIZE_BYTES,
                    component_name="M3 ReID (model.pth.tar-60)",
                )
            else:
                candidates = [
                    Path(os.getenv("M3_REID_PATH", "")),
                    Path("D:/checkpoints/method_3/model.pth.tar-60"),
                    Path("G:/My Drive/Football_Training_Assistant_MVP/methodology_comparison/checkpoints/method_3/model.pth.tar-60"),
                ]
                self._verified_reid_path = resolve_candidate_path(
                    candidates,
                    expected_sha256=M3_REID_SHA256,
                    expected_size_bytes=M3_REID_SIZE_BYTES,
                    component_name="M3 ReID (model.pth.tar-60)",
                )

        return self._verified_detector_path, self._verified_reid_path

    def _setup_m3_imports(self) -> Tuple[Any, Any]:
        """Import frozen DINOv3 FeatureExtractor and SRITrack modules lazily."""
        comp_root = Path("G:/My Drive/Football_Training_Assistant_MVP/methodology_comparison")
        m3_run = comp_root / "runs/method_3"
        reid_source = m3_run / "M3_P4_detection_reid_cache/source_bundle"
        tracker_source = m3_run / "M3_P5_identity_calibration/source_pinned"

        if str(reid_source) not in sys.path:
            sys.path.insert(0, str(reid_source))
        if str(tracker_source) not in sys.path:
            sys.path.insert(0, str(tracker_source))

        from reid.reid_extractor import FeatureExtractor
        from tracker.sri_track.Kfree_tracker_main import Tracker

        return FeatureExtractor, Tracker

    def _get_models(self):
        """Lazy load YOLO26 detector and DINOv3 feature extractor."""
        from ultralytics import YOLO

        det_path, reid_path = self._resolve_checkpoints()
        FeatureExtractor, Tracker = self._setup_m3_imports()

        if self._detector is None:
            self._detector = YOLO(str(det_path), task="detect")

        if self._feature_extractor is None:
            logger = logging.getLogger("M3_PRODUCTION_RUNNER")
            self._feature_extractor = FeatureExtractor(
                logger,
                model_name="dinov3_vit_b_16",
                weight_path=str(reid_path),
                device=self.device,
            )

        return self._detector, self._feature_extractor, Tracker

    def run_inference_and_tracking(
        self,
        video_path: Path,
        start_frame: int = 0,
        max_frames: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int, float, int]:
        """
        Execute real M3 inference with adapted YOLO26m, DINOv3 ReID,
        and SRITrack-v1 tracker with P5A score amendment.
        """
        import cv2

        detector, extractor, Tracker = self._get_models()

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"CANNOT_OPEN_VIDEO: Failed to open '{video_path}'")

        try:
            source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            source_fps = float(cap.get(cv2.CAP_PROP_FPS))
            total_container_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Instantiate fresh SRITrack tracker per run
            tracker_params = {
                "track_high_th": M3_SRITRACK_CONFIG["track_high_th"],
                "track_low_th": M3_SRITRACK_CONFIG["track_low_th"],
                "track_new_th": M3_SRITRACK_CONFIG["track_new_th"],
                "track_buffer": M3_SRITRACK_CONFIG["track_buffer"],
                "track_match_th": 0.8,
                "track_p_th": 0.5,
                "track_vc_th": 0.5,
                "track_vf_th": 0.25,
                "track_b_th": 0.7,
                "with_reid": True,
                "EIoU": True,
                "vp_dga": True,
                "ris": True,
                "det_min_area": 10,
            }
            tracker = Tracker(
                SimpleNamespace(**tracker_params),
                (1080, 1920),
                frame_rate=source_fps,
            )

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

                # YOLO26m inference on full frame
                results = detector.predict(
                    source=frame_1080p,
                    conf=M3_OPERATING_POINT,
                    iou=0.70,
                    max_det=300,
                    classes=[0],
                    imgsz=1280,
                    device=self.device,
                    verbose=False,
                )[0]

                xy = results.boxes.xyxy.cpu().numpy().astype(np.float32)
                sc = results.boxes.conf.cpu().numpy().astype(np.float32)
                n = len(sc)

                crops = []
                for x1, y1, x2, y2 in xy:
                    a, b = max(0, int(x1)), max(0, int(y1))
                    c, d = min(1920, int(x2)), min(1080, int(y2))
                    if c <= a or d <= b:
                        crops.append(np.zeros((64, 32, 3), dtype=np.uint8))
                    else:
                        crops.append(frame_1080p[b:d, a:c])

                if n > 0:
                    blocks = []
                    for offset in range(0, n, 16):
                        batch_crops = crops[offset : offset + 16]
                        batch_feat = extractor(batch_crops).cpu().numpy().astype(np.float32)
                        blocks.append(batch_feat)
                    features = np.concatenate(blocks, axis=0)
                    det = np.concatenate((xy, sc[:, None]), axis=1)
                else:
                    features = np.empty((0, 512), dtype=np.float32)
                    det = np.empty((0, 5), dtype=np.float32)

                online_tracks, _, _ = tracker.update(det, features, frame_1080p, None)

                frame_observations: List[Dict[str, Any]] = []
                for track in online_tracks:
                    tlwh = np.asarray(track.last_tlwh, dtype=float)
                    if tlwh[2] * tlwh[3] <= 10:  # det_min_area
                        continue
                    if tlwh[2] <= 0 or tlwh[3] <= 0:
                        continue

                    tid = int(track.track_id)
                    x, y, w, h = tlwh.tolist()
                    box_working = [float(x), float(y), float(x + w), float(y + h)]
                    confidence = float(track.score)

                    frame_observations.append({
                        "track_id": tid,
                        "box_working": box_working,
                        "confidence": confidence,
                        "class_id": 0,
                    })

                frames_data.append({
                    "frame_index": current_frame_idx,
                    "tracks": frame_observations,
                })

            actual_total_frames = len(frames_data)
            return frames_data, source_width, source_height, source_fps, actual_total_frames

        finally:
            cap.release()
