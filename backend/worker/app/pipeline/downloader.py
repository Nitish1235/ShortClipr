"""
downloader.py — Download source video from YouTube (yt-dlp) or Google Cloud Storage.

Download Strategy (in order of attempt):
  1. PRIMARY: Heavy browser impersonation via yt-dlp's --impersonate chrome flag.
     Tries multiple official YouTube player clients (web, ios, android, tv, safari).
     Works for most public videos without requiring user cookies.

  2. FALLBACK: Cookie-based authentication via YOUTUBE_COOKIES env var.
     Required for age-restricted or bot-detection-heavy environments.
     Set YOUTUBE_COOKIES to a base64-encoded Netscape cookies.txt from Firefox.

Supported GCS video_url formats:
  gs://bucket-name/path/to/file.mp4
  https://storage.googleapis.com/bucket/path/to/file.mp4
  https://storage.cloud.google.com/bucket/path/to/file.mp4
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

# Realistic Chrome 130 User-Agent — matches what yt-dlp impersonation expects
_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)


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
    """Convert any GCS URL format to a canonical gs://bucket/path URI."""
    if url.startswith("gs://"):
        return url
    m = _GCS_HTTPS_RE.match(url)
    if m:
        return f"gs://{m.group(1)}/{m.group(2)}"
    logger.warning(f"Unrecognised GCS URL format: {url}")
    return url


# ── Cookie helpers ────────────────────────────────────────────────────────────

def _write_cookie_file() -> str | None:
    """
    Read YOUTUBE_COOKIES env var (base64-encoded Netscape cookies.txt from Firefox),
    decode and write to a temp file. Returns path or None if not set.
    """
    raw = os.getenv("YOUTUBE_COOKIES", "").strip()
    if not raw:
        return None
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="yt_cookies_", delete=False
        )
        tmp.write(decoded)
        tmp.flush()
        tmp.close()
        logger.info(f"YouTube cookies written to: {tmp.name}")
        return tmp.name
    except Exception as e:
        logger.error(f"Failed to decode YOUTUBE_COOKIES: {e}")
        return None


# ── yt-dlp option builders ────────────────────────────────────────────────────

def _base_opts(output_path: str) -> dict:
    """Common yt-dlp options shared across all download strategies."""
    return {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path,
        "quiet": False,
        "no_warnings": False,
        "merge_output_format": "mp4",
        "socket_timeout": 60,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        # Human-like pacing — critical for avoiding rate limits in batch mode
        "sleep_interval": 2,
        "max_sleep_interval": 5,
        "sleep_interval_requests": 1,
    }


def _primary_impersonation_opts(output_path: str) -> dict:
    """
    PRIMARY strategy: Chrome browser impersonation + multi-client player fallback.
    Works for most public YouTube videos without cookies.
    """
    opts = _base_opts(output_path)
    opts.update({
        # Impersonate a real Chrome browser — yt-dlp spoofs TLS fingerprint + headers
        "impersonate": "chrome",
        "http_headers": {
            "User-Agent": _CHROME_UA,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        # Try 5 official YouTube player clients in order:
        # web       → standard desktop client
        # ios       → Apple mobile client (less bot-checked)
        # android   → Google mobile client
        # web_safari → Safari desktop spoofing (bypasses some SABR checks)
        # tv        → YouTube TV embedded client
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "ios", "android", "web_safari", "tv"],
            }
        },
    })
    return opts


def _cookie_fallback_opts(output_path: str, cookie_file: str) -> dict:
    """
    FALLBACK strategy: Authenticated download using browser-exported cookies.
    Required when impersonation is blocked by YouTube's bot detection.
    """
    opts = _base_opts(output_path)
    opts.update({
        "cookiefile": cookie_file,
        "http_headers": {"User-Agent": _CHROME_UA},
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "ios", "tv"],
            }
        },
    })
    return opts


# ── Download backends ─────────────────────────────────────────────────────────

def _download_youtube_sync(youtube_url: str, output_path: str) -> str:
    """
    Download a YouTube video using a two-phase strategy:
      1. Chrome impersonation (no cookies needed) — for public videos
      2. Cookie authentication fallback — for bot-detection-heavy environments

    Always runs in a thread via asyncio.to_thread().
    """
    cookie_file = _write_cookie_file()

    # ── Phase 1: Chrome impersonation ────────────────────────────────────────
    logger.info("YouTube download — Phase 1: Chrome impersonation + multi-client")
    try:
        opts = _primary_impersonation_opts(output_path)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([youtube_url])
        logger.info("Phase 1 succeeded (Chrome impersonation).")
        _cleanup_cookie(cookie_file)
        return _resolve_output_path(output_path)
    except Exception as e:
        logger.warning(f"Phase 1 failed: {e!s:.200}")

    # ── Phase 2: Cookie authentication ───────────────────────────────────────
    if cookie_file:
        logger.info("YouTube download — Phase 2: Cookie-based authentication")
        try:
            opts = _cookie_fallback_opts(output_path, cookie_file)
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([youtube_url])
            logger.info("Phase 2 succeeded (cookie auth).")
            _cleanup_cookie(cookie_file)
            return _resolve_output_path(output_path)
        except Exception as e:
            logger.error(f"Phase 2 failed: {e!s:.200}")
            _cleanup_cookie(cookie_file)
            raise RuntimeError(
                f"YouTube download failed after both strategies. "
                f"Re-export fresh Firefox cookies and update YOUTUBE_COOKIES. Error: {e}"
            ) from e
    else:
        raise RuntimeError(
            "YouTube download failed (Chrome impersonation blocked). "
            "Set YOUTUBE_COOKIES env var with fresh Firefox cookies to enable fallback."
        )


def _resolve_output_path(output_path: str) -> str:
    """yt-dlp sometimes auto-appends .mp4 — normalise the path."""
    if not os.path.exists(output_path) and os.path.exists(output_path + ".mp4"):
        return output_path + ".mp4"
    return output_path


def _cleanup_cookie(cookie_file: str | None) -> None:
    """Safely remove the temp cookie file."""
    if cookie_file and os.path.exists(cookie_file):
        try:
            os.unlink(cookie_file)
            logger.info("Temp cookie file cleaned up.")
        except Exception:
            pass


def _download_gcs_sync(gcs_url: str, output_path: str) -> str:
    """Download from GCS (blocking). Accepts both gs:// and HTTPS GCS URLs."""
    gcs_uri = _to_gcs_uri(gcs_url)
    without_scheme = gcs_uri.replace("gs://", "")
    bucket_name, blob_name = without_scheme.split("/", 1)
    client = _get_storage_client()
    blob = client.bucket(bucket_name).blob(blob_name)
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
