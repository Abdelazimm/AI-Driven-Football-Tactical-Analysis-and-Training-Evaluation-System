import { ApplicationMode, CalibrationMode } from '../constants/modes';
import { MethodologyId } from '../constants/methodology';
import { AnalysisStage } from '../constants/stages';
import { JobStatus } from '../constants/job';
import { ReportStatus } from '../constants/confidence';
import { IdentityEvaluation } from './identity';
import { MovementMetric } from './kinematics';
import { InstructionEvent } from './instruction';
import { AnalysisLimitation } from './limitation';
import { EvaluationMetrics } from './evaluation';
import { ArtifactReference } from './artifact';

/**
 * Aggregated analysis result returned to the client and stored in database.
 */
export interface AnalysisResult {
  id: string;
  session_id: string;
  job_id: string;
  methodology_id: MethodologyId;
  application_mode: ApplicationMode;
  calibration_mode: CalibrationMode;
  job_status: JobStatus;
  identity_evaluation: IdentityEvaluation;
  evaluation_metrics?: EvaluationMetrics | null;
  metrics: Record<string, MovementMetric>;
  instruction_events: InstructionEvent[];
  limitations: AnalysisLimitation[];
  artifact_references: ArtifactReference[];
  report_markdown?: string | null;
  report_status: ReportStatus;
  execution_manifest?: any;
  structured_evidence?: any;
  created_at: string;
}
