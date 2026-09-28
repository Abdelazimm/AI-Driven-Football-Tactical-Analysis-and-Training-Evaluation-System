"""
Method 1 (M1) Vision Pipeline Adapter: Fine-Tuned YOLO11m + Tiled NMS + BoT-SORT.
Consumes native M1 tracking observations (in VISION_WORKING_SPACE 1920x1080)
and projects them into canonical SessionVisionResult in MEDIA_SOURCE_SPACE.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 2.2)
M1_FINAL_EVALUATION_BASELINE.json
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


# Exact Frozen M1 Baseline Constants (Reconciled from M1_FINAL_EVALUATION_BASELINE.json)
M1_METHODOLOGY_ID = "METHOD_1_YOLO11_BOTSORT"
M1_DETECTOR_CHECKPOINT_PATH = "runs/method_1/M1_FORMAL_003_DOMAIN_ADAPTED/training/yolo11m_domain_adapted/weights/epoch28.pt"
M1_DETECTOR_FILENAME = "epoch28.pt"
M1_DETECTOR_ARCHITECTURE = "YOLO11m custom-domain-adapted"
M1_DETECTOR_SHA256 = "ad908a9caf757f3f2b68a92d260da85a8308fb115e220b91d1bdccef31393f8b"
M1_DETECTOR_SIZE_BYTES = 104950959

M1_REID_CHECKPOINT_PATH = "runs/method_1/M1_FINAL_EVALUATION_BASELINE/checkpoints/yolo26n-reid.onnx"
M1_REID_ARCHITECTURE = "official Ultralytics yolo26n-reid.onnx"
M1_REID_SHA256 = "8529c383197ae4c468eda535d1b165f8b4162cf17bf5fbcff49c7cb6455bc0bb"
M1_REID_SIZE_BYTES = 9873245

M1_THRESHOLDS = {
    "tracker_input_candidate_confidence_floor": 0.05,
    "standalone_qualification_confidence": 0.25,
    "tile_nms_iou": 0.70,
    "global_nms_iou": 0.50,
}

M1_BOTSORT_CONFIG = {
    "track_high_thresh": 0.35,
    "track_low_thresh": 0.10,
    "new_track_thresh": 0.35,
    "track_buffer": 120,
    "match_thresh": 0.85,
    "gmc_method": "none",
    "proximity_thresh": 0.15,
    "appearance_thresh": 0.88,
    "with_reid": True,
    "fuse_score": True,
}


@dataclass
class M1CheckpointProvenance:
    checkpoint_path: str
    checkpoint_filename: str
    checkpoint_sha256: str
    checkpoint_size_bytes: int
    architecture: str


M1_DETECTOR_PROVENANCE = M1CheckpointProvenance(
    checkpoint_path=M1_DETECTOR_CHECKPOINT_PATH,
    checkpoint_filename=M1_DETECTOR_FILENAME,
    checkpoint_sha256=M1_DETECTOR_SHA256,
    checkpoint_size_bytes=M1_DETECTOR_SIZE_BYTES,
    architecture=M1_DETECTOR_ARCHITECTURE,
)

M1_REID_PROVENANCE = M1CheckpointProvenance(
    checkpoint_path=M1_REID_CHECKPOINT_PATH,
    checkpoint_filename="yolo26n-reid.onnx",
    checkpoint_sha256=M1_REID_SHA256,
    checkpoint_size_bytes=M1_REID_SIZE_BYTES,
    architecture=M1_REID_ARCHITECTURE,
)

M1_DETECTION_CONFIG = M1_THRESHOLDS


class M1VisionAdapter:
    """
    Adapter for Method 1 (YOLO11m + BoT-SORT).
    Transforms native 1920x1080 tracking outputs to canonical MEDIA_SOURCE_SPACE.
    """

    def __init__(self):
        self.provenance_info = {
            "methodology_id": M1_METHODOLOGY_ID,
            "detector_checkpoint_sha256": M1_DETECTOR_SHA256,
            "detector_checkpoint_path": M1_DETECTOR_CHECKPOINT_PATH,
            "detector_architecture": M1_DETECTOR_ARCHITECTURE,
            "detector_size_bytes": M1_DETECTOR_SIZE_BYTES,
            "reid_checkpoint_sha256": M1_REID_SHA256,
            "reid_checkpoint_path": M1_REID_CHECKPOINT_PATH,
            "reid_architecture": M1_REID_ARCHITECTURE,
            "reid_size_bytes": M1_REID_SIZE_BYTES,
            "operating_point": M1_THRESHOLDS["standalone_qualification_confidence"],
            "tracker_parameters": {**M1_THRESHOLDS, **M1_BOTSORT_CONFIG},
        }

    def adapt_tracking_results(
        self,
        native_frames_data: List[Dict[str, Any]],
        source_width: int,
        source_height: int,
        source_fps: float,
        session_id: str = "sess_m1",
        job_id: str = "job_m1",
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
        Convert raw M1 tracker frame observations to canonical SessionVisionResult.
        """
        validate_source_metadata(source_width, source_height, fps, total_frames)

        scale_x = float(source_width) / 1920.0
        scale_y = float(source_height) / 1080.0

        provenance = MethodProvenance(
            methodology_id=M1_METHODOLOGY_ID,
            detector_checkpoint_sha256=M1_DETECTOR_SHA256,
            detector_checkpoint_path=M1_DETECTOR_CHECKPOINT_PATH,
            detector_architecture=M1_DETECTOR_ARCHITECTURE,
            reid_checkpoint_sha256=M1_REID_SHA256,
            reid_checkpoint_path=M1_REID_CHECKPOINT_PATH,
            reid_architecture=M1_REID_ARCHITECTURE,
            operating_point=M1_THRESHOLDS["standalone_qualification_confidence"],
            tracker_parameters={**M1_THRESHOLDS, **M1_BOTSORT_CONFIG},
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
                box_coords = track_item.get("box_working") or track_item.get("box")
                conf = float(track_item.get("confidence") if track_item.get("confidence") is not None else track_item.get("score", 1.0))
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


M1Adapter = M1VisionAdapter
