"""
Method 2 (M2) Vision Pipeline Adapter: RF-DETR-L + Deep-EIoU + GTA-Track.
Consumes native M2 tracking observations (in VISION_WORKING_SPACE 1920x1080)
and projects them into canonical SessionVisionResult in MEDIA_SOURCE_SPACE.

Scientific Reference:
P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.md (Section 2.3)
M2_FINAL_EVALUATION_BASELINE.json
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


# Exact Frozen M2 Baseline Constants (Reconciled from M2_FINAL_EVALUATION_BASELINE.json)
M2_METHODOLOGY_ID = "METHOD_2_RFDETR_GTATRACK"
M2_DETECTOR_CHECKPOINT_PATH = "runs/method_2/M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth"
M2_DETECTOR_FILENAME = "checkpoint_best_total.pth"
M2_DETECTOR_ARCHITECTURE = "RF-DETR-L"
M2_DETECTOR_SHA256 = "7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85"
M2_DETECTOR_SIZE_BYTES = 134747227
M2_OPERATING_POINT = 0.50
M2_EXTERNAL_NMS = False

M2_REID_CHECKPOINT_PATH = "runs/method_2/M2_P0_preflight/checkpoints/sports_model.pth.tar-60"
M2_REID_FILENAME = "sports_model.pth.tar-60"
M2_REID_ARCHITECTURE = "OSNet-x1.0"
M2_REID_SHA256 = "8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd"
M2_REID_SIZE_BYTES = 30393613

M2_DEEPEIOU_CONFIG = {
    "config_id": "M2_DEEPEIOU_RFDETR_COMPAT_BASELINE_REV1",
    "proximity_thresh": 0.5,
    "appearance_thresh": 0.25,
    "track_high_thresh": 0.7,
    "track_low_thresh": 0.4,
    "new_track_thresh": 0.7,
    "track_buffer": 90,
    "match_thresh": 0.8,
    "min_box_area": 20,
    "occ_iou_thresh": 0.6,
    "occ_sim_thresh": 0.75,
    "occ_buffer_frames": 48,
}

M2_GTA_CONFIG = {
    "config_id": "M2_GTA_PROVENANCE_BASELINE_REV1",
    "min_len": 50,
    "eps": 0.65,
    "min_samples": 15,
    "max_k": 2,
    "spatial_factor": 1.5,
    "merge_dist_thres": 0.35,
}


@dataclass
class M2CheckpointProvenance:
    checkpoint_path: str
    checkpoint_filename: str
    checkpoint_sha256: str
    checkpoint_size_bytes: int
    architecture: str


M2_DETECTOR_PROVENANCE = M2CheckpointProvenance(
    checkpoint_path=M2_DETECTOR_CHECKPOINT_PATH,
    checkpoint_filename=M2_DETECTOR_FILENAME,
    checkpoint_sha256=M2_DETECTOR_SHA256,
    checkpoint_size_bytes=M2_DETECTOR_SIZE_BYTES,
    architecture=M2_DETECTOR_ARCHITECTURE,
)

M2_REID_PROVENANCE = M2CheckpointProvenance(
    checkpoint_path=M2_REID_CHECKPOINT_PATH,
    checkpoint_filename=M2_REID_FILENAME,
    checkpoint_sha256=M2_REID_SHA256,
    checkpoint_size_bytes=M2_REID_SIZE_BYTES,
    architecture=M2_REID_ARCHITECTURE,
)

M2_RFDETR_CONFIG = {
    "score_threshold": M2_OPERATING_POINT,
    "external_nms": M2_EXTERNAL_NMS,
}
M2_GTATRACK_CONFIG = M2_GTA_CONFIG


class M2VisionAdapter:
    """
    Adapter for Method 2 (RF-DETR-L + Deep-EIoU + GTA-Track).
    Enforces anti-double-scaling rule: receives native 1920x1080 boxes from runner
    and projects ONLY to MEDIA_SOURCE_SPACE.
    """

    def __init__(self):
        self.provenance_info = {
            "methodology_id": M2_METHODOLOGY_ID,
            "detector_checkpoint_sha256": M2_DETECTOR_SHA256,
            "detector_checkpoint_path": M2_DETECTOR_CHECKPOINT_PATH,
            "detector_architecture": M2_DETECTOR_ARCHITECTURE,
            "detector_size_bytes": M2_DETECTOR_SIZE_BYTES,
            "reid_checkpoint_sha256": M2_REID_SHA256,
            "reid_checkpoint_path": M2_REID_CHECKPOINT_PATH,
            "reid_architecture": M2_REID_ARCHITECTURE,
            "reid_size_bytes": M2_REID_SIZE_BYTES,
            "operating_point": M2_OPERATING_POINT,
            "external_nms": M2_EXTERNAL_NMS,
            "tracker_parameters": {
                "deepeiou": M2_DEEPEIOU_CONFIG,
                "gta": M2_GTA_CONFIG,
            },
        }

    def adapt_tracking_results(
        self,
        native_frames_data: List[Dict[str, Any]],
        source_width: int,
        source_height: int,
        source_fps: float,
        session_id: str = "sess_m2",
        job_id: str = "job_m2",
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
        Convert raw M2 tracker frame observations to canonical SessionVisionResult.
        """
        validate_source_metadata(source_width, source_height, fps, total_frames)

        scale_x = float(source_width) / 1920.0
        scale_y = float(source_height) / 1080.0

        provenance = MethodProvenance(
            methodology_id=M2_METHODOLOGY_ID,
            detector_checkpoint_sha256=M2_DETECTOR_SHA256,
            detector_checkpoint_path=M2_DETECTOR_CHECKPOINT_PATH,
            detector_architecture=M2_DETECTOR_ARCHITECTURE,
            reid_checkpoint_sha256=M2_REID_SHA256,
            reid_checkpoint_path=M2_REID_CHECKPOINT_PATH,
            reid_architecture=M2_REID_ARCHITECTURE,
            operating_point=M2_OPERATING_POINT,
            tracker_parameters={
                "deepeiou": M2_DEEPEIOU_CONFIG,
                "gta": M2_GTA_CONFIG,
            },
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
                # Discard any detection below formal operating point 0.50
                if conf < M2_OPERATING_POINT:
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


M2Adapter = M2VisionAdapter
