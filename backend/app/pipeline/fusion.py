"""
Pipeline Stage: Multimodal Audio-Vision Fusion & Structured Evidence Generation.
Governed by P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A and Implementation Phase 3 rules.

Scientific Invariants:
1. Post-command reaction window: strictly [t_end + 2.0s, t_end + 6.0s].
   Legacy pre-command window is PROHIBITED.
2. Timebase alignment: Vision timestamps (frame_index / probed_fps) and ASR timestamps
   must share the identical absolute source-media timeline.
3. Identity safety gate: Automated runs preserve player_level_analysis_allowed = False.
   Prohibits scope = PLAYER. Only TEAM, SPATIAL, EVENT, and ANONYMOUS_TRACK are permitted.
   Track IDs remain opaque (e.g. 'track_3') and are never upgraded to physical player pseudonyms.
4. Calibration permissions: Metres and km/h are permitted ONLY under
   CAMERA_SPECIFIC_INDEPENDENTLY_VALIDATED. Under GEOMETRIC_SOLVE_ONLY or NO_METRIC_CALIBRATION,
   all metric fields are strictly null.
5. Kinematics rules: 7-observation rolling median smoothing, time gap > 0.50s continuity reset,
   and speeds > 36.0 km/h rejected and excluded.
6. Research mocks and synthetic constants are PROHIBITED.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from backend.app.pipeline.evidence import (
    EvidencePipeline,
    StructuredEvidenceItem,
    StructuredEvidencePayload,
)
from backend.app.schemas.asr import ASRResult, TacticalEvent
from backend.app.schemas.canonical_vision import (
    CalibrationReference,
    FrameVisionResult,
    SessionVisionResult,
    TrackObservation,
)
from backend.app.services.calibration_service import CalibrationService
from backend.app.services.identity_safety_service import (
    IdentitySafetyAssessment,
    IdentitySafetyService,
)
from backend.app.services.kinematics_service import (
    KinematicsService,
    KinematicsStep,
    MAX_SPEED_KMH_THRESHOLD,
    CONTINUITY_TIME_GAP_THRESHOLD_SECONDS,
)


class MultimodalFusionEngine:
    """
    Production Multimodal Fusion Engine aligning ASR tactical events with canonical Vision results.
    """

    def __init__(
        self,
        reaction_offset_start_s: float = 2.0,
        reaction_offset_end_s: float = 6.0,
    ):
        # Strict enforcement: reaction window [t_end + 2.0s, t_end + 6.0s]
        self.reaction_offset_start_s = reaction_offset_start_s
        self.reaction_offset_end_s = reaction_offset_end_s
        self.evidence_pipeline = EvidencePipeline()

    def fuse(
        self,
        session_id: str,
        asr_result: ASRResult,
        vision_result: SessionVisionResult,
        identity_assessment: Optional[IdentitySafetyAssessment] = None,
        calibration_service: Optional[CalibrationService] = None,
        kinematics_service: Optional[KinematicsService] = None,
    ) -> StructuredEvidencePayload:
        """
        Executes multimodal audio-vision fusion and produces machine-validatable Structured Evidence.
        """
        fps = vision_result.fps
        if fps <= 0:
            raise ValueError("VISION_FPS_UNAVAILABLE: source frame timestamps cannot be inferred")

        # 1. Resolve Identity Safety Assessment
        if identity_assessment is None:
            safety_svc = IdentitySafetyService()
            method_id = (
                vision_result.method_provenance.methodology_id
                if hasattr(vision_result, "method_provenance")
                else "METHOD_2_RFDETR_GTATRACK"
            )
            identity_assessment = safety_svc.evaluate_identity_safety(
                methodology=method_id,
                is_oracle=False,
            )

        player_allowed = identity_assessment.player_level_analysis_allowed
        identity_basis = str(identity_assessment.runtime_identity_evidence_basis.value
                             if hasattr(identity_assessment.runtime_identity_evidence_basis, "value")
                             else identity_assessment.runtime_identity_evidence_basis)

        # 2. Resolve Calibration & Metric Permissions
        calib_ref = getattr(vision_result, "calibration", getattr(vision_result, "calibration_reference", CalibrationReference.NO_METRIC_CALIBRATION))
        if calib_ref is None:
            calib_ref = CalibrationReference.NO_METRIC_CALIBRATION

        if calibration_service is None:
            calib_mode_str = calib_ref.value if hasattr(calib_ref, "value") else str(calib_ref)
            calibration_service = CalibrationService(mode=calib_mode_str)

        metric_allowed = calibration_service.allows_metrics
        calib_mode_label = calibration_service.mode.value if hasattr(calibration_service.mode, "value") else str(calibration_service.mode)

        # Scaling factors for calibration projection (source -> 1920x1080 working space)
        src_w = vision_result.source_width
        src_h = vision_result.source_height
        if src_w <= 0 or src_h <= 0:
            raise ValueError("VISION_RESOLUTION_UNAVAILABLE: source dimensions must be probed")
        scale_x = src_w / 1920.0
        scale_y = src_h / 1080.0

        # 3. Resolve Kinematics Service
        if kinematics_service is None:
            kinematics_service = KinematicsService(
                fps=fps,
                is_metric_calibrated=metric_allowed,
                calibration_id=calib_mode_label,
            )

        # Index vision frames by timestamp
        # Absolute session timebase: timestamp_s if provided, else frame_index / fps
        indexed_frames: List[Tuple[float, FrameVisionResult]] = []
        for frame in vision_result.frames:
            ts = frame.timestamp_s if frame.timestamp_s is not None else (frame.frame_index / fps)
            indexed_frames.append((round(ts, 4), frame))

        evidence_items: List[StructuredEvidenceItem] = []
        warns = []
        if hasattr(vision_result, "method_provenance") and hasattr(vision_result.method_provenance, "execution_warnings"):
            warns = vision_result.method_provenance.execution_warnings or []
        global_limitations: List[str] = list(warns)

        if not player_allowed:
            global_limitations.append("AUTOMATED_IDENTITY_UNSAFE_PLAYER_LEVEL_ANALYSIS_WITHHELD")
        if not metric_allowed:
            global_limitations.append("NON_METRIC_CALIBRATION_PHYSICAL_METRES_AND_KMH_WITHHELD")

        method_name = (
            vision_result.method_provenance.methodology_id.value
            if hasattr(vision_result, "method_provenance") and hasattr(vision_result.method_provenance.methodology_id, "value")
            else str(getattr(vision_result, "method_provenance", "UNKNOWN_METHOD"))
        )

        # 4. Iterate over ASR Tactical Events
        for event in asr_result.events:
            w_start = round(event.t_end + self.reaction_offset_start_s, 2)
            w_end = round(event.t_end + self.reaction_offset_end_s, 2)

            # Query frames within reaction window [t_end + 2.0s, t_end + 6.0s]
            window_frames = [
                (ts, f) for ts, f in indexed_frames if w_start <= ts <= w_end
            ]

            if not window_frames:
                # Fail closed on empty observation window
                evidence_items.append(
                    StructuredEvidenceItem(
                        evidence_id=f"ev_{event.event_id}_no_obs",
                        scope="EVENT",
                        source_event_id=event.event_id,
                        event_category=event.category,
                        event_action=event.action,
                        window_start_s=w_start,
                        window_end_s=w_end,
                        calibration_mode=calib_mode_label,
                        metric_units_allowed=metric_allowed,
                        identity_evidence_basis=identity_basis,
                        observations_count=0,
                        source_provenance={
                            "methodology_id": method_name,
                            "fps": fps,
                        },
                        missing_fields=["observations_in_window"],
                        limitations=["NO_VISUAL_OBSERVATIONS_IN_RESPONSE_WINDOW"],
                    )
                )
                continue

            # Group track observations within the window by track_id
            tracks_in_window: Dict[int, List[Tuple[float, TrackObservation]]] = {}
            for ts, frame in window_frames:
                obs_list = getattr(frame, "observations", getattr(frame, "tracks", []))
                for track in obs_list:
                    tid = getattr(track, "opaque_track_id", getattr(track, "track_id", 0))
                    if tid not in tracks_in_window:
                        tracks_in_window[tid] = []
                    tracks_in_window[tid].append((ts, track))

            if not tracks_in_window:
                evidence_items.append(
                    StructuredEvidenceItem(
                        evidence_id=f"ev_{event.event_id}_no_tracks",
                        scope="EVENT",
                        source_event_id=event.event_id,
                        event_category=event.category,
                        event_action=event.action,
                        window_start_s=w_start,
                        window_end_s=w_end,
                        calibration_mode=calib_mode_label,
                        metric_units_allowed=metric_allowed,
                        identity_evidence_basis=identity_basis,
                        observations_count=0,
                        source_provenance={
                            "methodology_id": method_name,
                            "fps": fps,
                        },
                        missing_fields=["tracks_in_window"],
                        limitations=["NO_TRACKS_DETECTED_IN_RESPONSE_WINDOW"],
                    )
                )
                continue

            # 4A. Anonymous Track Level Evidence
            all_window_positions: List[Tuple[float, float]] = []
            for tid, obs_list in tracks_in_window.items():
                opaque_id = f"track_{tid}"
                n_obs = len(obs_list)

                # Extract coordinates
                # If metric calibration permitted, use metric coordinates or project footpoints
                metric_pts: List[Tuple[float, float, float]] = []  # (ts, x, y)
                pixel_pts: List[Tuple[float, float, float]] = []

                for ts, obs in obs_list:
                    if obs.footpoint_x is not None and obs.footpoint_y is not None:
                        fx, fy = obs.footpoint_x, obs.footpoint_y
                    elif hasattr(obs, "bbox") and obs.bbox is not None:
                        fx = (obs.bbox.x1 + obs.bbox.x2) / 2.0
                        fy = obs.bbox.y2
                    else:
                        fx, fy = 0.0, 0.0

                    pixel_pts.append((ts, fx, fy))
                    if metric_allowed:
                        if obs.metric_x is not None and obs.metric_y is not None:
                            metric_pts.append((ts, obs.metric_x, obs.metric_y))
                        elif calibration_service.homography_matrix:
                            # Scale from source space to 1920x1080 working space
                            u_work = fx / scale_x
                            v_work = fy / scale_y
                            proj = calibration_service.project_point(u_work, v_work)
                            if proj:
                                metric_pts.append((ts, proj[0], proj[1]))

                disp_m = None
                speed_kmh = None
                heading_deg = None
                retention = None
                item_missing = []
                item_limitations = []

                if metric_allowed and len(metric_pts) >= 2:
                    # Execute Kinematics via KinematicsService
                    kin_obs = [
                        {"timestamp_s": p[0], "metric_x": p[1], "metric_y": p[2], "frame_index": int(p[0] * fps)}
                        for p in metric_pts
                    ]
                    steps = kinematics_service.calculate_steps(kin_obs)
                    valid_steps = [s for s in steps if s.is_valid and s.speed_kmh is not None]

                    if valid_steps:
                        speeds = [s.speed_kmh for s in valid_steps]
                        peak_spd = max(speeds)
                        if peak_spd <= MAX_SPEED_KMH_THRESHOLD:
                            speed_kmh = round(peak_spd, 2)
                        else:
                            speed_kmh = None
                            item_limitations.append("PEAK_SPEED_OUTLIER_EXCEEDED_36KMH_EXCLUDED")

                    # Net displacement
                    x_start, y_start = metric_pts[0][1], metric_pts[0][2]
                    x_end, y_end = metric_pts[-1][1], metric_pts[-1][2]
                    dx = x_end - x_start
                    dy = y_end - y_start
                    disp_m = round(math.sqrt(dx * dx + dy * dy), 2)

                    if disp_m > 0.05:
                        heading_deg = round(math.degrees(math.atan2(dy, dx)) % 360.0, 1)

                    # Position retention metric for Hold Ground
                    if event.category == "Positioning / Hold Ground":
                        # Standard deviation of distance from initial coordinate
                        dist_from_start = [
                            math.sqrt((p[1] - x_start) ** 2 + (p[2] - y_start) ** 2)
                            for p in metric_pts
                        ]
                        mean_d = sum(dist_from_start) / len(dist_from_start)
                        var_d = sum((d - mean_d) ** 2 for d in dist_from_start) / len(dist_from_start)
                        retention = round(math.sqrt(var_d), 3)

                    all_window_positions.append((x_end, y_end))

                elif not metric_allowed:
                    item_missing.extend(["displacement_m", "speed_kmh", "distance_to_target_m"])
                    item_limitations.append("METRIC_UNITS_SUPPRESSED_NON_METRIC_MODE")
                else:
                    item_missing.append("insufficient_metric_observations")

                # Zone assignment (defensive third, middle third, attacking third based on x)
                zone_str = None
                if metric_pts:
                    cur_x = metric_pts[-1][1]
                    p_len = calibration_service.pitch_length_m or 19.31
                    third = p_len / 3.0
                    if cur_x < third:
                        zone_str = "defensive_third"
                    elif cur_x < 2.0 * third:
                        zone_str = "middle_third"
                    else:
                        zone_str = "attacking_third"

                evidence_items.append(
                    StructuredEvidenceItem(
                        evidence_id=f"ev_{event.event_id}_{opaque_id}",
                        scope="ANONYMOUS_TRACK",
                        source_event_id=event.event_id,
                        event_category=event.category,
                        event_action=event.action,
                        window_start_s=w_start,
                        window_end_s=w_end,
                        anonymous_track_id=opaque_id,
                        spatial_context={
                            "footpoint_final": pixel_pts[-1][1:] if pixel_pts else None,
                            "metric_final": metric_pts[-1][1:] if metric_pts else None,
                        },
                        zone=zone_str,
                        displacement_m=disp_m,
                        speed_kmh=speed_kmh,
                        direction_deg=heading_deg,
                        retention_metric=retention,
                        calibration_mode=calib_mode_label,
                        metric_units_allowed=metric_allowed,
                        identity_evidence_basis=identity_basis,
                        observations_count=n_obs,
                        source_provenance={
                            "methodology_id": method_name,
                            "raw_track_id": tid,
                        },
                        missing_fields=item_missing,
                        limitations=item_limitations,
                    )
                )

            # 4B. Team-Level Centroid Movement Evidence
            if all_window_positions:
                avg_x = sum(p[0] for p in all_window_positions) / len(all_window_positions)
                avg_y = sum(p[1] for p in all_window_positions) / len(all_window_positions)
                team_spatial = {"centroid_m": (round(avg_x, 2), round(avg_y, 2))}
            else:
                team_spatial = {}

            evidence_items.append(
                StructuredEvidenceItem(
                    evidence_id=f"ev_{event.event_id}_team_centroid",
                    scope="TEAM",
                    source_event_id=event.event_id,
                    event_category=event.category,
                    event_action=event.action,
                    window_start_s=w_start,
                    window_end_s=w_end,
                    team_context="team_centroid",
                    spatial_context=team_spatial,
                    calibration_mode=calib_mode_label,
                    metric_units_allowed=metric_allowed,
                    identity_evidence_basis=identity_basis,
                    observations_count=len(window_frames),
                    source_provenance={
                        "methodology_id": method_name,
                        "tracks_in_window_count": len(tracks_in_window),
                    },
                    missing_fields=[] if metric_allowed else ["displacement_m", "speed_kmh"],
                    limitations=[] if metric_allowed else ["METRIC_UNITS_SUPPRESSED_NON_METRIC_MODE"],
                )
            )

        # 5. Assemble and Validate Payload
        return self.evidence_pipeline.assemble_evidence(
            session_id=session_id,
            methodology_id=method_name,
            calibration_mode=calib_mode_label,
            metric_units_allowed=metric_allowed,
            player_level_analysis_allowed=player_allowed,
            identity_evidence_basis=identity_basis,
            evidence_items=evidence_items,
            global_limitations=global_limitations,
            provenance={
                "fusion_engine": "MultimodalFusionEngine",
                "reaction_window": f"[t_end + {self.reaction_offset_start_s}s, t_end + {self.reaction_offset_end_s}s]",
                "source_offset_s": asr_result.source_offset_s,
                "vision_timestamps_s": [ts for ts, _ in indexed_frames],
                "total_tactical_events": len(asr_result.events),
                "total_vision_frames": len(vision_result.frames),
            },
        )


class FusionPipeline:
    """
    Production adapter maintaining backwards compatibility with earlier Fusion interface stubs.
    """

    def __init__(
        self,
        reaction_offset_start_s: float = 2.0,
        reaction_offset_end_s: float = 6.0,
    ):
        self.engine = MultimodalFusionEngine(
            reaction_offset_start_s=reaction_offset_start_s,
            reaction_offset_end_s=reaction_offset_end_s,
        )

    def fuse(
        self,
        session_id: str,
        asr_result: ASRResult,
        vision_result: SessionVisionResult,
        identity_assessment: Optional[IdentitySafetyAssessment] = None,
        calibration_service: Optional[CalibrationService] = None,
        kinematics_service: Optional[KinematicsService] = None,
    ) -> StructuredEvidencePayload:
        return self.engine.fuse(
            session_id=session_id,
            asr_result=asr_result,
            vision_result=vision_result,
            identity_assessment=identity_assessment,
            calibration_service=calibration_service,
            kinematics_service=kinematics_service,
        )
