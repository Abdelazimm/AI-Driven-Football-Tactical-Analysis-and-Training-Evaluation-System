"""
Phase 3 Tests: Supabase Persistence, Media Storage, Upload Flow, and Validation Guardrails.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.modes import CalibrationMode, AudioMode
from backend.app.schemas.media import MediaType, UploadStatus
from backend.app.schemas.stages import AnalysisStage
from backend.app.api.deps import (
    get_storage_service,
    get_session_repository,
    get_media_repository,
    get_job_repository,
)

client = TestClient(app)


def test_session_lifecycle():
    """Verify session creation and retrieval."""
    res = client.post(
        "/api/v1/sessions",
        json={
            "title": "Tactical Drill Session 1",
            "coach_name": "Coach Smith",
            "team_name": "Senior Academy",
            "notes": "Focus on high-pressing cues and defensive transition.",
        },
    )
    assert res.status_code == 201
    session = res.json()
    assert session["title"] == "Tactical Drill Session 1"
    assert session["coach_name"] == "Coach Smith"
    session_id = session["id"]

    get_res = client.get(f"/api/v1/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id


def test_session_not_found():
    res = client.get("/api/v1/sessions/non_existent_session_id_999")
    assert res.status_code == 404
    error = res.json()
    assert error["code"] == "SESSION_NOT_FOUND"


def test_upload_intent_video_validation():
    # Create session
    sess_res = client.post("/api/v1/sessions", json={"title": "Video Validation Session"})
    session_id = sess_res.json()["id"]

    # 1. Valid video intent
    valid_res = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "session_clip.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 50000000,
            "duration_seconds": 240.0,
        },
    )
    assert valid_res.status_code == 201
    intent = valid_res.json()
    assert intent["session_id"] == session_id
    assert intent["media_type"] == MediaType.VIDEO.value
    assert "signed_upload_url" in intent
    assert "session_clip.mp4" in intent["storage_path"]

    # 2. Unsupported video format (e.g. AVI)
    unsupported_res = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "session_clip.avi",
            "mime_type": "video/x-msvideo",
            "size_bytes": 50000000,
            "duration_seconds": 120.0,
        },
    )
    assert unsupported_res.status_code == 422
    assert unsupported_res.json()["code"] == "UNSUPPORTED_VIDEO_FORMAT"

    # 3. Video duration exceeds 360 seconds (6 minutes)
    toolong_res = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "long_match.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 50000000,
            "duration_seconds": 360.1,
        },
    )
    assert toolong_res.status_code == 422
    assert toolong_res.json()["code"] == "VIDEO_DURATION_EXCEEDED"

    # 4. File size exceeds maximum limit
    toobig_res = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "huge_file.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 2 * 1024 * 1024 * 1024,  # 2 GB
            "duration_seconds": 200.0,
        },
    )
    assert toobig_res.status_code == 422
    assert toobig_res.json()["code"] == "FILE_SIZE_EXCEEDED"


def test_upload_intent_audio_validation():
    sess_res = client.post("/api/v1/sessions", json={"title": "Audio Validation Session"})
    session_id = sess_res.json()["id"]

    # 1. Valid WAV audio
    valid_wav = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.COACH_AUDIO.value,
            "filename": "coach_mic.wav",
            "mime_type": "audio/wav",
            "size_bytes": 10000000,
            "duration_seconds": 180.0,
        },
    )
    assert valid_wav.status_code == 201

    # 2. Unsupported audio format (e.g. FLAC)
    unsupported_audio = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.COACH_AUDIO.value,
            "filename": "coach_mic.flac",
            "mime_type": "audio/flac",
            "size_bytes": 10000000,
        },
    )
    assert unsupported_audio.status_code == 422
    assert unsupported_audio.json()["code"] == "UNSUPPORTED_AUDIO_FORMAT"


def test_upload_completion_authoritative_verification():
    sess_res = client.post("/api/v1/sessions", json={"title": "Completion Test Session"})
    session_id = sess_res.json()["id"]

    intent_res = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "clip.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 10240,
            "duration_seconds": 60.0,
        },
    )
    media_id = intent_res.json()["media_id"]
    storage_path = intent_res.json()["storage_path"]
    bucket = intent_res.json()["storage_bucket"]

    # Attempting to complete before object actually exists in storage must fail
    fail_comp = client.post(f"/api/v1/sessions/{session_id}/media/{media_id}/complete", json={})
    assert fail_comp.status_code == 400
    assert fail_comp.json()["code"] == "OBJECT_NOT_FOUND_IN_STORAGE"

    # Simulate storage arrival (e.g. from direct browser PUT)
    storage = get_storage_service()
    if hasattr(storage, "simulate_upload"):
        storage.simulate_upload(bucket, storage_path, 10240)

    # Now completion must succeed
    succ_comp = client.post(f"/api/v1/sessions/{session_id}/media/{media_id}/complete", json={})
    assert succ_comp.status_code == 200
    asset = succ_comp.json()
    assert asset["upload_status"] == UploadStatus.VALIDATED.value
    assert asset["size_bytes"] == 10240

    # Idempotent completion call succeeds without error
    idem_comp = client.post(f"/api/v1/sessions/{session_id}/media/{media_id}/complete", json={})
    assert idem_comp.status_code == 200


def test_job_creation_media_and_safety_guardrails():
    # 1. Unknown session
    res_no_sess = client.post(
        "/api/v1/analysis/jobs",
        json={
            "session_id": "missing_session_uuid",
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        },
    )
    assert res_no_sess.status_code == 404
    assert res_no_sess.json()["code"] == "SESSION_NOT_FOUND"

    # 2. Session exists but NO media uploaded
    sess = client.post("/api/v1/sessions", json={"title": "Empty Session"}).json()
    res_no_media = client.post(
        "/api/v1/analysis/jobs",
        json={
            "session_id": sess["id"],
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        },
    )
    assert res_no_media.status_code == 422
    assert res_no_media.json()["code"] == "REQUIRED_MEDIA_MISSING"

    # 3. Scientific safety rule: DEMO_FIXED_CALIBRATION rejected for arbitrary uploaded sessions
    sess_demo = client.post("/api/v1/sessions", json={"title": "Demo Attempt Session"}).json()
    res_demo = client.post(
        "/api/v1/analysis/jobs",
        json={
            "session_id": sess_demo["id"],
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "calibration_mode": CalibrationMode.DEMO_FIXED_CALIBRATION.value,
        },
    )
    assert res_demo.status_code == 422
    assert res_demo.json()["code"] == "INVALID_CALIBRATION_MODE"
    assert "strictly calibrated for frozen research" in res_demo.json()["message"]

    # 4. Audio mode SEPARATE_AUDIO_FILE requires separate audio asset
    sess_audio = client.post("/api/v1/sessions", json={"title": "Audio Mode Session"}).json()
    # Add video only
    intent = client.post(
        f"/api/v1/sessions/{sess_audio['id']}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "vid.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 1000,
        },
    ).json()
    storage = get_storage_service()
    if hasattr(storage, "simulate_upload"):
        storage.simulate_upload(intent["storage_bucket"], intent["storage_path"], 1000)
    client.post(f"/api/v1/sessions/{sess_audio['id']}/media/{intent['media_id']}/complete", json={})

    # Try creating job with SEPARATE_AUDIO_FILE before audio is uploaded
    res_miss_audio = client.post(
        "/api/v1/analysis/jobs",
        json={
            "session_id": sess_audio["id"],
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
            "audio_mode": AudioMode.SEPARATE_AUDIO_FILE.value,
        },
    )
    assert res_miss_audio.status_code == 422
    assert res_miss_audio.json()["code"] == "REQUIRED_AUDIO_MISSING"


def test_job_persisted_and_retrievable():
    """Verify job record is persisted and can be retrieved via GET /api/v1/analysis/jobs/{job_id}."""
    sess = client.post("/api/v1/sessions", json={"title": "Durable Job Session"}).json()
    session_id = sess["id"]

    # Upload video
    intent = client.post(
        f"/api/v1/sessions/{session_id}/media/upload-intent",
        json={
            "media_type": MediaType.VIDEO.value,
            "filename": "training.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 2048,
        },
    ).json()
    storage = get_storage_service()
    if hasattr(storage, "simulate_upload"):
        storage.simulate_upload(intent["storage_bucket"], intent["storage_path"], 2048)
    client.post(f"/api/v1/sessions/{session_id}/media/{intent['media_id']}/complete", json={})

    # Create job
    create_res = client.post(
        "/api/v1/analysis/jobs",
        json={
            "session_id": session_id,
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
            "audio_mode": AudioMode.EXTRACT_FROM_VIDEO.value,
        },
    )
    assert create_res.status_code == 201
    job = create_res.json()
    job_id = job["id"]
    assert job["status"] == "QUEUED"
    assert job["current_stage"] == AnalysisStage.UPLOADED.value

    # Retrieve job
    get_res = client.get(f"/api/v1/analysis/jobs/{job_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == job_id
    assert retrieved["session_id"] == session_id
    assert retrieved["status"] == "QUEUED"
    assert retrieved["current_stage"] == AnalysisStage.UPLOADED.value
    assert retrieved["progress_percent"] == 0.0

    # Media assets should now be linked to the job
    media_list = client.get(f"/api/v1/sessions/{session_id}/media").json()
    video_asset = next(m for m in media_list if m["media_type"] == MediaType.VIDEO.value)
    assert video_asset["job_id"] == job_id
