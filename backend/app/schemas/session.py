from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Session(BaseModel):
    id: str = Field(..., description="Unique session identifier")
    title: str = Field(..., description="Human-readable title of the session")
    coach_name: Optional[str] = Field(None, description="Coach name (pseudonymized if required)")
    team_name: Optional[str] = Field(None, description="Team or group name")
    notes: Optional[str] = Field(None, description="Session description or coaching context")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
