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
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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
SUPABASE_DB_URL     = os.getenv("SUPABASE_DB_URL", "")
UPSTASH_REDIS_URL   = os.getenv("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN", "")
REDIS_JOB_QUEUE     = os.getenv("REDIS_JOB_QUEUE", "shortclipr:jobs")
MAX_JOB_ATTEMPTS    = 3
MIN_POLL_INTERVAL_SEC = 2
MAX_POLL_INTERVAL_SEC = 15

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
            statement_cache_size=0,
            max_inactive_connection_lifetime=300,
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
            data = json.loads(result)
            # Upstash sometimes stores payload inside an array if pushed via json=[payload]
            while isinstance(data, list):
                if not data:
                    return None
                data = data[0]
                if isinstance(data, str):
                    data = json.loads(data)
            
            if isinstance(data, str):
                data = json.loads(data)
                
            if isinstance(data, dict):
                return data
                
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
    # Prevent overwriting a 'cancelled' status set by the API
    sql = f"UPDATE jobs SET {', '.join(sets)} WHERE job_id = ${i} AND status != 'cancelled' RETURNING job_id"

    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(sql, *vals)
        return result is not None


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
        success = await _update_job(job_id, "processing", pct, step)
        if not success:
            raise RuntimeError("Job Cancelled")

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

    except RuntimeError as e:
        if str(e) == "Job Cancelled":
            logger.info(f"[{job_id}] Aborted — Job was cancelled by user.")
            return
        # If it's a different RuntimeError, let it fall through or re-raise
        raise e
        
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


# ── environment audit ──────────────────────────────────────────────────────────
def _run_env_audit():
    """Logs the yt-dlp version and checks for registered PO Token providers."""
    try:
        import yt_dlp
        logger.info(f"[Audit] yt-dlp version: {yt_dlp.version.__version__}")
        
        # Check if the bgutil plugin is loaded into the extractor list
        from yt_dlp.extractor.youtube import YoutubeIE
        # Note: We look for identifiers in the extractor classes
        try:
            from yt_dlp.extractor import _ALL_CLASSES
            classes = [c.__name__ for c in _ALL_CLASSES]
            if "YoutubePOTProviderIE" in classes or any("POT" in c for c in classes):
                logger.info("[Audit] Found PO Token provider classes in yt-dlp")
            else:
                logger.warning("[Audit] No PO Token provider classes found in yt-dlp plugin list")
        except Exception:
            pass
            
    except Exception as e:
        logger.warning(f"[Audit] Failed environment check: {e}")


# ── bgutil-pot readiness check ───────────────────────────────────────────────
async def _wait_for_bgutil(timeout: int = 30) -> bool:
    """
    Wait up to `timeout` seconds for the bgutil-pot HTTP server to be ready.
    This server starts in the background (start.sh) at the same time as Python,
    so there's a short race window. We must wait before processing YouTube jobs
    or the PO token provider will fail silently and yt-dlp hits bot detection.
    """
    port = int(os.getenv("BGUTIL_HTTP_SERVER_PORT", "4416"))
    url  = f"http://127.0.0.1:{port}/token"
    async with httpx.AsyncClient() as client:
        for i in range(timeout):
            try:
                r = await client.get(url, timeout=2.0)
                if r.status_code < 500:
                    logger.info(f"bgutil-pot ready after {i}s on port {port}")
                    return True
            except Exception:
                pass
            await asyncio.sleep(1)
    logger.warning(f"bgutil-pot did not respond within {timeout}s — proceeding without PO tokens")
    return False


# ── Main loop ─────────────────────────────────────────────────────────────────
async def worker_loop() -> None:
    # Initialise DB pool on startup
    await _get_pool()
    logger.info(f"Worker started. Polling {REDIS_JOB_QUEUE} natively balancing between min {MIN_POLL_INTERVAL_SEC}s and max {MAX_POLL_INTERVAL_SEC}s")

    # Audit the environment for yt-dlp and plugins
    _run_env_audit()

    # Wait for bgutil-pot before processing any YouTube jobs
    await _wait_for_bgutil()

    consecutive_errors = 0
    current_poll_interval = MIN_POLL_INTERVAL_SEC

    # Hide httpx info logs to clean up your Cloud Run logs
    logging.getLogger("httpx").setLevel(logging.WARNING)

    async with httpx.AsyncClient() as redis_client:
        while not _shutdown.is_set():
            try:
                job = await _pop_job(redis_client)
                if job:
                    consecutive_errors = 0
                    current_poll_interval = MIN_POLL_INTERVAL_SEC # Reset polling speed when busy
                    await _process_job(job, redis_client)
                else:
                    # Dynamically back off if queue is empty to save Upstash limits
                    await asyncio.sleep(current_poll_interval)
                    current_poll_interval = min(current_poll_interval + 1.0, MAX_POLL_INTERVAL_SEC)
            except Exception as e:
                consecutive_errors += 1
                backoff = min(2 ** consecutive_errors, 60)
                logger.error(f"Loop error #{consecutive_errors}: {e} — sleeping {backoff}s")
                await asyncio.sleep(backoff)

    if _pool:
        await _pool.close()
    logger.info("Worker exited cleanly.")


def _run_dummy_server():
    """Cloud Run requires listening on $PORT for health checks."""
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        def log_message(self, *args):
            pass # Suppress noisy access logs
            
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    # ── Health server starts FIRST — always — so Cloud Run startup probe passes
    # regardless of secret availability or any downstream errors.
    threading.Thread(target=_run_dummy_server, daemon=True, name="health-server").start()
    logger.info(f"Health server started on port {os.environ.get('PORT', 8080)}")

    required = ["SUPABASE_DB_URL", "UPSTASH_REDIS_URL", "UPSTASH_REDIS_TOKEN"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        logger.critical(
            f"Missing required env vars: {missing}. "
            "Worker is idle — add secrets in Cloud Run console then redeploy."
        )
        # Block forever so the container stays alive and healthy for Cloud Run.
        # The health server thread is daemon=True so it keeps running.
        threading.Event().wait()
    else:
        asyncio.run(worker_loop())
