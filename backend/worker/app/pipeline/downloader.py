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

_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

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

def _yt_base_opts() -> dict:
    """
    Common yt-dlp options.
    - Forces the web player client so bgutil PO tokens are actually injected.
      (Android VR client doesn't use PO tokens → still gets bot-detected.)
    - bgutil-ytdlp-pot-provider pip plugin auto-registers and injects PO tokens;
      extractor_args tells it where our bgutil-pot HTTP server is.
    - ios client is tried first: no PO tokens needed, different rate-limit bucket,
      works for public videos from datacenter IPs. web is kept as fallback so
      bgutil kicks in if ios is unavailable for a specific video.
    """
    verbose = os.getenv("YTDLP_VERBOSE", "").lower() == "true"
    return {
        "quiet": False,
        "no_warnings": False,
        "verbose": True,      # Hardcoded for absolute visibility in Cloud Run
        "no_color": True,      # Cleaner machine-readable logs
        "nocheckcertificate": True,
        "socket_timeout": 60,
        "retries": 3,
        "fragment_retries": 8,
        "http_headers": {
            "Accept-Language": "en-US,en;q=0.9",
        },
        "sleep_interval": 2,
        "max_sleep_interval": 5,
        "impersonate": "chrome",
        "extractor_args": {
            "youtube": {
                # 2026 Best Practice: Lock to mweb for most reliable PO token injection.
                "player_client": ["mweb"],
                # Do NOT skip webpage/configs; we need the Visitor ID for token binding.
            },
            # 2026 Standard dictionary format for the bgutil-pot plugin.
            "youtubepot": {
                "provider": "bgutil-http",
                "base_url": _BGUTIL_BASE_URL,
                "service": "mweb",       # Must match the youtube client above.
                "always_update": True,   # Required for datacenter IPs to bypass SABR blocks.
            },
        },
    }






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
