import { CalibrationMode } from '../constants/modes';
import { MetricConfidence } from '../constants/confidence';

/**
 * Pitch calibration specification and homography transform definition.
 */
export interface Calibration {
  id: string;
  session_id: string;
  mode: CalibrationMode;
  confidence: MetricConfidence;
  pitch_length_m: number;
  pitch_width_m: number;
  homography_matrix?: number[][] | null;
  landmark_rmse_m?: number | null;
  source_resolution: [number, number]; // [width, height]
  tracking_resolution: [number, number]; // [width, height]
  created_at: string;
}
