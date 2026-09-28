"""
Base Vision Runner Infrastructure for CM3070 Vision Execution Layer.
Defines abstract runner contracts, cryptographic verification of model weights,
source metadata probing, and adapter invocation.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 2)
IMPLEMENTATION_PHASE2_SOURCE_READBACK.md
"""
from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.adapters.common_adapter import validate_source_metadata
from backend.app.pipeline.registry import MethodologyExecutor
from backend.app.schemas.canonical_vision import (
    CalibrationReference,
    SessionVisionResult,
)
from backend.app.schemas.methodology import MethodologyId


def compute_file_sha256(path: Path) -> str:
    """Compute cryptographic SHA-256 digest in 8MB streaming chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


_VERIFIED_CHECKPOINTS_CACHE = set()


def verify_checkpoint_file(
    file_path: Path,
    expected_sha256: str,
    expected_size_bytes: Optional[int] = None,
    component_name: str = "checkpoint",
) -> Path:
    """
    Cryptographic verification gate for frozen research checkpoints.
    Fails closed if the file does not exist, byte size mismatches, or SHA-256 differs.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"FROZEN_CHECKPOINT_MISSING: {component_name} not found at '{file_path}'"
        )

    actual_size = file_path.stat().st_size
    if expected_size_bytes is not None and actual_size != expected_size_bytes:
        raise ValueError(
            f"FROZEN_CHECKPOINT_CORRUPTION: {component_name} at '{file_path}' "
            f"has size {actual_size} bytes, expected {expected_size_bytes} bytes."
        )

    cache_key = (str(file_path.resolve()), actual_size, expected_sha256.lower())
    if cache_key in _VERIFIED_CHECKPOINTS_CACHE:
        return file_path

    actual_sha = compute_file_sha256(file_path)
    if actual_sha.lower() != expected_sha256.lower():
        raise ValueError(
            f"FROZEN_CHECKPOINT_INTEGRITY_MISMATCH: {component_name} at '{file_path}' "
            f"has SHA-256 '{actual_sha}', expected '{expected_sha256}'."
        )

    _VERIFIED_CHECKPOINTS_CACHE.add(cache_key)
    return file_path


def resolve_candidate_path(
    candidate_paths: List[Path],
    expected_sha256: str,
    expected_size_bytes: Optional[int] = None,
    component_name: str = "checkpoint",
) -> Path:
    """
    Search list of candidate paths (local cache, project root, Google Drive mirror)
    and return the first verified matching file.
    """
    for candidate in candidate_paths:
        if candidate and candidate.exists() and candidate.is_file():
            try:
                return verify_checkpoint_file(
                    candidate,
                    expected_sha256=expected_sha256,
                    expected_size_bytes=expected_size_bytes,
                    component_name=component_name,
                )
            except Exception as ex:
                import logging
                logging.getLogger(__name__).debug("Candidate %s rejected: %s", candidate, ex)
                continue

    raise FileNotFoundError(
        f"NO_VERIFIED_CHECKPOINT_FOUND: Could not resolve verified {component_name} "
        f"with SHA-256 '{expected_sha256}' across candidate paths: {[str(p) for p in candidate_paths]}"
    )


class BaseVisionRunner(MethodologyExecutor, ABC):
    """
    Base class for real frozen vision execution runners.
    Adheres strictly to the P0 REV2A frozen execution contract.
    """

    def __init__(self, device: Optional[str] = None):
        self._device_override = device
        self._device = None

    @property
    def device(self) -> str:
        """Determine device lazily upon first execution."""
        if self._device is None:
            if self._device_override:
                self._device = self._device_override
            else:
                try:
                    import torch
                    self._device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    self._device = "cpu"
        return self._device

    @property
    @abstractmethod
    def methodology_id(self) -> MethodologyId:
        """The frozen methodology ID."""
        pass

    @abstractmethod
    def run_inference_and_tracking(
        self,
        video_path: Path,
        start_frame: int = 0,
        max_frames: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int, int, float, int]:
        """
        Execute real model inference and tracking on video frames.
        Returns:
            (native_frames_data, source_width, source_height, fps, total_frames)
        """
        pass

    def execute(self, payload: dict) -> SessionVisionResult:
        """
        Execute end-to-end vision pipeline:
        1. Probes video container metadata
        2. Runs real frozen inference & tracking
        3. Transforms native observations via methodology adapter to SessionVisionResult
        4. Validates identity withholding gate
        """
        raw_video_path = payload.get("video_path")
        if not raw_video_path:
            raise ValueError("VISION_EXECUTION_ERROR: 'video_path' is required in payload")

        video_path = Path(raw_video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"VISION_EXECUTION_ERROR: Video file not found: {video_path}")

        session_id = payload.get("session_id", "sess_exec")
        job_id = payload.get("job_id", "job_exec")
        start_frame = int(payload.get("start_frame", 0))
        max_frames = payload.get("max_frames")
        if max_frames is not None:
            max_frames = int(max_frames)
        calibration = payload.get("calibration", CalibrationReference.NO_METRIC_CALIBRATION)

        # Run model inference and tracking
        (
            native_frames_data,
            source_width,
            source_height,
            fps,
            total_frames,
        ) = self.run_inference_and_tracking(
            video_path=video_path,
            start_frame=start_frame,
            max_frames=max_frames,
        )

        validate_source_metadata(source_width, source_height, fps, total_frames)

        # Transform through methodology adapter
        adapter = self.get_adapter()
        session_result = adapter.convert_native_tracks_to_session_result(
            session_id=session_id,
            job_id=job_id,
            source_width=source_width,
            source_height=source_height,
            fps=fps,
            total_frames=total_frames,
            native_frames_data=native_frames_data,
            calibration=calibration,
        )

        # Enforce fail-closed identity gate invariant
        if session_result.player_level_analysis_allowed is not False:
            raise RuntimeError(
                "IDENTITY_GATE_VIOLATION: Automated vision runner must emit "
                "player_level_analysis_allowed = False per formal benchmark safety contract."
            )

        return session_result

    @abstractmethod
    def get_adapter(self) -> Any:
        """Return the methodology adapter instance."""
        pass
