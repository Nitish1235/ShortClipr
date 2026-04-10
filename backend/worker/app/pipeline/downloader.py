"""
downloader.py — Download source video from YouTube (yt-dlp) or Google Cloud Storage.

Supported video_url formats:
  gs://bucket-name/path/to/file.mp4          — GCS native URI
  https://storage.googleapis.com/bucket/...   — GCS public/signed HTTPS URL
  https://storage.cloud.google.com/bucket/... — alternate GCS HTTPS URL

YouTube is always preferred over GCS URL when both are provided.
"""
import asyncio
import logging
import os
import re
import yt_dlp
from google.cloud import storage

logger = logging.getLogger(__name__)

GCP_PROJECT_ID  = os.getenv("GCP_PROJECT_ID")
_storage_client = None


def _get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=GCP_PROJECT_ID)
    return _storage_client


# ── URL normalisation ─────────────────────────────────────────────────────────

_GCS_HTTPS_RE = re.compile(
    r"https://storage(?:\.googleapis\.com|\.cloud\.google\.com)/([^/]+)/(.+)"
)

def _to_gcs_uri(url: str) -> str:
    """
    Convert any GSC URL format to a canonical gs://bucket/path URI.
    Passes through gs:// URIs unchanged.
    """
    if url.startswith("gs://"):
        return url
    m = _GCS_HTTPS_RE.match(url)
    if m:
        bucket, blob = m.group(1), m.group(2)
        return f"gs://{bucket}/{blob}"
    # Unknown format — return as-is and let the download attempt fail gracefully
    logger.warning(f"Unrecognised GCS URL format: {url}")
    return url


# ── Download backends ─────────────────────────────────────────────────────────

def _download_youtube_sync(youtube_url: str, output_path: str) -> str:
    """Download a YouTube video via yt-dlp (blocking). Runs in a thread."""
    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    # yt-dlp sometimes appends the extension automatically
    if not os.path.exists(output_path) and os.path.exists(output_path + ".mp4"):
        return output_path + ".mp4"
    return output_path


def _download_gcs_sync(gcs_url: str, output_path: str) -> str:
    """Download from GCS (blocking). Accepts both gs:// and HTTPS GCS URLs. Runs in a thread."""
    gcs_uri = _to_gcs_uri(gcs_url)
    without_scheme = gcs_uri.replace("gs://", "")
    bucket_name, blob_name = without_scheme.split("/", 1)
    client = _get_storage_client()
    blob   = client.bucket(bucket_name).blob(blob_name)
    blob.download_to_filename(output_path)
    logger.info(f"Downloaded gs://{bucket_name}/{blob_name} → {output_path}")
    return output_path


# ── Public API ────────────────────────────────────────────────────────────────

async def download(
    job_id:      str,
    youtube_url: str | None,
    video_url:   str | None,
    work_dir:    str,
) -> str:
    """
    Download the source video and return the local file path.
    Prefers youtube_url over video_url (GCS) when both are provided.
    """
    os.makedirs(work_dir, exist_ok=True)
    output_path = os.path.join(work_dir, "source.mp4")

    if youtube_url:
        logger.info(f"[{job_id}] Downloading YouTube: {youtube_url}")
        result = await asyncio.to_thread(_download_youtube_sync, youtube_url, output_path)
        logger.info(f"[{job_id}] YouTube download complete → {result}")
        return result

    if video_url:
        logger.info(f"[{job_id}] Downloading GCS source: {video_url}")
        result = await asyncio.to_thread(_download_gcs_sync, video_url, output_path)
        logger.info(f"[{job_id}] GCS download complete → {result}")
        return result

    raise ValueError("No video source provided. Provide youtube_url or video_url.")
