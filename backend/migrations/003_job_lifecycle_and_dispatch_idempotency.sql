-- ==============================================================================
-- AI-Driven Football Tactical Analysis and Training Evaluation System
-- Migration 003: AnalysisJob Lifecycle Columns & Atomic Dispatch Idempotency
-- Target: Supabase PostgreSQL
-- Targets: public.analysis_jobs, public.worker_dispatches
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. ANALYSIS JOBS LIFECYCLE EXTENSIONS
-- Adds missing durable lifecycle fields to track real-time stage progress,
-- execution messages, provider call references, errors, and completion timestamps.
-- ------------------------------------------------------------------------------
ALTER TABLE public.analysis_jobs
    ADD COLUMN IF NOT EXISTS progress_percent NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS stage_message TEXT,
    ADD COLUMN IF NOT EXISTS error_code TEXT,
    ADD COLUMN IF NOT EXISTS error_details TEXT,
    ADD COLUMN IF NOT EXISTS modal_call_id TEXT,
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Progress percentage domain constraint (0.0 to 100.0)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_analysis_jobs_progress_percent'
    ) THEN
        ALTER TABLE public.analysis_jobs
            ADD CONSTRAINT chk_analysis_jobs_progress_percent
            CHECK (progress_percent >= 0.0 AND progress_percent <= 100.0);
    END IF;
END $$;

-- Index completed_at for historical retention and job filtering
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_completed_at
    ON public.analysis_jobs (completed_at);

-- ------------------------------------------------------------------------------
-- 2. ATOMIC ACTIVE-DISPATCH UNIQUE CONSTRAINT
-- Enforces at the database engine level that at most ONE active worker dispatch
-- (CREATED, SUBMITTED, or RUNNING) can exist per analysis job at any moment.
-- This eliminates concurrency races in check-then-insert dispatch orchestration.
-- ------------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_worker_dispatch_per_job
    ON public.worker_dispatches (job_id)
    WHERE state IN ('CREATED', 'SUBMITTED', 'RUNNING');

-- ------------------------------------------------------------------------------
-- 3. RLS DEFENSE-IN-DEPTH
-- Re-verify RLS enabled on worker_dispatches
-- ------------------------------------------------------------------------------
ALTER TABLE public.worker_dispatches ENABLE ROW LEVEL SECURITY;
