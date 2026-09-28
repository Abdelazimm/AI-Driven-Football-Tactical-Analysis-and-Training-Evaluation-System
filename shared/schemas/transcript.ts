/**
 * Individual timestamped word from speech recognition.
 */
export interface WordTimestamp {
  word: string;
  start_s: number;
  end_s: number;
  probability: number;
}

/**
 * Speech recognition segment with timestamps and privacy metadata.
 */
export interface TranscriptSegment {
  segment_id: number;
  start_s: number;
  end_s: number;
  text: string;
  confidence: number;
  words: WordTimestamp[];
  is_private: boolean; // Raw transcripts must remain private
}
