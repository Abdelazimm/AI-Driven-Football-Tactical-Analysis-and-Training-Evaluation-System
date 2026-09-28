-- ==============================================================================
-- AI-Driven Football Tactical Analysis and Training Evaluation System
-- Migration 001: Phase 3 Initial Persistence Schema
-- Target: Supabase PostgreSQL
-- ==============================================================================

-- Enable UUID extension if not already present
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. SESSIONS TABLE
-- Persists coaching / training session grouping before analysis.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    coach_name TEXT,
    team_name TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 2. ANALYSIS JOBS TABLE
-- Persists the lifecycle, configuration, and execution status of an analysis run.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.sessions(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'QUEUED' CHECK (status IN (
        'QUEUED', 'PROCESSING', 'COMPLETED', 'COMPLETED_WITH_LIMITATIONS', 'FAILED'
    )),
    current_stage TEXT NOT NULL DEFAULT 'UPLOADED' CHECK (current_stage IN (
        'UPLOADED', 'VALIDATING', 'PREPROCESSING', 'DETECTING', 'TRACKING',
        'IDENTITY_EVALUATION', 'CALIBRATING', 'KINEMATICS', 'AUDIO_EXTRACTION',
        'TRANSCRIBING', 'INSTRUCTION_PARSING', 'FUSION', 'GENERATING_EVIDENCE',
        'GENERATING_REPORT', 'RENDERING', 'UPLOADING_RESULTS'
    )),
    methodology_id TEXT NOT NULL CHECK (methodology_id IN (
        'METHOD_1_YOLO11_BOTSORT', 'METHOD_2_RFDETR_GTATRACK', 'METHOD_3_YOLO26_SRITRACK'
    )),
    application_mode TEXT NOT NULL DEFAULT 'AUTOMATED_ANALYSIS' CHECK (application_mode IN (
        'AUTOMATED_ANALYSIS', 'ORACLE_ASSISTED_SHOWCASE', 'ANALYSIS_WITHOUT_METRICS'
    )),
    calibration_mode TEXT NOT NULL DEFAULT 'NO_METRIC_CALIBRATION' CHECK (calibration_mode IN (
        'NO_METRIC_CALIBRATION', 'DEMO_FIXED_CALIBRATION', 'CUSTOM_PITCH_CALIBRATION'
    )),
    audio_mode TEXT NOT NULL DEFAULT 'EXTRACT_FROM_VIDEO' CHECK (audio_mode IN (
        'EXTRACT_FROM_VIDEO', 'SEPARATE_AUDIO_FILE', 'NO_AUDIO'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 3. MEDIA ASSETS TABLE
-- Persists raw uploaded videos, coach audio tracks, and future output artifacts.
-- Raw media files are stored in private Supabase Storage buckets, NOT in DB.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.sessions(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.analysis_jobs(id) ON DELETE SET NULL,
    media_type TEXT NOT NULL CHECK (media_type IN (
        'VIDEO', 'COACH_AUDIO', 'ANNOTATED_VIDEO', 'REPORT', 'OTHER'
    )),
    storage_bucket TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    duration_seconds DOUBLE PRECISION,
    width INTEGER,
    height INTEGER,
    fps DOUBLE PRECISION,
    upload_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (upload_status IN (
        'PENDING', 'UPLOADED', 'FAILED'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- INDEXES
-- Optimize lookups by session, job, and asset state
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_session_id ON public.analysis_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_session_id ON public.media_assets(session_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_job_id ON public.media_assets(job_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_media_type ON public.media_assets(media_type);
CREATE INDEX IF NOT EXISTS idx_media_assets_upload_status ON public.media_assets(upload_status);

-- ------------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Default secure: private data accessible only by service-role backend
-- ------------------------------------------------------------------------------
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.media_assets ENABLE ROW LEVEL SECURITY;

-- Allow service-role (backend FastAPI) full access to sessions
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'sessions' AND policyname = 'service_role_all_sessions'
    ) THEN
        CREATE POLICY service_role_all_sessions ON public.sessions
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- Allow service-role full access to analysis_jobs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'analysis_jobs' AND policyname = 'service_role_all_jobs'
    ) THEN
        CREATE POLICY service_role_all_jobs ON public.analysis_jobs
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- Allow service-role full access to media_assets
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'media_assets' AND policyname = 'service_role_all_media'
    ) THEN
        CREATE POLICY service_role_all_media ON public.media_assets
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- STORAGE BUCKETS (Private by default)
-- Insert private buckets into storage.buckets if storage schema exists
-- ------------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'storage' AND table_name = 'buckets') THEN
        INSERT INTO storage.buckets (id, name, public, allowed_mime_types)
        VALUES 
            ('analysis-inputs', 'analysis-inputs', false, ARRAY['video/mp4', 'video/quicktime', 'audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3', 'audio/m4a', 'audio/x-m4a', 'audio/aac']),
            ('analysis-outputs', 'analysis-outputs', false, NULL)
        ON CONFLICT (id) DO UPDATE SET
            public = EXCLUDED.public;
    END IF;
END $$;
