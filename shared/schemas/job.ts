import { ApplicationMode, CalibrationMode, AudioMode } from '../constants/modes';
import { AnalysisStage } from '../constants/stages';
import { MethodologyId } from '../constants/methodology';
import { JobStatus } from '../constants/job';

/**
 * Public request schema for creating an analysis job.
 * Note: methodology_id is STRICTLY REQUIRED.
 */
export interface CreateAnalysisJobRequest {
  methodology_id: MethodologyId | 'AUTO';
  session_id: string;
  calibration_mode?: CalibrationMode | undefined;
  audio_mode?: AudioMode | undefined;
  video_file_name?: string | null | undefined;
}

/**
 * Analysis background job tracking.
 */
export interface AnalysisJob {
  id: string;
  session_id: string;
  methodology_id: MethodologyId;
  mode: ApplicationMode;
  calibration_mode: CalibrationMode;
  audio_mode: AudioMode;
  status: JobStatus;
  current_stage: AnalysisStage;
  progress_percent: number; // 0.0 to 100.0
  stage_message?: string | null;
  modal_call_id?: string | null;
  error_code?: string | null;
  error_details?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}
