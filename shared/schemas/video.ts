/**
 * Video container and stream metadata extracted via probe.
 */
export interface VideoMetadata {
  duration_seconds: number;
  width: number;
  height: number;
  fps: number;
  total_frames: number;
  codec: string;
  format: string;
  file_size_bytes: number;
  has_audio: boolean;
  checksum_sha256?: string | null;
}
