-- ==============================================================================
-- AI-Driven Football Tactical Analysis and Training Evaluation System
-- Migration 004: Media Validation Schema Extensions
-- Target: Supabase PostgreSQL
-- Targets: public.media_assets
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXPAND upload_status CHECK CONSTRAINT
-- Adds VALIDATING, VALIDATED, and VALIDATION_FAILED states to the media
-- asset lifecycle. Analysis jobs now require VALIDATED (not just UPLOADED).
-- ------------------------------------------------------------------------------
ALTER TABLE public.media_assets DROP CONSTRAINT IF EXISTS media_assets_upload_status_check;
ALTER TABLE public.media_assets ADD CONSTRAINT media_assets_upload_status_check
    CHECK (upload_status IN (
        'PENDING', 'UPLOADED', 'VALIDATING', 'VALIDATED', 'VALIDATION_FAILED', 'FAILED'
    ));

-- ------------------------------------------------------------------------------
-- 2. AUTHORITATIVE PROBE METADATA COLUMNS
-- Persists server-verified container, codec, and validation state.
-- These are populated by ffprobe and are NEVER client-declared.
-- ------------------------------------------------------------------------------
ALTER TABLE public.media_assets
    ADD COLUMN IF NOT EXISTS container_format TEXT,
    ADD COLUMN IF NOT EXISTS video_codec TEXT,
    ADD COLUMN IF NOT EXISTS audio_codec TEXT,
    ADD COLUMN IF NOT EXISTS validation_status TEXT,
    ADD COLUMN IF NOT EXISTS validation_error_code TEXT;

-- Index validation status for querying unvalidated / failed media
CREATE INDEX IF NOT EXISTS idx_media_assets_validation_status
    ON public.media_assets (validation_status);
