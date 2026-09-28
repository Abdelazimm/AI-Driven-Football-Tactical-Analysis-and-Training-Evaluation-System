/**
 * Worker dispatch contracts.
 * Represents serverless compute execution state and dispatch responses.
 */

export type WorkerDispatchState =
  | 'CREATED'
  | 'SUBMITTED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'CANCELLED';

export interface WorkerDispatchResponse {
  dispatch_id: string;
  job_id: string;
  provider: string;
  provider_execution_id: string | null;
  state: WorkerDispatchState;
  created_at: string;
  message?: string | null;
}
