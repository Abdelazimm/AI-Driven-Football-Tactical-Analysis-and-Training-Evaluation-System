import re
from pathlib import Path
import pytest
from backend.app.schemas import (
    ApplicationMode,
    CalibrationMode,
    AnalysisStage,
    IdentityStatus,
    ReportStatus,
    MethodologyId,
    MethodologyAvailability,
    AudioMode,
    MediaType,
    UploadStatus,
    JobStatus,
    AnalysisJob,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SHARED_DIR = REPO_ROOT / "shared" / "constants"


def parse_ts_const_object(ts_file_path: Path, object_name: str) -> dict:
    """Simple parser to extract key-value mappings from TS const objects."""
    content = ts_file_path.read_text(encoding="utf-8")
    pattern = rf"export const {object_name}\s*=\s*\{{([^}}]+)\}}\s*as const;"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find const object {object_name} in {ts_file_path}")

    body = match.group(1)
    results = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        kv_match = re.match(r"([A-Za-z0-9_]+)\s*:\s*['\"]([^'\"]+)['\"],?", line)
        if kv_match:
            results[kv_match.group(1)] = kv_match.group(2)
    return results


def test_methodology_alignment():
    ts_file = SHARED_DIR / "methodology.ts"
    ts_values = parse_ts_const_object(ts_file, "METHODOLOGY_IDS")

    py_values = {m.name: m.value for m in MethodologyId}
    assert py_values == ts_values, f"Methodology mismatch: Py {py_values} != TS {ts_values}"


def test_identity_status_alignment():
    ts_file = SHARED_DIR / "confidence.ts"
    ts_values = parse_ts_const_object(ts_file, "IDENTITY_STATUS")

    py_values = {m.name: m.value for m in IdentityStatus}
    assert py_values == ts_values, f"IdentityStatus mismatch: Py {py_values} != TS {ts_values}"


def test_application_mode_alignment():
    ts_file = SHARED_DIR / "modes.ts"
    ts_values = parse_ts_const_object(ts_file, "APPLICATION_MODES")

    py_values = {m.name: m.value for m in ApplicationMode}
    assert py_values == ts_values, f"ApplicationMode mismatch: Py {py_values} != TS {ts_values}"


def test_calibration_mode_alignment():
    ts_file = SHARED_DIR / "modes.ts"
    ts_values = parse_ts_const_object(ts_file, "CALIBRATION_MODES")

    py_values = {m.name: m.value for m in CalibrationMode}
    assert py_values == ts_values, f"CalibrationMode mismatch: Py {py_values} != TS {ts_values}"


def test_analysis_stage_alignment():
    ts_file = SHARED_DIR / "stages.ts"
    ts_values = parse_ts_const_object(ts_file, "ANALYSIS_STAGES")

    py_values = {m.name: m.value for m in AnalysisStage}
    assert py_values == ts_values, f"AnalysisStage mismatch: Py {py_values} != TS {ts_values}"


def test_report_status_alignment():
    ts_file = SHARED_DIR / "confidence.ts"
    ts_values = parse_ts_const_object(ts_file, "REPORT_STATUS")

    py_values = {m.name: m.value for m in ReportStatus}
    assert py_values == ts_values, f"ReportStatus mismatch: Py {py_values} != TS {ts_values}"


def test_audio_mode_alignment():
    ts_file = SHARED_DIR / "modes.ts"
    ts_values = parse_ts_const_object(ts_file, "AUDIO_MODES")

    py_values = {m.name: m.value for m in AudioMode}
    assert py_values == ts_values, f"AudioMode mismatch: Py {py_values} != TS {ts_values}"


def test_methodology_availability_alignment():
    ts_file = SHARED_DIR / "methodology.ts"
    ts_values = parse_ts_const_object(ts_file, "METHODOLOGY_AVAILABILITY")

    py_values = {m.name: m.value for m in MethodologyAvailability}
    assert py_values == ts_values, f"MethodologyAvailability mismatch: Py {py_values} != TS {ts_values}"


def test_media_type_alignment():
    ts_file = REPO_ROOT / "shared" / "schemas" / "media.ts"
    ts_values = parse_ts_const_object(ts_file, "MEDIA_TYPES")

    py_values = {m.name: m.value for m in MediaType}
    assert py_values == ts_values, f"MediaType mismatch: Py {py_values} != TS {ts_values}"


def test_upload_status_alignment():
    ts_file = REPO_ROOT / "shared" / "schemas" / "media.ts"
    ts_values = parse_ts_const_object(ts_file, "UPLOAD_STATUSES")

    py_values = {m.name: m.value for m in UploadStatus}
    assert py_values == ts_values, f"UploadStatus mismatch: Py {py_values} != TS {ts_values}"


def test_job_status_alignment():
    ts_file = SHARED_DIR / "job.ts"
    ts_values = parse_ts_const_object(ts_file, "JOB_STATUSES")

    py_values = {m.name: m.value for m in JobStatus}
    assert py_values == ts_values, f"JobStatus mismatch: Py {py_values} != TS {ts_values}"
    assert "COMPLETED_WITH_LIMITATIONS" in py_values
    assert JobStatus.COMPLETED_WITH_LIMITATIONS == "COMPLETED_WITH_LIMITATIONS"


def test_analysis_stage_strictly_sixteen_processing_stages():
    """
    CRITICAL CONTRACT RULE:
    AnalysisStage represents processing pipeline position only (exactly 16 stages).
    Terminal statuses (COMPLETED, COMPLETED_WITH_LIMITATIONS, FAILED) and
    initial lifecycle state (QUEUED) are strictly JobStatus, NOT AnalysisStage.
    """
    expected_16 = [
        "UPLOADED",
        "VALIDATING",
        "PREPROCESSING",
        "DETECTING",
        "TRACKING",
        "IDENTITY_EVALUATION",
        "CALIBRATING",
        "KINEMATICS",
        "AUDIO_EXTRACTION",
        "TRANSCRIBING",
        "INSTRUCTION_PARSING",
        "FUSION",
        "GENERATING_EVIDENCE",
        "GENERATING_REPORT",
        "RENDERING",
        "UPLOADING_RESULTS",
    ]
    py_stages = [s.value for s in AnalysisStage]
    assert py_stages == expected_16
    assert len(AnalysisStage) == 16

    # 1. Non-stage statuses must NOT be in Python AnalysisStage
    for non_stage in ["COMPLETED", "COMPLETED_WITH_LIMITATIONS", "FAILED", "QUEUED"]:
        assert non_stage not in py_stages
        with pytest.raises(ValueError):
            AnalysisStage(non_stage)

    # 2. Non-stage statuses must NOT be in TS ANALYSIS_STAGES
    ts_file = SHARED_DIR / "stages.ts"
    ts_values = parse_ts_const_object(ts_file, "ANALYSIS_STAGES")
    assert list(ts_values.values()) == expected_16
    assert len(ts_values) == 16
    for non_stage in ["COMPLETED", "COMPLETED_WITH_LIMITATIONS", "FAILED", "QUEUED"]:
        assert non_stage not in ts_values.values()


def test_identity_status_complete_seven_values():
    """
    CANONICAL IDENTITY STATUS RULE:
    Must contain exactly 7 canonical states.
    """
    expected_7 = {
        "NOT_EVALUATED",
        "EVALUATING",
        "PASS_RELIABLE",
        "FAIL_HIGH_FRAGMENTATION",
        "FAIL_IDENTITY_CONFLICT",
        "FAIL_UNSAFE_MERGE",
        "FAIL_INVALID_OUTPUT",
    }
    py_values = {s.value for s in IdentityStatus}
    assert py_values == expected_7
    assert len(IdentityStatus) == 7

    ts_file = SHARED_DIR / "confidence.ts"
    ts_values = parse_ts_const_object(ts_file, "IDENTITY_STATUS")
    assert set(ts_values.values()) == expected_7
    assert len(ts_values) == 7


def test_new_job_initial_state():
    """Verify newly created AnalysisJob is status=QUEUED and current_stage=UPLOADED."""
    job = AnalysisJob(
        id="job_test_stage",
        session_id="sess_test_stage",
        methodology_id=MethodologyId.METHOD_1_YOLO11_BOTSORT,
        mode=ApplicationMode.AUTOMATED_ANALYSIS,
        calibration_mode=CalibrationMode.NO_METRIC_CALIBRATION,
    )
    assert job.status == JobStatus.QUEUED
    assert job.status.value == "QUEUED"
    assert job.current_stage == AnalysisStage.UPLOADED
    assert job.current_stage.value == "UPLOADED"


