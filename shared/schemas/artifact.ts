/**
 * Durable storage artifact reference.
 */
export interface ArtifactReference {
  id: string;
  session_id: string;
  job_id?: string | null;
  kind: 'VIDEO_RAW' | 'AUDIO_WAV' | 'OVERLAY_VIDEO' | 'CONTACT_SHEET' | 'OBSERVATIONS_PARQUET' | 'REPORT_MARKDOWN' | 'GOLDEN_PAYLOAD' | 'RESULT_JSON' | 'EXECUTION_MANIFEST';
  storage_path: string;
  file_size_bytes: number;
  mime_type: string;
  checksum_sha256?: string | null;
  is_frozen: boolean;
  created_at: string;
}
