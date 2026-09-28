/**
 * Media assets contract for uploaded and generated audio/video objects.
 */
export const MEDIA_TYPES = {
  VIDEO: "VIDEO",
  COACH_AUDIO: "COACH_AUDIO",
  ANNOTATED_VIDEO: "ANNOTATED_VIDEO",
  REPORT: "REPORT",
  OTHER: "OTHER",
} as const;

export type MediaType = (typeof MEDIA_TYPES)[keyof typeof MEDIA_TYPES];

export const UPLOAD_STATUSES = {
  PENDING: "PENDING",
  UPLOADED: "UPLOADED",
  VALIDATING: "VALIDATING",
  VALIDATED: "VALIDATED",
  VALIDATION_FAILED: "VALIDATION_FAILED",
  FAILED: "FAILED",
} as const;

export type UploadStatus = (typeof UPLOAD_STATUSES)[keyof typeof UPLOAD_STATUSES];

export interface MediaAsset {
  id: string;
  session_id: string;
  job_id?: string | null | undefined;
  media_type: MediaType;
  storage_bucket: string;
  storage_path: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  duration_seconds?: number | null | undefined;
  width?: number | null | undefined;
  height?: number | null | undefined;
  fps?: number | null | undefined;
  container_format?: string | null | undefined;
  video_codec?: string | null | undefined;
  audio_codec?: string | null | undefined;
  validation_status?: string | null | undefined;
  validation_error_code?: string | null | undefined;
  upload_status: UploadStatus;
  created_at: string;
  updated_at: string;
}
