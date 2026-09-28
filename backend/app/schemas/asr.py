"""
ASR Schemas and Data Models for Implementation Phase 3.
Governed by ASR_SELECTED_MODEL_INTEGRATION_CONTRACT.json and ASR_TEXT_NORMALIZATION_CONTRACT.json.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ASRSegment(BaseModel):
    """Whisper speech recognition segment."""
    segment_id: int = Field(..., ge=0, description="Segment sequence identifier")
    start_s: float = Field(..., ge=0.0, description="Segment start timestamp in seconds (source session time)")
    end_s: float = Field(..., ge=0.0, description="Segment end timestamp in seconds (source session time)")
    raw_text: str = Field(..., description="Verbatim raw transcribed text")
    normalized_text: str = Field(..., description="Normalized text according to frozen normalization contract")
    words: List[Dict[str, Any]] = Field(default_factory=list, description="Word-level timestamps if available")
    avg_logprob: Optional[float] = Field(None, description="Average log probability of segment")
    no_speech_prob: Optional[float] = Field(None, description="Probability that segment contains no speech")


class TacticalEvent(BaseModel):
    """Deterministic tactical coaching event extracted from an ASR speech segment."""
    event_id: str = Field(..., description="Unique tactical event identifier, e.g. 'evt_0'")
    category: str = Field(..., description="Tactical category (Positioning / Hold Ground, Pressing, Passing, Defensive, Offensive)")
    action: str = Field(..., description="Matched tactical keyword or phrase")
    t_start: float = Field(..., ge=0.0, description="Instruction start timestamp in seconds (source session time)")
    t_end: float = Field(..., ge=0.0, description="Instruction end timestamp in seconds (source session time)")
    source_segment_id: int = Field(..., ge=0, description="ID of the parent Whisper segment")
    source_text: str = Field(..., description="Verbatim raw text of parent segment")
    target_player: Optional[str] = Field(None, description="Addressed player identity (always None for automated runs)")
    target_resolution_status: str = Field(default="UNRESOLVED_TARGET", description="Status of target resolution (fails closed to UNRESOLVED_TARGET)")
    alignment_window_start_s: float = Field(..., description="Start of multimodal reaction evaluation window (t_end + 2.0s)")
    alignment_window_end_s: float = Field(..., description="End of multimodal reaction evaluation window (t_end + 6.0s)")
    expected_movement_profile: Optional[str] = Field(None, description="Heuristic movement profile (e.g. High Intensity, Hold Zone)")


class ASRResult(BaseModel):
    """Result of successful ASR processing and tactical extraction."""
    session_id: str = Field(..., description="Associated session identifier")
    audio_path: str = Field(..., description="Path to processed audio file")
    audio_duration_s: float = Field(..., ge=0.0, description="Total duration of processed audio in seconds")
    model_id: str = Field(default="base.en", description="Frozen faster-whisper model identifier")
    device: str = Field(default="cpu", description="Execution device")
    compute_type: str = Field(default="int8", description="Execution quantization")
    cpu_threads: int = Field(default=8, description="Number of CPU threads allocated")
    source_offset_s: float = Field(default=0.0, description="Source timeline offset for bounded audio intervals")
    segments: List[ASRSegment] = Field(default_factory=list, description="Extracted speech segments")
    events: List[TacticalEvent] = Field(default_factory=list, description="Extracted tactical events")
    raw_transcript: str = Field(default="", description="Concatenated raw transcript")
    normalized_transcript: str = Field(default="", description="Concatenated normalized transcript")
    limitations: List[str] = Field(default_factory=list, description="Methodological limitations")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Execution provenance and audit metadata")


class ASRFailure(BaseModel):
    """Typed failure model returned when audio extraction or transcription cannot complete."""
    status: Literal["FAILURE"] = "FAILURE"
    error_type: str = Field(..., description="Classification of failure (AUDIO_EXTRACTION_FAILED, WHISPER_INFERENCE_FAILED, ASR_EMPTY, NO_USABLE_AUDIO)")
    error_message: str = Field(..., description="Human-readable explanation of error")
    recoverable_vision_only: bool = Field(default=True, description="Whether pipeline can complete Vision-only with COMPLETED_WITH_LIMITATIONS")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic details")
