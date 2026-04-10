"""
Jobs Router — create, list, get, cancel video processing jobs
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List

from app.middleware.auth import get_current_user
from app.models.user import UserDB
from app.models.job import JobCreate, JobPublic, JobStatus
from app.services.database import (
    create_job, get_job, get_user_jobs, update_job_status, delete_job
)
from app.services.queue import push_job, get_job_status

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _check_job_ownership(job, user: UserDB):
    if job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied to this job.")


@router.post("", response_model=JobPublic, status_code=201, summary="Create a new video processing job")
async def create_new_job(
    job_data: JobCreate,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Create a job and push it to the Upstash Redis queue for async worker pickup.
    Requires either video_url (after GCS upload) or youtube_url.
    """
    if not job_data.video_url and not job_data.youtube_url:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'video_url' (from GCS upload) or 'youtube_url'.",
        )

    # Check credits
    if current_user.credits_used >= current_user.credits_limit:
        raise HTTPException(
            status_code=402,
            detail=f"Credit limit reached ({current_user.credits_limit} clips). Upgrade your plan.",
        )

    # Create job record in Firestore
    job = await create_job(current_user.id, job_data)

    # Update to queued status
    await update_job_status(job.job_id, JobStatus.QUEUED, progress=2, current_step="Queued for processing")

    # Push to Redis queue
    queue_payload = {
        "job_id": job.job_id,
        "user_id": current_user.id,
        "video_url": job_data.video_url,
        "youtube_url": job_data.youtube_url,
        "options": job_data.options or {},
        "template_id": job_data.template_id or "viral-hook",
    }
    await push_job(queue_payload)

    # Return updated job
    updated_job = await get_job(job.job_id)
    return JobPublic(**updated_job.model_dump())


@router.get("", response_model=List[JobPublic], summary="List all jobs for the current user")
async def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserDB = Depends(get_current_user),
):
    """Return paginated list of the user's jobs, newest first."""
    jobs = await get_user_jobs(current_user.id, limit=limit, offset=offset)
    return [JobPublic(**j.model_dump()) for j in jobs]


@router.get("/{job_id}", response_model=JobPublic, summary="Get a specific job's status and results")
async def get_job_detail(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Get full job details including clip URLs once processing completes.
    Also checks Redis for real-time progress data.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    _check_job_ownership(job, current_user)

    # Merge Redis real-time status if available
    realtime = await get_job_status(job_id)
    if realtime and job.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
        job.progress = realtime.get("progress", job.progress)
        job.current_step = realtime.get("current_step", job.current_step)

    return JobPublic(**job.model_dump())


@router.delete("/{job_id}", status_code=204, summary="Cancel or delete a job")
async def cancel_job(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Cancel a pending/queued job, or delete a completed/failed job.
    Active processing jobs are marked for cancellation.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    _check_job_ownership(job, current_user)

    if job.status in (JobStatus.PENDING, JobStatus.QUEUED):
        await update_job_status(job_id, JobStatus.CANCELLED, current_step="Cancelled by user")
    elif job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
        await delete_job(job_id)
    else:
        await update_job_status(job_id, JobStatus.CANCELLED, current_step="Cancellation requested")

    return None
