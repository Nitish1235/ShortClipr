from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.middleware.auth import get_current_user
from app.models.user import UserDB, UserPublic
from app.services.database import update_user, get_user_jobs

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserPublic, summary="Get current user profile")
async def get_me(current_user: UserDB = Depends(get_current_user)):
    return current_user


@router.get("/me/usage", summary="Get user shorts usage")
async def get_usage(current_user: UserDB = Depends(get_current_user)):
    return {
        "shorts_generated":  current_user.credits_used,
        "shorts_limit":      current_user.credits_limit,
        "shorts_remaining":  max(0, current_user.credits_limit - current_user.credits_used),
        "subscription_tier": current_user.subscription_tier,
    }


@router.get("/me/stats", summary="Get user stats for dashboard")
async def get_stats(current_user: UserDB = Depends(get_current_user)):
    """
    Returns shorts usage + subscription tier + job/clip aggregates.
    Used by the dashboard header shorts bar.
    """
    try:
        all_jobs = await get_user_jobs(current_user.id, limit=200)
    except Exception:
        all_jobs = []

    completed  = sum(1 for j in all_jobs if j.status == "completed")
    processing = sum(1 for j in all_jobs if j.status == "processing")
    total_clips = sum(j.clip_count or 0 for j in all_jobs)

    return {
        "shorts_generated":  current_user.credits_used,
        "shorts_limit":      current_user.credits_limit,
        "shorts_remaining":  max(0, current_user.credits_limit - current_user.credits_used),
        "subscription_tier": current_user.subscription_tier,
        "jobs_total":        len(all_jobs),
        "jobs_completed":    completed,
        "jobs_processing":   processing,
        "clips_generated":   total_clips,
    }
