"""
main.py — Worker entry point.

Database: Supabase (asyncpg) for job/user status updates.
Storage:  GCS (unchanged) for video files and clip outputs.
Queue:    Upstash Redis REST API.
"""
import asyncio
import asyncpg
import httpx
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone

from pipeline import orchestrator

# ── Structured logging ────────────────────────────────────────────────────────
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("shortclipr.worker")

# ── Config ────────────────────────────────────────────────────────────────────
SUPABASE_DB_URL     = os.environ["SUPABASE_DB_URL"]
UPSTASH_REDIS_URL   = os.environ["UPSTASH_REDIS_URL"]
UPSTASH_REDIS_TOKEN = os.environ["UPSTASH_REDIS_TOKEN"]
REDIS_JOB_QUEUE     = os.getenv("REDIS_JOB_QUEUE", "shortclipr:jobs")
MAX_JOB_ATTEMPTS    = 3
POLL_INTERVAL_SEC   = 2

# ── DB pool (module-level, initialised in worker_loop) ───────────────────────
_pool: asyncpg.Pool | None = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=SUPABASE_DB_URL,
            min_size=1,
            max_size=5,
            command_timeout=30,
            init=_init_conn,
        )
    return _pool


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json",  encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


# ── Graceful shutdown ─────────────────────────────────────────────────────────
_shutdown = asyncio.Event()

def _handle_signal(*_):
    logger.info("Shutdown signal received — finishing current job then exiting.")
    _shutdown.set()

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT,  _handle_signal)


# ── Redis helpers ─────────────────────────────────────────────────────────────
async def _pop_job(client: httpx.AsyncClient) -> dict | None:
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
    except Exception as e:
        logger.error(f"Redis pop error: {e}")
    return None


async def _push_back(client: httpx.AsyncClient, job: dict) -> None:
    try:
        await client.post(
            f"{UPSTASH_REDIS_URL}/rpush/{REDIS_JOB_QUEUE}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
            json=json.dumps(job),
            timeout=10.0,
        )
    except Exception as e:
        logger.error(f"Failed to re-queue job {job.get('job_id')}: {e}")


# ── DB helpers ────────────────────────────────────────────────────────────────
async def _update_job(
    job_id: str,
    status: str,
    progress: int | None = None,
    step: str | None = None,
    error: str | None = None,
) -> None:
    sets = ["status = $1", "updated_at = NOW()"]
    vals = [status]
    i = 2
    if progress is not None:
        sets.append(f"progress = ${i}"); vals.append(progress); i += 1
    if step is not None:
        sets.append(f"current_step = ${i}"); vals.append(step); i += 1
    if error is not None:
        sets.append(f"error_message = ${i}"); vals.append(error[:1000]); i += 1
    if status == "completed":
        sets.append("completed_at = NOW()")

    vals.append(job_id)
    sql = f"UPDATE jobs SET {', '.join(sets)} WHERE job_id = ${i}"

    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(sql, *vals)


async def _save_clips(job_id: str, user_id: str, clips: list[dict]) -> None:
    """Bulk-insert clip rows and update job clip_count."""
    if not clips:
        return
    import uuid
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            for c in clips:
                await conn.execute(
                    """
                    INSERT INTO clips
                        (clip_id, job_id, user_id, clip_url, thumbnail_url,
                         duration, start_time, end_time, transcript_snippet,
                         viral_score, top_title, bottom_tag, template_id)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                    ON CONFLICT (clip_id) DO NOTHING
                    """,
                    c.get("clip_id", str(uuid.uuid4())),
                    job_id, user_id,
                    c.get("clip_url", ""),
                    c.get("thumbnail_url", ""),
                    float(c.get("duration", 0)),
                    float(c.get("start_time", 0)),
                    float(c.get("end_time", 0)),
                    c.get("transcript_snippet", ""),
                    float(c.get("viral_score", 0)),
                    c.get("top_title", ""),
                    c.get("bottom_tag", ""),
                    c.get("template_id", "viral-hook"),
                )
            await conn.execute(
                "UPDATE jobs SET clip_count = $1 WHERE job_id = $2",
                len(clips), job_id,
            )


async def _increment_shorts(user_id: str, count: int) -> None:
    """Atomically add to user's shorts-generated counter."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET credits_used = credits_used + $1 WHERE id = $2",
                count, user_id,
            )
        logger.info(f"User {user_id}: +{count} shorts credited")
    except Exception as e:
        logger.warning(f"Could not increment shorts for {user_id}: {e}")


# ── Job processor ─────────────────────────────────────────────────────────────
async def _process_job(job: dict, redis_client: httpx.AsyncClient) -> None:
    job_id  = job["job_id"]
    user_id = job["user_id"]
    attempt = job.get("_attempt", 1)

    logger.info(f"[{job_id}] Processing (attempt {attempt}/{MAX_JOB_ATTEMPTS})")
    await _update_job(job_id, "processing", 5, "Pipeline starting")

    async def _status_cb(step: str, pct: int):
        await _update_job(job_id, "processing", pct, step)

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

        # Save clips to Supabase
        await _save_clips(job_id, user_id, clips)

        # Mark job completed
        await _update_job(job_id, "completed", 100, "Done")

        # Increment user's shorts counter
        await _increment_shorts(user_id, len(clips))

        logger.info(f"[{job_id}] Completed — {len(clips)} clips.")

    except ValueError as e:
        # Validation error — don't retry
        logger.warning(f"[{job_id}] Validation error: {e}")
        await _update_job(job_id, "failed", error=str(e), step="Validation failed")

    except Exception as e:
        logger.exception(f"[{job_id}] Pipeline error (attempt {attempt}): {e}")
        if attempt < MAX_JOB_ATTEMPTS:
            job["_attempt"] = attempt + 1
            await _push_back(redis_client, job)
            await _update_job(
                job_id, "queued",
                step=f"Retrying (attempt {attempt + 1}/{MAX_JOB_ATTEMPTS})"
            )
        else:
            await _update_job(
                job_id, "failed",
                error=f"{type(e).__name__}: {str(e)[:500]}",
                step="Failed after max retries",
            )


# ── Main loop ─────────────────────────────────────────────────────────────────
async def worker_loop() -> None:
    # Initialise DB pool on startup
    await _get_pool()
    logger.info(f"Worker started. Polling {REDIS_JOB_QUEUE} every {POLL_INTERVAL_SEC}s")

    consecutive_errors = 0
    async with httpx.AsyncClient() as redis_client:
        while not _shutdown.is_set():
            try:
                job = await _pop_job(redis_client)
                if job:
                    consecutive_errors = 0
                    await _process_job(job, redis_client)
                else:
                    await asyncio.sleep(POLL_INTERVAL_SEC)
            except Exception as e:
                consecutive_errors += 1
                backoff = min(2 ** consecutive_errors, 60)
                logger.error(f"Loop error #{consecutive_errors}: {e} — sleeping {backoff}s")
                await asyncio.sleep(backoff)

    if _pool:
        await _pool.close()
    logger.info("Worker exited cleanly.")


if __name__ == "__main__":
    required = ["SUPABASE_DB_URL", "UPSTASH_REDIS_URL", "UPSTASH_REDIS_TOKEN"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        logger.critical(f"Missing env vars: {missing}")
        sys.exit(1)

    asyncio.run(worker_loop())
