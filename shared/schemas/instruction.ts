/**
 * Coach tactical instruction event parsed from transcript.
 */
export interface InstructionEvent {
  id: string;
  session_id: string;
  start_s: number;
  end_s: number;
  raw_text: string;
  category: string; // e.g., 'PRESSING', 'MARKING', 'HOLD_POSITION'
  action?: string | null;
  target_player_pseudonym?: string | null;
  is_target_resolved: boolean;
  alignment_window_start_s: number; // e.g., start_s - 2.0s
  alignment_window_end_s: number; // e.g., end_s + 5.0s
  confidence: number;
}
