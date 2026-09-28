/**
 * Short-term track observation with spatial and projected coordinates.
 */
export interface TrackObservation {
  frame_index: number;
  timestamp_s: number;
  track_id: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  footpoint_x: number;
  footpoint_y: number;
  confidence: number;
  metric_x?: number | null;
  metric_y?: number | null;
}
