import { MetricConfidence } from '../constants/confidence';

/**
 * Physical movement or distance metric with explicit calibration confidence and limitations.
 */
export interface MovementMetric {
  name: string;
  value?: number | null; // e.g., 4.52 (null when withheld or uncalibrated)
  unit: string; // 'm', 'km/h', 'm/s', 'px'
  confidence: MetricConfidence;
  calibration_id?: string | null;
  display_value: string; // e.g., "4.5 m" or "Withheld (Uncalibrated)"
  limitations: string[];
}
