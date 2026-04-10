"""
main.py — FastAPI application entry point.

Production hardening:
  - Structured JSON logging
  - Global rate limiting (slowapi)
  - Trusted proxy header forwarding (Cloud Run sits behind Google's LB)
  - /health and /readiness endpoints for Cloud Run probes
  - OpenAPI disabled in production
  - Startup validation of required env vars
"""
import logging
import os
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.routers import auth, jobs, videos, users, templates, payments

# ── Structured logging ────────────────────────────────────────────────────────
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("shortclipr.api")


# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ── Startup validation ────────────────────────────────────────────────────────
REQUIRED_ENV_VARS = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "JWT_SECRET_KEY",
    "GCP_PROJECT_ID",
    "UPSTASH_REDIS_URL",
    "UPSTASH_REDIS_TOKEN",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate required environment variables at startup
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        logger.critical(f"Missing required env vars: {missing}")
        sys.exit(1)
    logger.info(f"ShortClipr API starting — env={settings.ENVIRONMENT}")
    yield
    logger.info("ShortClipr API shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ShortClipr — AI Video to Shorts SaaS",
    lifespan=lifespan,
    # Disable interactive docs in production for security
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=86400,
)

# ── Request timing middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 1)
    response.headers["X-Response-Time-Ms"] = str(elapsed)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
    return response

# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(videos.router)
app.include_router(users.router)
app.include_router(templates.router)
app.include_router(payments.router)

# ── Health probes (Cloud Run / load balancer) ─────────────────────────────────
@app.get("/health", tags=["Health"], include_in_schema=False)
async def health():
    """Liveness probe — always returns 200 if process is alive."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.get("/readiness", tags=["Health"], include_in_schema=False)
async def readiness():
    """Readiness probe — checks critical dependencies."""
    checks: dict = {}
    # Quick Firestore ping
    try:
        from app.services.database import _get_db
        db = _get_db()
        await db.collection("_health").document("ping").get()
        checks["firestore"] = "ok"
    except Exception as e:
        checks["firestore"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )
