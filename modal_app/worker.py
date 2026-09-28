"""Modal functions for infrastructure checks and bounded production analysis."""
import hashlib
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from modal_app.app import app, cpu_image, model_volume, worker_image, worker_secret
from modal_app.contracts import InfrastructureSmokeRequest, InfrastructureSmokeResponse, WorkerExecutionResponse


CHECKPOINTS = {
    "checkpoint_best_total.pth": (134747227, "7539cfb3eca3125136c1446d7a522a5a46abb14136d55f79aec8daececc00b85"),
    "sports_model.pth.tar-60": (30393613, "8d5b2fd8763db34c2aad69810466adf413f0426d9f8119d322227e0e639c5fbd"),
}


def verify_m2_checkpoints(root: Path) -> dict:
    """Fail closed unless mounted files match the frozen M2 artifacts."""
    files = {}
    for name, (size, digest) in CHECKPOINTS.items():
        path = root / name
        if not path.is_file() or path.stat().st_size != size:
            raise RuntimeError(f"M2_CHECKPOINT_MISSING_OR_SIZE_MISMATCH: {name}")
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        actual = hasher.hexdigest()
        if actual != digest:
            raise RuntimeError(f"M2_CHECKPOINT_HASH_MISMATCH: {name}")
        files[name] = {"size_bytes": size, "sha256": actual, "path": str(path)}
    return files


@app.function(image=cpu_image, cpu=1.0, memory=512, timeout=60)
def infrastructure_smoke(payload: dict) -> dict:
    req = InfrastructureSmokeRequest(**payload)
    return InfrastructureSmokeResponse(
        test_id=req.test_id, server_timestamp=datetime.now(timezone.utc).isoformat(),
        environment="modal_serverless_cpu", python_version=sys.version.split()[0],
        status="SUCCESS", cpu_only=True, marker=req.marker,
    ).model_dump()


@app.function(image=cpu_image, volumes={"/data/models": model_volume}, timeout=180)
def m2_model_preflight() -> dict:
    return {"status": "PASS", "environment": "modal_remote_volume", "files": verify_m2_checkpoints(Path("/data/models/m2"))}


@app.function(image=worker_image, gpu="T4", volumes={"/data/models": model_volume}, timeout=300)
def m2_runtime_preflight() -> dict:
    import subprocess
    import torch
    import torchvision
    import cv2
    import scipy
    import sklearn
    import rfdetr
    import ultralytics
    import faster_whisper
    import ctranslate2
    import supabase
    from backend.app.runners.m2_runner import M2VisionRunner

    M2VisionRunner()._setup_m2_imports()
    return {
        "status": "PASS", "python": sys.version.split()[0],
        "torch": torch.__version__, "torchvision": torchvision.__version__,
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "ffmpeg": subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True).stdout.decode().splitlines()[0],
        "checkpoint_files": verify_m2_checkpoints(Path(os.environ["M2_MODEL_ROOT"])),
    }


@app.function(image=cpu_image, cpu=1.0, memory=512, timeout=60)
def dispatch_placeholder(payload: dict) -> dict:
    """Legacy infrastructure probe, never called by ProductionModalClient."""
    return {"status": "DISPATCH_ACKNOWLEDGED", "job_id": payload.get("job_id")}


def _post_progress(req, *, stage, percent, state="RUNNING", job_status=None, message=None, error_code=None, error_details=None):
    from backend.app.schemas.dispatch import WorkerProgressCallbackRequest, WorkerDispatchState
    from backend.app.schemas.stages import AnalysisStage
    from backend.app.schemas.job import JobStatus

    body = WorkerProgressCallbackRequest(
        job_id=req.job_id, dispatch_id=req.dispatch_id,
        dispatch_state=WorkerDispatchState(state), current_stage=AnalysisStage(stage),
        progress_percent=percent, job_status=JobStatus(job_status) if job_status else None,
        stage_message=message, error_code=error_code, error_details=error_details,
    )
    response = httpx.post(
        req.callback_url, json=body.model_dump(mode="json"),
        headers={"X-Worker-Secret": os.environ["WORKER_CALLBACK_SECRET"]}, timeout=30.0,
    )
    response.raise_for_status()
    acknowledgement = response.json()
    if acknowledgement.get("job_id") != req.job_id or acknowledgement.get("dispatch_id") != req.dispatch_id:
        raise RuntimeError("Worker callback acknowledgement ownership mismatch")
    return acknowledgement


@app.function(
    image=worker_image, gpu="T4", cpu=4.0, memory=16384,
    volumes={"/data/models": model_volume}, secrets=[worker_secret], timeout=10800,
)
def execute_analysis_worker(payload: dict) -> dict:
    """Download private media, run M2, persist, then send terminal callback."""
    from supabase import create_client
    from backend.app.schemas.dispatch import WorkerDispatchRequest
    from backend.app.pipeline.orchestrator import execute_analysis_job
    from backend.app.services.job_repository import SupabaseAnalysisJobRepository

    req = WorkerDispatchRequest.model_validate(payload)
    if req.input_asset_role == "DERIVED_TRANSPORT_COPY" and not req.has_transport_provenance:
        raise ValueError("Derived transport copy requires both source and copy SHA-256 provenance")
    if not (req.dispatch_id and req.callback_url and req.video_storage_bucket and req.video_storage_path):
        raise ValueError("Production worker requires dispatch, callback, and private video storage references")
    if req.video_storage_bucket != "analysis-inputs" or (req.audio_storage_bucket and req.audio_storage_bucket != "analysis-inputs"):
        raise ValueError("Production worker accepts only private analysis-inputs media")

    timings = {}
    last_progress = 0.0
    started = time.monotonic()
    temp_dir = Path(tempfile.mkdtemp(prefix="football_worker_"))
    try:
        _post_progress(req, stage="VALIDATING", percent=5.0, message="Worker acquired job.")
        last_progress = 5.0
        client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
        video_path = temp_dir / "video.mp4"
        video_path.write_bytes(client.storage.from_(req.video_storage_bucket).download(req.video_storage_path))
        if not video_path.stat().st_size:
            raise RuntimeError("Remote video download was empty")
        if req.input_asset_role == "DERIVED_TRANSPORT_COPY":
            downloaded_sha256 = hashlib.sha256(video_path.read_bytes()).hexdigest()
            if downloaded_sha256 != req.transport_copy_sha256:
                raise RuntimeError("TRANSPORT_COPY_SHA256_MISMATCH")
        audio_path = None
        if req.audio_storage_path:
            audio_path = temp_dir / "audio.wav"
            audio_path.write_bytes(client.storage.from_(req.audio_storage_bucket).download(req.audio_storage_path))
            if not audio_path.stat().st_size:
                raise RuntimeError("Remote audio download was empty")
        timings["media_acquisition_s"] = round(time.monotonic() - started, 3)

        model_started = time.monotonic()
        files = verify_m2_checkpoints(Path(os.environ["M2_MODEL_ROOT"]))
        timings["model_verification_s"] = round(time.monotonic() - model_started, 3)

        def progress(stage, percent, message):
            nonlocal last_progress
            stage_value = stage.value if hasattr(stage, "value") else str(stage)
            safe_percent = min(float(percent), 99.0)
            _post_progress(req, stage=stage_value, percent=safe_percent, message=message)
            last_progress = safe_percent

        pipeline_started = time.monotonic()
        result = execute_analysis_job(
            job_id=req.job_id, session_id=req.session_id,
            video_path=video_path, audio_path=audio_path,
            methodology=req.methodology_id, calibration_mode=req.calibration_mode,
            application_mode=req.application_mode, audio_mode=req.audio_mode,
            start_frame=req.start_frame, max_frames=req.max_frames,
            progress_callback=progress,
            force_deterministic_fallback=req.force_deterministic_fallback,
            audio_source_offset_s=req.audio_source_offset_s,
            video_source_offset_s=req.video_source_offset_s,
            input_asset_role=req.input_asset_role,
            authoritative_source_sha256=req.authoritative_source_sha256,
            transport_copy_sha256=req.transport_copy_sha256,
        )
        timings["pipeline_s"] = round(time.monotonic() - pipeline_started, 3)
        persistence_started = time.monotonic()
        repository = SupabaseAnalysisJobRepository(client)
        import asyncio
        asyncio.run(repository.store_result(result))
        stored = asyncio.run(SupabaseAnalysisJobRepository(client).get_result(req.job_id))
        if stored is None or stored.model_dump(mode="json") != result.model_dump(mode="json"):
            raise RuntimeError("Persisted canonical result readback mismatch")
        timings["persistence_s"] = round(time.monotonic() - persistence_started, 3)
        _post_progress(
            req, stage="UPLOADING_RESULTS", percent=100.0,
            state="SUCCEEDED", job_status=result.job_status.value,
            message="Canonical result persisted and verified.",
        )
        timings["total_s"] = round(time.monotonic() - started, 3)
        response = WorkerExecutionResponse(
            job_id=req.job_id, provider_execution_id=req.dispatch_id,
            status=result.job_status.value, stage="UPLOADING_RESULTS",
        ).model_dump()
        response.update({"timings": timings, "checkpoint_files": files, "result_path": f"jobs/{req.job_id}/results/result.json"})
        return response
    except Exception as exc:
        try:
            _post_progress(
                req, stage="UPLOADING_RESULTS", percent=100.0,
                state="FAILED", job_status="FAILED", message="Worker execution failed.",
                error_code="WORKER_EXECUTION_FAILURE", error_details=str(exc)[:1000],
            )
        except Exception as callback_exc:
            raise RuntimeError(f"Worker failure and callback delivery failure: {type(exc).__name__}; {type(callback_exc).__name__}") from callback_exc
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
