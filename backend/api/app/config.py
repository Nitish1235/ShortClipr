import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "ShortClipr API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    ALLOWED_ORIGINS: str = "https://shortclipr.com,http://localhost:3000"

    # ── Google OAuth ─────────────────────────────────────
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Google Cloud ─────────────────────────────────────
    GCP_PROJECT_ID: str
    GCS_BUCKET_INPUT: str = "shortclipr-input-videos"
    GCS_BUCKET_OUTPUT: str = "shortclipr-output-clips"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # ── Firestore ────────────────────────────────────────
    FIRESTORE_DATABASE: str = "(default)"

    # ── Upstash Redis ────────────────────────────────────
    UPSTASH_REDIS_URL: str
    UPSTASH_REDIS_TOKEN: str
    REDIS_JOB_QUEUE: str = "shortclipr:jobs"

    # ── Worker ───────────────────────────────────────────
    WORKER_SERVICE_URL: str = ""

    # ── Rate Limiting ────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
