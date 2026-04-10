"""
main.py — Worker entry point.

Production hardening:
  - Graceful SIGTERM shutdown (Cloud Run sends SIGTERM before killing)
  - Global exception handler with structured logging
  - Job retry tracking (max 3 attempts per job)
  - credits_used increment in Firestore on job completion
  - Exponential backoff on Redis pop failures
  - Startup env validation
"""
import asyncio
import httpx
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from google.cloud import firestore

from pipeline import orchestrator

# ── Structured logging ────────────────────────────────────────────────────────
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("shortclipr.worker")

# ── Config ────────────────────────────────────────────────────────────────────
UPSTASH_REDIS_URL   = os.environ["UPSTASH_REDIS_URL"]
UPSTASH_REDIS_TOKEN = os.environ["UPSTASH_REDIS_TOKEN"]
REDIS_JOB_QUEUE     = os.getenv("REDIS_JOB_QUEUE", "shortclipr:jobs")
GCP_PROJECT_ID      = os.environ["GCP_PROJECT_ID"]
FIRESTORE_DATABASE  = os.getenv("FIRESTORE_DATABASE", "(default)")
MAX_JOB_ATTEMPTS    = 3
POLL_INTERVAL_SEC   = 2

db = firestore.AsyncClient(project=GCP_PROJECT_ID, database=FIRESTORE_DATABASE)

# ── Graceful shutdown ─────────────────────────────────────────────────────────
_shutdown = asyncio.Event()

def _handle_sigterm(*_):
    logger.info("SIGTERM received — finishing current job then exiting.")
    _shutdown.set()

signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT,  _handle_sigterm)


# ── Redis helpers ─────────────────────────────────────────────────────────────
async def _pop_job(client: httpx.AsyncClient) -> dict | None:
    """Non-blocking LPOP from Upstash Redis queue."""
    try:
        resp = await client.get(
            f"{UPSTASH_REDIS_URL}/lpop/{REDIS_JOB_QUEUE}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        result = resp.json().get("result")
        if result:
            return json.loads(result)
    except httpx.HTTPStatusError as e:
        logger.error(f"Redis HTTP error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Redis pop error: {e}")
    return None


async def _push_back(client: httpx.AsyncClient, job: dict) -> None:
    """Push a job back to the TAIL of the queue for retry (RPUSH)."""
    try:
        await client.post(
            f"{UPSTASH_REDIS_URL}/rpush/{REDIS_JOB_QUEUE}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
            json=json.dumps(job),
            timeout=10.0,
        )
    except Exception as e:
        logger.error(f"Failed to re-queue job {job.get('job_id')}: {e}")


# ── Firestore helpers ─────────────────────────────────────────────────────────
async def _update_status(
    job_id: str,
    status: str,
    progress: int | None = None,
    current_step: str | None = None,
    error: str | None = None,
) -> None:
    updates: dict = {
        "status":     status,
        "updated_at": datetime.now(timezone.utc),
    }
    if progress is not None:
        updates["progress"] = progress
    if current_step is not None:
        updates["current_step"] = current_step
    if error is not None:
        updates["error_message"] = error[:1000]   # cap at 1 KB
    if status == "completed":
        updates["completed_at"] = datetime.now(timezone.utc)
    await db.collection("jobs").document(job_id).update(updates)


async def _increment_user_shorts(user_id: str, count: int) -> None:
    """Atomically increment credits_used (= shorts generated) for the user."""
    try:
        user_ref = db.collection("users").document(user_id)
        await user_ref.update({"credits_used": firestore.Increment(count)})
        logger.info(f"User {user_id}: +{count} shorts credited")
    except Exception as e:
        logger.warning(f"Failed to increment shorts for user {user_id}: {e}")


# ── Job processor ─────────────────────────────────────────────────────────────
async def _process_job(job: dict) -> None:
    job_id    = job["job_id"]
    user_id   = job["user_id"]
    attempt   = job.get("_attempt", 1)

    logger.info(f"[{job_id}] Starting (attempt {attempt}/{MAX_JOB_ATTEMPTS})")
    await _update_status(job_id, "processing", 5, "Pipeline starting")

    async def _status_cb(step: str, pct: int):
        await _update_status(job_id, "processing", pct, step)

    try:
        clips = await orchestrator.run_pipeline(
            job_id=job_id,
            user_id=user_id,
            video_url=job.get("video_url"),
            youtube_url=job.get("youtube_url"),
            options=job.get("options", {}),
            template_id=job.get("template_id", "viral-hook"),
            status_callback=_status_cb,
        )

        # Persist results
        await db.collection("jobs").document(job_id).update({
            "clips":        clips,
            "clip_count":   len(clips),
            "status":       "completed",
            "progress":     100,
            "current_step": "Done",
            "completed_at": datetime.now(timezone.utc),
        })

        # Increment user's shorts counter (= credits_used in the model)
        await _increment_user_shorts(user_id, len(clips))

        logger.info(f"[{job_id}] Completed — {len(clips)} clips generated.")

    except ValueError as e:
        # ValueError = user-facing validation error (e.g. duration exceeded)
        # Do NOT retry — mark failed immediately
        logger.warning(f"[{job_id}] Validation error (no retry): {e}")
        await _update_status(job_id, "failed", error=str(e), current_step="Validation failed")

    except Exception as e:
        logger.exception(f"[{job_id}] Pipeline error (attempt {attempt}): {e}")
        if attempt < MAX_JOB_ATTEMPTS:
            # Bump attempt counter and re-queue
            job["_attempt"] = attempt + 1
            logger.info(f"[{job_id}] Re-queuing for attempt {attempt + 1}")
            async with httpx.AsyncClient() as c:
                await _push_back(c, job)
            await _update_status(
                job_id, "queued",
                current_step=f"Retrying (attempt {attempt + 1}/{MAX_JOB_ATTEMPTS})"
            )
        else:
            await _update_status(
                job_id, "failed",
                error=f"{type(e).__name__}: {str(e)[:500]}",
                current_step="Failed after max retries",
            )


# ── Main loop ─────────────────────────────────────────────────────────────────
async def worker_loop() -> None:
    logger.info(f"Worker started — polling {REDIS_JOB_QUEUE} every {POLL_INTERVAL_SEC}s")

    consecutive_errors = 0

    async with httpx.AsyncClient() as redis_client:
        while not _shutdown.is_set():
            try:
                job = await _pop_job(redis_client)
                if job:
                    consecutive_errors = 0
                    await _process_job(job)
                else:
                    await asyncio.sleep(POLL_INTERVAL_SEC)
            except Exception as e:
                consecutive_errors += 1
                backoff = min(2 ** consecutive_errors, 60)   # max 60s backoff
                logger.error(f"Worker loop error ({consecutive_errors}): {e} — sleeping {backoff}s")
                await asyncio.sleep(backoff)

    logger.info("Worker loop exited cleanly.")


if __name__ == "__main__":
    # Validate required env vars before booting
    required = ["UPSTASH_REDIS_URL", "UPSTASH_REDIS_TOKEN", "GCP_PROJECT_ID"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        logger.critical(f"Missing required env vars: {missing}")
        sys.exit(1)

    asyncio.run(worker_loop())
