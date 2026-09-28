import pytest
from datetime import datetime
from backend.app.schemas import (
    ApplicationMode,
    CalibrationMode,
    AnalysisStage,
    JobStatus,
    MetricConfidence,
    IdentityStatus,
    ReportStatus,
    Session,
    VideoMetadata,
    Calibration,
    AnalysisJob,
    Detection,
    TrackObservation,
    IdentityEvaluation,
    WordTimestamp,
    TranscriptSegment,
    InstructionEvent,
    MovementMetric,
    AnalysisLimitation,
    ArtifactReference,
    AnalysisResult,
    ShowcaseUseCase,
    MethodologyId,
    MethodologyMetadata,
    EvaluationMetrics,
    DetectionEvaluationMetrics,
    IdentityTrackingEvaluationMetrics,
    GroundTruthTrackingMetrics,
    EngineeringMetrics,
)


def test_modes_and_stages_enums():
    assert ApplicationMode.AUTOMATED_ANALYSIS == "AUTOMATED_ANALYSIS"
    assert ApplicationMode.VALIDATED_SHOWCASE == "VALIDATED_SHOWCASE"
    assert ApplicationMode.ANALYSIS_WITHOUT_METRICS == "ANALYSIS_WITHOUT_METRICS"

    assert CalibrationMode.DEMO_FIXED_CALIBRATION == "DEMO_FIXED_CALIBRATION"
    assert CalibrationMode.CUSTOM_PITCH_CALIBRATION == "CUSTOM_PITCH_CALIBRATION"
    assert CalibrationMode.NO_METRIC_CALIBRATION == "NO_METRIC_CALIBRATION"

    assert AnalysisStage.UPLOADED == "UPLOADED"
    assert AnalysisStage.UPLOADING_RESULTS == "UPLOADING_RESULTS"
    assert len(AnalysisStage) == 16

    assert JobStatus.QUEUED == "QUEUED"
    assert JobStatus.PROCESSING == "PROCESSING"
    assert JobStatus.COMPLETED == "COMPLETED"
    assert JobStatus.COMPLETED_WITH_LIMITATIONS == "COMPLETED_WITH_LIMITATIONS"
    assert JobStatus.FAILED == "FAILED"
    assert len(JobStatus) == 5


def test_identity_safety_contract_failure_withholding():
    """
    Test scientific safety contract:
    When identity fails (fragmentation ratio > 1.5), player_level_analysis_allowed must be false,
    and withholding reason must be captured.
    """
    identity_eval = IdentityEvaluation(
        identity_status=IdentityStatus.FAIL_HIGH_FRAGMENTATION,
        player_level_analysis_allowed=False,
        withholding_reason="Persistent player identity did not meet the required reliability threshold.",
        raw_track_ids=115,
        meaningful_identities=37,
        fragmentation_ratio=6.1667,
        acceptance_threshold=1.5,
    )
    assert identity_eval.identity_status == IdentityStatus.FAIL_HIGH_FRAGMENTATION
    assert identity_eval.player_level_analysis_allowed is False
    assert identity_eval.fragmentation_ratio > identity_eval.acceptance_threshold
    assert "reliability threshold" in identity_eval.withholding_reason


def test_metric_confidence_contract():
    """
    Test metric confidence model with calibrated and uncalibrated values.
    """
    calibrated_speed = MovementMetric(
        name="max_speed",
        value=18.4,
        unit="km/h",
        confidence=MetricConfidence.MEASURED_METRIC_ESTIMATE,
        calibration_id="cal_3v3_demo",
        display_value="18.4 km/h",
        limitations=["Subject to 7-frame median smoothing and camera perspective sensitivity."],
    )
    assert calibrated_speed.value == 18.4
    assert calibrated_speed.unit == "km/h"

    uncalibrated_metric = MovementMetric(
        name="total_distance",
        value=None,
        unit="m",
        confidence=MetricConfidence.NO_METRIC_CALIBRATION,
        calibration_id=None,
        display_value="Withheld (Uncalibrated)",
        limitations=["Video ingested without pitch calibration."],
    )
    assert uncalibrated_metric.value is None
    assert uncalibrated_metric.confidence == MetricConfidence.NO_METRIC_CALIBRATION


def test_video_metadata_constraints():
    meta = VideoMetadata(
        duration_seconds=240.5,
        width=3840,
        height=2160,
        fps=59.972,
        total_frames=14424,
        codec="h264",
        format="mp4",
        file_size_bytes=104857600,
        has_audio=True,
    )
    assert meta.duration_seconds <= 300.0
    assert meta.fps == 59.972


def test_analysis_result_with_limitations():
    res = AnalysisResult(
        id="res_001",
        session_id="sess_001",
        job_id="job_001",
        application_mode=ApplicationMode.AUTOMATED_ANALYSIS,
        job_status=JobStatus.COMPLETED_WITH_LIMITATIONS,
        identity_evaluation=IdentityEvaluation(
            identity_status=IdentityStatus.FAIL_HIGH_FRAGMENTATION,
            player_level_analysis_allowed=False,
            withholding_reason="High fragmentation ratio (6.1667 > 1.5).",
            raw_track_ids=115,
            meaningful_identities=37,
            fragmentation_ratio=6.1667,
            acceptance_threshold=1.5,
        ),
        metrics={},
        instruction_events=[],
        limitations=[
            AnalysisLimitation(
                code="LIMITATION_IDENTITY_FRAGMENTATION",
                category="IDENTITY",
                severity="WARNING",
                message="Persistent player identities could not be resolved reliably across the session.",
                technical_details="Raw track IDs: 115, meaningful identities: 37, ratio: 6.1667.",
            )
        ],
        report_status="DETERMINISTIC_FALLBACK",
    )
    assert res.job_status == JobStatus.COMPLETED_WITH_LIMITATIONS
    assert res.identity_evaluation.player_level_analysis_allowed is False
    assert len(res.limitations) == 1


def test_methodology_id_enum():
    assert MethodologyId.METHOD_1_YOLO11_BOTSORT == "METHOD_1_YOLO11_BOTSORT"
    assert MethodologyId.METHOD_2_RFDETR_GTATRACK == "METHOD_2_RFDETR_GTATRACK"
    assert MethodologyId.METHOD_3_YOLO26_SRITRACK == "METHOD_3_YOLO26_SRITRACK"


def test_expanded_identity_statuses():
    assert IdentityStatus.FAIL_UNSAFE_MERGE == "FAIL_UNSAFE_MERGE"
    assert IdentityStatus.FAIL_INVALID_OUTPUT == "FAIL_INVALID_OUTPUT"
    assert IdentityStatus.EVALUATING == "EVALUATING"
    assert IdentityStatus.PASS_RELIABLE == "PASS_RELIABLE"
    assert IdentityStatus.FAIL_HIGH_FRAGMENTATION == "FAIL_HIGH_FRAGMENTATION"
    assert IdentityStatus.FAIL_IDENTITY_CONFLICT == "FAIL_IDENTITY_CONFLICT"


def test_evaluation_metrics_unavailable_is_not_zero():
    """
    Scientific integrity test:
    Verify that an uncomputed/unavailable metric is explicitly None, NOT 0.0 or 0.
    """
    eval_metrics = EvaluationMetrics(
        detection=DetectionEvaluationMetrics(precision=0.85, recall=None),
        identity_tracking=IdentityTrackingEvaluationMetrics(
            raw_track_count=115,
            final_identity_count=37,
            fragmentation_ratio=3.11,
            reentry_recovery_rate=None,  # Not 0.0!
        ),
        ground_truth=GroundTruthTrackingMetrics(
            ground_truth_available=False,
            hota=None,
            idf1=None,
            unavailable_reason="User session recorded without ground-truth annotations.",
        ),
        engineering=EngineeringMetrics(
            runtime_seconds=42.5,
            effective_fps=28.2,
        )
    )

    assert eval_metrics.detection.precision == 0.85
    assert eval_metrics.detection.recall is None
    assert eval_metrics.detection.recall != 0.0

    assert eval_metrics.identity_tracking.raw_track_count == 115
    assert eval_metrics.identity_tracking.reentry_recovery_rate is None
    assert eval_metrics.identity_tracking.reentry_recovery_rate != 0

    assert eval_metrics.ground_truth.ground_truth_available is False
    assert eval_metrics.ground_truth.hota is None
    assert eval_metrics.ground_truth.hota != 0.0
    assert eval_metrics.ground_truth.unavailable_reason is not None


def test_analysis_job_with_methodology():
    job = AnalysisJob(
        id="job_test_01",
        session_id="sess_test_01",
        methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
        mode=ApplicationMode.AUTOMATED_ANALYSIS,
        calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
    )
    assert job.methodology_id == MethodologyId.METHOD_1_YOLO11_BOTSORT
    assert job.mode == ApplicationMode.AUTOMATED_ANALYSIS
    assert job.calibration_mode == CalibrationMode.NO_METRIC_CALIBRATION


def test_analysis_result_with_contract_alignment():
    eval_metrics = EvaluationMetrics(
        detection=DetectionEvaluationMetrics(precision=0.91, recall=0.88),
        identity_tracking=IdentityTrackingEvaluationMetrics(
            raw_track_count=80,
            final_identity_count=22,
            fragmentation_ratio=2.2,
        ),
        ground_truth=GroundTruthTrackingMetrics(ground_truth_available=False),
        engineering=EngineeringMetrics(runtime_seconds=15.0),
    )
    res = AnalysisResult(
        id="res_test_01",
        session_id="sess_test_01",
        job_id="job_test_01",
        methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
        application_mode=ApplicationMode.AUTOMATED_ANALYSIS,
        calibration_mode=CalibrationMode.DEMO_FIXED_CALIBRATION,
        job_status=JobStatus.COMPLETED_WITH_LIMITATIONS,
        identity_evaluation=IdentityEvaluation(
            identity_status=IdentityStatus.FAIL_HIGH_FRAGMENTATION,
            player_level_analysis_allowed=False,
            withholding_reason="High fragmentation",
            expected_players=6,
            raw_track_ids=80,
            meaningful_identities=22,
            fragmentation_ratio=2.2,
            acceptance_threshold=1.5,
        ),
        evaluation_metrics=eval_metrics,
        artifact_references=[],
    )
    assert res.methodology_id == MethodologyId.METHOD_1_YOLO11_BOTSORT
    assert res.calibration_mode == CalibrationMode.DEMO_FIXED_CALIBRATION
    assert res.identity_evaluation.expected_players == 6
    assert res.evaluation_metrics is not None
    assert res.evaluation_metrics.detection.precision == 0.91


def test_report_status_enum():
    assert ReportStatus.GROUNDED_LLM == "GROUNDED_LLM"
    assert ReportStatus.DETERMINISTIC_FALLBACK == "DETERMINISTIC_FALLBACK"
    assert ReportStatus.WITHHELD == "WITHHELD"


