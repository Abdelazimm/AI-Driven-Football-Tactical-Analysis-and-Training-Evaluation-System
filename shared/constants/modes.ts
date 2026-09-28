/**
 * Application operating modes.
 */
export const APPLICATION_MODES = {
  AUTOMATED_ANALYSIS: 'AUTOMATED_ANALYSIS',
  VALIDATED_SHOWCASE: 'VALIDATED_SHOWCASE',
  ANALYSIS_WITHOUT_METRICS: 'ANALYSIS_WITHOUT_METRICS',
} as const;

export type ApplicationMode = (typeof APPLICATION_MODES)[keyof typeof APPLICATION_MODES];

/**
 * Pitch calibration modes.
 */
export const CALIBRATION_MODES = {
  DEMO_FIXED_CALIBRATION: 'DEMO_FIXED_CALIBRATION',
  CUSTOM_PITCH_CALIBRATION: 'CUSTOM_PITCH_CALIBRATION',
  NO_METRIC_CALIBRATION: 'NO_METRIC_CALIBRATION',
} as const;

export type CalibrationMode = (typeof CALIBRATION_MODES)[keyof typeof CALIBRATION_MODES];

/**
 * Coach audio processing modes.
 */
export const AUDIO_MODES = {
  EXTRACT_FROM_VIDEO: 'EXTRACT_FROM_VIDEO',
  SEPARATE_AUDIO_FILE: 'SEPARATE_AUDIO_FILE',
  NO_AUDIO: 'NO_AUDIO',
} as const;

export type AudioMode = (typeof AUDIO_MODES)[keyof typeof AUDIO_MODES];

