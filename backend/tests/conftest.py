import pytest
from pathlib import Path
from backend.app.services.media_probe import MediaProbeResult, ProbeStatus
from backend.app.api.deps import (
    set_override_job_repository,
    set_override_session_repository,
    set_override_media_repository,
    set_override_storage_service,
    set_override_dispatch_repository,
    set_override_modal_client,
    set_override_media_probe_service,
    _in_memory_jobs,
    _in_memory_sessions,
    _in_memory_media,
    _in_memory_storage,
    _in_memory_dispatch,
    _in_memory_modal,
    _in_memory_probe,
)


@pytest.fixture(autouse=True)
def use_test_repositories(monkeypatch):
    """
    Ensure offline unit/contract tests use isolated in-memory doubles
    to avoid querying unmigrated live database tables or polluting production state.
    """
    # Local integration fixtures may read frozen checkpoints from the research
    # reference. Production runners themselves have no research-drive paths.
    research = Path("G:/My Drive/Football_Training_Assistant_MVP/methodology_comparison/runs/method_2")
    detector = research / "M2_FORMAL_001_DOMAIN_ADAPTED/checkpoint_best_total.pth"
    reid = research / "M2_P0_preflight/checkpoints/sports_model.pth.tar-60"
    if detector.is_file() and reid.is_file():
        monkeypatch.setenv("M2_DETECTOR_PATH", str(detector))
        monkeypatch.setenv("M2_REID_PATH", str(reid))
    _in_memory_jobs.clear() if hasattr(_in_memory_jobs, "clear") else None
    _in_memory_sessions.clear()
    _in_memory_media.clear()
    _in_memory_storage.clear()
    _in_memory_dispatch.clear()
    _in_memory_modal.set_configured(True)
    _in_memory_modal.set_force_failure(False)

    _in_memory_probe.clear()
    _in_memory_probe.set_default_result(
        MediaProbeResult(
            probe_status=ProbeStatus.SUCCESS,
            container_format="mov,mp4,m4a,3gp,3g2,mj2",
            duration_seconds=120.0,
            video_streams=1,
            audio_streams=1,
            video_codec="h264",
            audio_codec="aac",
            width=1920,
            height=1080,
            fps=30.0,
        )
    )

    set_override_job_repository(_in_memory_jobs)
    set_override_session_repository(_in_memory_sessions)
    set_override_media_repository(_in_memory_media)
    set_override_storage_service(_in_memory_storage)
    set_override_dispatch_repository(_in_memory_dispatch)
    set_override_modal_client(_in_memory_modal)
    set_override_media_probe_service(_in_memory_probe)
    yield
    set_override_job_repository(None)
    set_override_session_repository(None)
    set_override_media_repository(None)
    set_override_storage_service(None)
    set_override_dispatch_repository(None)
    set_override_modal_client(None)
    set_override_media_probe_service(None)
