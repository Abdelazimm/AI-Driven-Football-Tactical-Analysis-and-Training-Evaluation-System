/**
 * Training session contract.
 */
export interface Session {
  id: string;
  title: string;
  coach_name?: string | null;
  team_name?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}
