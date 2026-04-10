"""
videos.py — Video upload endpoints.

Two upload strategies:
  1. Signed URL (preferred for large files):
     Frontend → GET /videos/signed-url → PUT directly to GCS → pass gcs_uri to /jobs
  2. Direct upload (small files / convenience):
     Frontend → POST /videos/upload (multipart) → API streams to GCS → returns gcs_uri
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.user import UserDB
from app.services.gcs import generate_signed_upload_url, stream_upload_to_gcs
from app.config import settings

router = APIRouter(prefix="/videos", tags=["Videos"])

MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024   # 4 GB hard cap

ALLOWED_CONTENT_TYPES = {
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm", "video/mpeg",
}


# ── 1. Signed URL (preferred) ─────────────────────────────────────────────────

class SignedUrlRequest(BaseModel):
    filename:     str
    content_type: str = "video/mp4"
    file_size:    Optional[int] = None   # bytes, for validation

class SignedUrlResponse(BaseModel):
    upload_url: str
    gcs_uri:    str
    expires_in: int   # seconds

@router.post(
    "/signed-url",
    response_model=SignedUrlResponse,
    summary="Get a signed URL for direct client → GCS upload",
)
async def get_signed_url(
    req: SignedUrlRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Returns a short-lived signed PUT URL.
    The frontend uploads the video file directly to GCS using this URL.
    This avoids sending large files through the API gateway.
    """
    if req.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type: {req.content_type}. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )
    if req.file_size and req.file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Max 4 GB.")

    safe_filename = req.filename.replace("/", "_").replace("\\", "_")[:128]

    try:
        info = generate_signed_upload_url(
            user_id=current_user.id,
            filename=safe_filename,
            content_type=req.content_type,
        )
        return SignedUrlResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate signed URL: {e}")


# ── 2. Direct multipart upload (convenience) ──────────────────────────────────

class UploadResponse(BaseModel):
    url:     str   # public HTTPS URL
    gcs_uri: str   # gs://bucket/path — pass this to POST /jobs

@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a video file directly through the API (max 500 MB)",
)
async def upload_video(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Streams a multipart upload to GCS.
    For files > 500 MB, use the /videos/signed-url endpoint instead.
    """
    DIRECT_UPLOAD_LIMIT = 500 * 1024 * 1024   # 500 MB for direct path

    content_type = file.content_type or "video/mp4"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported video type: {content_type}")

    safe_name  = (file.filename or "upload.mp4").replace("/", "_").replace("\\", "_")[:128]
    blob_name  = f"uploads/{current_user.id}/{uuid.uuid4().hex}/{safe_name}"

    try:
        data = await file.read(DIRECT_UPLOAD_LIMIT + 1)
        if len(data) > DIRECT_UPLOAD_LIMIT:
            raise HTTPException(
                status_code=413,
                detail="File too large for direct upload (max 500 MB). Use /videos/signed-url.",
            )
        result = await stream_upload_to_gcs(
            blob_name=blob_name,
            data=data,
            content_type=content_type,
            bucket=settings.GCS_BUCKET_INPUT,
        )
        return UploadResponse(url=result["public_url"], gcs_uri=result["gcs_uri"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
