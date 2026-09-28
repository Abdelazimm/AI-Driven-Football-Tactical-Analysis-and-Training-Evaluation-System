"""
Pipeline Stage: Coaching Instruction Parsing
Source Research: 02_audio_pipeline.ipynb

Responsibilities:
- Parse tactical instruction events from transcribed segments
- Categorize tactical keywords (PRESSING, MARKING, HOLD_POSITION)
- Apply pseudonymization to player references
- Mark unresolved targets explicitly as UNRESOLVED_TARGET

NOTE: Integration placeholder.
"""
from typing import List
from backend.app.schemas.transcript import TranscriptSegment
from backend.app.schemas.instruction import InstructionEvent


class InstructionParsingPipeline:
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold

    def parse_instructions(self, segments: List[TranscriptSegment]) -> List[InstructionEvent]:
        """Placeholder for coaching instruction parsing."""
        raise NotImplementedError("Instruction parsing extraction will occur in a later controlled step.")
