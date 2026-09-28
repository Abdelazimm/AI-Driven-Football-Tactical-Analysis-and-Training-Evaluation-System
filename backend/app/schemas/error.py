from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ApiError(BaseModel):
    """
    Standard typed API error response model.
    Used consistently across validation errors, job not found (404),
    and result not ready (409 Conflict).
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional diagnostic details")
