/**
 * Visual bounding box detection output per frame.
 */
export interface Detection {
  frame_index: number;
  timestamp_s: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
  class_id: number; // 0 = person
  track_id?: number | null;
  source_width: number;
  source_height: number;
  detector_manifest_id?: string | null;
}
