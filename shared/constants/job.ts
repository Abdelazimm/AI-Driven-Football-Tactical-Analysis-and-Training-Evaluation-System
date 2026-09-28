/**
 * Analysis Job lifecycle status.
 * Distinct from sequential execution stages (AnalysisStage).
 */
export const JOB_STATUSES = {
  QUEUED: 'QUEUED',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  COMPLETED_WITH_LIMITATIONS: 'COMPLETED_WITH_LIMITATIONS',
  FAILED: 'FAILED',
} as const;

export type JobStatus = (typeof JOB_STATUSES)[keyof typeof JOB_STATUSES];

/**
 * Terminal statuses for analysis jobs.
 */
export const TERMINAL_JOB_STATUSES: readonly JobStatus[] = [
  JOB_STATUSES.COMPLETED,
  JOB_STATUSES.COMPLETED_WITH_LIMITATIONS,
  JOB_STATUSES.FAILED,
] as const;
