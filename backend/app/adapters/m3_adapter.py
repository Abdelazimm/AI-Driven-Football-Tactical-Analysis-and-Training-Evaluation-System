"""
Method 3 (M3) Vision Pipeline Adapter: Domain-Adapted YOLO26m + SRITrack-v1 + DINOv3.
Consumes native M3 tracking observations (in VISION_WORKING_SPACE 1920x1080)
and projects them into canonical SessionVisionResult in MEDIA_SOURCE_SPACE.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 2.4)
M3_score_compatibility_amendment.json
M3_ADAPTED_YOLO26M.pt
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from backend.app.schemas.canonical_vision import (
    CoordinateSpace,
    SessionVisionResult,
    FrameVisionResult,
    TrackObservation,
    MethodProvenance,
    FormalIdentityStatus,
    RuntimeIdentityStatus,
    IdentityEvidenceBasis,
    CalibrationReference,
)
from backend.app.adapters.common_adapter import (
    validate_source_metadata,
    build_track_observation,
    create_empty_frame,
)


# Exact Frozen M3 Baseline Constants (Reconciled from M3_score_compatibility_amendment.json & Checkpoint Readback)
M3_METHODOLOGY_ID = "METHOD_3_YOLO26_SRITRACK"
M3_DETECTOR_CHECKPOINT_PATH = "methodology_comparison/runs/method_3/M3_FORMAL_001_DOMAIN_ADAPTED/checkpoints/M3_ADAPTED_YOLO26M.pt"
M3_DETECTOR_FILENAME = "M3_ADAPTED_YOLO26M.pt"
M3_DETECTOR_ARCHITECTURE = "YOLO26m domain-adapted"
M3_DETECTOR_SHA256 = "ea9b3e434ffd7c2ca7ebcd563497accd90e03cfc8da1e8e9fc883e4790199dbf"
M3_DETECTOR_SIZE_BYTES = 44081689
M3_OPERATING_POINT = 0.30

M3_SRITRACK_CONFIG = {
    "algorithm": "SRITrack-v1",
    "track_new_th": 0.30,  # Amended from source default 0.70 via P5A score compatibility amendment
    "track_new_th_provenance": "amended from source-default 0.70 via P5A score compatibility amendment",
    "track_new_th_amendment": "P5A_SCORE_COMPATIBILITY_AMENDMENT",
    "track_high_th": 0.60,
    "track_low_th": 0.10,
    "track_buffer": 1000,
    "detector_operating_point": 0.30,
}


@dataclass
class M3CheckpointProvenance:
    checkpoint_path: str
    checkpoint_filename: str
    checkpoint_sha256: str
    checkpoint_size_bytes: int
    architecture: str


M3_DETECTOR_PROVENANCE = M3CheckpointProvenance(
    checkpoint_path=M3_DETECTOR_CHECKPOINT_PATH,
    checkpoint_filename=M3_DETECTOR_FILENAME,
    checkpoint_sha256=M3_DETECTOR_SHA256,
    checkpoint_size_bytes=M3_DETECTOR_SIZE_BYTES,
    architecture=M3_DETECTOR_ARCHITECTURE,
)


class M3VisionAdapter:
    """
    Adapter for Method 3 (YOLO26m + SRITrack-v1).
    Enforces anti-double-scaling rule: receives native 1920x1080 boxes from SRITrack
    and projects ONLY to MEDIA_SOURCE_SPACE.
    """

    def __init__(self):
        self.provenance_info = {
            "methodology_id": M3_METHODOLOGY_ID,
            "detector_checkpoint_sha256": M3_DETECTOR_SHA256,
            "detector_checkpoint_path": M3_DETECTOR_CHECKPOINT_PATH,
            "detector_architecture": M3_DETECTOR_ARCHITECTURE,
            "detector_size_bytes": M3_DETECTOR_SIZE_BYTES,
            "operating_point": M3_OPERATING_POINT,
            "tracker_parameters": M3_SRITRACK_CONFIG,
        }

    def adapt_tracking_results(
        self,
        native_frames_data: List[Dict[str, Any]],
        source_width: int,
        source_height: int,
        source_fps: float,
        session_id: str = "sess_m3",
        job_id: str = "job_m3",
        total_frames: Optional[int] = None,
        calibration: Optional[CalibrationReference] = None,
    ) -> SessionVisionResult:
        if total_frames is None:
            total_frames = (
                max(f["frame_index"] for f in native_frames_data) + 1
                if native_frames_data
                else 1
            )
        return self.convert_native_tracks_to_session_result(
            session_id=session_id,
            job_id=job_id,
            source_width=source_width,
            source_height=source_height,
            fps=source_fps,
            total_frames=total_frames,
            native_frames_data=native_frames_data,
            calibration=calibration,
        )

    def convert_native_tracks_to_session_result(
        self,
        session_id: str,
        job_id: str,
        source_width: int,
        source_height: int,
        fps: float,
        total_frames: int,
        native_frames_data: List[Dict[str, Any]],
        calibration: Optional[CalibrationReference] = None,
    ) -> SessionVisionResult:
        """
        Convert raw M3 tracker frame observations to canonical SessionVisionResult.
        """
        validate_source_metadata(source_width, source_height, fps, total_frames)

        scale_x = float(source_width) / 1920.0
        scale_y = float(source_height) / 1080.0

        provenance = MethodProvenance(
            methodology_id=M3_METHODOLOGY_ID,
            detector_checkpoint_sha256=M3_DETECTOR_SHA256,
            detector_checkpoint_path=M3_DETECTOR_CHECKPOINT_PATH,
            detector_architecture=M3_DETECTOR_ARCHITECTURE,
            operating_point=M3_OPERATING_POINT,
            tracker_parameters=M3_SRITRACK_CONFIG,
            native_runner_output_space=CoordinateSpace.VISION_WORKING_SPACE,
            source_resolution=(source_width, source_height),
            working_resolution=(1920, 1080),
            scale_factors=(round(scale_x, 4), round(scale_y, 4)),
        )

        canonical_frames: List[FrameVisionResult] = []

        for frame_dict in native_frames_data:
            frame_idx = frame_dict["frame_index"]
            timestamp_s = round(frame_idx / fps, 4)
            raw_tracks = frame_dict.get("tracks", [])

            if not raw_tracks:
                canonical_frames.append(create_empty_frame(frame_idx, fps))
                continue

            frame_observations: List[TrackObservation] = []
            for track_item in raw_tracks:
                conf = float(track_item.get("confidence") if track_item.get("confidence") is not None else track_item.get("score", 1.0))
                # Discard detections below 0.30 operating point
                if conf < M3_OPERATING_POINT:
                    continue

                box_coords = track_item.get("box_working") or track_item.get("box")
                obs = build_track_observation(
                    opaque_track_id=track_item["track_id"],
                    box_working=tuple(box_coords),
                    confidence=conf,
                    source_width=source_width,
                    source_height=source_height,
                    working_width=1920,
                    working_height=1080,
                    class_id=track_item.get("class_id", 0),
                    tracklet_id=track_item.get("tracklet_id"),
                    source_detection_id=track_item.get("source_detection_id"),
                    physical_player_pseudonym=None,  # Strictly None under automated runs
                )
                frame_observations.append(obs)

            canonical_frames.append(
                FrameVisionResult(
                    frame_index=frame_idx,
                    timestamp_s=timestamp_s,
                    is_empty_frame=len(frame_observations) == 0,
                    observations=frame_observations,
                )
            )

        return SessionVisionResult(
            session_id=session_id,
            job_id=job_id,
            source_width=source_width,
            source_height=source_height,
            fps=fps,
            total_frames=total_frames,
            coordinate_space=CoordinateSpace.MEDIA_SOURCE_SPACE,
            provenance=provenance,
            frames=canonical_frames,
            calibration_reference=calibration or CalibrationReference.NO_METRIC_CALIBRATION,
            method_formal_identity_status=FormalIdentityStatus.FAIL_UNSAFE_MERGE,
            method_formal_identity_evidence_basis=IdentityEvidenceBasis.FORMAL_DENSE_GT,
            runtime_identity_status=RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS,
            runtime_identity_evidence_basis=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
            player_level_analysis_allowed=False,  # Enforce fail-closed identity gate
            withholding_reason=(
                "Automated tracking methodology has not demonstrated sufficiently safe persistent "
                "physical-player identity under formal benchmark evaluation."
            ),
        )


M3Adapter = M3VisionAdapter
