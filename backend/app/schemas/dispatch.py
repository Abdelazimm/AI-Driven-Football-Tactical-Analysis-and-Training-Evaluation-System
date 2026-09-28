"""
Worker dispatch contracts.
Defines provider-level execution state and dispatch request/response models.
CRITICAL: WorkerDispatchState is provider execution state.
It must NEVER be confused or overloaded with JobStatus or AnalysisStage.
"""
from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.job import JobStatus
from backend.app.schemas.stages import AnalysisStage


class WorkerDispatchState(str, Enum):
    """
    Provider-level execution lifecycle states.
    Strictly separate from JobStatus (lifecycle) and AnalysisStage (pipeline stage).
    """
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkerDispatchRequest(BaseModel):
    """Internal request to dispatch a job to a serverless worker provider."""
    job_id: str = Field(..., description="UUID of the analysis job")
    session_id: str = Field(..., description="UUID of the session")
    methodology_id: MethodologyId = Field(..., description="Methodology to execute")
    dispatch_id: Optional[str] = None
    video_storage_bucket: Optional[str] = None
    video_storage_path: Optional[str] = None
    audio_storage_bucket: Optional[str] = None
    audio_storage_path: Optional[str] = None
    callback_url: Optional[str] = None
    calibration_mode: str = "NO_METRIC_CALIBRATION"
    application_mode: str = "AUTOMATED_ANALYSIS"
    audio_mode: str = "EXTRACT_FROM_VIDEO"
    start_frame: int = Field(0, ge=0)
    max_frames: Optional[int] = Field(None, gt=0)
    audio_source_offset_s: float = Field(0.0, ge=0.0)
    video_source_offset_s: float = Field(0.0, ge=0.0)
    force_deterministic_fallback: bool = False
    input_asset_role: Optional[str] = None
    authoritative_source_sha256: Optional[str] = Field(None, pattern=r"^[0-9a-f]{64}$")
    transport_copy_sha256: Optional[str] = Field(None, pattern=r"^[0-9a-f]{64}$")

    @property
    def has_transport_provenance(self) -> bool:
        return self.input_asset_role == "DERIVED_TRANSPORT_COPY" and bool(
            self.authoritative_source_sha256 and self.transport_copy_sha256
        )


class WorkerDispatch(BaseModel):
    """Durable domain model for a worker dispatch attempt."""
    id: str = Field(..., description="Dispatch UUID")
    job_id: str = Field(..., description="Associated analysis job UUID")
    provider: str = Field(default="MODAL", description="Compute provider")
    provider_execution_id: Optional[str] = Field(None, description="External provider execution/call ID")
    state: WorkerDispatchState = Field(default=WorkerDispatchState.CREATED, description="Dispatch lifecycle state")
    attempt: int = Field(default=1, ge=1, description="Execution attempt number")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="When worker execution commenced")
    finished_at: Optional[datetime] = Field(None, description="When worker execution finalized")
    error_code: Optional[str] = Field(None, description="Normalized error code if failed")
    error_message: Optional[str] = Field(None, description="Technical diagnostics if failed")


class WorkerDispatchResponse(BaseModel):
    """Public API response confirming dispatch registration or retrieval."""
    dispatch_id: str = Field(..., description="Dispatch UUID")
    job_id: str = Field(..., description="Analysis job UUID")
    provider: str = Field(default="MODAL", description="Execution provider")
    provider_execution_id: Optional[str] = Field(None, description="Provider execution call identifier")
    state: WorkerDispatchState = Field(..., description="Current dispatch state")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: Optional[str] = Field(None, description="Informational message (e.g. idempotency confirmation)")


class WorkerProgressCallbackRequest(BaseModel):
    """
    Authenticated callback payload sent by serverless workers during execution.
    Transfers progress, stage transition, and terminal status/error diagnostics.
    """
    job_id: str = Field(..., description="Target analysis job UUID")
    dispatch_id: str = Field(..., description="Target worker dispatch UUID")
    dispatch_state: WorkerDispatchState = Field(..., description="Worker dispatch state")
    current_stage: AnalysisStage = Field(..., description="Current pipeline execution stage")
    progress_percent: float = Field(..., ge=0.0, le=100.0, description="Stage execution progress percentage (0.0 to 100.0)")
    job_status: Optional[JobStatus] = Field(None, description="Optional target job status (e.g. COMPLETED or FAILED)")
    stage_message: Optional[str] = Field(None, description="Descriptive execution progress message")
    error_code: Optional[str] = Field(None, description="Standardized error code if worker failed")
    error_details: Optional[str] = Field(None, description="Diagnostic error details or traceback if worker failed")


class WorkerProgressCallbackResponse(BaseModel):
    """Response returned to serverless worker acknowledging progress receipt."""
    job_id: str = Field(..., description="Analysis job UUID")
    dispatch_id: str = Field(..., description="Worker dispatch UUID")
    dispatch_state: WorkerDispatchState = Field(..., description="Acknowledged worker dispatch state")
    job_status: JobStatus = Field(..., description="Current job status")
    current_stage: AnalysisStage = Field(..., description="Current pipeline stage")
    progress_percent: float = Field(..., description="Current recorded progress percentage")
    message: str = Field(..., description="Status summary or idempotency acknowledgment message")
