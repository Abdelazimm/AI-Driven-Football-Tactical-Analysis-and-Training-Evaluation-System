from __future__ import annotations
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.modes import ApplicationMode, CalibrationMode
from backend.app.schemas.methodology import MethodologyId
from backend.app.schemas.stages import AnalysisStage
from backend.app.schemas.job import JobStatus
from backend.app.schemas.confidence import ReportStatus
from backend.app.schemas.identity import IdentityEvaluation
from backend.app.schemas.kinematics import MovementMetric
from backend.app.schemas.instruction import InstructionEvent
from backend.app.schemas.limitation import AnalysisLimitation
from backend.app.schemas.evaluation import EvaluationMetrics
from backend.app.schemas.artifact import ArtifactReference
from backend.app.schemas.manifest import JobExecutionManifest


class AnalysisResult(BaseModel):
    id: str = Field(..., description="Unique result identifier")
    session_id: str = Field(..., description="Associated session identifier")
    job_id: str = Field(..., description="Associated job identifier")
    methodology_id: MethodologyId = Field(
        default=MethodologyId.METHOD_1_YOLO11_BOTSORT,
        description="Computer-vision methodology pipeline used"
    )
    application_mode: ApplicationMode = Field(..., description="Application mode used")
    calibration_mode: CalibrationMode = Field(
        default=CalibrationMode.NO_METRIC_CALIBRATION,
        description="Operating calibration mode used"
    )
    job_status: JobStatus = Field(..., description="Final job status (e.g. COMPLETED or COMPLETED_WITH_LIMITATIONS)")
    identity_evaluation: IdentityEvaluation = Field(..., description="Persistent identity evaluation and safety gate record")
    evaluation_metrics: Optional[EvaluationMetrics] = Field(None, description="Detailed scientific evaluation metrics")
    metrics: Dict[str, MovementMetric] = Field(default_factory=dict, description="Calculated movement metrics")
    instruction_events: List[InstructionEvent] = Field(default_factory=list, description="Extracted instruction events")
    limitations: List[AnalysisLimitation] = Field(default_factory=list, description="Active analysis limitations")
    artifact_references: List[ArtifactReference] = Field(default_factory=list, description="Associated artifact references")
    report_markdown: Optional[str] = Field(None, description="Grounded coach evaluation report in Markdown")
    report_status: ReportStatus = Field(
        default=ReportStatus.DETERMINISTIC_FALLBACK,
        description="Status of the generated report"
    )
    execution_manifest: Optional[JobExecutionManifest] = Field(None, description="Dynamic job execution manifest")
    structured_evidence: Optional[Dict[str, Any]] = Field(None, description="Structured multimodal evidence payload")
    created_at: datetime = Field(default_factory=datetime.utcnow)


AnalysisResult.model_rebuild()
