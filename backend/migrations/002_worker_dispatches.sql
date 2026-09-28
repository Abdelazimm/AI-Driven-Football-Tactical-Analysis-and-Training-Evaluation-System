-- ==============================================================================
-- AI-Driven Football Tactical Analysis and Training Evaluation System
-- Migration 002: Worker Dispatches Persistence Schema
-- Target: Supabase PostgreSQL
-- Target Table: public.worker_dispatches
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.worker_dispatches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.analysis_jobs(id) ON DELETE CASCADE,
    provider TEXT NOT NULL DEFAULT 'MODAL',
    provider_execution_id TEXT,
    state TEXT NOT NULL DEFAULT 'CREATED' CHECK (state IN (
        'CREATED', 'SUBMITTED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED'
    )),
    attempt INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    error_code TEXT,
    error_message TEXT
);

-- ------------------------------------------------------------------------------
-- INDEXES
-- Support fast lookup by job_id and filtering by active execution state
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_worker_dispatches_job_id ON public.worker_dispatches(job_id);
CREATE INDEX IF NOT EXISTS idx_worker_dispatches_state ON public.worker_dispatches(state);

-- ------------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS)
-- Secure by default: restricted to backend service-role
-- ------------------------------------------------------------------------------
ALTER TABLE public.worker_dispatches ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'worker_dispatches' AND policyname = 'service_role_all_worker_dispatches'
    ) THEN
        CREATE POLICY service_role_all_worker_dispatches ON public.worker_dispatches
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;
