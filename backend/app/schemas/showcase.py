from __future__ import annotations
from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field


class ShowcasePrimaryMetric(BaseModel):
    """Individual primary metric in a showcase demonstration card."""
    label: str = Field(..., description="Metric label (e.g. 'Event 1 closing')")
    value: str = Field(..., description="Formatted metric value string (e.g. '≈ 0.8 m')")


class ShowcaseCard(BaseModel):
    """
    Demonstration card representing a single validated capability case (C06, C04, C03).
    Matches the exact schema and types of the frozen showcase_frontend_payload.json.
    """
    id: str = Field(..., description="Card identifier (e.g. C06_PRESSING, C04_DEFENSIVE_MARKING, C03_HOLD_POSITION)")
    priority: Optional[Union[str, int]] = Field(None, description="Display priority designation (e.g. 'hero' or integer)")
    title: str = Field(..., description="Human-readable title")
    player: str = Field(..., description="Manually verified player pseudonym (e.g. RED_01)")
    instructions: List[str] = Field(default_factory=list, description="List of coaching spoken commands")
    time: str = Field(..., description="Time interval description (e.g. '271.600–276.740 s')")
    response_summary: str = Field(..., description="Narrative summary of tactical response")
    primary_metrics: List[ShowcasePrimaryMetric] = Field(default_factory=list, description="Primary metrics for card")
    media: str = Field(..., description="Original frozen payload relative media reference")
    manual_verification_badge: Union[bool, str] = Field(default=True, description="Manual verification status flag or label")
    metric_estimate_badge: Union[bool, str] = Field(default=True, description="Metric estimate status flag or label")


class HomographyRmse(BaseModel):
    """Homography landmark RMSE specification."""
    value: Union[float, str] = Field(..., description="RMSE value (0.651)")
    unit: str = Field(default="m", description="Measurement unit")


class ShowcaseFrontendPayload(BaseModel):
    """
    Exact contract matching the frozen showcase_frontend_payload.json artifact.
    """
    schema_version: str = Field(..., description="Payload schema version (1.0)")
    project_title: str = Field(..., description="Project title")
    showcase_mode: str = Field(..., description="Mode (ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION)")
    scientific_automated_status: str = Field(..., description="Automated identity status (FAIL_HIGH_FRAGMENTATION)")
    manual_verification: bool = Field(..., description="Flag indicating human manual verification")
    metric_calibration: str = Field(..., description="Calibration assessment level")
    homography_rmse: HomographyRmse = Field(..., description="Landmark RMSE")
    badges: List[str] = Field(default_factory=list, description="Top-level status badges")
    cards: List[ShowcaseCard] = Field(default_factory=list, description="Showcase use-case cards")
    full_coach_report_markdown: str = Field(..., description="Complete coach evaluation report in Markdown")
    limitations: List[str] = Field(default_factory=list, description="Scientific and technical limitations")
    methodology_note: str = Field(..., description="Methodology and measurement explanation")


class ShowcaseResolvedMedia(BaseModel):
    """Resolved media reference for client display."""
    logical_key: str = Field(..., description="Stable logical identifier (e.g. c06_pressing_overlay)")
    card_id: str = Field(..., description="Associated card ID")
    use_case: str = Field(..., description="Case identifier: C03, C04, or C06")
    title: str = Field(..., description="Media display title")
    fixture_path: str = Field(..., description="Local fixture relative path")
    media_type: str = Field(..., description="MIME type (video/mp4 or image/png)")
    file_size_bytes: int = Field(..., description="Payload size in bytes")
    sha256: str = Field(..., description="SHA-256 integrity checksum")
    storage_key: Optional[str] = Field(None, description="Future Supabase storage key")


class ShowcaseResponse(BaseModel):
    """
    Clean application response contract for GET /showcase.
    Serves the validated demonstration data with resolved media and explicit disclaimers.
    """
    showcase_status: str = Field(
        default="PASS_FINAL_ORACLE_ASSISTED_CAPABILITY_SHOWCASE",
        description="Official golden showcase status"
    )
    showcase_mode: str = Field(
        default="ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION",
        description="Operating showcase demonstration mode"
    )
    scientific_automated_status: str = Field(
        default="FAIL_HIGH_FRAGMENTATION",
        description="Definitive automated persistent identity status"
    )
    disclaimer: str = Field(
        default="Player identity and coach-instruction targets were manually verified for this capability demonstration. Automated persistent identity is evaluated separately and remains FAIL_HIGH_FRAGMENTATION.",
        description="Mandatory scientific disclaimer"
    )
    badges: List[str] = Field(default_factory=list, description="Display badges")
    cards: List[ShowcaseCard] = Field(default_factory=list, description="Demonstration cards")
    resolved_media: Dict[str, ShowcaseResolvedMedia] = Field(default_factory=dict, description="Resolved media map by use case")
    full_coach_report_markdown: str = Field(..., description="Grounded coach evaluation report")
    limitations: List[str] = Field(default_factory=list, description="Evaluation limitations")
    methodology_note: str = Field(..., description="Measurement and homography methodology note")
    homography_rmse: HomographyRmse = Field(..., description="Calibration independent RMSE")


# Backwards-compatible alias for single use case cards
ShowcaseUseCase = ShowcaseCard
