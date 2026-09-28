from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class WordTimestamp(BaseModel):
    word: str = Field(..., description="Recognized word token")
    start_s: float = Field(..., ge=0.0, description="Word start timestamp in seconds")
    end_s: float = Field(..., ge=0.0, description="Word end timestamp in seconds")
    probability: float = Field(..., ge=0.0, le=1.0, description="Word recognition confidence probability")


class TranscriptSegment(BaseModel):
    segment_id: int = Field(..., ge=0, description="Segment sequence identifier")
    start_s: float = Field(..., ge=0.0, description="Segment start timestamp in seconds")
    end_s: float = Field(..., ge=0.0, description="Segment end timestamp in seconds")
    text: str = Field(..., description="Transcribed text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Segment-level confidence score")
    words: List[WordTimestamp] = Field(default_factory=list, description="Word-level timestamps")
    is_private: bool = Field(default=True, description="Privacy flag (raw transcripts must remain private)")
