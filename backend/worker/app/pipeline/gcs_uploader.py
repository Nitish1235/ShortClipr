"""
gcs_uploader.py — Upload final clip/thumbnail to GCS and optionally delete source blob.

All GCS paths follow: users/{user_id}/jobs/{job_id}/clips/{clip_id}.mp4
                      users/{user_id}/jobs/{job_id}/thumbnails/{clip_id}.jpg

Source deletion: after all clips for a job are generated, the original uploaded
video is deleted from GCS automatically to avoid storage costs.
"""
import asyncio
import logging
import os
import re
from google.cloud import storage

logger = logging.getLogger(__name__)

GCP_PROJECT_ID    = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_OUTPUT = os.getenv("GCS_BUCKET_OUTPUT", "shortclipr-output-clips")

_storage_client = None


def _get_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=GCP_PROJECT_ID)
    return _storage_client


# ── URL → (bucket, blob) parser ───────────────────────────────────────────────

_GCS_HTTPS_RE = re.compile(
    r"https://storage(?:\.googleapis\.com|\.cloud\.google\.com)/([^/]+)/(.+)"
)

def _parse_gcs_url(url: str) -> tuple[str, str] | None:
    """
    Parse any GCS URL into (bucket_name, blob_name).
    Supports gs:// and HTTPS GCS formats.
    Returns None if the URL is not a recognised GCS URL.
    """
    if url.startswith("gs://"):
        without = url.replace("gs://", "")
        parts   = without.split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
    m = _GCS_HTTPS_RE.match(url)
    if m:
        return m.group(1), m.group(2)
    return None


# ── Core upload helper ────────────────────────────────────────────────────────

def _upload_sync(
    local_path:   str,
    gcs_path:     str,
    content_type: str,
    make_public:  bool = True,
) -> str:
    client = _get_client()
    bucket = client.bucket(GCS_BUCKET_OUTPUT)
    blob   = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path, content_type=content_type)
    if make_public:
        blob.make_public()
        return blob.public_url
    return f"gs://{GCS_BUCKET_OUTPUT}/{gcs_path}"


# ── Public upload functions ───────────────────────────────────────────────────

async def upload_clip(local_path: str, user_id: str, job_id: str, clip_id: str) -> str:
    """Upload the final rendered MP4 clip. Returns public HTTPS URL."""
    gcs_path = f"users/{user_id}/jobs/{job_id}/clips/{clip_id}.mp4"
    logger.info(f"Uploading clip → gs://{GCS_BUCKET_OUTPUT}/{gcs_path}")
    url = await asyncio.to_thread(_upload_sync, local_path, gcs_path, "video/mp4", True)
    logger.info(f"Clip uploaded: {url}")
    return url


async def upload_thumbnail(local_path: str, user_id: str, job_id: str, clip_id: str) -> str:
    """Upload the thumbnail JPEG. Returns public HTTPS URL."""
    gcs_path = f"users/{user_id}/jobs/{job_id}/thumbnails/{clip_id}.jpg"
    logger.info(f"Uploading thumbnail → gs://{GCS_BUCKET_OUTPUT}/{gcs_path}")
    url = await asyncio.to_thread(_upload_sync, local_path, gcs_path, "image/jpeg", True)
    logger.info(f"Thumbnail uploaded: {url}")
    return url


# ── Source video deletion ─────────────────────────────────────────────────────

def _delete_blob_sync(bucket_name: str, blob_name: str) -> None:
    """Delete a single GCS blob (blocking)."""
    try:
        client = _get_client()
        blob   = client.bucket(bucket_name).blob(blob_name)
        blob.delete()
        logger.info(f"Deleted source blob: gs://{bucket_name}/{blob_name}")
    except Exception as exc:
        # Non-fatal: log and continue. Don't let deletion failure break the job.
        logger.warning(f"Could not delete source blob gs://{bucket_name}/{blob_name}: {exc}")


async def delete_source_video(video_url: str) -> None:
    """
    Delete the original uploaded video from GCS after all clips are generated.
    Accepts gs:// URIs and HTTPS GCS URLs.
    Silently skips if the URL cannot be parsed (e.g. YouTube URL passed by mistake).
    """
    if not video_url:
        return
    parsed = _parse_gcs_url(video_url)
    if parsed is None:
        logger.debug(f"delete_source_video: not a GCS URL, skipping: {video_url}")
        return
    bucket_name, blob_name = parsed
    logger.info(f"Deleting source video from GCS: gs://{bucket_name}/{blob_name}")
    await asyncio.to_thread(_delete_blob_sync, bucket_name, blob_name)
