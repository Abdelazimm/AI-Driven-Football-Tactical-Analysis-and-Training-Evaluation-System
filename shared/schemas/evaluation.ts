/**
 * Evaluation metrics schema for the scientific/engineering assessment of analysis runs.
 *
 * CRITICAL: Unavailable metric !== zero.
 * Use null to represent metrics that are not available, not computed, or not applicable.
 * Never substitute 0 for an unavailable metric value.
 */

/**
 * Object detection performance metrics.
 */
export interface DetectionEvaluationMetrics {
  precision: number | null;
  recall: number | null;
  map50: number | null;
  map50_95: number | null;
}

/**
 * Identity and tracking metrics derived from the pipeline itself.
 * These do NOT require external ground truth.
 */
export interface IdentityTrackingEvaluationMetrics {
  raw_track_count: number | null;
  final_identity_count: number | null;
  fragmentation_ratio: number | null;
  observation_retention: number | null;
  track_coverage: number | null;
  reentry_recovery_rate: number | null;
}

/**
 * Tracking metrics that require validated ground truth annotations.
 * For normal user uploads without ground truth, all metric fields will be null
 * and ground_truth_available will be false.
 */
export interface GroundTruthTrackingMetrics {
  ground_truth_available: boolean;
  hota: number | null;
  deta: number | null;
  assa: number | null;
  idf1: number | null;
  mota: number | null;
  id_switches: number | null;
  false_positives: number | null;
  false_negatives: number | null;
  /** Explanation of why GT metrics are unavailable when ground_truth_available is false. */
  unavailable_reason?: string | null;
}

/**
 * System engineering performance metrics for the analysis run.
 */
export interface EngineeringMetrics {
  runtime_seconds: number | null;
  effective_fps: number | null;
  peak_gpu_memory_mb: number | null;
}

/**
 * Aggregate evaluation metrics for a complete analysis run.
 * Separates detection, identity/tracking, GT-dependent, and engineering concerns.
 */
export interface EvaluationMetrics {
  detection: DetectionEvaluationMetrics;
  identity_tracking: IdentityTrackingEvaluationMetrics;
  ground_truth: GroundTruthTrackingMetrics;
  engineering: EngineeringMetrics;
}
