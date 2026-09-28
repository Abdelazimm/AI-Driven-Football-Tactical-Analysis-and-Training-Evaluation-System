from __future__ import annotations
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ArtifactReference(BaseModel):
    id: str = Field(..., description="Unique artifact identifier")
    session_id: str = Field(..., description="Associated session identifier")
    job_id: Optional[str] = Field(None, description="Associated job identifier")
    kind: Literal[
        "VIDEO_RAW",
        "AUDIO_WAV",
        "OVERLAY_VIDEO",
        "CONTACT_SHEET",
        "OBSERVATIONS_PARQUET",
        "REPORT_MARKDOWN",
        "GOLDEN_PAYLOAD",
        "RESULT_JSON",
        "EXECUTION_MANIFEST",
    ] = Field(..., description="Storage artifact category")
    storage_path: str = Field(..., description="Relative storage bucket path")
    file_size_bytes: int = Field(..., ge=0, description="Payload byte size")
    mime_type: str = Field(..., description="MIME content type")
    checksum_sha256: Optional[str] = Field(None, description="SHA-256 integrity checksum")
    is_frozen: bool = Field(default=False, description="Flag indicating immutable research golden status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
