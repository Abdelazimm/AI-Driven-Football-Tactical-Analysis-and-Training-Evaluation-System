"""
Job repository abstraction and implementations (InMemory and Supabase PostgreSQL).
Handles durable job persistence, lifecycle state transitions, and stage progress.
"""
from __future__ import annotations
import json
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict
from datetime import datetime

from backend.app.schemas.job import AnalysisJob, CreateAnalysisJobRequest, JobStatus
from backend.app.schemas.modes import ApplicationMode, CalibrationMode, AudioMode
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.stages import AnalysisStage
from backend.app.schemas.result import AnalysisResult
from backend.app.pipeline.registry import resolve_methodology


class InvalidJobTransitionError(Exception):
    """Raised when an illegal job lifecycle state transition is requested."""
    def __init__(self, job_id: str, current_status: JobStatus, target_status: JobStatus, reason: str = ""):
        self.job_id = job_id
        self.current_status = current_status
        self.target_status = target_status
        msg = f"Cannot transition job '{job_id}' from {current_status.value} to {target_status.value}."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


TERMINAL_JOB_STATUSES = {
    JobStatus.COMPLETED,
    JobStatus.COMPLETED_WITH_LIMITATIONS,
    JobStatus.FAILED,
}


class AnalysisJobRepository(ABC):
    """
    Abstract interface for analysis job and result storage operations.
    Hides storage implementation behind a clean domain interface.
    """

    @abstractmethod
    async def create_job(self, request: CreateAnalysisJobRequest) -> AnalysisJob:
        """Create and store a new analysis job."""
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """Retrieve an analysis job by ID."""
        pass

    @abstractmethod
    async def update_job_lifecycle(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        current_stage: Optional[AnalysisStage] = None,
        progress_percent: Optional[float] = None,
        stage_message: Optional[str] = None,
        modal_call_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_details: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> AnalysisJob:
        """Update job lifecycle status, stage, progress, or diagnostic errors."""
        pass

    @abstractmethod
    async def get_result(self, job_id: str) -> Optional[AnalysisResult]:
        """Retrieve an analysis result by job ID, if computed."""
        pass

    @abstractmethod
    async def store_result(self, result: AnalysisResult) -> AnalysisResult:
        """Persist an analysis result."""
        pass


class InMemoryJobRepository(AnalysisJobRepository):
    """
    DEVELOPMENT ONLY: In-memory job repository for testing.
    Resets on process restart. Zero external persistence.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, AnalysisJob] = {}
        self._results: Dict[str, AnalysisResult] = {}

    async def create_job(self, request: CreateAnalysisJobRequest) -> AnalysisJob:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

        # Infer operating application mode from calibration
        if request.calibration_mode == CalibrationMode.NO_METRIC_CALIBRATION:
            app_mode = ApplicationMode.ANALYSIS_WITHOUT_METRICS
        else:
            app_mode = ApplicationMode.AUTOMATED_ANALYSIS

        now = datetime.utcnow()
        job = AnalysisJob(
            id=job_id,
            session_id=session_id,
            methodology_id=resolve_methodology(request.methodology_id),
            mode=app_mode,
            calibration_mode=request.calibration_mode,
            audio_mode=request.audio_mode,
            status=JobStatus.QUEUED,
            current_stage=AnalysisStage.UPLOADED,
            progress_percent=0.0,
            stage_message="Job registered; awaiting video ingestion.",
            created_at=now,
            updated_at=now,
        )
        self._jobs[job_id] = job
        return job

    async def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        return self._jobs.get(job_id)

    async def update_job_lifecycle(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        current_stage: Optional[AnalysisStage] = None,
        progress_percent: Optional[float] = None,
        stage_message: Optional[str] = None,
        modal_call_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_details: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> AnalysisJob:
        current_job = self._jobs.get(job_id)
        if not current_job:
            raise RuntimeError(f"Job '{job_id}' not found for lifecycle update.")

        # State transition validation
        if current_job.status in TERMINAL_JOB_STATUSES:
            if status is not None and status != current_job.status:
                raise InvalidJobTransitionError(
                    job_id, current_job.status, status, "Terminal job status cannot be transitioned."
                )
            if status is None and (current_stage is not None or progress_percent is not None):
                raise InvalidJobTransitionError(
                    job_id, current_job.status, current_job.status, "Cannot modify stage/progress of a terminal job."
                )

        now = datetime.utcnow()
        target_status = status if status is not None else current_job.status
        final_completed_at = completed_at or current_job.completed_at
        if target_status in TERMINAL_JOB_STATUSES and final_completed_at is None:
            final_completed_at = now

        updated_job = current_job.model_copy(
            update={
                "status": target_status,
                "current_stage": current_stage if current_stage is not None else current_job.current_stage,
                "progress_percent": (
                    max(0.0, min(100.0, float(progress_percent)))
                    if progress_percent is not None
                    else current_job.progress_percent
                ),
                "stage_message": stage_message if stage_message is not None else current_job.stage_message,
                "modal_call_id": modal_call_id if modal_call_id is not None else current_job.modal_call_id,
                "error_code": error_code if error_code is not None else current_job.error_code,
                "error_details": error_details if error_details is not None else current_job.error_details,
                "completed_at": final_completed_at,
                "updated_at": now,
            }
        )
        self._jobs[job_id] = updated_job
        return updated_job

    async def get_result(self, job_id: str) -> Optional[AnalysisResult]:
        return self._results.get(job_id)

    async def store_result(self, result: AnalysisResult) -> AnalysisResult:
        self._results[result.job_id] = result
        return result

    # Helper method for tests
    def store_result_for_testing(self, job_id: str, result: AnalysisResult) -> None:
        """Testing utility to associate a test result with a job."""
        self._results[job_id] = result

    def clear(self) -> None:
        self._jobs.clear()
        self._results.clear()


# Alias for explicit naming consistency
InMemoryAnalysisJobRepository = InMemoryJobRepository


class SupabaseAnalysisJobRepository(AnalysisJobRepository):
    """
    Supabase PostgreSQL implementation of AnalysisJobRepository.
    Provides durable persistence for jobs across server restarts and browser refreshes.
    """

    def __init__(self, client) -> None:
        self._client = client
        self._results_cache: Dict[str, AnalysisResult] = {}

    async def create_job(self, request: CreateAnalysisJobRequest) -> AnalysisJob:
        job_id = str(uuid.uuid4())

        # Infer operating application mode from calibration
        if request.calibration_mode == CalibrationMode.NO_METRIC_CALIBRATION:
            app_mode = ApplicationMode.ANALYSIS_WITHOUT_METRICS
        else:
            app_mode = ApplicationMode.AUTOMATED_ANALYSIS

        now = datetime.utcnow()
        job = AnalysisJob(
            id=job_id,
            session_id=request.session_id,
            methodology_id=resolve_methodology(request.methodology_id),
            mode=app_mode,
            calibration_mode=request.calibration_mode,
            audio_mode=request.audio_mode,
            status=JobStatus.QUEUED,
            current_stage=AnalysisStage.UPLOADED,
            progress_percent=0.0,
            stage_message="Job registered; awaiting video ingestion.",
            created_at=now,
            updated_at=now,
        )

        payload = {
            "id": job.id,
            "session_id": job.session_id,
            "methodology_id": job.methodology_id.value,
            "application_mode": job.mode.value,
            "calibration_mode": job.calibration_mode.value,
            "audio_mode": request.audio_mode.value,
            "status": job.status.value,
            "current_stage": job.current_stage.value,
            "progress_percent": job.progress_percent,
            "stage_message": job.stage_message,
            "modal_call_id": job.modal_call_id,
            "error_code": job.error_code,
            "error_details": job.error_details,
            "completed_at": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        res = self._client.table("analysis_jobs").insert(payload).execute()
        if not res.data:
            raise RuntimeError(f"Failed to insert job into Supabase: {res}")
        return job

    async def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        res = self._client.table("analysis_jobs").select("*").eq("id", job_id).execute()
        if not res.data or len(res.data) == 0:
            return None
        row = res.data[0]
        completed_at_raw = row.get("completed_at")
        completed_at = (
            datetime.fromisoformat(completed_at_raw.replace("Z", "+00:00"))
            if completed_at_raw
            else None
        )
        return AnalysisJob(
            id=row["id"],
            session_id=row["session_id"],
            methodology_id=MethodologyId(row["methodology_id"]),
            mode=ApplicationMode(row.get("application_mode", ApplicationMode.AUTOMATED_ANALYSIS.value)),
            calibration_mode=CalibrationMode(row.get("calibration_mode", CalibrationMode.NO_METRIC_CALIBRATION.value)),
            audio_mode=AudioMode(row.get("audio_mode", AudioMode.EXTRACT_FROM_VIDEO.value)),
            status=JobStatus(row.get("status", JobStatus.QUEUED.value)),
            current_stage=AnalysisStage(row.get("current_stage", AnalysisStage.UPLOADED.value)),
            progress_percent=float(row.get("progress_percent") if row.get("progress_percent") is not None else 0.0),
            stage_message=row.get("stage_message"),
            modal_call_id=row.get("modal_call_id"),
            error_code=row.get("error_code"),
            error_details=row.get("error_details"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
            completed_at=completed_at,
        )

    async def update_job_lifecycle(
        self,
        job_id: str,
        *,
        status: Optional[JobStatus] = None,
        current_stage: Optional[AnalysisStage] = None,
        progress_percent: Optional[float] = None,
        stage_message: Optional[str] = None,
        modal_call_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_details: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> AnalysisJob:
        current_job = await self.get_job(job_id)
        if not current_job:
            raise RuntimeError(f"Job '{job_id}' not found for lifecycle update.")

        # State transition validation
        if current_job.status in TERMINAL_JOB_STATUSES:
            if status is not None and status != current_job.status:
                raise InvalidJobTransitionError(
                    job_id, current_job.status, status, "Terminal job status cannot be transitioned."
                )
            if status is None and (current_stage is not None or progress_percent is not None):
                raise InvalidJobTransitionError(
                    job_id, current_job.status, current_job.status, "Cannot modify stage/progress of a terminal job."
                )

        now = datetime.utcnow()
        updates = {"updated_at": now.isoformat()}
        if status is not None:
            updates["status"] = status.value
        if current_stage is not None:
            updates["current_stage"] = current_stage.value
        if progress_percent is not None:
            updates["progress_percent"] = max(0.0, min(100.0, float(progress_percent)))
        if stage_message is not None:
            updates["stage_message"] = stage_message
        if modal_call_id is not None:
            updates["modal_call_id"] = modal_call_id
        if error_code is not None:
            updates["error_code"] = error_code
        if error_details is not None:
            updates["error_details"] = error_details

        target_status = status if status is not None else current_job.status
        if completed_at is not None:
            updates["completed_at"] = completed_at.isoformat()
        elif target_status in TERMINAL_JOB_STATUSES and current_job.completed_at is None:
            updates["completed_at"] = now.isoformat()

        res = self._client.table("analysis_jobs").update(updates).eq("id", job_id).execute()
        if not res.data:
            raise RuntimeError(f"Failed to update lifecycle for job {job_id}")

        updated_job = await self.get_job(job_id)
        if not updated_job:
            raise RuntimeError(f"Failed to reload updated job {job_id}")
        return updated_job

    async def store_result(self, result: AnalysisResult) -> AnalysisResult:
        """
        Persist canonical result and supporting artifacts in private Storage.
        The deployed schema migrations do not define an analysis_results table.
        """
        if result.execution_manifest is None or result.structured_evidence is None:
            raise ValueError("Canonical remote result requires execution manifest and structured evidence")
        root = f"jobs/{result.job_id}"
        artifacts = {
            f"{root}/results/result.json": (result.model_dump_json(indent=2).encode("utf-8"), "application/json"),
            f"{root}/reports/coach_report.md": (result.report_markdown.encode("utf-8"), "text/markdown"),
            f"{root}/reports/report_metadata.json": (json.dumps({
                "job_id": result.job_id,
                "report_status": result.report_status.value,
                "limitations": [lim.model_dump(mode="json") for lim in result.limitations],
            }, sort_keys=True).encode("utf-8"), "application/json"),
            f"{root}/logs/execution_manifest.json": (result.execution_manifest.model_dump_json(indent=2).encode("utf-8"), "application/json"),
        }
        bucket = self._client.storage.from_("analysis-outputs")
        result_path = f"{root}/results/result.json"
        # The canonical JSON is uploaded last as a retrieval commit marker.
        for path in [p for p in artifacts if p != result_path] + [result_path]:
            data, content_type = artifacts[path]
            try:
                bucket.upload(path=path, file=data, file_options={"upsert": "false", "content-type": content_type})
            except Exception:
                # Identical retries are safe; different bytes cannot overwrite a result.
                if bucket.download(path) != data:
                    raise
        self._results_cache[result.job_id] = result
        return result

    async def get_result(self, job_id: str) -> Optional[AnalysisResult]:
        if job_id in self._results_cache:
            return self._results_cache[job_id]
        path = f"jobs/{job_id}/results/result.json"
        bucket = self._client.storage.from_("analysis-outputs")
        matches = bucket.list(f"jobs/{job_id}/results", {"search": "result.json", "limit": 5})
        if not any(item.get("name") == "result.json" for item in matches):
            return None
        parsed = AnalysisResult.model_validate_json(bucket.download(path))
        if parsed.job_id != job_id:
            raise ValueError("Stored result job ID does not match requested job")
        self._results_cache[job_id] = parsed
        return parsed
