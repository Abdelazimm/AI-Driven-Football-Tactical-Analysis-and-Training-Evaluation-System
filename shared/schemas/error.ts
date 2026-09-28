/**
 * Canonical typed API error response model.
 * Consistent across validation errors, job not found (404), and result not ready (409).
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}
