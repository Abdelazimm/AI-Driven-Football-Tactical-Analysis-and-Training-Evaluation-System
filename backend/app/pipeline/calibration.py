"""Pipeline Stage: Pitch Calibration & Homography Mapping
Source Research: build_corrected_metric_showcase.py, config/3v3_homography_measured_metric_corrected.json

Responsibilities:
- Support DEMO_FIXED_CALIBRATION, CUSTOM_PITCH_CALIBRATION, and NO_METRIC_CALIBRATION
- Transform 2D pixel footpoints ([x_mid, y_bottom]) to physical pitch metric coordinates (x, y in metres)
- Validate resolution compatibility and geometric bounds
"""
from typing import Optional, Tuple
from backend.app.schemas.calibration import Calibration
from backend.app.services.calibration_service import CalibrationService, CalibrationValidationError


class CalibrationPipeline:
    """Wrapper pipeline delegating to the authoritative CalibrationService."""

    def __init__(self, calibration: Calibration, source_video_sha256: Optional[str] = None):
        self.calibration = calibration
        self.service = CalibrationService(
            mode=calibration.mode,
            homography_matrix=calibration.homography_matrix,
            pitch_length_m=calibration.pitch_length_m,
            pitch_width_m=calibration.pitch_width_m,
            independent_rmse_m=calibration.landmark_rmse_m,
            source_video_sha256=source_video_sha256,
        )

    def project_point(self, u: float, v: float) -> Optional[Tuple[float, float]]:
        """Planar homography forward projection (pixel working space -> pitch metres/coordinates)."""
        return self.service.project_point(u, v)

    def inverse_project_point(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        """Inverse homography projection (pitch metres/coordinates -> pixel working space)."""
        return self.service.inverse_project_point(x, y)
