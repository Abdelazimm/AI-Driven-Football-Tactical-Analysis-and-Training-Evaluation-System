"""
Production Player Detection Pipeline Module.
Source Provenance: 01_vision_pipeline_corrected.ipynb (Stage 4 / Stage 4B)
Deployment Detector: Stage 4B fine-tuned YOLO11m (best.pt)

Responsibilities:
- Ingest video frames of arbitrary resolution (numpy.ndarray HWC)
- Split frame into 3 horizontal tiles with 15% overlap
- Execute person detection per tile at imgsz=1280, confidence=0.20, class=0
- Remap tile bounding boxes to full-frame pixel coordinates with boundary clipping
- Merge duplicate detections across overlapping seams using Global NMS (IoU=0.70)
- Emit typed Detection schema records with full coordinate provenance
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any
import numpy as np

from backend.app.schemas.detection import Detection


# ==============================================================================
# 1. Custom Exceptions
# ==============================================================================

class DetectionError(Exception):
    """Base exception for detection pipeline failures."""
    pass


class InvalidFrameError(DetectionError):
    """Raised when an invalid, corrupt, or unsupported frame is passed."""
    pass


class ModelNotLoadedError(DetectionError):
    """Raised when frame detection is attempted before loading a model."""
    pass


# ==============================================================================
# 2. Configuration Contract
# ==============================================================================

@dataclass
class DetectionConfig:
    """
    Typed configuration for the production player detection pipeline.
    Default values match the verified Stage 4B deployment configuration.
    """
    model_path: Optional[str] = None
    imgsz: int = 1280
    confidence_threshold: float = 0.20
    nms_iou_threshold: float = 0.70
    person_class_id: int = 0
    tile_count: int = 3
    tile_overlap_fraction: float = 0.15
    device: str = "cpu"
    detector_manifest_id: str = "stage4b_fine_tuned_tiled_yolo11m"


# ==============================================================================
# 3. Geometry & Tiling Helpers
# ==============================================================================

@dataclass(frozen=True)
class TileBox:
    """Definition of a single tile crop within full-frame coordinates."""
    tile_index: int
    x1: int
    y1: int
    x2: int
    y2: int
    width: int
    height: int


def generate_horizontal_tiles(
    width: int,
    height: int,
    tile_count: int = 3,
    overlap_fraction: float = 0.15,
) -> List[TileBox]:
    """
    Generates horizontal tiles covering the full frame width with a guaranteed overlap.
    
    Given width W, tile count n, and overlap o, the nominal tile width is derived such
    that n tiles overlapping by fraction o span the entire width:
        w_tile * [1 + (n - 1) * (1 - o)] = W
    
    Guarantees:
    - 100% full-frame horizontal coverage (no gaps)
    - Consecutive tiles overlap by at least overlap_fraction
    - Tile coordinates stay strictly within [0, width] and [0, height]
    - Works dynamically for any positive frame resolution
    """
    if width <= 0 or height <= 0:
        raise InvalidFrameError(f"Invalid frame dimensions for tiling: {width}x{height}")
    if tile_count < 1:
        raise DetectionError(f"tile_count must be >= 1, got {tile_count}")
    if not (0.0 <= overlap_fraction < 1.0):
        raise DetectionError(f"overlap_fraction must be in [0.0, 1.0), got {overlap_fraction}")

    if tile_count == 1:
        return [TileBox(tile_index=0, x1=0, y1=0, x2=width, y2=height, width=width, height=height)]

    # Compute tile width
    multiplier = 1.0 + (tile_count - 1) * (1.0 - overlap_fraction)
    tile_w = int(math.ceil(width / multiplier))
    tile_w = max(1, min(width, tile_w))

    # Compute step between tile starting positions
    step_x = max(1, int(math.floor(tile_w * (1.0 - overlap_fraction))))

    tiles: List[TileBox] = []
    for i in range(tile_count):
        if i == 0:
            x1 = 0
            x2 = min(width, tile_w)
        elif i == tile_count - 1:
            x2 = width
            x1 = max(0, width - tile_w)
        else:
            x1 = min(width - tile_w, i * step_x)
            x2 = x1 + tile_w

        tiles.append(TileBox(
            tile_index=i,
            x1=x1,
            y1=0,
            x2=x2,
            y2=height,
            width=x2 - x1,
            height=height,
        ))

    return tiles


def remap_tile_bbox_to_full_frame(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    tile_x_offset: int,
    tile_y_offset: int,
    frame_width: int,
    frame_height: int,
) -> Optional[Tuple[float, float, float, float]]:
    """
    Remaps a bounding box detected inside a tile to full-frame pixel coordinates
    and clips the box strictly to the frame boundaries.
    
    Returns (clipped_x1, clipped_y1, clipped_x2, clipped_y2) or None if degenerate.
    """
    fx1 = x1 + float(tile_x_offset)
    fy1 = y1 + float(tile_y_offset)
    fx2 = x2 + float(tile_x_offset)
    fy2 = y2 + float(tile_y_offset)

    # Clip to frame boundary
    cx1 = max(0.0, min(float(frame_width), fx1))
    cy1 = max(0.0, min(float(frame_height), fy1))
    cx2 = max(0.0, min(float(frame_width), fx2))
    cy2 = max(0.0, min(float(frame_height), fy2))

    if cx2 <= cx1 or cy2 <= cy1:
        return None

    return (round(cx1, 2), round(cy1, 2), round(cx2, 2), round(cy2, 2))


def compute_box_iou(
    box_a: Tuple[float, float, float, float],
    box_b: Tuple[float, float, float, float],
) -> float:
    """Computes Intersection-over-Union (IoU) between two boxes [x1, y1, x2, y2]."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    if inter_area <= 0.0:
        return 0.0

    area_a = max(0.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(0.0, (bx2 - bx1) * (by2 - by1))
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0

    return inter_area / union_area


@dataclass
class RawCandidateDetection:
    """Intermediate candidate detection prior to Global NMS."""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    tile_index: int


def apply_global_nms(
    candidates: List[RawCandidateDetection],
    iou_threshold: float = 0.70,
) -> List[RawCandidateDetection]:
    """
    Performs greedy Non-Maximum Suppression across merged full-frame candidate detections.
    Operates in full-frame pixel coordinates without external deep-learning framework dependencies.
    """
    if not candidates:
        return []

    # Sort descending by confidence
    sorted_candidates = sorted(candidates, key=lambda c: c.confidence, reverse=True)
    kept: List[RawCandidateDetection] = []

    for current in sorted_candidates:
        current_box = (current.x1, current.y1, current.x2, current.y2)
        should_keep = True
        for kept_item in kept:
            # Only suppress within the same class
            if current.class_id != kept_item.class_id:
                continue
            kept_box = (kept_item.x1, kept_item.y1, kept_item.x2, kept_item.y2)
            if compute_box_iou(current_box, kept_box) >= iou_threshold:
                should_keep = False
                break
        if should_keep:
            kept.append(current)

    return kept


# ==============================================================================
# 4. Detector Engine Protocol & Implementations
# ==============================================================================

class BaseDetectorEngine:
    """Abstract base detector engine interface for model loading and inference."""
    def load(self, model_path: str, device: str) -> None:
        raise NotImplementedError

    def predict_tile(
        self,
        tile_image: np.ndarray,
        imgsz: int,
        conf: float,
        classes: List[int],
        device: str,
    ) -> List[Tuple[float, float, float, float, float, int]]:
        """
        Runs model inference on a single tile crop.
        Returns list of (x1, y1, x2, y2, confidence, class_id) in tile-local coordinates.
        """
        raise NotImplementedError


class UltralyticsDetectorEngine(BaseDetectorEngine):
    """Ultralytics YOLO inference adapter."""
    def __init__(self):
        self.model: Optional[Any] = None

    def load(self, model_path: str, device: str) -> None:
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
        except ImportError as e:
            raise DetectionError("Ultralytics package is required to run UltralyticsDetectorEngine.") from e
        except Exception as e:
            raise DetectionError(f"Failed to load YOLO model from '{model_path}': {e}") from e

    def predict_tile(
        self,
        tile_image: np.ndarray,
        imgsz: int,
        conf: float,
        classes: List[int],
        device: str,
    ) -> List[Tuple[float, float, float, float, float, int]]:
        if self.model is None:
            raise ModelNotLoadedError("Detector model is not loaded. Call load() before predict_tile().")

        try:
            results = self.model.predict(
                tile_image,
                imgsz=imgsz,
                conf=conf,
                classes=classes,
                device=device,
                verbose=False,
            )
        except Exception as e:
            raise DetectionError(f"Inference execution failed on tile: {e}") from e

        detections: List[Tuple[float, float, float, float, float, int]] = []
        for res in results:
            if res.boxes is None or len(res.boxes) == 0:
                continue
            boxes_xyxy = res.boxes.xyxy.cpu().numpy()
            confidences = res.boxes.conf.cpu().numpy()
            classes_out = res.boxes.cls.cpu().numpy()

            for box, score, cls_id in zip(boxes_xyxy, confidences, classes_out):
                detections.append((
                    float(box[0]),
                    float(box[1]),
                    float(box[2]),
                    float(box[3]),
                    float(score),
                    int(cls_id),
                ))

        return detections


class MockDetectorEngine(BaseDetectorEngine):
    """Mock detector engine for test suites and headless evaluation without model weights."""
    def __init__(self, mock_predictions_by_tile: Optional[Dict[int, List[Tuple[float, float, float, float, float, int]]]] = None):
        self.is_loaded = False
        self.mock_predictions_by_tile = mock_predictions_by_tile or {}
        self.current_tile_call_count = 0

    def load(self, model_path: str, device: str) -> None:
        self.is_loaded = True

    def predict_tile(
        self,
        tile_image: np.ndarray,
        imgsz: int,
        conf: float,
        classes: List[int],
        device: str,
    ) -> List[Tuple[float, float, float, float, float, int]]:
        if not self.is_loaded:
            raise ModelNotLoadedError("Mock detector engine is not loaded.")
        tile_idx = self.current_tile_call_count
        self.current_tile_call_count += 1
        return self.mock_predictions_by_tile.get(tile_idx, [])


# ==============================================================================
# 5. Production Detection Pipeline
# ==============================================================================

class DetectionPipeline:
    """
    Stage 4B Tiled Player Detection Pipeline.
    Encapsulates horizontal tiling, tile-based inference, coordinate remapping,
    and Global NMS duplicate suppression.
    """

    def __init__(
        self,
        config: Optional[DetectionConfig] = None,
        detector_engine: Optional[BaseDetectorEngine] = None,
    ):
        self.config = config or DetectionConfig()
        self.engine = detector_engine or UltralyticsDetectorEngine()

    def load_model(self, model_path: Optional[str] = None) -> None:
        """Loads model weights into the underlying detector engine."""
        path = model_path or self.config.model_path
        if not path:
            raise DetectionError("Cannot load detector: model_path was not provided in config or load_model call.")
        self.engine.load(path, self.config.device)

    def detect_frame(
        self,
        frame: np.ndarray,
        frame_index: int,
        timestamp_s: Optional[float] = None,
        fps: Optional[float] = None,
    ) -> List[Detection]:
        """
        Executes player detection on a single frame.
        
        Parameters:
        - frame: OpenCV-style numpy array (H, W, C)
        - frame_index: 0-indexed integer frame position
        - timestamp_s: Explicit timestamp in seconds (optional)
        - fps: Dynamic video FPS from container metadata (optional)
        
        Returns:
        - List of Detection records in full-frame pixel coordinates.
        """
        # 1. Validate frame input
        if not isinstance(frame, np.ndarray):
            raise InvalidFrameError(f"Frame must be a numpy.ndarray, got {type(frame)}")
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise InvalidFrameError(f"Frame must have shape (H, W, 3), got {frame.shape}")
        if frame.size == 0 or frame.shape[0] <= 0 or frame.shape[1] <= 0:
            raise InvalidFrameError(f"Empty or zero-dimension frame received: {frame.shape}")

        height, width, _ = frame.shape

        # 2. Derive frame timestamp dynamically
        if timestamp_s is not None:
            resolved_timestamp = float(timestamp_s)
        elif fps is not None and fps > 0.0:
            resolved_timestamp = float(frame_index) / float(fps)
        else:
            raise InvalidFrameError("Either timestamp_s or positive fps must be supplied to derive frame timing.")

        # 3. Generate horizontal tiles
        tiles = generate_horizontal_tiles(
            width=width,
            height=height,
            tile_count=self.config.tile_count,
            overlap_fraction=self.config.tile_overlap_fraction,
        )

        raw_candidates: List[RawCandidateDetection] = []

        # 4. Predict on each tile and remap coordinates
        for tile in tiles:
            tile_crop = frame[tile.y1:tile.y2, tile.x1:tile.x2]

            tile_predictions = self.engine.predict_tile(
                tile_image=tile_crop,
                imgsz=self.config.imgsz,
                conf=self.config.confidence_threshold,
                classes=[self.config.person_class_id],
                device=self.config.device,
            )

            for tx1, ty1, tx2, ty2, conf, cls_id in tile_predictions:
                # Class filter
                if cls_id != self.config.person_class_id:
                    continue
                # Confidence filter
                if conf < self.config.confidence_threshold:
                    continue

                # Remap from tile-local to full-frame coordinates
                remapped = remap_tile_bbox_to_full_frame(
                    x1=tx1,
                    y1=ty1,
                    x2=tx2,
                    y2=ty2,
                    tile_x_offset=tile.x1,
                    tile_y_offset=tile.y1,
                    frame_width=width,
                    frame_height=height,
                )
                if remapped is None:
                    continue

                fx1, fy1, fx2, fy2 = remapped
                raw_candidates.append(RawCandidateDetection(
                    x1=fx1,
                    y1=fy1,
                    x2=fx2,
                    y2=fy2,
                    confidence=float(conf),
                    class_id=int(cls_id),
                    tile_index=tile.tile_index,
                ))

        # 5. Apply Global NMS to suppress duplicates across overlapping tiles
        filtered_candidates = apply_global_nms(
            candidates=raw_candidates,
            iou_threshold=self.config.nms_iou_threshold,
        )

        # 6. Convert to typed Detection records
        detections: List[Detection] = []
        for c in filtered_candidates:
            detections.append(Detection(
                frame_index=frame_index,
                timestamp_s=round(resolved_timestamp, 4),
                x1=c.x1,
                y1=c.y1,
                x2=c.x2,
                y2=c.y2,
                confidence=round(c.confidence, 4),
                class_id=c.class_id,
                track_id=None,  # Short-term tracking occurs in a subsequent stage
                source_width=width,
                source_height=height,
                detector_manifest_id=self.config.detector_manifest_id,
            ))

        return detections
