from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class InstructionEvent(BaseModel):
    id: str = Field(..., description="Unique instruction event identifier")
    session_id: str = Field(..., description="Associated session identifier")
    start_s: float = Field(..., ge=0.0, description="Instruction start timestamp in seconds")
    end_s: float = Field(..., ge=0.0, description="Instruction end timestamp in seconds")
    raw_text: str = Field(..., description="Verbatim transcribed spoken command")
    category: str = Field(..., description="Tactical category (e.g. PRESSING, MARKING, HOLD_POSITION)")
    action: Optional[str] = Field(None, description="Matched tactical keyword or action phrase")
    target_player_pseudonym: Optional[str] = Field(None, description="Addressed player pseudonym (e.g. Black01)")
    is_target_resolved: bool = Field(..., description="True if coach target is unambiguously resolved")
    alignment_window_start_s: float = Field(..., description="Multimodal fusion window start timestamp")
    alignment_window_end_s: float = Field(..., description="Multimodal fusion window end timestamp")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Instruction detection confidence score")
