"""Calibration Service for pitch geometry and homography transforms.

Implements the four contract calibration modes:
- CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED
- GEOMETRIC_SOLVE_ONLY
- NO_METRIC_CALIBRATION
- INVALID_CALIBRATION

Authoritative Research Geometry:
- Homography Config: config/3v3_homography_measured_metric_corrected.json
- SHA-256: d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507
- Pitch Dimensions: 19.31m x 19.88m
- Independent Landmark RMSE: ~0.6505m (max error 0.841m)
- Verified Research Video SHA-256: 0e676f4327d1e7e7ed458d619e5558f6630fc7efb0dda7bc608aec45cb9a5c71
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.app.schemas.canonical_vision import CalibrationReference
from backend.app.schemas.modes import CalibrationMode


RESEARCH_HOMOGRAPHY_SHA256 = "d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507"
RESEARCH_VIDEO_SHA256 = "0e676f4327d1e7e7ed458d619e5558f6630fc7efb0dda7bc608aec45cb9a5c71"
RESEARCH_PITCH_LENGTH_M = 19.31
RESEARCH_PITCH_WIDTH_M = 19.88
RESEARCH_INDEPENDENT_RMSE_M = 0.6505


class CalibrationValidationError(Exception):
    """Raised when calibration geometry or compatibility validation fails."""
    pass


class CalibrationService:
    """Service governing planar homography calibration and metric permissions."""

    def __init__(
        self,
        mode: Union[CalibrationReference, CalibrationMode, str] = CalibrationReference.NO_METRIC_CALIBRATION,
        homography_matrix: Optional[List[List[float]]] = None,
        inverse_homography_matrix: Optional[List[List[float]]] = None,
        pitch_length_m: Optional[float] = None,
        pitch_width_m: Optional[float] = None,
        independent_rmse_m: Optional[float] = None,
        source_video_sha256: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        self.mode = self._normalize_mode(mode)
        self.pitch_length_m = pitch_length_m
        self.pitch_width_m = pitch_width_m
        self.independent_rmse_m = independent_rmse_m
        self.source_video_sha256 = source_video_sha256
        self.homography_matrix = homography_matrix
        self.inverse_homography_matrix = inverse_homography_matrix
        self.homography_sha256: Optional[str] = None

        if self.mode == CalibrationReference.CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED:
            self._load_and_validate_research_calibration(config_path)
        elif self.mode == CalibrationReference.GEOMETRIC_SOLVE_ONLY:
            # User 4-point solve: independent RMSE is strictly None
            self.independent_rmse_m = None
            if self.homography_matrix and not self.inverse_homography_matrix:
                self.inverse_homography_matrix = self._invert_3x3(self.homography_matrix)
        elif self.mode in (CalibrationReference.NO_METRIC_CALIBRATION, CalibrationReference.INVALID_CALIBRATION):
            self.homography_matrix = None
            self.inverse_homography_matrix = None
            self.pitch_length_m = None
            self.pitch_width_m = None
            self.independent_rmse_m = None

    @staticmethod
    def _normalize_mode(mode: Union[CalibrationReference, CalibrationMode, str]) -> CalibrationReference:
        if isinstance(mode, CalibrationReference):
            return mode
        val = str(mode.value if hasattr(mode, "value") else mode).strip()
        if val in ("DEMO_FIXED_CALIBRATION", "CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED"):
            return CalibrationReference.CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED
        if val in ("CUSTOM_PITCH_CALIBRATION", "GEOMETRIC_SOLVE_ONLY"):
            return CalibrationReference.GEOMETRIC_SOLVE_ONLY
        if val in ("NO_METRIC_CALIBRATION", "ANALYSIS_WITHOUT_METRICS"):
            return CalibrationReference.NO_METRIC_CALIBRATION
        if val == "INVALID_CALIBRATION":
            return CalibrationReference.INVALID_CALIBRATION
        return CalibrationReference.NO_METRIC_CALIBRATION

    def _load_and_validate_research_calibration(self, config_path: Optional[str] = None) -> None:
        """Load and verify the authoritative research homography config."""
        path = None
        candidates = [
            config_path,
            "config/3v3_homography_measured_metric_corrected.json",
            os.path.join(os.path.dirname(__file__), "../../../config/3v3_homography_measured_metric_corrected.json"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                path = Path(c).resolve()
                break

        if not path or not path.exists():
            raise CalibrationValidationError(
                "Authoritative research homography config not found at config/3v3_homography_measured_metric_corrected.json"
            )

        content_bytes = path.read_bytes()
        actual_sha = hashlib.sha256(content_bytes).hexdigest()
        self.homography_sha256 = actual_sha

        if actual_sha != RESEARCH_HOMOGRAPHY_SHA256:
            raise CalibrationValidationError(
                f"Research homography SHA-256 mismatch. Expected {RESEARCH_HOMOGRAPHY_SHA256}, got {actual_sha}"
            )

        data = json.loads(content_bytes.decode("utf-8"))
        self.homography_matrix = data["homography_matrix_tracking_to_metric"]
        self.inverse_homography_matrix = data.get("inverse_homography_matrix_metric_to_tracking")
        if not self.inverse_homography_matrix:
            self.inverse_homography_matrix = self._invert_3x3(self.homography_matrix)
        self.pitch_length_m = data.get("pitch_length_m", RESEARCH_PITCH_LENGTH_M)
        self.pitch_width_m = data.get("pitch_width_m", RESEARCH_PITCH_WIDTH_M)
        self.independent_rmse_m = RESEARCH_INDEPENDENT_RMSE_M

    def validate_compatibility(
        self,
        source_video_sha256: Optional[str] = None,
        source_resolution: Optional[Tuple[int, int]] = None,
        allow_unverified_geometry: bool = False,
    ) -> None:
        """Enforces that the research homography is never silently applied to arbitrary uploads."""
        if self.mode == CalibrationReference.CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED:
            target_sha = source_video_sha256 or self.source_video_sha256
            if allow_unverified_geometry:
                return
            if not target_sha:
                raise CalibrationValidationError(
                    "CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED requires verified camera geometry. "
                    "Cannot apply research calibration without verified video source identity."
                )
            if target_sha != RESEARCH_VIDEO_SHA256:
                raise CalibrationValidationError(
                    f"Research calibration is restricted to validated iPhone16 research geometry (SHA {RESEARCH_VIDEO_SHA256}). "
                    f"Incompatible video source SHA: {target_sha}. Silently applying research calibration is strictly prohibited."
                )

    @property
    def allows_metrics(self) -> bool:
        """Whether metric measurements (metres, km/h) are permitted."""
        return self.mode == CalibrationReference.CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED

    @property
    def allows_visualization(self) -> bool:
        """Whether 2D top-down pitch radar visualization is permitted."""
        return self.mode in (
            CalibrationReference.CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED,
            CalibrationReference.GEOMETRIC_SOLVE_ONLY,
        )

    def project_point(self, u: float, v: float) -> Optional[Tuple[float, float]]:
        """Project a 2D footpoint from 1920x1080 working space to pitch plane.

        If mode is NO_METRIC_CALIBRATION or INVALID_CALIBRATION, returns None.
        If mode is GEOMETRIC_SOLVE_ONLY, returns pitch coordinates for visualization (suppress metric units).
        If mode is CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED, returns pitch coordinates in metres.
        """
        if not self.allows_visualization or not self.homography_matrix:
            return None

        h = self.homography_matrix
        x_prime = h[0][0] * u + h[0][1] * v + h[0][2]
        y_prime = h[1][0] * u + h[1][1] * v + h[1][2]
        w_prime = h[2][0] * u + h[2][1] * v + h[2][2]

        if abs(w_prime) < 1e-9:
            return None

        x = x_prime / w_prime
        y = y_prime / w_prime
        return (x, y)

    def inverse_project_point(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        """Project pitch plane point back to 1920x1080 working space."""
        if not self.allows_visualization or not self.inverse_homography_matrix:
            return None

        h_inv = self.inverse_homography_matrix
        u_prime = h_inv[0][0] * x + h_inv[0][1] * y + h_inv[0][2]
        v_prime = h_inv[1][0] * x + h_inv[1][1] * y + h_inv[1][2]
        w_prime = h_inv[2][0] * x + h_inv[2][1] * y + h_inv[2][2]

        if abs(w_prime) < 1e-9:
            return None

        u = u_prime / w_prime
        v = v_prime / w_prime
        return (u, v)

    @staticmethod
    def _invert_3x3(m: List[List[float]]) -> Optional[List[List[float]]]:
        """Compute the inverse of a 3x3 matrix."""
        det = (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )
        if abs(det) < 1e-12:
            return None
        invdet = 1.0 / det
        return [
            [
                (m[1][1] * m[2][2] - m[1][2] * m[2][1]) * invdet,
                (m[0][2] * m[2][1] - m[0][1] * m[2][2]) * invdet,
                (m[0][1] * m[1][2] - m[0][2] * m[1][1]) * invdet,
            ],
            [
                (m[1][2] * m[2][0] - m[1][0] * m[2][2]) * invdet,
                (m[0][0] * m[2][2] - m[0][2] * m[2][0]) * invdet,
                (m[0][2] * m[1][0] - m[0][0] * m[1][2]) * invdet,
            ],
            [
                (m[1][0] * m[2][1] - m[1][1] * m[2][0]) * invdet,
                (m[0][1] * m[2][0] - m[0][0] * m[2][1]) * invdet,
                (m[0][0] * m[1][1] - m[0][1] * m[1][0]) * invdet,
            ],
        ]
