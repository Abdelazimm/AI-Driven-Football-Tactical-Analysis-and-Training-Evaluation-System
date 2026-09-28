"""
Modal Worker Contracts.
Defines typed request and response schemas for Modal serverless execution.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class InfrastructureSmokeRequest(BaseModel):
    """Payload sent to verify Modal CPU worker infrastructure connectivity."""
    test_id: str = Field(..., description="Unique test invocation identifier")
    client_timestamp: str = Field(..., description="ISO timestamp of caller")
    marker: str = Field(default="PHASE_4A_INFRA_SMOKE", description="Verification marker")


class InfrastructureSmokeResponse(BaseModel):
    """Payload returned by Modal CPU worker proving successful remote execution."""
    test_id: str = Field(..., description="Echoed test invocation identifier")
    server_timestamp: str = Field(..., description="ISO timestamp recorded inside Modal container")
    environment: str = Field(..., description="Execution environment tag")
    python_version: str = Field(..., description="Python runtime version in Modal container")
    status: str = Field(default="SUCCESS", description="Execution outcome status")
    cpu_only: bool = Field(default=True, description="Confirmation that no GPU was allocated")
    marker: str = Field(..., description="Echoed verification marker")


class WorkerExecutionRequest(BaseModel):
    """Future full analysis execution request sent to Modal worker."""
    job_id: str = Field(..., description="Analysis job UUID")
    session_id: str = Field(..., description="Associated session UUID")
    methodology_id: str = Field(..., description="Canonical methodology identifier")
    calibration_mode: str = Field(..., description="Pitch calibration mode")
    audio_mode: str = Field(..., description="Coach audio handling mode")
    video_storage_path: str = Field(..., description="Storage path in analysis-inputs bucket")
    audio_storage_path: Optional[str] = Field(None, description="Optional audio storage path")


class WorkerExecutionResponse(BaseModel):
    """Future response returned by Modal worker upon completion."""
    job_id: str
    provider_execution_id: str
    status: str
    stage: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
