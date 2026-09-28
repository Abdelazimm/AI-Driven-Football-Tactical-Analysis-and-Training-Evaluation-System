/**
 * Individual primary metric within a showcase demonstration card.
 */
export interface ShowcasePrimaryMetric {
  label: string;
  value: string; // e.g. "≈ 0.8 m", "44.4%"
}

/**
 * Validated capability showcase demonstration card (C06, C04, C03).
 * Exactly represents cards in the frozen showcase_frontend_payload.json.
 */
export interface ShowcaseCard {
  id: string; // 'C06_PRESSING' | 'C04_DEFENSIVE_MARKING' | 'C03_HOLD_POSITION'
  priority?: string | number | null; // e.g. 'hero'
  title: string;
  player: string;
  instructions: string[];
  time: string;
  response_summary: string;
  primary_metrics: ShowcasePrimaryMetric[];
  media: string;
  manual_verification_badge: boolean | string;
  metric_estimate_badge: boolean | string;
}

/**
 * Homography landmark RMSE specification.
 */
export interface HomographyRmse {
  value: number | string; // e.g. 0.651
  unit: string;
}

/**
 * Exact schema for the frozen showcase_frontend_payload.json fixture.
 */
export interface ShowcaseFrontendPayload {
  schema_version: string;
  project_title: string;
  showcase_mode: string;
  scientific_automated_status: string;
  manual_verification: boolean;
  metric_calibration: string;
  homography_rmse: HomographyRmse;
  badges: string[];
  cards: ShowcaseCard[];
  full_coach_report_markdown: string;
  limitations: string[];
  methodology_note: string;
}

/**
 * Resolved media reference for client display.
 */
export interface ShowcaseResolvedMedia {
  logical_key: string;
  card_id: string;
  use_case: string; // 'C03' | 'C04' | 'C06'
  title: string;
  fixture_path: string;
  media_type: string;
  file_size_bytes: number;
  sha256: string;
  storage_key?: string | null;
}

/**
 * Client response contract for GET /showcase.
 */
export interface ShowcaseResponse {
  showcase_status: string;
  showcase_mode: string;
  scientific_automated_status: string;
  disclaimer: string;
  badges: string[];
  cards: ShowcaseCard[];
  resolved_media: Record<string, ShowcaseResolvedMedia>;
  full_coach_report_markdown: string;
  limitations: string[];
  methodology_note: string;
  homography_rmse: HomographyRmse;
}

/**
 * Backwards-compatible alias for single use case cards.
 */
export type ShowcaseUseCase = ShowcaseCard;
