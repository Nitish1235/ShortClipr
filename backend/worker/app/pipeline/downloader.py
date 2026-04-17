"""
downloader.py — Download source video from YouTube (yt-dlp) or Google Cloud Storage.

Supported video_url formats:
  gs://bucket-name/path/to/file.mp4          — GCS native URI
  https://storage.googleapis.com/bucket/...   — GCS public/signed HTTPS URL
  https://storage.cloud.google.com/bucket/... — alternate GCS HTTPS URL

YouTube is always preferred over GCS URL when both are provided.

YouTube Authentication:
  Set the YOUTUBE_COOKIES env var to the base64-encoded contents of a
  Netscape-format cookies.txt file exported from a logged-in browser.
  This is required for Cloud Run datacenter IPs to bypass bot detection.

  To generate the env var value:
    1. Export cookies.txt from YouTube (use "Get cookies.txt LOCALLY" extension)
    2. Run: base64 -w 0 cookies.txt
    3. Paste the output as the YOUTUBE_COOKIES env var in Cloud Run
"""
import asyncio
import base64
import logging
import os
import re
import tempfile
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
    Convert any GCS URL format to a canonical gs://bucket/path URI.
    Passes through gs:// URIs unchanged.
    """
    if url.startswith("gs://"):
        return url
    m = _GCS_HTTPS_RE.match(url)
    if m:
        bucket, blob = m.group(1), m.group(2)
        return f"gs://{bucket}/{blob}"
    logger.warning(f"Unrecognised GCS URL format: {url}")
    return url


# ── Cookie helpers ────────────────────────────────────────────────────────────

def _write_cookie_file() -> str | None:
    """
    Read YOUTUBE_COOKIES env var (base64-encoded Netscape cookies.txt),
    decode it, write to a temp file, and return the path.
    Returns None if the env var is not set.
    """
    raw = os.getenv("YOUTUBE_COOKIES", "").strip()
    if not raw:
        logger.warning(
            "YOUTUBE_COOKIES env var not set — attempting unauthenticated download. "
            "This will likely fail on Cloud Run datacenter IPs."
        )
        return None
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="yt_cookies_", delete=False
        )
        tmp.write(decoded)
        tmp.flush()
        tmp.close()
        logger.info(f"YouTube cookies written to temp file: {tmp.name}")
        return tmp.name
    except Exception as e:
        logger.error(f"Failed to decode YOUTUBE_COOKIES: {e}")
        return None


# ── Download backends ─────────────────────────────────────────────────────────

def _download_youtube_sync(youtube_url: str, output_path: str) -> str:
    """Download a YouTube video via yt-dlp (blocking). Runs in a thread."""
    cookie_file = _write_cookie_file()

    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path,
        "quiet": False,
        "no_warnings": False,
        "socket_timeout": 60,
        "merge_output_format": "mp4",
        "retries": 5,
        "fragment_retries": 5,
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file
        logger.info("Using authenticated YouTube cookies for download.")
    else:
        # Fallback: try mweb client without cookies (likely to fail on Cloud Run)
        ydl_opts["extractor_args"] = {
            "youtube": {
                "player_client": ["mweb", "web_creator"],
            }
        }
        logger.warning("No cookies — falling back to mweb client (may fail).")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    finally:
        # Always clean up the temp cookie file
        if cookie_file and os.path.exists(cookie_file):
            os.unlink(cookie_file)
            logger.info("Cleaned up temp cookie file.")

    # yt-dlp sometimes appends the extension automatically
    if not os.path.exists(output_path) and os.path.exists(output_path + ".mp4"):
        return output_path + ".mp4"
    return output_path


def _download_gcs_sync(gcs_url: str, output_path: str) -> str:
    """Download from GCS (blocking). Accepts both gs:// and HTTPS GCS URLs."""
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
