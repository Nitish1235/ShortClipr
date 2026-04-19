"""
downloader.py — Download source video/audio from YouTube (yt-dlp) or GCS.

Download Strategy:
  YouTube:
    • Audio-first: download ONLY the audio track (bestaudio ~5-30MB vs 2GB video).
      This is used for Whisper transcription and moment detection.
    • Clip segments: after GPT identifies viral timestamps, download ONLY those
      specific video segments using yt-dlp's download_ranges feature.
    • bgutil-ytdlp-pot-provider plugin auto-generates YouTube PO tokens to bypass
      datacenter IP bot detection — no cookies required.

  GCS (user-uploaded file):
    • Download the full video from GCS (fast — Google internal network).
    • Audio is extracted from the local file via FFmpeg (audio_extractor.py).

Supported GCS video_url formats:
  gs://bucket-name/path/to/file.mp4
  https://storage.googleapis.com/bucket/path/to/file.mp4
"""
import asyncio
import logging
import os
import re

import yt_dlp
from yt_dlp.utils import download_range_func
from google.cloud import storage

logger = logging.getLogger(__name__)

GCP_PROJECT_ID  = os.getenv("GCP_PROJECT_ID")
_storage_client = None


_BGUTIL_BASE_URL = (
    f"http://127.0.0.1:{os.getenv('BGUTIL_HTTP_SERVER_PORT', '4416')}"
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
    if url.startswith("gs://"):
        return url
    m = _GCS_HTTPS_RE.match(url)
    if m:
        return f"gs://{m.group(1)}/{m.group(2)}"
    logger.warning(f"Unrecognised GCS URL format: {url}")
    return url


# ── yt-dlp base options ───────────────────────────────────────────────────────


# ── Cookie resolution (mounted secret or env var) ─────────────────────────────

# Cloud Run Secret Manager can mount secrets as files or inject as env vars.
# We support both patterns so the operator can choose the easiest approach.

_COOKIE_PATH = "/tmp/shortclipr_yt_cookies.txt"   # where we write the resolved cookie file

def _resolve_cookie_file() -> str | None:
    """
    Resolve a YouTube cookies.txt file from one of two sources (in priority order):

    1. YOUTUBE_COOKIES_FILE  — path to a mounted secret file (e.g. Cloud Run secret volume).
    2. YOUTUBE_COOKIES       — base64-encoded Netscape cookies.txt content injected as env var.

    Returns the path to the cookie file to pass to yt-dlp, or None if no cookies.

    How to export cookies (official yt-dlp recommendation):
      1. Open a private/incognito Chrome window and log into YouTube.
      2. Visit https://www.youtube.com/robots.txt in the SAME tab.
      3. Use "Get cookies.txt LOCALLY" Chrome extension to export youtube.com cookies.
      4. Close the private window immediately (prevents session rotation).
      5. base64-encode the file: base64 cookies.txt | tr -d '\\n'
      6. Add to Cloud Run as secret env var YOUTUBE_COOKIES.
    """

    # Source 1: mounted file (highest precedence)
    file_path = os.getenv("YOUTUBE_COOKIES_FILE", "/app/cookies.txt")
    if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
        logger.info(f"[cookies] Using mounted cookie file: {file_path}")
        return file_path

    # Source 2: base64-encoded env var (Cloud Run secret)
    b64_cookies = os.getenv("YOUTUBE_COOKIES", "").strip()
    if b64_cookies:
        try:
            import base64
            cookie_bytes = base64.b64decode(b64_cookies)
            with open(_COOKIE_PATH, "wb") as f:
                f.write(cookie_bytes)
            logger.info(f"[cookies] Decoded YOUTUBE_COOKIES env var → {_COOKIE_PATH}")
            return _COOKIE_PATH
        except Exception as e:
            logger.warning(f"[cookies] Failed to decode YOUTUBE_COOKIES env var: {e}")

    logger.info("[cookies] No cookie source found — running cookie-free (may hit bot detection)")
    return None


def _yt_base_opts() -> dict:
    """
    Common yt-dlp options shared by audio and clip downloads.
    """
    opts = {
        "quiet": False,
        "no_warnings": False,
        "verbose": True,       # Hardcoded for full visibility in Cloud Run logs
        "no_color": True,
        "nocheckcertificate": True,
        "socket_timeout": 60,
        "retries": 3,
        "fragment_retries": 8,
        "http_headers": {
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Mode": "navigate",
        },
        "sleep_interval": 2,
        "max_sleep_interval": 5,
        "extractor_args": {
            "youtube": {
                # Lists of strings — the canonical yt-dlp extractor_args format
                "player_client": ["web", "mweb", "android"],
            },
            # Correct key for the bgutil-http PO Token provider.
            # Values MUST be lists of strings — yt-dlp parses extractor_args this way
            # even in the Python API. A raw string or bool causes the URL to be lost.
            "youtubepot-bgutilhttp": {
                "base_url": [_BGUTIL_BASE_URL],
            },
        },
    }

    # Attach cookies if available — massively improves bot bypass on datacenter IPs
    cookie_file = _resolve_cookie_file()
    if cookie_file:
        opts["cookiefile"] = cookie_file
        logger.info(f"[cookies] Attached cookiefile to yt-dlp opts: {cookie_file}")

    return opts






# ── Audio-only download ───────────────────────────────────────────────────────

def _download_audio_sync(youtube_url: str, output_path: str) -> str:
    """
    Download only the audio track from YouTube. ~5-30MB vs 1-2GB for full video.
    Used for Whisper transcription. Runs in a thread.
    """
    opts = _yt_base_opts()
    opts.update({
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        # Use a predictable output template so we can find the file reliably
        "outtmpl": output_path,
        "postprocessors": [{
            # Convert to 16kHz mono WAV — Whisper's native format
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "0",
        }],
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([youtube_url])

    # yt-dlp replaces the extension of outtmpl with .wav after postprocessing.
    # e.g. /tmp/.../audio.m4a → /tmp/.../audio.wav
    base_dir = os.path.dirname(output_path)
    stem     = os.path.splitext(os.path.basename(output_path))[0]

    # Primary: exact expected path
    wav_path = os.path.join(base_dir, f"{stem}.wav")
    if os.path.exists(wav_path):
        return wav_path

    # Fallback: any audio file in the working dir
    for fname in sorted(os.listdir(base_dir)):
        if fname.endswith((".wav", ".m4a", ".mp3", ".webm", ".opus")):
            fpath = os.path.join(base_dir, fname)
            logger.info(f"Audio fallback resolved: {fpath}")
            return fpath

    raise FileNotFoundError(
        f"yt-dlp finished but no audio file found in {base_dir}. "
        f"Check yt-dlp postprocessor logs above."
    )


# ── Clip segment download ─────────────────────────────────────────────────────

def _download_clip_segment_sync(
    youtube_url: str,
    start: float,
    end: float,
    output_path: str,
) -> str:
    """
    Download only a specific time range of a YouTube video.
    e.g. start=120.0, end=165.0 downloads only seconds 120-165.
    This avoids downloading the entire video — critical for large podcasts/streams.
    Runs in a thread.
    """
    opts = _yt_base_opts()
    opts.update({
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path,
        "merge_output_format": "mp4",
        # download_range_func tells yt-dlp to only fetch the specified byte ranges
        "download_ranges": download_range_func(None, [(start, end)]),
        # Force keyframe cuts at exact timestamps (may be slightly imprecise but fast)
        "force_keyframes_at_cuts": True,
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([youtube_url])

    return _resolve_path(output_path)


# ── GCS download ──────────────────────────────────────────────────────────────

def _download_gcs_sync(gcs_url: str, output_path: str) -> str:
    gcs_uri = _to_gcs_uri(gcs_url)
    without_scheme = gcs_uri.replace("gs://", "")
    bucket_name, blob_name = without_scheme.split("/", 1)
    client = _get_storage_client()
    blob = client.bucket(bucket_name).blob(blob_name)
    blob.download_to_filename(output_path)
    logger.info(f"Downloaded gs://{bucket_name}/{blob_name} → {output_path}")
    return output_path


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_path(output_path: str) -> str:
    """Handle yt-dlp auto-appending extensions."""
    if os.path.exists(output_path):
        return output_path
    for ext in (".mp4", ".webm", ".mkv"):
        if os.path.exists(output_path + ext):
            return output_path + ext
    return output_path


# ── Public API ────────────────────────────────────────────────────────────────

async def download_audio(
    job_id: str,
    youtube_url: str,
    work_dir: str,
) -> str:
    """
    Download only the audio track from YouTube for Whisper transcription.
    Returns path to the local audio file (.wav).
    """
    os.makedirs(work_dir, exist_ok=True)
    output_path = os.path.join(work_dir, "audio.m4a")
    logger.info(f"[{job_id}] Downloading YouTube audio-only: {youtube_url}")
    result = await asyncio.to_thread(_download_audio_sync, youtube_url, output_path)
    logger.info(f"[{job_id}] Audio download complete → {result}")
    return result


async def download_clip(
    job_id: str,
    youtube_url: str,
    start: float,
    end: float,
    work_dir: str,
    clip_index: int,
) -> str:
    """
    Download a specific time-range segment of a YouTube video.
    Returns path to the local .mp4 clip file.
    """
    output_path = os.path.join(work_dir, f"raw_clip_{clip_index}.mp4")
    logger.info(f"[{job_id}] Downloading clip segment {clip_index}: {start:.1f}s → {end:.1f}s")
    result = await asyncio.to_thread(
        _download_clip_segment_sync, youtube_url, start, end, output_path
    )
    logger.info(f"[{job_id}] Clip {clip_index} download complete → {result}")
    return result


async def download_gcs(
    job_id: str,
    video_url: str,
    work_dir: str,
) -> str:
    """
    Download a full video from Google Cloud Storage.
    Used for user-uploaded files (not YouTube).
    """
    os.makedirs(work_dir, exist_ok=True)
    output_path = os.path.join(work_dir, "source.mp4")
    logger.info(f"[{job_id}] Downloading GCS source: {video_url}")
    result = await asyncio.to_thread(_download_gcs_sync, video_url, output_path)
    logger.info(f"[{job_id}] GCS download complete → {result}")
    return result


# ── Legacy compatibility (keep old signature working) ────────────────────────

async def download(
    job_id: str,
    youtube_url: str | None,
    video_url: str | None,
    work_dir: str,
) -> str:
    """Legacy entry point — used by GCS video_url path only."""
    os.makedirs(work_dir, exist_ok=True)
    if video_url:
        return await download_gcs(job_id, video_url, work_dir)
    raise ValueError("No video source provided.")
