"""
Modal Serverless Application Package.
Hosts remote execution definitions for football tactical analysis.
"""
from modal_app.app import app, cpu_image
from modal_app.contracts import (
    InfrastructureSmokeRequest,
    InfrastructureSmokeResponse,
    WorkerExecutionRequest,
    WorkerExecutionResponse,
)

__all__ = [
    "app",
    "cpu_image",
    "InfrastructureSmokeRequest",
    "InfrastructureSmokeResponse",
    "WorkerExecutionRequest",
    "WorkerExecutionResponse",
]
