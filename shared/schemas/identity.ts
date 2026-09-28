import { IdentityStatus } from '../constants/confidence';

/**
 * Persistent identity evaluation contract and safety gate output.
 *
 * PLAYER-LEVEL SAFETY RULE:
 * Player-level UI may only render when player_level_analysis_allowed === true.
 * A job may still finish successfully as COMPLETED_WITH_LIMITATIONS while
 * player-level analysis is withheld. This is NOT equivalent to technical failure.
 *
 * When identity_status is any FAIL_* value, player_level_analysis_allowed must be false,
 * and player-specific conclusions must be withheld while allowing team-level analysis to continue.
 */
export interface IdentityEvaluation {
  identity_status: IdentityStatus;
  method_formal_identity_status?: string | null;
  method_formal_identity_evidence_basis?: string | null;
  runtime_identity_status?: string | null;
  runtime_identity_evidence_basis?: string | null;
  player_level_analysis_allowed: boolean;
  withholding_reason?: string | null;
  expected_players?: number | null;
  raw_track_ids: number;
  meaningful_identities: number;
  fragmentation_ratio: number;
  acceptance_threshold: number; // default: 1.5
  evaluated_at: string;
}
