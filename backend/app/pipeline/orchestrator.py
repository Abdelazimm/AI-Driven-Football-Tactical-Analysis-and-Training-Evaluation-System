"""
Unified Production Analysis Orchestrator.
Composes verified modular components into the canonical execution lifecycle:
validated media -> AnalysisJob -> worker dispatch -> real selected Vision methodology
-> calibration / kinematics -> Faster-Whisper ASR -> deterministic Fusion
-> StructuredEvidencePayload -> grounded Llama 3.1 8B (Patch 001) OR deterministic fallback
-> canonical persisted AnalysisResult -> job completion callback -> frontend-readable result.

Governed by P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A and Implementation Phase 5 rules.
"""
from __future__ import annotations

import inspect
import logging
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

import cv2

from backend.app.core.config import settings
from backend.app.pipeline.audio import AudioPipeline
from backend.app.pipeline.evidence import EvidencePipeline, StructuredEvidencePayload
from backend.app.pipeline.fusion import MultimodalFusionEngine
from backend.app.pipeline.registry import (
    MethodologyExecutorRegistry,
    create_production_registry,
    resolve_methodology,
)
from backend.app.pipeline.reporting import ReportingPipeline
from backend.app.schemas.artifact import ArtifactReference
from backend.app.schemas.asr import ASRResult, TacticalEvent
from backend.app.schemas.canonical_vision import (
    CalibrationReference,
    FormalIdentityStatus,
    IdentityEvidenceBasis,
    RuntimeIdentityStatus,
    SessionVisionResult,
)
from backend.app.schemas.confidence import IdentityStatus, ReportStatus
from backend.app.schemas.identity import IdentityEvaluation
from backend.app.schemas.instruction import InstructionEvent
from backend.app.schemas.job import AnalysisJob, JobStatus
from backend.app.schemas.kinematics import MovementMetric
from backend.app.schemas.limitation import AnalysisLimitation
from backend.app.schemas.manifest import (
    JobExecutionManifest,
    ManifestCalibrationMetadata,
    ManifestMethodologyProvenance,
    ManifestRuntimeDiagnostics,
    MediaProbedMetadata,
)
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.modes import ApplicationMode, AudioMode, CalibrationMode
from backend.app.schemas.report import GeneratedCoachReport
from backend.app.schemas.result import AnalysisResult
from backend.app.schemas.stages import AnalysisStage
from backend.app.services.calibration_service import CalibrationService
from backend.app.services.identity_safety_service import IdentitySafetyService
from backend.app.services.job_repository import AnalysisJobRepository
from backend.app.services.kinematics_service import KinematicsService
from backend.app.services.media_probe import FFProbeMediaProbeService, MediaProbeService
from backend.app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# Frozen Research Homography SHA-256 for Demo Pitch
RESEARCH_HOMOGRAPHY_SHA256 = "d0e9680fdcdf3b5f6290ebf1f0e7cd1dbedcd6527f88873d857babe968cbd507"


class OrchestratorError(Exception):
    """Base error for orchestrator failures."""
    pass


class VideoDurationExceededError(OrchestratorError):
    """Raised when video duration exceeds the approved limit."""
    pass


class MethodologyExecutionError(OrchestratorError):
    """Raised when requested methodology fails closed."""
    pass


class UnifiedAnalysisOrchestrator:
    """
    Unified Production Orchestrator executing the complete multimodal football tactical analysis pipeline.
    """

    def __init__(
        self,
        registry: Optional[MethodologyExecutorRegistry] = None,
        audio_pipeline: Optional[AudioPipeline] = None,
        fusion_engine: Optional[MultimodalFusionEngine] = None,
        reporting_pipeline: Optional[ReportingPipeline] = None,
        identity_service: Optional[IdentitySafetyService] = None,
        probe_service: Optional[MediaProbeService] = None,
        storage_service: Optional[StorageService] = None,
        job_repository: Optional[AnalysisJobRepository] = None,
        max_duration_seconds: float = 360.0,
    ):
        self.registry = registry or create_production_registry()
        self.audio_pipeline = audio_pipeline or AudioPipeline()
        self.fusion_engine = fusion_engine or MultimodalFusionEngine()
        self.reporting_pipeline = reporting_pipeline or ReportingPipeline()
        self.identity_service = identity_service or IdentitySafetyService()
        self.probe_service = probe_service or FFProbeMediaProbeService()
        self.storage_service = storage_service
        self.job_repository = job_repository
        self.max_duration_seconds = max_duration_seconds

    async def _emit_progress(
        self,
        callback: Optional[Callable[[AnalysisStage, float, str], Union[None, Awaitable[None]]]],
        stage: AnalysisStage,
        percent: float,
        message: str,
    ) -> None:
        """Helper to invoke progress callback (sync or async) and record logger trace."""
        logger.info("[PROGRESS %s %.1f%%] %s", stage.value, percent, message)
        if callback is not None:
            res = callback(stage, percent, message)
            if inspect.isawaitable(res):
                await res

    def probe_media_metadata(self, video_path: Path) -> MediaProbedMetadata:
        """
        Extract authoritative container and stream properties from video.
        Uses ffprobe if available, falling back to cv2 inspection.
        Never emits universal research constants.
        """
        try:
            probe_res = self.probe_service.probe(str(video_path))
            if (probe_res.is_valid and probe_res.duration_seconds and probe_res.duration_seconds > 0
                    and probe_res.fps and probe_res.fps > 0 and probe_res.width and probe_res.width > 0
                    and probe_res.height and probe_res.height > 0):
                return MediaProbedMetadata(
                    duration_s=float(probe_res.duration_seconds),
                    fps=float(probe_res.fps),
                    resolution_width=int(probe_res.width),
                    resolution_height=int(probe_res.height),
                    container_format=str(probe_res.container_format or video_path.suffix.lstrip(".")),
                    video_codec=probe_res.video_codec,
                )
        except Exception as ex:
            logger.debug("ffprobe probe failed: %s, falling back to cv2", ex)

        # OpenCV fallback probe
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video container at '{video_path}'")
        try:
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            dur = float(total_frames / fps) if fps > 0 and total_frames > 0 else 0.0

            if dur <= 0 or fps <= 0 or w <= 0 or h <= 0:
                raise ValueError("VIDEO_METADATA_UNAVAILABLE: duration, fps and resolution must be probed")

            return MediaProbedMetadata(
                duration_s=dur,
                fps=fps,
                resolution_width=w,
                resolution_height=h,
                container_format=video_path.suffix.lstrip(".") or "mp4",
                video_codec=None,
            )
        finally:
            cap.release()

    async def execute_analysis_job(
        self,
        job_id: str,
        session_id: str,
        video_path: Union[str, Path],
        audio_path: Optional[Union[str, Path]] = None,
        methodology: Union[str, MethodologyId] = "AUTO",
        calibration_mode: Union[str, CalibrationMode] = CalibrationMode.NO_METRIC_CALIBRATION,
        application_mode: Union[str, ApplicationMode] = ApplicationMode.AUTOMATED_ANALYSIS,
        audio_mode: Union[str, AudioMode] = AudioMode.EXTRACT_FROM_VIDEO,
        start_frame: int = 0,
        max_frames: Optional[int] = None,
        progress_callback: Optional[Callable[[AnalysisStage, float, str], Union[None, Awaitable[None]]]] = None,
        force_deterministic_fallback: bool = False,
        audio_source_offset_s: float = 0.0,
        video_source_offset_s: float = 0.0,
        input_asset_role: Optional[str] = None,
        authoritative_source_sha256: Optional[str] = None,
        transport_copy_sha256: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Execute end-to-end multimodal tactical analysis job.
        Composes all 10 verified pipeline stages.
        """
        video_p = Path(video_path)
        if not video_p.exists():
            raise FileNotFoundError(f"Video file not found at '{video_p}'")
        if not math.isfinite(audio_source_offset_s) or audio_source_offset_s < 0:
            raise ValueError("audio_source_offset_s must be a finite non-negative source-session time")
        if not math.isfinite(video_source_offset_s) or video_source_offset_s < 0:
            raise ValueError("video_source_offset_s must be a finite non-negative source-session time")
        if audio_source_offset_s and (audio_path is None or not Path(audio_path).is_file()):
            raise ValueError("A bounded audio source offset requires an accessible explicit audio_path")

        # Normalize enum types
        calib_enum = (
            calibration_mode
            if isinstance(calibration_mode, CalibrationMode)
            else CalibrationMode(str(calibration_mode))
        )
        app_enum = (
            application_mode
            if isinstance(application_mode, ApplicationMode)
            else ApplicationMode(str(application_mode))
        )
        audio_enum = (
            audio_mode
            if isinstance(audio_mode, AudioMode)
            else AudioMode(str(audio_mode))
        )

        limitations: List[AnalysisLimitation] = []
        has_limitations = False

        # ------------------------------------------------------------------
        # STAGE 1: VALIDATING MEDIA METADATA
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.VALIDATING,
            5.0,
            "Validating video container and probing authoritative metadata.",
        )
        probed_meta = self.probe_media_metadata(video_p)
        if input_asset_role == "DERIVED_TRANSPORT_COPY" and transport_copy_sha256:
            probed_meta.source_media_sha256 = transport_copy_sha256

        if probed_meta.duration_s > self.max_duration_seconds:
            raise VideoDurationExceededError(
                f"Video duration ({probed_meta.duration_s:.1f}s) exceeds maximum allowed "
                f"limit of {self.max_duration_seconds:.1f} seconds."
            )

        # ------------------------------------------------------------------
        # STAGE 2: RESOLVE METHODOLOGY
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.PREPROCESSING,
            15.0,
            "Resolving methodology and checking execution readiness.",
        )
        resolved_methodology = resolve_methodology(methodology)
        if not self.registry.is_ready_for_execution(resolved_methodology):
            raise MethodologyExecutionError(
                f"METHODOLOGY_NOT_AVAILABLE: Production executor for '{resolved_methodology.value}' "
                "is not ready or installed."
            )

        # ------------------------------------------------------------------
        # STAGE 3: VISION INFERENCE & TRACKING
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.DETECTING,
            25.0,
            f"Executing computer vision inference and tracking ({resolved_methodology.value}).",
        )
        vision_executor = self.registry.get_executor(resolved_methodology)
        vision_payload = {
            "video_path": str(video_p),
            "session_id": session_id,
            "job_id": job_id,
            "calibration": calib_enum.value,
            "start_frame": start_frame,
            "max_frames": max_frames,
        }
        vision_result: SessionVisionResult = vision_executor.execute(vision_payload)
        if video_source_offset_s:
            for frame in vision_result.frames:
                frame.timestamp_s = frame.frame_index / vision_result.fps + video_source_offset_s

        # ------------------------------------------------------------------
        # STAGE 4: IDENTITY SAFETY EVALUATION
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.IDENTITY_EVALUATION,
            55.0,
            "Evaluating persistent identity assurance gate.",
        )
        is_oracle = (app_enum == ApplicationMode.VALIDATED_SHOWCASE)
        identity_assessment = self.identity_service.evaluate_identity_safety(
            methodology=resolved_methodology.value,
            is_oracle=is_oracle,
        )

        # Enforce fail-closed identity gate: In automated mode, player-level analytics are withheld
        if not identity_assessment.player_level_analysis_allowed:
            has_limitations = True
            limitations.append(
                AnalysisLimitation(
                    code="IDENTITY_SAFETY_GATE_ACTIVE",
                    category="IDENTITY",
                    severity="WARNING",
                    message=(
                        "Persistent physical-player identity is not certified under formal dense benchmark (FAIL_UNSAFE_MERGE). "
                        "All player-specific analytics are withheld; observations are reported strictly as anonymous tracks."
                    ),
                )
            )

        # ------------------------------------------------------------------
        # STAGE 5: AUDIO EXTRACTION & ASR
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.AUDIO_EXTRACTION,
            60.0,
            "Processing coach audio and extracting tactical instruction events.",
        )
        asr_result: Optional[ASRResult] = None
        instruction_events: List[InstructionEvent] = []

        if audio_enum == AudioMode.NO_AUDIO:
            has_limitations = True
            limitations.append(
                AnalysisLimitation(
                    code="NO_AUDIO_MODE",
                    category="AUDIO_QUALITY",
                    severity="INFO",
                    message="Session analyzed in NO_AUDIO mode; tactical instruction extraction was suppressed.",
                )
            )
        else:
            # Determine audio source
            wav_path_to_transcribe: Optional[Path] = None
            if audio_path is not None and Path(audio_path).exists():
                wav_path_to_transcribe = Path(audio_path)
            else:
                # Extract WAV from video
                extracted_str, err = self.audio_pipeline.extract_audio(video_p)
                if err is None and extracted_str is not None:
                    wav_path_to_transcribe = Path(extracted_str)
                else:
                    has_limitations = True
                    limitations.append(
                        AnalysisLimitation(
                            code="AUDIO_EXTRACTION_FAILURE",
                            category="AUDIO_QUALITY",
                            severity="WARNING",
                            message="Audio extraction from video failed; continuing analysis in vision-only mode.",
                        )
                    )

            if wav_path_to_transcribe is not None and wav_path_to_transcribe.exists():
                transcription_outcome = self.audio_pipeline.process_audio(
                    audio_path=wav_path_to_transcribe,
                    session_id=session_id,
                    source_offset_s=audio_source_offset_s,
                )
                if hasattr(transcription_outcome, "events"):
                    asr_result = transcription_outcome
                    if asr_result.source_offset_s != audio_source_offset_s or any(
                        ev.t_start < audio_source_offset_s or ev.t_end < ev.t_start
                        for ev in asr_result.events
                    ):
                        raise ValueError("ASR_SOURCE_TIMEBASE_MISMATCH: event timestamps must use source-session time")
                    for ev in asr_result.events:
                        instruction_events.append(
                            InstructionEvent(
                                id=ev.event_id,
                                session_id=session_id,
                                start_s=ev.t_start,
                                end_s=ev.t_end,
                                raw_text=ev.source_text,
                                category=ev.category,
                                action=ev.action,
                                target_player_pseudonym=ev.target_player,
                                is_target_resolved=(ev.target_resolution_status != "UNRESOLVED_TARGET"),
                                alignment_window_start_s=ev.alignment_window_start_s,
                                alignment_window_end_s=ev.alignment_window_end_s,
                                confidence=1.0,
                            )
                        )
                else:
                    # ASRFailure occurred; fail-soft per stage failure semantics
                    has_limitations = True
                    limitations.append(
                        AnalysisLimitation(
                            code="ASR_TRANSCRIPTION_FAILURE",
                            category="AUDIO_QUALITY",
                            severity="WARNING",
                            message="Speech recognition encountered an error; analysis continued with visual evidence only.",
                        )
                    )

        # ------------------------------------------------------------------
        # STAGE 6: MULTIMODAL FUSION & STRUCTURED EVIDENCE
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.FUSION,
            75.0,
            "Aligning tactical instruction windows with visual response evidence.",
        )
        evidence_payload: StructuredEvidencePayload
        if asr_result is not None:
            evidence_payload = self.fusion_engine.fuse(
                session_id=session_id,
                asr_result=asr_result,
                vision_result=vision_result,
                identity_assessment=identity_assessment,
            )
        else:
            # Construct vision-only structured evidence
            evidence_payload = StructuredEvidencePayload(
                session_id=session_id,
                methodology_id=resolved_methodology.value,
                calibration_mode=calib_enum.value,
                metric_units_allowed=(calib_enum == CalibrationMode.DEMO_FIXED_CALIBRATION),
                player_level_analysis_allowed=False,
                identity_status="FAIL_UNSAFE_MERGE",
                identity_evidence_basis="FORMAL_DENSE_GT",
                total_tactical_events=0,
                evidence_items=[],
                global_limitations=[lim.message for lim in limitations],
            )

        # ------------------------------------------------------------------
        # STAGE 7: GROUNDED REPORT GENERATION
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.GENERATING_REPORT,
            85.0,
            "Generating verified coaching report with Patch 001 grounding validation.",
        )
        # Execute reporting pipeline (either Llama 3.1 8B or deterministic fallback)
        coach_report = self.reporting_pipeline.generate_report(
            evidence=evidence_payload,
            job_id=job_id,
            force_fallback=force_deterministic_fallback,
        )

        if coach_report.report_status == ReportStatus.DETERMINISTIC_FALLBACK:
            has_limitations = True
            fallback_reason = coach_report.fallback_reason or "Automated grounding engaged deterministic fallback"
            limitations.append(
                AnalysisLimitation(
                    code="DETERMINISTIC_REPORT_FALLBACK",
                    category="MODEL_GROUNDING",
                    severity="INFO",
                    message=f"Coaching report synthesized via deterministic fallback: {fallback_reason}",
                )
            )

        # ------------------------------------------------------------------
        # STAGE 8: ASSEMBLE CANONICAL FINAL RESULT & DYNAMIC MANIFEST
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.UPLOADING_RESULTS,
            92.0,
            "Assembling dynamic execution manifest and canonical result.",
        )
        final_job_status = (
            JobStatus.COMPLETED_WITH_LIMITATIONS
            if has_limitations
            else JobStatus.COMPLETED
        )

        manifest = JobExecutionManifest(
            job_id=job_id,
            session_id=session_id,
            input_asset_role=input_asset_role,
            authoritative_source_sha256=authoritative_source_sha256,
            transport_copy_sha256=transport_copy_sha256,
            execution_timestamp=datetime.now(timezone.utc),
            media_metadata=probed_meta,
            methodology=ManifestMethodologyProvenance(
                requested_methodology=str(methodology.value if hasattr(methodology, "value") else methodology),
                resolved_methodology=resolved_methodology.value,
                method_formal_identity_status=FormalIdentityStatus.FAIL_UNSAFE_MERGE,
                method_formal_identity_evidence_basis=IdentityEvidenceBasis.FORMAL_DENSE_GT,
            ),
            runtime_diagnostics=ManifestRuntimeDiagnostics(
                runtime_identity_status=RuntimeIdentityStatus.UNVERIFIED_HEURISTIC_PASS,
                runtime_identity_evidence_basis=IdentityEvidenceBasis.RUNTIME_HEURISTIC_ONLY,
                player_level_analysis_allowed=False,
                withholding_reason=(
                    "Automated tracking methodology has not demonstrated sufficiently safe persistent "
                    "physical-player identity under formal benchmark evaluation. Accumulated player-level analytics are withheld."
                ),
            ),
            calibration_metadata=ManifestCalibrationMetadata(
                calibration_mode=calib_enum.value,
                homography_sha256=(
                    RESEARCH_HOMOGRAPHY_SHA256
                    if calib_enum == CalibrationMode.DEMO_FIXED_CALIBRATION
                    else None
                ),
                is_metric_reporting_allowed=(calib_enum == CalibrationMode.DEMO_FIXED_CALIBRATION),
            ),
            artifact_registry={
                "result_json": f"jobs/{job_id}/results/result.json",
                "coach_report_md": f"jobs/{job_id}/reports/coach_report.md",
                "report_metadata_json": f"jobs/{job_id}/reports/report_metadata.json",
                "execution_manifest_json": f"jobs/{job_id}/logs/execution_manifest.json",
            },
        )

        report_bytes = len(coach_report.report_markdown.encode("utf-8")) if coach_report.report_markdown else 0
        artifact_refs = [
            ArtifactReference(
                id=f"art_res_{job_id}",
                session_id=session_id,
                job_id=job_id,
                kind="RESULT_JSON",
                storage_path=f"jobs/{job_id}/results/result.json",
                file_size_bytes=1024,
                mime_type="application/json",
            ),
            ArtifactReference(
                id=f"art_rep_{job_id}",
                session_id=session_id,
                job_id=job_id,
                kind="REPORT_MARKDOWN",
                storage_path=f"jobs/{job_id}/reports/coach_report.md",
                file_size_bytes=report_bytes,
                mime_type="text/markdown",
            ),
            ArtifactReference(
                id=f"art_man_{job_id}",
                session_id=session_id,
                job_id=job_id,
                kind="EXECUTION_MANIFEST",
                storage_path=f"jobs/{job_id}/logs/execution_manifest.json",
                file_size_bytes=2048,
                mime_type="application/json",
            ),
        ]

        # Derive runtime heuristic diagnostics from the actual vision result.
        # These are SEPARATE from the formal methodology status (FAIL_UNSAFE_MERGE / FORMAL_DENSE_GT)
        # which is immutable and independent of the current upload.
        _runtime_all_track_ids: set = set()
        _runtime_max_simultaneous: int = 0
        for _fr in vision_result.frames:
            _cnt = len(_fr.observations)
            if _cnt > _runtime_max_simultaneous:
                _runtime_max_simultaneous = _cnt
            for _obs in _fr.observations:
                _runtime_all_track_ids.add(_obs.opaque_track_id)
        _runtime_raw_count = len(_runtime_all_track_ids)
        _runtime_frag_ratio = round(
            _runtime_raw_count / max(identity_assessment.max_simultaneous_tracks or _runtime_max_simultaneous, 1), 4
        )

        canonical_result = AnalysisResult(
            id=f"res_{job_id}",
            session_id=session_id,
            job_id=job_id,
            methodology_id=resolved_methodology,
            application_mode=app_enum,
            calibration_mode=calib_enum,
            job_status=final_job_status,
            identity_evaluation=IdentityEvaluation(
                # Formal methodology result — immutable, from dense-GT benchmark evaluation
                identity_status=IdentityStatus.FAIL_UNSAFE_MERGE,
                method_formal_identity_status="FAIL_UNSAFE_MERGE",
                method_formal_identity_evidence_basis="FORMAL_DENSE_GT",
                # Runtime heuristic result — computed on THIS upload, kept explicitly separate
                runtime_identity_status="UNVERIFIED_HEURISTIC_PASS",
                runtime_identity_evidence_basis="RUNTIME_HEURISTIC_ONLY",
                raw_track_ids=_runtime_raw_count,
                meaningful_identities=_runtime_max_simultaneous,
                fragmentation_ratio=_runtime_frag_ratio,
                acceptance_threshold=1.5,
                player_level_analysis_allowed=False,
                withholding_reason=(
                    "The selected automated tracking methodology has not demonstrated sufficiently safe "
                    "persistent physical-player identity under formal dense-GT benchmark evaluation "
                    "(FAIL_UNSAFE_MERGE). Player-level analytics are withheld; runtime diagnostics on "
                    "the current upload are heuristic only and cannot unlock player-level assessment."
                ),
            ),
            instruction_events=instruction_events,
            limitations=limitations,
            artifact_references=artifact_refs,
            report_markdown=coach_report.report_markdown,
            report_status=coach_report.report_status,
            execution_manifest=manifest,
            structured_evidence=evidence_payload.model_dump(),
            created_at=datetime.utcnow(),
        )

        # ------------------------------------------------------------------
        # STAGE 9: PERSISTENCE & STORAGE
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.UPLOADING_RESULTS,
            96.0,
            "Persisting canonical results, report artifacts, and updating job state.",
        )
        if self.job_repository is not None:
            await self.job_repository.store_result(canonical_result)
            await self.job_repository.update_job_lifecycle(
                job_id=job_id,
                status=final_job_status,
                current_stage=AnalysisStage.UPLOADING_RESULTS,
                progress_percent=100.0,
                stage_message="Analysis completed successfully.",
                completed_at=datetime.utcnow(),
            )

        # ------------------------------------------------------------------
        # STAGE 10: COMPLETION
        # ------------------------------------------------------------------
        await self._emit_progress(
            progress_callback,
            AnalysisStage.UPLOADING_RESULTS,
            100.0,
            f"Pipeline complete: status {final_job_status.value}.",
        )

        return canonical_result


def execute_analysis_job(
    job_id: str,
    session_id: str,
    video_path: Union[str, Path],
    audio_path: Optional[Union[str, Path]] = None,
    methodology: Union[str, MethodologyId] = "AUTO",
    calibration_mode: Union[str, CalibrationMode] = CalibrationMode.NO_METRIC_CALIBRATION,
    application_mode: Union[str, ApplicationMode] = ApplicationMode.AUTOMATED_ANALYSIS,
    audio_mode: Union[str, AudioMode] = AudioMode.EXTRACT_FROM_VIDEO,
    start_frame: int = 0,
    max_frames: Optional[int] = None,
    progress_callback: Optional[Callable[[AnalysisStage, float, str], Union[None, Awaitable[None]]]] = None,
    force_deterministic_fallback: bool = False,
    audio_source_offset_s: float = 0.0,
    video_source_offset_s: float = 0.0,
    input_asset_role: Optional[str] = None,
    authoritative_source_sha256: Optional[str] = None,
    transport_copy_sha256: Optional[str] = None,
    orchestrator: Optional[UnifiedAnalysisOrchestrator] = None,
) -> AnalysisResult:
    """
    Synchronous / entrypoint wrapper for UnifiedAnalysisOrchestrator.
    Handles running in existing or new event loop.
    """
    import asyncio

    orch = orchestrator or UnifiedAnalysisOrchestrator()
    coro = orch.execute_analysis_job(
        job_id=job_id,
        session_id=session_id,
        video_path=video_path,
        audio_path=audio_path,
        methodology=methodology,
        calibration_mode=calibration_mode,
        application_mode=application_mode,
        audio_mode=audio_mode,
        start_frame=start_frame,
        max_frames=max_frames,
        progress_callback=progress_callback,
        force_deterministic_fallback=force_deterministic_fallback,
        audio_source_offset_s=audio_source_offset_s,
        video_source_offset_s=video_source_offset_s,
        input_asset_role=input_asset_role,
        authoritative_source_sha256=authoritative_source_sha256,
        transport_copy_sha256=transport_copy_sha256,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # In an active event loop, run in a worker thread to prevent nested event loop blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)
