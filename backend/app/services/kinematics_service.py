"""Kinematics Service for trajectory smoothing, velocity derivation, and outlier rejection.

Implements frozen scientific rules:
1. 7-observation rolling/centered median smoothing on spatial coordinates.
2. Time-based velocity continuity: delta_t = (frame_i - frame_{i-1}) / fps.
   If delta_t > 0.50 seconds:
   - Reset velocity continuity; do NOT interpolate across gap.
   - The 120-frame quantity belongs strictly to BoT-SORT's track buffer and is NOT used as kinematics continuity.
3. Outlier rejection:
   speed > 36.0 km/h => REJECT_AND_EXCLUDE_OUTLIER
   Rejected velocity steps are excluded from accepted distance and velocity calculations; never clamped.
4. Non-metric mode:
   In NO_METRIC_CALIBRATION or uncalibrated mode, suppress metric distance (m) and speed (km/h) entirely.
"""
from __future__ import annotations

import math
from statistics import median
from typing import Any, Dict, List, Optional, Sequence, Union
from pydantic import BaseModel, Field

from backend.app.schemas.confidence import MetricConfidence
from backend.app.schemas.kinematics import MovementMetric


MAX_SPEED_KMH_THRESHOLD = 36.0
CONTINUITY_TIME_GAP_THRESHOLD_SECONDS = 0.50
MEDIAN_FILTER_WINDOW_SIZE = 7


class KinematicsStep(BaseModel):
    """Detailed kinematics result for a single observation step."""
    frame_index: int
    timestamp_s: float
    raw_x: float
    raw_y: float
    smoothed_x: float
    smoothed_y: float
    delta_t: Optional[float] = None
    displacement_m: Optional[float] = None
    speed_mps: Optional[float] = None
    speed_kmh: Optional[float] = None
    is_valid: bool = True
    is_continuity_gap: bool = False
    exclusion_reason: Optional[str] = None


class KinematicsService:
    """Service for computing kinematics metrics across trajectory observations."""

    def __init__(
        self,
        fps: float,
        is_metric_calibrated: bool = True,
        calibration_id: Optional[str] = None,
        confidence: MetricConfidence = MetricConfidence.MEASURED_METRIC_ESTIMATE,
    ):
        if fps <= 0:
            raise ValueError(f"Probed FPS must be positive, got {fps}")
        self.fps = fps
        self.is_metric_calibrated = is_metric_calibrated
        self.calibration_id = calibration_id
        self.confidence = confidence

    @staticmethod
    def apply_7point_median_filter(coords: Sequence[float]) -> List[float]:
        """Apply a 7-observation centered rolling median filter to a coordinate series."""
        n = len(coords)
        if n == 0:
            return []
        half_w = MEDIAN_FILTER_WINDOW_SIZE // 2  # 3
        smoothed: List[float] = []
        for i in range(n):
            start_idx = max(0, i - half_w)
            end_idx = min(n, i + half_w + 1)
            window = coords[start_idx:end_idx]
            smoothed.append(float(median(window)))
        return smoothed

    def calculate_steps(self, observations: Sequence[Any]) -> List[KinematicsStep]:
        """Calculate step-by-step kinematics for a sequence of observations."""
        if not observations:
            return []

        # Extract coordinates and timestamps
        raw_x_list: List[float] = []
        raw_y_list: List[float] = []
        frames: List[int] = []
        timestamps: List[float] = []

        for obs in observations:
            # Support both dict and object with metric_x/metric_y or footpoint_x/footpoint_y
            if hasattr(obs, "metric_x") and obs.metric_x is not None:
                x = float(obs.metric_x)
                y = float(obs.metric_y if obs.metric_y is not None else 0.0)
            elif isinstance(obs, dict) and obs.get("metric_x") is not None:
                x = float(obs["metric_x"])
                y = float(obs.get("metric_y", 0.0))
            elif hasattr(obs, "footpoint_x"):
                x = float(obs.footpoint_x)
                y = float(obs.footpoint_y)
            elif isinstance(obs, dict) and "footpoint_x" in obs:
                x = float(obs["footpoint_x"])
                y = float(obs["footpoint_y"])
            elif isinstance(obs, (tuple, list)) and len(obs) >= 2:
                x = float(obs[0])
                y = float(obs[1])
            else:
                x = 0.0
                y = 0.0

            frame_idx = getattr(obs, "frame_index", None)
            if frame_idx is None and isinstance(obs, dict):
                frame_idx = obs.get("frame_index")
            if frame_idx is None:
                frame_idx = len(frames)

            ts = getattr(obs, "timestamp_s", None)
            if ts is None and isinstance(obs, dict):
                ts = obs.get("timestamp_s")
            if ts is None:
                ts = frame_idx / self.fps

            raw_x_list.append(x)
            raw_y_list.append(y)
            frames.append(int(frame_idx))
            timestamps.append(float(ts))

        # Segment observations by temporal continuity (delta_t <= 0.50s)
        # to ensure smoothing never bleeds across temporal tracking gaps
        segments: List[List[int]] = []
        curr_segment: List[int] = [0]
        for i in range(1, len(observations)):
            dt = (frames[i] - frames[i - 1]) / self.fps
            if dt > CONTINUITY_TIME_GAP_THRESHOLD_SECONDS or dt <= 0:
                segments.append(curr_segment)
                curr_segment = [i]
            else:
                curr_segment.append(i)
        segments.append(curr_segment)

        smoothed_x_list = list(raw_x_list)
        smoothed_y_list = list(raw_y_list)

        for seg_indices in segments:
            if len(seg_indices) >= 3:
                seg_raw_x = [raw_x_list[idx] for idx in seg_indices]
                seg_raw_y = [raw_y_list[idx] for idx in seg_indices]
                seg_smooth_x = self.apply_7point_median_filter(seg_raw_x)
                seg_smooth_y = self.apply_7point_median_filter(seg_raw_y)
                for k, idx in enumerate(seg_indices):
                    smoothed_x_list[idx] = seg_smooth_x[k]
                    smoothed_y_list[idx] = seg_smooth_y[k]

        steps: List[KinematicsStep] = []
        for i in range(len(observations)):
            curr_frame = frames[i]
            curr_ts = timestamps[i]
            curr_x = smoothed_x_list[i]
            curr_y = smoothed_y_list[i]

            if i == 0:
                # First observation has no previous step
                steps.append(
                    KinematicsStep(
                        frame_index=curr_frame,
                        timestamp_s=curr_ts,
                        raw_x=raw_x_list[i],
                        raw_y=raw_y_list[i],
                        smoothed_x=curr_x,
                        smoothed_y=curr_y,
                        is_valid=True,
                    )
                )
                continue

            prev_frame = frames[i - 1]
            prev_x = smoothed_x_list[i - 1]
            prev_y = smoothed_y_list[i - 1]

            # Time continuity rule: delta_t = (frame_i - frame_{i-1}) / fps
            delta_t = (curr_frame - prev_frame) / self.fps

            if delta_t > CONTINUITY_TIME_GAP_THRESHOLD_SECONDS:
                # Continuity gap: reset velocity continuity, do NOT interpolate across gap
                steps.append(
                    KinematicsStep(
                        frame_index=curr_frame,
                        timestamp_s=curr_ts,
                        raw_x=raw_x_list[i],
                        raw_y=raw_y_list[i],
                        smoothed_x=curr_x,
                        smoothed_y=curr_y,
                        delta_t=delta_t,
                        is_valid=False,
                        is_continuity_gap=True,
                        exclusion_reason=f"Continuity reset: temporal gap delta_t={delta_t:.3f}s exceeds threshold {CONTINUITY_TIME_GAP_THRESHOLD_SECONDS}s",
                    )
                )
                continue

            if delta_t <= 0:
                # Duplicate or reversed frame index
                steps.append(
                    KinematicsStep(
                        frame_index=curr_frame,
                        timestamp_s=curr_ts,
                        raw_x=raw_x_list[i],
                        raw_y=raw_y_list[i],
                        smoothed_x=curr_x,
                        smoothed_y=curr_y,
                        delta_t=delta_t,
                        is_valid=False,
                        exclusion_reason="Invalid non-positive delta_t",
                    )
                )
                continue

            # Compute displacement and speed
            dx = curr_x - prev_x
            dy = curr_y - prev_y
            disp = math.sqrt(dx * dx + dy * dy)
            speed_mps = disp / delta_t
            speed_kmh = speed_mps * 3.6

            # Outlier rejection: speed > 36.0 km/h => REJECT_AND_EXCLUDE_OUTLIER
            if speed_kmh > MAX_SPEED_KMH_THRESHOLD:
                steps.append(
                    KinematicsStep(
                        frame_index=curr_frame,
                        timestamp_s=curr_ts,
                        raw_x=raw_x_list[i],
                        raw_y=raw_y_list[i],
                        smoothed_x=curr_x,
                        smoothed_y=curr_y,
                        delta_t=delta_t,
                        displacement_m=disp,
                        speed_mps=speed_mps,
                        speed_kmh=speed_kmh,
                        is_valid=False,
                        exclusion_reason=f"REJECT_AND_EXCLUDE_OUTLIER: speed {speed_kmh:.2f} km/h exceeds maximum physical threshold {MAX_SPEED_KMH_THRESHOLD} km/h",
                    )
                )
            else:
                steps.append(
                    KinematicsStep(
                        frame_index=curr_frame,
                        timestamp_s=curr_ts,
                        raw_x=raw_x_list[i],
                        raw_y=raw_y_list[i],
                        smoothed_x=curr_x,
                        smoothed_y=curr_y,
                        delta_t=delta_t,
                        displacement_m=disp,
                        speed_mps=speed_mps,
                        speed_kmh=speed_kmh,
                        is_valid=True,
                    )
                )

        return steps

    def calculate_track_kinematics(self, observations: Sequence[Any]) -> Dict[str, MovementMetric]:
        """Derive aggregated MovementMetric records for a track."""
        if not self.is_metric_calibrated:
            return {
                "total_distance": MovementMetric(
                    name="total_distance",
                    value=None,
                    unit="m",
                    confidence=MetricConfidence.NO_METRIC_CALIBRATION,
                    calibration_id=self.calibration_id,
                    display_value="Unavailable (No metric calibration)",
                    limitations=["Physical distance metric withheld: video lacks pitch calibration."],
                ),
                "average_speed": MovementMetric(
                    name="average_speed",
                    value=None,
                    unit="km/h",
                    confidence=MetricConfidence.NO_METRIC_CALIBRATION,
                    calibration_id=self.calibration_id,
                    display_value="Unavailable (No metric calibration)",
                    limitations=["Physical speed metric withheld: video lacks pitch calibration."],
                ),
                "max_speed": MovementMetric(
                    name="max_speed",
                    value=None,
                    unit="km/h",
                    confidence=MetricConfidence.NO_METRIC_CALIBRATION,
                    calibration_id=self.calibration_id,
                    display_value="Unavailable (No metric calibration)",
                    limitations=["Physical speed metric withheld: video lacks pitch calibration."],
                ),
            }

        steps = self.calculate_steps(observations)
        valid_steps = [s for s in steps if s.is_valid and s.displacement_m is not None and s.speed_kmh is not None]

        if not valid_steps:
            return {
                "total_distance": MovementMetric(
                    name="total_distance",
                    value=0.0,
                    unit="m",
                    confidence=self.confidence,
                    calibration_id=self.calibration_id,
                    display_value="0.00 m",
                    limitations=["No valid continuous motion detected."],
                ),
                "average_speed": MovementMetric(
                    name="average_speed",
                    value=0.0,
                    unit="km/h",
                    confidence=self.confidence,
                    calibration_id=self.calibration_id,
                    display_value="0.00 km/h",
                    limitations=["No valid continuous motion detected."],
                ),
                "max_speed": MovementMetric(
                    name="max_speed",
                    value=0.0,
                    unit="km/h",
                    confidence=self.confidence,
                    calibration_id=self.calibration_id,
                    display_value="0.00 km/h",
                    limitations=["No valid continuous motion detected."],
                ),
            }

        total_distance_m = sum(s.displacement_m for s in valid_steps if s.displacement_m is not None)
        speeds = [s.speed_kmh for s in valid_steps if s.speed_kmh is not None]
        avg_speed_kmh = sum(speeds) / len(speeds) if speeds else 0.0
        max_speed_kmh = max(speeds) if speeds else 0.0

        limitations: List[str] = [
            "Anonymous track kinematics only; not accumulated physical-player conclusions."
        ]
        outliers_count = sum(1 for s in steps if not s.is_valid and not s.is_continuity_gap and s.speed_kmh is not None)
        if outliers_count > 0:
            limitations.append(f"Excluded {outliers_count} anomalous speed step(s) exceeding 36 km/h.")
        gaps_count = sum(1 for s in steps if s.is_continuity_gap)
        if gaps_count > 0:
            limitations.append(f"Continuity reset across {gaps_count} temporal tracking gap(s) exceeding 0.50s.")

        return {
            "total_distance": MovementMetric(
                name="total_distance",
                value=round(total_distance_m, 2),
                unit="m",
                confidence=self.confidence,
                calibration_id=self.calibration_id,
                display_value=f"{total_distance_m:.2f} m",
                limitations=limitations,
            ),
            "average_speed": MovementMetric(
                name="average_speed",
                value=round(avg_speed_kmh, 2),
                unit="km/h",
                confidence=self.confidence,
                calibration_id=self.calibration_id,
                display_value=f"{avg_speed_kmh:.2f} km/h",
                limitations=limitations,
            ),
            "max_speed": MovementMetric(
                name="max_speed",
                value=round(max_speed_kmh, 2),
                unit="km/h",
                confidence=self.confidence,
                calibration_id=self.calibration_id,
                display_value=f"{max_speed_kmh:.2f} km/h",
                limitations=limitations,
            ),
        }
