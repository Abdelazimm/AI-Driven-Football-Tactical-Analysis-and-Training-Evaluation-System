import { MethodologyId, MethodologyAvailability } from '../constants/methodology';

/**
 * Methodology metadata for the GET /api/v1/methodologies endpoint.
 *
 * No methodology may be marked as "best".
 * No invented scientific performance claims.
 */
export interface MethodologyMetadata {
  id: MethodologyId;
  display_name: string;
  short_description: string;
  pipeline_summary: string[];
  availability: MethodologyAvailability;
  available: boolean;
  availability_reason?: string | null;
}

