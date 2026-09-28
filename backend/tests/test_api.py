"""
API endpoint tests for FastAPI application.
Validates HTTP contracts, status codes, error payloads, and non-persistence behavior.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas import (
    MethodologyId,
    CalibrationMode,
    AudioMode,
    AnalysisStage,
)

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "project" in data
    assert "environment" in data


def test_get_methodologies():
    response = client.get("/api/v1/methodologies")
    assert response.status_code == 200
    methodologies = response.json()
    assert len(methodologies) == 3

    # Validate IDs and availability
    ids = {m["id"] for m in methodologies}
    assert ids == {
        MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
        MethodologyId.METHOD_2_RFDETR_GTATRACK.value,
        MethodologyId.METHOD_3_YOLO26_SRITRACK.value,
    }

    # Ensure no method is falsely marked as "best"
    for m in methodologies:
        assert "best" not in m["display_name"].lower()
        assert "best" not in m["short_description"].lower()

    # Method 1 availability is temporarily EXPERIMENTAL pending formal validation
    method_1 = next(m for m in methodologies if m["id"] == MethodologyId.METHOD_1_YOLO11_BOTSORT.value)
    assert method_1["availability"] == "EXPERIMENTAL"
    assert "validation are in progress" in method_1["availability_reason"]

    # Method 2 & 3 are marked experimental
    method_2 = next(m for m in methodologies if m["id"] == MethodologyId.METHOD_2_RFDETR_GTATRACK.value)
    assert method_2["available"] is False
    assert method_2["availability"] == "EXPERIMENTAL"


from backend.app.schemas.media import MediaType


def create_valid_session_with_media(audio_mode: str = AudioMode.EXTRACT_FROM_VIDEO.value) -> str:
    sess_res = client.post("/api/v1/sessions", json={"title": "Test Session"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # Upload video
    intent_res = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "training_clip.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 10485760,
            "duration_seconds": 120.0,
        },
    )
    assert intent_res.status_code == 201
    video_id = intent_res.json()["media_id"]
    storage_path = intent_res.json()["storage_path"]
    bucket = intent_res.json()["storage_bucket"]

    from backend.app.api.deps import get_storage_service
    storage = get_storage_service()
    if hasattr(storage, "simulate_upload"):
        storage.simulate_upload(bucket, storage_path, 10485760)

    comp_res = client.post(
        f"/api/v1/sessions/{session_id}/media/{video_id}/complete",
        json={"size_bytes": 10485760},
    )
    assert comp_res.status_code == 200

    if audio_mode == AudioMode.SEPARATE_AUDIO_FILE.value:
        audio_intent = client.post(
            f"/api/v1/sessions/{session_id}/media/upload-intent",
            json={
                "media_type": MediaType.COACH_AUDIO.value,
                "filename": "coach_instructions.wav",
                "mime_type": "audio/wav",
                "size_bytes": 5242880,
                "duration_seconds": 120.0,
            },
        )
        assert audio_intent.status_code == 201
        audio_id = audio_intent.json()["media_id"]
        a_path = audio_intent.json()["storage_path"]
        a_bucket = audio_intent.json()["storage_bucket"]
        if hasattr(storage, "simulate_upload"):
            storage.simulate_upload(a_bucket, a_path, 5242880)
        client.post(f"/api/v1/sessions/{session_id}/media/{audio_id}/complete", json={})

    return session_id


def test_create_job_success():
    session_id = create_valid_session_with_media()
    payload = {
        "session_id": session_id,
        "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
        "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        "audio_mode": AudioMode.EXTRACT_FROM_VIDEO.value,
        "video_file_name": "training_clip.mp4",
    }
    response = client.post("/api/v1/analysis/jobs", json=payload)
    assert response.status_code == 201
    job = response.json()
    assert job["id"].startswith("job_")
    assert job["session_id"] == session_id
    assert job["methodology_id"] == MethodologyId.METHOD_1_YOLO11_BOTSORT.value
    assert job["calibration_mode"] == CalibrationMode.NO_METRIC_CALIBRATION.value
    assert job["current_stage"] == AnalysisStage.UPLOADED.value
    assert job["progress_percent"] == 0.0
    assert "awaiting video ingestion" in job["stage_message"].lower()


def test_create_job_missing_methodology_rejected():
    """
    CRITICAL: Job creation must require an explicit methodology_id.
    It must NOT silently fall back to Method 1.
    """
    session_id = create_valid_session_with_media()
    payload = {
        "session_id": session_id,
        "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        "audio_mode": AudioMode.NO_AUDIO.value,
    }
    response = client.post("/api/v1/analysis/jobs", json=payload)
    assert response.status_code == 422  # Unprocessable Entity


def test_create_job_invalid_methodology_rejected():
    session_id = create_valid_session_with_media()
    payload = {
        "session_id": session_id,
        "methodology_id": "NON_EXISTENT_MAGIC_AI_METHOD",
        "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        "audio_mode": AudioMode.NO_AUDIO.value,
    }
    response = client.post("/api/v1/analysis/jobs", json=payload)
    assert response.status_code == 422


def test_get_job_success():
    session_id = create_valid_session_with_media(audio_mode=AudioMode.SEPARATE_AUDIO_FILE.value)
    # First create a job
    create_payload = {
        "session_id": session_id,
        "methodology_id": MethodologyId.METHOD_2_RFDETR_GTATRACK.value,
        "calibration_mode": CalibrationMode.CUSTOM_PITCH_CALIBRATION.value,
        "audio_mode": AudioMode.SEPARATE_AUDIO_FILE.value,
    }
    create_res = client.post("/api/v1/analysis/jobs", json=create_payload)
    assert create_res.status_code == 201
    created_job = create_res.json()
    job_id = created_job["id"]

    # Now get the job
    get_res = client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert get_res.status_code == 200
    retrieved_job = get_res.json()
    assert retrieved_job["id"] == job_id
    assert retrieved_job["methodology_id"] == MethodologyId.METHOD_2_RFDETR_GTATRACK.value
    assert retrieved_job["calibration_mode"] == CalibrationMode.CUSTOM_PITCH_CALIBRATION.value


def test_get_job_not_found():
    response = client.get("/api/v1/analysis/jobs/non_existent_job_12345")
    assert response.status_code == 404
    error = response.json()
    assert error["code"] == "JOB_NOT_FOUND"
    assert "not found" in error["message"].lower()
    assert error["details"]["job_id"] == "non_existent_job_12345"


def test_get_result_not_ready():
    """
    CRITICAL: Never return fake metrics for an uncompleted job.
    Must return 409 Conflict with RESULT_NOT_READY.
    """
    session_id = create_valid_session_with_media(audio_mode=AudioMode.NO_AUDIO.value)
    create_payload = {
        "session_id": session_id,
        "methodology_id": MethodologyId.METHOD_3_YOLO26_SRITRACK.value,
        "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        "audio_mode": AudioMode.NO_AUDIO.value,
    }
    create_res = client.post("/api/v1/analysis/jobs", json=create_payload)
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]

    res = client.get(f"/api/v1/analysis/jobs/{job_id}/result")
    assert res.status_code == 409
    error = res.json()
    assert error["code"] == "RESULT_NOT_READY"
    assert "not ready" in error["message"].lower()
    assert error["details"]["current_stage"] == AnalysisStage.UPLOADED.value


def test_get_result_unknown_job():
    res = client.get("/api/v1/analysis/jobs/unknown_job_999/result")
    assert res.status_code == 404
    error = res.json()
    assert error["code"] == "JOB_NOT_FOUND"
