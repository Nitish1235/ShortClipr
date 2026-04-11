-- ─────────────────────────────────────────────────────────────────────────────
-- ShortClipr — Supabase / PostgreSQL Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query → Run
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                 TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    email              TEXT        NOT NULL UNIQUE,
    name               TEXT        NOT NULL,
    picture            TEXT,
    google_id          TEXT        NOT NULL UNIQUE,
    subscription_tier  TEXT        NOT NULL DEFAULT 'free',
    credits_used       INTEGER     NOT NULL DEFAULT 0,
    credits_limit      INTEGER     NOT NULL DEFAULT 3,
    is_active          BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email     ON users(email);

-- ─────────────────────────────────────────────────────────────────────────────
-- JOBS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs (
    job_id          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    user_id         TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_url       TEXT,
    youtube_url     TEXT,
    template_id     TEXT        NOT NULL DEFAULT 'viral-hook',
    options         JSONB       NOT NULL DEFAULT '{}',
    status          TEXT        NOT NULL DEFAULT 'pending',
    progress        INTEGER     NOT NULL DEFAULT 0,
    current_step    TEXT        NOT NULL DEFAULT '',
    error_message   TEXT,
    clip_count      INTEGER     NOT NULL DEFAULT 0,
    video_duration  FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_user_id    ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- CLIPS  (separate table — one row per generated short)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clips (
    clip_id            TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    job_id             TEXT        NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    user_id            TEXT        NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    clip_url           TEXT        NOT NULL,
    thumbnail_url      TEXT        NOT NULL DEFAULT '',
    duration           FLOAT       NOT NULL DEFAULT 0,
    start_time         FLOAT       NOT NULL DEFAULT 0,
    end_time           FLOAT       NOT NULL DEFAULT 0,
    transcript_snippet TEXT        NOT NULL DEFAULT '',
    viral_score        FLOAT       NOT NULL DEFAULT 0,
    top_title          TEXT        NOT NULL DEFAULT '',
    bottom_tag         TEXT        NOT NULL DEFAULT '',
    template_id        TEXT        NOT NULL DEFAULT 'viral-hook',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clips_job_id  ON clips(job_id);
CREATE INDEX IF NOT EXISTS idx_clips_user_id ON clips(user_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- auto-update updated_at trigger
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION _set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION _set_updated_at();

DROP TRIGGER IF EXISTS trg_jobs_updated_at ON jobs;
CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION _set_updated_at();

-- ─────────────────────────────────────────────────────────────────────────────
-- Row-Level Security (Supabase RLS) — API accesses via service role key
-- so RLS is kept simple: service role bypasses all policies.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE clips ENABLE ROW LEVEL SECURITY;

-- Service role (used by our API) can do everything
CREATE POLICY "service_role_all_users" ON users FOR ALL USING (TRUE);
CREATE POLICY "service_role_all_jobs"  ON jobs  FOR ALL USING (TRUE);
CREATE POLICY "service_role_all_clips" ON clips FOR ALL USING (TRUE);
