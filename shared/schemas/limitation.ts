/**
 * Explicit scientific or technical analysis limitation.
 */
export interface AnalysisLimitation {
  code: string; // e.g., 'LIMITATION_IDENTITY_FRAGMENTATION', 'LIMITATION_NO_METRIC_CALIBRATION'
  category: 'IDENTITY' | 'CALIBRATION' | 'TARGET_RESOLUTION' | 'AUDIO_QUALITY' | 'MODEL_GROUNDING';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  message: string;
  technical_details?: string | null;
}
