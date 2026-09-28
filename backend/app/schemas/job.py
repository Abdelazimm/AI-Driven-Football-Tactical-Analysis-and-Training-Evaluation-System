from __future__ import annotations
from typing import Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from backend.app.schemas.modes import ApplicationMode, CalibrationMode, AudioMode
from backend.app.schemas.stages import AnalysisStage
from backend.app.schemas.methodology import MethodologyId


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_LIMITATIONS = "COMPLETED_WITH_LIMITATIONS"
    FAILED = "FAILED"


class CreateAnalysisJobRequest(BaseModel):
    """
    Public API request schema to register a new analysis job.
    CRITICAL: methodology_id is REQUIRED. No silent default to Method 1.
    """
    methodology_id: Union[MethodologyId, Literal["AUTO"]] = Field(..., description="Explicit methodology or AUTO selection (required)")
    session_id: str = Field(..., description="Associated session UUID (required)")
    calibration_mode: CalibrationMode = Field(default=CalibrationMode.NO_METRIC_CALIBRATION, description="Operating pitch calibration mode")
    audio_mode: AudioMode = Field(default=AudioMode.EXTRACT_FROM_VIDEO, description="Coach audio source mode")
    video_file_name: Optional[str] = Field(None, description="Optional original video filename")


class AnalysisJob(BaseModel):
    id: str = Field(..., description="Unique job identifier")
    session_id: str = Field(..., description="Associated session identifier")
    methodology_id: MethodologyId = Field(
        default=MethodologyId.METHOD_1_YOLO11_BOTSORT,
        description="Computer-vision methodology pipeline to run"
    )
    mode: ApplicationMode = Field(..., description="Operating application mode")
    calibration_mode: CalibrationMode = Field(..., description="Operating calibration mode")
    audio_mode: AudioMode = Field(default=AudioMode.EXTRACT_FROM_VIDEO, description="Persisted coach audio source mode")
    status: JobStatus = Field(default=JobStatus.QUEUED, description="Job lifecycle status")
    current_stage: AnalysisStage = Field(default=AnalysisStage.UPLOADED, description="Current pipeline execution stage")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage (0.0 to 100.0)")
    stage_message: Optional[str] = Field(None, description="Human-readable stage progress message")
    modal_call_id: Optional[str] = Field(None, description="Modal serverless invocation call ID")
    error_code: Optional[str] = Field(None, description="Failure error code if FAILED")
    error_details: Optional[str] = Field(None, description="Detailed stack trace or failure context")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="Timestamp of completion")
