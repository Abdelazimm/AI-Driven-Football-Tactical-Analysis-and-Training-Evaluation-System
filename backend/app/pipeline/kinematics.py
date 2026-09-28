"""Pipeline Stage: Kinematics Calculation
Source Research: build_corrected_metric_showcase.py::build_track_kinematics

Responsibilities:
- Apply 7-observation centered rolling median smoothing on metric positions
- Calculate displacement and instantaneous speed (km/h) using true video FPS
- Enforce speed outlier rejection (> 36 km/h rejected)
- Disallow interpolation across tracking gaps (> 0.50s) or missing observations
- In NO_METRIC_CALIBRATION mode, suppress metric distance and speed calculations entirely
"""
from typing import Dict, List, Sequence
from backend.app.schemas.tracking import TrackObservation
from backend.app.schemas.kinematics import MovementMetric
from backend.app.services.kinematics_service import KinematicsService


class KinematicsPipeline:
    """Wrapper pipeline delegating to the authoritative KinematicsService."""

    def __init__(self, fps: float, is_metric_calibrated: bool, calibration_id: str = None):
        self.fps = fps
        self.is_metric_calibrated = is_metric_calibrated
        self.service = KinematicsService(
            fps=fps,
            is_metric_calibrated=is_metric_calibrated,
            calibration_id=calibration_id,
        )

    def calculate_track_kinematics(self, observations: Sequence[TrackObservation]) -> Dict[str, MovementMetric]:
        """Derive kinematics metrics for track observations."""
        return self.service.calculate_track_kinematics(observations)
