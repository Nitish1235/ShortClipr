"""
database.py — Supabase / PostgreSQL database service using asyncpg.

Replaces Firestore entirely.
Storage (GCS) is unchanged.

Connection: asyncpg pool connecting to Supabase's Postgres via the
            direct connection string (not PostgREST).
"""
import json
import uuid
import asyncpg
import logging
from datetime import datetime, timezone
from typing import Optional, List

from app.config import settings
from app.models.user import UserDB, UserCreate
from app.models.job import JobDB, JobCreate, JobStatus, ClipResult

logger = logging.getLogger("shortclipr.db")

# ── Connection pool (singleton) ───────────────────────────────────────────────
_pool: Optional[asyncpg.Pool] = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.SUPABASE_DB_URL,
            min_size=2,
            max_size=10,
            command_timeout=30,
            # Needed for asyncpg to decode JSONB columns automatically
            init=_init_connection,
        )
    return _pool


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Register custom codecs for JSONB."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


# Used by main.py readiness probe
def _get_db():
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_user(row: asyncpg.Record) -> UserDB:
    return UserDB(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        picture=row["picture"],
        google_id=row["google_id"],
        subscription_tier=row["subscription_tier"],
        credits_used=row["credits_used"],
        credits_limit=row["credits_limit"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_job(row: asyncpg.Record, clips: List[ClipResult] | None = None) -> JobDB:
    return JobDB(
        job_id=row["job_id"],
        user_id=row["user_id"],
        video_url=row["video_url"],
        youtube_url=row["youtube_url"],
        template_id=row.get("template_id", "viral-hook"),
        options=row["options"] or {},
        status=JobStatus(row["status"]),
        progress=row["progress"],
        current_step=row["current_step"] or "",
        error_message=row["error_message"],
        clip_count=row["clip_count"],
        video_duration=row["video_duration"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
        clips=clips or [],
    )


def _row_to_clip(row: asyncpg.Record) -> ClipResult:
    return ClipResult(
        clip_id=row["clip_id"],
        clip_url=row["clip_url"],
        thumbnail_url=row["thumbnail_url"],
        duration=row["duration"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        transcript_snippet=row["transcript_snippet"],
        viral_score=row["viral_score"],
        top_title=row["top_title"],
        bottom_tag=row["bottom_tag"],
        template_id=row["template_id"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

async def get_user_by_google_id(google_id: str) -> Optional[UserDB]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE google_id = $1", google_id
        )
    return _row_to_user(row) if row else None


async def get_user_by_id(user_id: str) -> Optional[UserDB]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
    return _row_to_user(row) if row else None


async def get_user_by_email(email: str) -> Optional[UserDB]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1", email
        )
    return _row_to_user(row) if row else None


async def create_user(user_data: UserCreate) -> UserDB:
    pool = await _get_pool()
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users
                (id, email, name, picture, google_id,
                 subscription_tier, credits_used, credits_limit,
                 is_active, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,'free',0,3,TRUE,$6,$7)
            RETURNING *
            """,
            user_id, user_data.email, user_data.name,
            user_data.picture, user_data.google_id,
            now, now,
        )
    return _row_to_user(row)


async def update_user(user_id: str, updates: dict) -> Optional[UserDB]:
    """Generic key-value update for the users row."""
    if not updates:
        return await get_user_by_id(user_id)

    # Build SET clause dynamically
    set_clauses = []
    values = []
    for i, (key, val) in enumerate(updates.items(), start=1):
        set_clauses.append(f"{key} = ${i}")
        values.append(val)

    values.append(user_id)  # last param for WHERE
    sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ${len(values)} RETURNING *"

    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *values)
    return _row_to_user(row) if row else None


async def increment_user_shorts(user_id: str, count: int = 1) -> None:
    """Atomically increment credits_used (= shorts generated)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET credits_used = credits_used + $1 WHERE id = $2",
            count, user_id,
        )


# ─────────────────────────────────────────────────────────────────────────────
# JOB OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

async def create_job(user_id: str, job_create: JobCreate) -> JobDB:
    pool = await _get_pool()
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    options_json = json.dumps(job_create.options or {})

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO jobs
                (job_id, user_id, video_url, youtube_url, template_id,
                 options, status, progress, current_step,
                 clip_count, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,'pending',0,'Queued',0,$7,$8)
            RETURNING *
            """,
            job_id, user_id,
            job_create.video_url, job_create.youtube_url,
            job_create.template_id or "viral-hook",
            options_json, now, now,
        )
    return _row_to_job(row)


async def get_job(job_id: str) -> Optional[JobDB]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        job_row = await conn.fetchrow(
            "SELECT * FROM jobs WHERE job_id = $1", job_id
        )
        if not job_row:
            return None
        clip_rows = await conn.fetch(
            "SELECT * FROM clips WHERE job_id = $1 ORDER BY created_at",
            job_id,
        )
    clips = [_row_to_clip(r) for r in clip_rows]
    return _row_to_job(job_row, clips)


async def get_user_jobs(
    user_id: str, limit: int = 20, offset: int = 0
) -> List[JobDB]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        job_rows = await conn.fetch(
            """
            SELECT * FROM jobs
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id, limit, offset,
        )
        if not job_rows:
            return []
        job_ids = [r["job_id"] for r in job_rows]
        clip_rows = await conn.fetch(
            "SELECT * FROM clips WHERE job_id = ANY($1::text[]) ORDER BY created_at",
            job_ids,
        )

    # Group clips by job_id
    clips_by_job: dict[str, List[ClipResult]] = {}
    for cr in clip_rows:
        jid = cr["job_id"]
        clips_by_job.setdefault(jid, []).append(_row_to_clip(cr))

    return [_row_to_job(r, clips_by_job.get(r["job_id"], [])) for r in job_rows]


async def update_job_status(
    job_id: str,
    status: JobStatus,
    progress: int = None,
    current_step: str = None,
    error_message: str = None,
    extra_fields: dict = None,
) -> None:
    sets  = ["status = $1", "updated_at = NOW()"]
    vals  = [status.value]
    i     = 2

    if progress is not None:
        sets.append(f"progress = ${i}"); vals.append(progress); i += 1
    if current_step is not None:
        sets.append(f"current_step = ${i}"); vals.append(current_step); i += 1
    if error_message is not None:
        sets.append(f"error_message = ${i}"); vals.append(error_message[:1000]); i += 1
    if status == JobStatus.COMPLETED:
        sets.append(f"completed_at = NOW()")
    if extra_fields:
        for k, v in extra_fields.items():
            sets.append(f"{k} = ${i}"); vals.append(v); i += 1

    vals.append(job_id)
    sql = f"UPDATE jobs SET {', '.join(sets)} WHERE job_id = ${i}"

    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(sql, *vals)


async def save_clips(job_id: str, user_id: str, clips: list[dict]) -> None:
    """Bulk-insert clip results and update job clip_count."""
    if not clips:
        return
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


async def delete_job(job_id: str) -> bool:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM jobs WHERE job_id = $1", job_id
        )
    return result == "DELETE 1"
