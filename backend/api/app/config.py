import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────────
    APP_NAME:       str  = "ShortClipr API"
    APP_VERSION:    str  = "1.0.0"
    DEBUG:          bool = False
    ENVIRONMENT:    str  = "production"
    ALLOWED_ORIGINS: str = "https://shortclipr.com,https://www.shortclipr.com,http://localhost:3000"

    # ── Google OAuth ───────────────────────────────────────────────────────────
    # ── Google OAuth ───────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID:     str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI:  str = "http://localhost:8000/auth/callback"

    # ── JWT ────────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY:                  str = ""
    JWT_ALGORITHM:                   str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS:   int = 30

    # ── Supabase — Postgres (users, jobs, clips) ───────────────────────────────
    # Supabase Dashboard → Project Settings → Database → Connection string
    # Format: postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
    SUPABASE_DB_URL: str = ""

    # ── Google Cloud Storage (video files only) ────────────────────────────────
    GCP_PROJECT_ID:    str = ""
    GCS_BUCKET_INPUT:  str = "shortclipr-input-videos"
    GCS_BUCKET_OUTPUT: str = "shortclipr-output-clips"

    # ── Upstash Redis (job queue + real-time status) ───────────────────────────
    UPSTASH_REDIS_URL:   str = ""
    UPSTASH_REDIS_TOKEN: str = ""
    REDIS_JOB_QUEUE:     str = "shortclipr:jobs"

    # ── Dodo Payments ──────────────────────────────────────────────────────────
    DODO_PAYMENTS_API_KEY: str = ""
    DODO_WEBHOOK_SECRET:   str = ""
    DODO_ENV:              str = "test"   # test | live

    # ── Rate Limiting ──────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file       = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
