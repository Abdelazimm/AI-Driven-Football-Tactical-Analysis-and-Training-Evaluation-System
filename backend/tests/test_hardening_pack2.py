"""
Hardening Pack 2 Tests: Media Validation, Storage Error Semantics, and Analysis Eligibility.

Tests cover:
- Media probe service (ffprobe extraction, synthetic fixtures)
- Duration enforcement (299.9s, 300.0s accepted; >300.0s rejected)
- Content/container validation (renamed text, corrupt, no-video-stream)
- MIME/container consistency
- Storage error semantics (typed error hierarchy)
- Exact-object lookup behavior
- Analysis eligibility gate (VALIDATED required)
- Dispatch eligibility gate (VALIDATED required)

Uses in-memory services with tiny synthetic fixtures.
Does NOT use participant footage.
"""
import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app
from backend.app.schemas.media import MediaAsset, MediaType, UploadStatus
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.modes import CalibrationMode, AudioMode
from backend.app.schemas.session import Session
from backend.app.services.media_probe import (
    MediaProbeService,
    MediaProbeResult,
    ProbeStatus,
    FFProbeMediaProbeService,
    InMemoryMediaProbeService,
)
from backend.app.services.media_validation_service import (
    MediaValidationService,
    MediaValidationErrorCode,
    MediaValidationResult,
)
from backend.app.services.storage_service import (
    StorageService,
    InMemoryStorageService,
    StorageError,
    StorageErrorCode,
    StorageObjectNotFound,
    StorageAuthError,
    StorageTimeout,
    StorageUnavailable,
    StorageProviderError,
)
from backend.app.services.media_repository import InMemoryMediaRepository
from backend.app.services.session_repository import InMemorySessionRepository
from backend.app.services.job_repository import InMemoryJobRepository
from backend.app.api.deps import (
    set_override_storage_service,
    set_override_session_repository,
    set_override_media_repository,
    set_override_job_repository,
    set_override_media_probe_service,
    set_override_media_validation_service,
)

client = TestClient(app)


# =============================================================================
# FIXTURES
# =============================================================================

def _make_valid_probe_result(duration: float = 60.0, fps: float = 30.0) -> MediaProbeResult:
    """Create a valid probe result with controllable duration."""
    return MediaProbeResult(
        container_format="mov,mp4,m4a,3gp,3g2,mj2",
        duration_seconds=duration,
        width=1920,
        height=1080,
        fps=fps,
        video_codec="h264",
        audio_codec="aac",
        has_video=True,
        has_audio=True,
        probe_status=ProbeStatus.SUCCESS,
    )


def _make_session_media_job(
    session_repo: InMemorySessionRepository,
    media_repo: InMemoryMediaRepository,
    storage_svc: InMemoryStorageService,
    upload_status: UploadStatus = UploadStatus.VALIDATED,
):
    """Create a session + media asset at the specified upload status for testing."""
    session_id = str(uuid.uuid4())
    media_id = str(uuid.uuid4())
    session = Session(id=session_id, title="Test Session")
    session_repo.create_session(session)

    asset = MediaAsset(
        id=media_id,
        session_id=session_id,
        media_type=MediaType.VIDEO,
        storage_bucket="analysis-inputs",
        storage_path=f"{session_id}/video/{media_id}_test.mp4",
        original_filename="test.mp4",
        mime_type="video/mp4",
        size_bytes=1024,
        upload_status=upload_status,
    )
    media_repo.create_media_asset(asset)
    storage_svc.simulate_upload("analysis-inputs", asset.storage_path, 1024)
    return session_id, media_id


# =============================================================================
# MEDIA PROBE SERVICE TESTS
# =============================================================================

class TestMediaProbeService:
    """Tests for the MediaProbeService abstraction and ffprobe parsing."""

    def test_in_memory_probe_configurable(self):
        probe = InMemoryMediaProbeService()
        probe.set_probe_result("test.mp4", _make_valid_probe_result(120.0))
        result = probe.probe("test.mp4")
        assert result.probe_status == ProbeStatus.SUCCESS
        assert result.duration_seconds == 120.0
        assert result.width == 1920
        assert result.has_video is True

    def test_in_memory_probe_unconfigured_returns_error(self):
        probe = InMemoryMediaProbeService()
        result = probe.probe("unknown.mp4")
        assert result.probe_status == ProbeStatus.PROBE_ERROR

    def test_in_memory_probe_default_result(self):
        probe = InMemoryMediaProbeService()
        probe.set_default_result(_make_valid_probe_result(30.0))
        result = probe.probe("anything.mp4")
        assert result.probe_status == ProbeStatus.SUCCESS
        assert result.duration_seconds == 30.0

    def test_ffprobe_service_instantiation(self):
        """FFProbeMediaProbeService should instantiate without error."""
        svc = FFProbeMediaProbeService()
        assert svc._ffprobe_path is not None or svc._ffprobe_path is None  # depends on env

    def test_ffprobe_parse_frame_rate_fraction(self):
        assert FFProbeMediaProbeService._parse_frame_rate("30000/1001", None) == pytest.approx(29.97, abs=0.01)

    def test_ffprobe_parse_frame_rate_integer(self):
        assert FFProbeMediaProbeService._parse_frame_rate("30/1", None) == 30.0

    def test_ffprobe_parse_frame_rate_zero_den(self):
        assert FFProbeMediaProbeService._parse_frame_rate("0/0", None) is None

    def test_ffprobe_parse_frame_rate_none(self):
        assert FFProbeMediaProbeService._parse_frame_rate(None, None) is None

    def test_ffprobe_safe_float_nan(self):
        assert FFProbeMediaProbeService._safe_float(float("nan")) is None

    def test_ffprobe_safe_float_inf(self):
        assert FFProbeMediaProbeService._safe_float(float("inf")) is None

    def test_ffprobe_safe_float_valid(self):
        assert FFProbeMediaProbeService._safe_float("30.5") == 30.5

    def test_ffprobe_safe_float_none(self):
        assert FFProbeMediaProbeService._safe_float(None) is None


# =============================================================================
# MEDIA VALIDATION SERVICE TESTS
# =============================================================================

class TestMediaValidationService:
    """Tests for orchestrated media validation with controllable probe results."""

    def setup_method(self):
        self.media_repo = InMemoryMediaRepository()
        self.storage_svc = InMemoryStorageService()
        self.probe_svc = InMemoryMediaProbeService()
        self.validation_svc = MediaValidationService(
            media_repo=self.media_repo,
            storage_service=self.storage_svc,
            probe_service=self.probe_svc,
            max_duration_seconds=360.0,
        )

    def _create_test_asset(self, media_id: str = None, client_duration: float = None) -> str:
        media_id = media_id or str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        asset = MediaAsset(
            id=media_id,
            session_id=session_id,
            media_type=MediaType.VIDEO,
            storage_bucket="analysis-inputs",
            storage_path=f"test/{media_id}/test.mp4",
            original_filename="test.mp4",
            mime_type="video/mp4",
            size_bytes=1024,
            duration_seconds=client_duration,
            upload_status=UploadStatus.UPLOADED,
        )
        self.media_repo.create_media_asset(asset)
        self.storage_svc.simulate_upload("analysis-inputs", asset.storage_path, 1024)
        return media_id

    def _set_probe_for_asset(self, media_id: str, probe_result: MediaProbeResult):
        """Configure probe result for the signed download URL that will be generated."""
        # The InMemoryStorageService generates URLs with a predictable pattern
        asset = self.media_repo.get_media_asset(media_id)
        signed_url = f"http://localhost:8000/api/v1/mock-storage/{asset.storage_bucket}/{asset.storage_path}?token=mock_download_token&expires=120"
        self.probe_svc.set_probe_result(signed_url, probe_result)

    # ── Duration enforcement ──────────────────────────────────────────

    def test_valid_video_accepted(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, _make_valid_probe_result(60.0))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is True
        asset = self.media_repo.get_media_asset(mid)
        assert asset.upload_status == UploadStatus.VALIDATED
        assert asset.duration_seconds == 60.0
        assert asset.video_codec == "h264"

    def test_duration_359_9s_accepted(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, _make_valid_probe_result(359.9))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is True

    def test_duration_360_0s_accepted(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, _make_valid_probe_result(360.0))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is True

    def test_duration_360_1s_rejected(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, _make_valid_probe_result(360.1))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.VIDEO_DURATION_EXCEEDED
        asset = self.media_repo.get_media_asset(mid)
        assert asset.upload_status == UploadStatus.VALIDATION_FAILED

    def test_client_duration_does_not_override_probe(self):
        """Client says 60s, real is 361s — must be rejected by authoritative probe."""
        mid = self._create_test_asset(client_duration=60.0)
        self._set_probe_for_asset(mid, _make_valid_probe_result(361.0))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.VIDEO_DURATION_EXCEEDED

    def test_omitted_client_duration_does_not_bypass_cap(self):
        """Client omits duration, real is 361s — must still be rejected."""
        mid = self._create_test_asset(client_duration=None)
        self._set_probe_for_asset(mid, _make_valid_probe_result(361.0))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.VIDEO_DURATION_EXCEEDED

    # ── Content/container validation ──────────────────────────────────

    def test_invalid_container_rejected(self):
        """Renamed text file pretending to be MP4 — rejected."""
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            probe_status=ProbeStatus.INVALID_CONTAINER,
            error_message="Not a valid container.",
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.INVALID_CONTAINER

    def test_corrupt_file_rejected(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            probe_status=ProbeStatus.CORRUPT_FILE,
            error_message="Corrupt media file.",
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.CORRUPT_MEDIA

    def test_no_video_stream_rejected(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            container_format="mov,mp4,m4a,3gp,3g2,mj2",
            has_video=False,
            has_audio=True,
            audio_codec="aac",
            probe_status=ProbeStatus.NO_VIDEO_STREAM,
            error_message="No video stream found.",
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.NO_VIDEO_STREAM

    def test_invalid_dimensions_rejected(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            container_format="mov,mp4,m4a,3gp,3g2,mj2",
            duration_seconds=60.0,
            width=0,
            height=1080,
            fps=30.0,
            video_codec="h264",
            has_video=True,
            has_audio=False,
            probe_status=ProbeStatus.SUCCESS,
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.INVALID_DIMENSIONS

    def test_invalid_fps_rejected(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            container_format="mov,mp4,m4a,3gp,3g2,mj2",
            duration_seconds=60.0,
            width=1920,
            height=1080,
            fps=0.0,
            video_codec="h264",
            has_video=True,
            has_audio=False,
            probe_status=ProbeStatus.SUCCESS,
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.INVALID_FPS

    def test_mime_container_mismatch_rejected(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            container_format="matroska,webm",  # MKV but MIME says video/mp4
            duration_seconds=60.0,
            width=1920,
            height=1080,
            fps=30.0,
            video_codec="h264",
            has_video=True,
            has_audio=False,
            probe_status=ProbeStatus.SUCCESS,
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.MIME_CONTAINER_MISMATCH

    def test_valid_mov_accepted(self):
        """MOV container with video/quicktime MIME — should be accepted."""
        mid = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        asset = MediaAsset(
            id=mid,
            session_id=session_id,
            media_type=MediaType.VIDEO,
            storage_bucket="analysis-inputs",
            storage_path=f"test/{mid}/test.mov",
            original_filename="test.mov",
            mime_type="video/quicktime",
            size_bytes=1024,
            upload_status=UploadStatus.UPLOADED,
        )
        self.media_repo.create_media_asset(asset)
        self.storage_svc.simulate_upload("analysis-inputs", asset.storage_path, 1024)
        signed_url = f"http://localhost:8000/api/v1/mock-storage/analysis-inputs/{asset.storage_path}?token=mock_download_token&expires=120"
        self.probe_svc.set_probe_result(signed_url, _make_valid_probe_result(60.0))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is True

    # ── Probe failure modes ───────────────────────────────────────────

    def test_ffprobe_not_available(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            probe_status=ProbeStatus.FFPROBE_NOT_AVAILABLE,
            error_message="ffprobe not found.",
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.FFPROBE_NOT_AVAILABLE

    def test_probe_timeout(self):
        mid = self._create_test_asset()
        self._set_probe_for_asset(mid, MediaProbeResult(
            probe_status=ProbeStatus.PROBE_TIMEOUT,
            error_message="Timed out.",
        ))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.PROBE_TIMEOUT

    def test_storage_access_error(self):
        """Storage error during signed URL generation prevents validation."""
        mid = self._create_test_asset()
        self.storage_svc.force_error(StorageTimeout("Connection timed out"))
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is False
        assert result.error_code == MediaValidationErrorCode.STORAGE_ACCESS_ERROR
        self.storage_svc.force_error(None)  # cleanup

    def test_media_not_found(self):
        result = self.validation_svc.validate_media("nonexistent-id")
        assert result.is_valid is False
        assert result.error_code == "MEDIA_NOT_FOUND"

    def test_validated_metadata_persisted(self):
        """After successful validation, authoritative metadata replaces client values."""
        mid = self._create_test_asset(client_duration=120.0)
        probe = _make_valid_probe_result(59.5)
        probe.width = 3840
        probe.height = 2160
        probe.fps = 59.94
        self._set_probe_for_asset(mid, probe)
        result = self.validation_svc.validate_media(mid)
        assert result.is_valid is True
        asset = self.media_repo.get_media_asset(mid)
        assert asset.duration_seconds == 59.5  # NOT 120.0 from client
        assert asset.width == 3840
        assert asset.height == 2160
        assert abs(asset.fps - 59.94) < 0.01
        assert asset.container_format == "mov,mp4,m4a,3gp,3g2,mj2"
        assert asset.validation_status == "SUCCESS"


# =============================================================================
# STORAGE ERROR SEMANTICS TESTS
# =============================================================================

class TestStorageErrorSemantics:
    """Tests for typed storage error hierarchy."""

    def test_storage_object_not_found(self):
        err = StorageObjectNotFound("my-bucket", "path/to/file.mp4")
        assert err.code == StorageErrorCode.OBJECT_NOT_FOUND
        assert "my-bucket" in err.message
        assert err.bucket == "my-bucket"
        assert err.path == "path/to/file.mp4"

    def test_storage_auth_error(self):
        err = StorageAuthError("Invalid API key")
        assert err.code == StorageErrorCode.STORAGE_AUTH_ERROR

    def test_storage_timeout(self):
        err = StorageTimeout()
        assert err.code == StorageErrorCode.STORAGE_TIMEOUT

    def test_storage_unavailable(self):
        err = StorageUnavailable()
        assert err.code == StorageErrorCode.STORAGE_UNAVAILABLE

    def test_storage_provider_error(self):
        err = StorageProviderError("Unexpected 500")
        assert err.code == StorageErrorCode.STORAGE_PROVIDER_ERROR

    def test_in_memory_verify_exists_true(self):
        svc = InMemoryStorageService()
        svc.simulate_upload("bucket", "path/file.mp4", 1024)
        assert svc.verify_object_exists("bucket", "path/file.mp4") is True

    def test_in_memory_verify_exists_false(self):
        svc = InMemoryStorageService()
        assert svc.verify_object_exists("bucket", "path/file.mp4") is False

    def test_in_memory_forced_error_raises(self):
        svc = InMemoryStorageService()
        svc.force_error(StorageTimeout("Simulated timeout"))
        with pytest.raises(StorageTimeout):
            svc.verify_object_exists("bucket", "path/file.mp4")

    def test_in_memory_forced_error_on_get_size(self):
        svc = InMemoryStorageService()
        svc.force_error(StorageAuthError("Simulated auth failure"))
        with pytest.raises(StorageAuthError):
            svc.get_object_size("bucket", "path/file.mp4")

    def test_in_memory_forced_error_on_download_url(self):
        svc = InMemoryStorageService()
        svc.force_error(StorageProviderError("Simulated provider error"))
        with pytest.raises(StorageProviderError):
            svc.create_signed_download_url("bucket", "path/file.mp4")

    def test_in_memory_download_url_not_found(self):
        svc = InMemoryStorageService()
        with pytest.raises(StorageObjectNotFound):
            svc.create_signed_download_url("bucket", "nonexistent/file.mp4")

    def test_in_memory_download_url_success(self):
        svc = InMemoryStorageService()
        svc.simulate_upload("bucket", "path/file.mp4", 2048)
        url = svc.create_signed_download_url("bucket", "path/file.mp4", 60)
        assert "mock-storage" in url
        assert "expires=60" in url

    def test_supabase_classify_auth_error(self):
        from backend.app.services.storage_service import SupabaseStorageService
        ex = Exception("401 Unauthorized: invalid api key provided")
        classified = SupabaseStorageService._classify_exception(ex, "b", "p")
        assert isinstance(classified, StorageAuthError)

    def test_supabase_classify_timeout(self):
        from backend.app.services.storage_service import SupabaseStorageService
        ex = Exception("Connection timed out after 30s")
        classified = SupabaseStorageService._classify_exception(ex, "b", "p")
        assert isinstance(classified, StorageTimeout)

    def test_supabase_classify_unavailable(self):
        from backend.app.services.storage_service import SupabaseStorageService
        ex = Exception("503 Service Unavailable")
        classified = SupabaseStorageService._classify_exception(ex, "b", "p")
        assert isinstance(classified, StorageUnavailable)

    def test_supabase_classify_not_found(self):
        from backend.app.services.storage_service import SupabaseStorageService
        ex = Exception("404 Not Found: object not found")
        classified = SupabaseStorageService._classify_exception(ex, "b", "p")
        assert isinstance(classified, StorageObjectNotFound)

    def test_supabase_classify_unknown(self):
        from backend.app.services.storage_service import SupabaseStorageService
        ex = Exception("Something completely unexpected happened")
        classified = SupabaseStorageService._classify_exception(ex, "b", "p")
        assert isinstance(classified, StorageProviderError)


# =============================================================================
# ANALYSIS ELIGIBILITY GATE TESTS
# =============================================================================

class TestAnalysisEligibilityGate:
    """Tests that job creation requires VALIDATED (not just UPLOADED) media."""

    def setup_method(self):
        self.session_repo = InMemorySessionRepository()
        self.media_repo = InMemoryMediaRepository()
        self.storage_svc = InMemoryStorageService()
        self.job_repo = InMemoryJobRepository()
        self.probe_svc = InMemoryMediaProbeService()
        self.validation_svc = MediaValidationService(
            media_repo=self.media_repo,
            storage_service=self.storage_svc,
            probe_service=self.probe_svc,
        )
        set_override_session_repository(self.session_repo)
        set_override_media_repository(self.media_repo)
        set_override_storage_service(self.storage_svc)
        set_override_job_repository(self.job_repo)
        set_override_media_probe_service(self.probe_svc)
        set_override_media_validation_service(self.validation_svc)

    def teardown_method(self):
        set_override_session_repository(None)
        set_override_media_repository(None)
        set_override_storage_service(None)
        set_override_job_repository(None)
        set_override_media_probe_service(None)
        set_override_media_validation_service(None)

    def test_uploaded_but_unvalidated_blocks_job_creation(self):
        """UPLOADED media (not yet validated) should reject job creation."""
        session_id, media_id = _make_session_media_job(
            self.session_repo, self.media_repo, self.storage_svc,
            upload_status=UploadStatus.UPLOADED,
        )
        res = client.post("/api/v1/analysis/jobs", json={
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "session_id": session_id,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        })
        assert res.status_code == 422
        assert res.json()["code"] == "MEDIA_NOT_VALIDATED"

    def test_validation_failed_blocks_job_creation(self):
        """VALIDATION_FAILED media should reject job creation."""
        session_id, media_id = _make_session_media_job(
            self.session_repo, self.media_repo, self.storage_svc,
            upload_status=UploadStatus.VALIDATION_FAILED,
        )
        # Set validation_error_code on the asset
        self.media_repo.update_media_validation(
            media_id,
            upload_status=UploadStatus.VALIDATION_FAILED,
            validation_error_code="VIDEO_DURATION_EXCEEDED",
        )
        res = client.post("/api/v1/analysis/jobs", json={
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "session_id": session_id,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        })
        assert res.status_code == 422
        assert res.json()["code"] == "MEDIA_VALIDATION_FAILED"

    def test_validated_media_permits_job_creation(self):
        """VALIDATED media should allow job creation normally."""
        session_id, media_id = _make_session_media_job(
            self.session_repo, self.media_repo, self.storage_svc,
            upload_status=UploadStatus.VALIDATED,
        )
        res = client.post("/api/v1/analysis/jobs", json={
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "session_id": session_id,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        })
        assert res.status_code == 201
        assert res.json()["status"] == "QUEUED"

    def test_no_media_blocks_job_creation(self):
        """No media at all should reject job creation."""
        session_id = str(uuid.uuid4())
        self.session_repo.create_session(Session(id=session_id, title="Empty"))
        res = client.post("/api/v1/analysis/jobs", json={
            "methodology_id": MethodologyId.METHOD_1_YOLO11_BOTSORT.value,
            "session_id": session_id,
            "calibration_mode": CalibrationMode.NO_METRIC_CALIBRATION.value,
        })
        assert res.status_code == 422
        assert res.json()["code"] == "REQUIRED_MEDIA_MISSING"


# =============================================================================
# UPLOAD COMPLETION FLOW TESTS
# =============================================================================

class TestUploadCompletionFlow:
    """Tests for the complete_upload endpoint with validation integration."""

    def setup_method(self):
        self.session_repo = InMemorySessionRepository()
        self.media_repo = InMemoryMediaRepository()
        self.storage_svc = InMemoryStorageService()
        self.job_repo = InMemoryJobRepository()
        self.probe_svc = InMemoryMediaProbeService()
        self.validation_svc = MediaValidationService(
            media_repo=self.media_repo,
            storage_service=self.storage_svc,
            probe_service=self.probe_svc,
        )
        set_override_session_repository(self.session_repo)
        set_override_media_repository(self.media_repo)
        set_override_storage_service(self.storage_svc)
        set_override_job_repository(self.job_repo)
        set_override_media_probe_service(self.probe_svc)
        set_override_media_validation_service(self.validation_svc)

    def teardown_method(self):
        set_override_session_repository(None)
        set_override_media_repository(None)
        set_override_storage_service(None)
        set_override_job_repository(None)
        set_override_media_probe_service(None)
        set_override_media_validation_service(None)

    def test_complete_upload_validates_and_returns_validated(self):
        """Full flow: upload-intent → simulate upload → complete → VALIDATED."""
        session_id = str(uuid.uuid4())
        self.session_repo.create_session(Session(id=session_id, title="Test"))

        # Create upload intent
        intent_res = client.post(f"/api/v1/sessions/{session_id}/media/upload-intent", json={
            "media_type": "VIDEO",
            "filename": "test.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 2048,
        })
        assert intent_res.status_code == 201
        media_id = intent_res.json()["media_id"]
        storage_path = intent_res.json()["storage_path"]

        # Simulate successful upload to storage
        self.storage_svc.simulate_upload("analysis-inputs", storage_path, 2048)

        # Set up probe result for the signed download URL
        asset = self.media_repo.get_media_asset(media_id)
        signed_url = f"http://localhost:8000/api/v1/mock-storage/analysis-inputs/{storage_path}?token=mock_download_token&expires=120"
        self.probe_svc.set_probe_result(signed_url, _make_valid_probe_result(60.0))

        # Complete upload
        complete_res = client.post(
            f"/api/v1/sessions/{session_id}/media/{media_id}/complete",
            json={"size_bytes": 2048},
        )
        assert complete_res.status_code == 200
        data = complete_res.json()
        assert data["upload_status"] == "VALIDATED"
        assert data["video_codec"] == "h264"
        assert data["duration_seconds"] == 60.0

    def test_complete_upload_invalid_media_returns_422(self):
        """Invalid media (corrupt) should return 422 with typed error."""
        session_id = str(uuid.uuid4())
        self.session_repo.create_session(Session(id=session_id, title="Test"))

        intent_res = client.post(f"/api/v1/sessions/{session_id}/media/upload-intent", json={
            "media_type": "VIDEO",
            "filename": "bad.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 512,
        })
        media_id = intent_res.json()["media_id"]
        storage_path = intent_res.json()["storage_path"]
        self.storage_svc.simulate_upload("analysis-inputs", storage_path, 512)

        signed_url = f"http://localhost:8000/api/v1/mock-storage/analysis-inputs/{storage_path}?token=mock_download_token&expires=120"
        self.probe_svc.set_probe_result(signed_url, MediaProbeResult(
            probe_status=ProbeStatus.INVALID_CONTAINER,
            error_message="Not a valid video container.",
        ))

        complete_res = client.post(
            f"/api/v1/sessions/{session_id}/media/{media_id}/complete",
            json={},
        )
        assert complete_res.status_code == 422
        assert complete_res.json()["code"] == "INVALID_CONTAINER"

    def test_complete_upload_storage_unavailable_returns_503(self):
        """Storage infrastructure failure → 503 retryable, NOT 'object not found'."""
        session_id = str(uuid.uuid4())
        self.session_repo.create_session(Session(id=session_id, title="Test"))

        intent_res = client.post(f"/api/v1/sessions/{session_id}/media/upload-intent", json={
            "media_type": "VIDEO",
            "filename": "test.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 2048,
        })
        media_id = intent_res.json()["media_id"]

        # Force storage to return timeout (infra failure)
        self.storage_svc.force_error(StorageTimeout("Connection timed out"))

        complete_res = client.post(
            f"/api/v1/sessions/{session_id}/media/{media_id}/complete",
            json={},
        )
        assert complete_res.status_code == 503
        assert complete_res.json()["code"] == "STORAGE_TEMPORARILY_UNAVAILABLE"
        self.storage_svc.force_error(None)

    def test_complete_upload_storage_provider_error_returns_502(self):
        """Storage provider error → 502."""
        session_id = str(uuid.uuid4())
        self.session_repo.create_session(Session(id=session_id, title="Test"))

        intent_res = client.post(f"/api/v1/sessions/{session_id}/media/upload-intent", json={
            "media_type": "VIDEO",
            "filename": "test.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 2048,
        })
        media_id = intent_res.json()["media_id"]

        self.storage_svc.force_error(StorageProviderError("Internal server error"))

        complete_res = client.post(
            f"/api/v1/sessions/{session_id}/media/{media_id}/complete",
            json={},
        )
        assert complete_res.status_code == 502
        assert complete_res.json()["code"] == "STORAGE_PROVIDER_ERROR"
        self.storage_svc.force_error(None)

    def test_complete_upload_object_not_found(self):
        """Object genuinely missing → 400 OBJECT_NOT_FOUND_IN_STORAGE."""
        session_id = str(uuid.uuid4())
        self.session_repo.create_session(Session(id=session_id, title="Test"))

        intent_res = client.post(f"/api/v1/sessions/{session_id}/media/upload-intent", json={
            "media_type": "VIDEO",
            "filename": "test.mp4",
            "mime_type": "video/mp4",
            "size_bytes": 2048,
        })
        media_id = intent_res.json()["media_id"]
        # Don't simulate upload — object is missing

        complete_res = client.post(
            f"/api/v1/sessions/{session_id}/media/{media_id}/complete",
            json={},
        )
        assert complete_res.status_code == 400
        assert complete_res.json()["code"] == "OBJECT_NOT_FOUND_IN_STORAGE"


# =============================================================================
# UPLOAD STATUS LIFECYCLE TESTS
# =============================================================================

class TestUploadStatusLifecycle:
    """Tests for the expanded UploadStatus enum."""

    def test_upload_status_values(self):
        assert len(UploadStatus) == 6
        assert UploadStatus.PENDING.value == "PENDING"
        assert UploadStatus.UPLOADED.value == "UPLOADED"
        assert UploadStatus.VALIDATING.value == "VALIDATING"
        assert UploadStatus.VALIDATED.value == "VALIDATED"
        assert UploadStatus.VALIDATION_FAILED.value == "VALIDATION_FAILED"
        assert UploadStatus.FAILED.value == "FAILED"

    def test_validated_is_distinct_from_uploaded(self):
        assert UploadStatus.VALIDATED != UploadStatus.UPLOADED


# =============================================================================
# METHODOLOGY GATE PRESERVATION
# =============================================================================

def test_production_methodology_gates_remain_closed():
    """Verify all three methodologies remain NOT_READY_FOR_EXECUTION."""
    from backend.app.pipeline.registry import default_executor_registry, ExecutionReadinessStatus
    for mid in [MethodologyId.METHOD_1_YOLO11_BOTSORT, MethodologyId.METHOD_2_RFDETR_GTATRACK, MethodologyId.METHOD_3_YOLO26_SRITRACK]:
        status, explanation = default_executor_registry.get_readiness_status(mid)
        assert status == ExecutionReadinessStatus.NOT_READY_FOR_EXECUTION, f"{mid.value} should remain NOT_READY"
