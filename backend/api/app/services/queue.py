"""
Upstash Redis Queue Service — push/pop jobs, status tracking
"""
import json
import httpx
from typing import Optional

from app.config import settings

REDIS_BASE_URL = settings.UPSTASH_REDIS_URL
REDIS_TOKEN = settings.UPSTASH_REDIS_TOKEN
QUEUE_KEY = settings.REDIS_JOB_QUEUE


def _redis_headers() -> dict:
    return {"Authorization": f"Bearer {REDIS_TOKEN}"}


async def push_job(job_data: dict) -> bool:
    """Push a job to the Redis queue (RPUSH). Returns True on success."""
    payload = json.dumps(job_data)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{REDIS_BASE_URL}/rpush/{QUEUE_KEY}",
            headers=_redis_headers(),
            json=[payload],
        )
        resp.raise_for_status()
        return True


async def pop_job() -> Optional[dict]:
    """
    Non-blocking pop (LPOP) from the Redis queue.
    Returns the job dict or None if queue is empty.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{REDIS_BASE_URL}/lpop/{QUEUE_KEY}",
            headers=_redis_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") is None:
            return None
        return json.loads(data["result"])


async def queue_length() -> int:
    """Return the current number of jobs in the queue."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{REDIS_BASE_URL}/llen/{QUEUE_KEY}",
            headers=_redis_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("result", 0)


async def set_job_status(job_id: str, status_data: dict, ttl_seconds: int = 86400) -> None:
    """Store real-time job status in Redis (for SSE/polling). TTL: 1 day."""
    key = f"shortclipr:status:{job_id}"
    payload = json.dumps(status_data)
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{REDIS_BASE_URL}/set/{key}",
            headers=_redis_headers(),
            json=[payload, "EX", ttl_seconds],
        )


async def get_job_status(job_id: str) -> Optional[dict]:
    """Retrieve real-time job status from Redis."""
    key = f"shortclipr:status:{job_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{REDIS_BASE_URL}/get/{key}",
            headers=_redis_headers(),
        )
        resp.raise_for_status()
        result = resp.json().get("result")
        if result is None:
            return None
        return json.loads(result)
