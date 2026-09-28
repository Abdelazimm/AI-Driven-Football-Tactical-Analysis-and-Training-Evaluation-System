/**
 * Upload intent and completion contracts for direct browser -> Supabase Storage transfer.
 */
import type { MediaType } from "./media";

export interface UploadIntentRequest {
  media_type: MediaType;
  filename: string;
  mime_type: string;
  size_bytes: number;
  duration_seconds?: number | null | undefined;
}

export interface UploadIntentResponse {
  media_id: string;
  session_id: string;
  media_type: MediaType;
  storage_bucket: string;
  storage_path: string;
  signed_upload_url: string;
  expires_in: number;
}

export interface CompleteUploadRequest {
  size_bytes?: number | null | undefined;
}
