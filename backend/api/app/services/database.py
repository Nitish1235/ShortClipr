"""
Firestore Database Service — Users and Jobs CRUD
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from google.cloud import firestore

from app.config import settings
from app.models.user import UserDB, UserCreate
from app.models.job import JobDB, JobCreate, JobStatus

_db: Optional[firestore.AsyncClient] = None


def get_db() -> firestore.AsyncClient:
    global _db
    if _db is None:
        _db = firestore.AsyncClient(
            project=settings.GCP_PROJECT_ID,
            database=settings.FIRESTORE_DATABASE,
        )
    return _db


# ─────────────────────────────────────────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

async def get_user_by_google_id(google_id: str) -> Optional[UserDB]:
    db = get_db()
    query = db.collection("users").where("google_id", "==", google_id).limit(1)
    docs = query.stream()
    async for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        return UserDB(**data)
    return None


async def get_user_by_id(user_id: str) -> Optional[UserDB]:
    db = get_db()
    doc = await db.collection("users").document(user_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return UserDB(**data)


async def get_user_by_email(email: str) -> Optional[UserDB]:
    db = get_db()
    query = db.collection("users").where("email", "==", email).limit(1)
    async for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        return UserDB(**data)
    return None


async def create_user(user_data: UserCreate) -> UserDB:
    db = get_db()
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    data = {
        **user_data.model_dump(),
        "id": user_id,
        "created_at": now,
        "updated_at": now,
        "subscription_tier": "free",
        "credits_used": 0,
        "credits_limit": 3,
        "is_active": True,
    }
    await db.collection("users").document(user_id).set(data)
    return UserDB(**data)


async def update_user(user_id: str, updates: dict) -> Optional[UserDB]:
    db = get_db()
    updates["updated_at"] = datetime.now(timezone.utc)
    await db.collection("users").document(user_id).update(updates)
    return await get_user_by_id(user_id)


# ─────────────────────────────────────────────────────────────────────────────
# JOB OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

async def create_job(user_id: str, job_create: JobCreate) -> JobDB:
    db = get_db()
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    data = {
        "job_id": job_id,
        "user_id": user_id,
        "video_url": job_create.video_url,
        "youtube_url": job_create.youtube_url,
        "options": job_create.options or {},
        "status": JobStatus.PENDING,
        "progress": 0,
        "current_step": "Queued for processing",
        "clips": [],
        "clip_count": 0,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "video_duration": None,
    }
    await db.collection("jobs").document(job_id).set(data)
    return JobDB(**data)


async def get_job(job_id: str) -> Optional[JobDB]:
    db = get_db()
    doc = await db.collection("jobs").document(job_id).get()
    if not doc.exists:
        return None
    return JobDB(**doc.to_dict())


async def get_user_jobs(
    user_id: str, limit: int = 20, offset: int = 0
) -> List[JobDB]:
    db = get_db()
    query = (
        db.collection("jobs")
        .where("user_id", "==", user_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .offset(offset)
    )
    jobs = []
    async for doc in query.stream():
        jobs.append(JobDB(**doc.to_dict()))
    return jobs


async def update_job_status(
    job_id: str,
    status: JobStatus,
    progress: int = None,
    current_step: str = None,
    error_message: str = None,
    extra_fields: dict = None,
) -> None:
    db = get_db()
    updates = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if progress is not None:
        updates["progress"] = progress
    if current_step is not None:
        updates["current_step"] = current_step
    if error_message is not None:
        updates["error_message"] = error_message
    if status == JobStatus.COMPLETED:
        updates["completed_at"] = datetime.now(timezone.utc)
    if extra_fields:
        updates.update(extra_fields)
    await db.collection("jobs").document(job_id).update(updates)


async def add_clip_result(job_id: str, clip: dict) -> None:
    db = get_db()
    await db.collection("jobs").document(job_id).update({
        "clips": firestore.ArrayUnion([clip]),
        "clip_count": firestore.Increment(1),
        "updated_at": datetime.now(timezone.utc),
    })


async def delete_job(job_id: str) -> bool:
    db = get_db()
    doc_ref = db.collection("jobs").document(job_id)
    doc = await doc_ref.get()
    if not doc.exists:
        return False
    await doc_ref.delete()
    return True
