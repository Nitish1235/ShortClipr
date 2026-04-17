"""
audio_extractor.py — Extract the audio track from a video using FFmpeg.

Handles:
  - Normal videos with audio   → extract 16kHz mono WAV
  - Videos with NO audio track → generate 1-second silent WAV as placeholder
    (Whisper will return empty transcript gracefully)
"""
import asyncio
import logging
import os
import ffmpeg

logger = logging.getLogger(__name__)


def _has_audio(video_path: str) -> bool:
    """Return True if the video has at least one audio stream."""
    try:
        probe = ffmpeg.probe(video_path)
        return any(s["codec_type"] == "audio" for s in probe.get("streams", []))
    except Exception:
        return False


def _extract_sync(video_path: str, audio_path: str) -> str:
    """Blocking FFmpeg audio extraction to 16kHz mono WAV."""
    if not _has_audio(video_path):
        # Generate a 1-second silent WAV so Whisper doesn't crash
        logger.warning(f"No audio stream in {video_path} — generating silent placeholder")
        (
            ffmpeg
            .input("anullsrc=r=16000:cl=mono", f="lavfi", t=1)
            .output(audio_path, acodec="pcm_s16le", ar=16000, ac=1)
            .overwrite_output()
            .global_args('-nostdin')
            .run(quiet=True)
        )
        return audio_path

    (
        ffmpeg
        .input(video_path)
        .output(
            audio_path,
            acodec="pcm_s16le",   # WAV PCM — required by Whisper file upload
            ar=16000,             # 16kHz — Whisper's native sample rate
            ac=1,                 # mono
            vn=None,              # drop video stream
        )
        .overwrite_output()
        .global_args('-nostdin')
        .run(quiet=True)
    )
    return audio_path


async def extract(video_path: str, work_dir: str) -> str:
    """
    Extract audio from video_path to a 16kHz mono WAV file.
    Returns the path to the audio file.
    """
    audio_path = os.path.join(work_dir, "audio.wav")
    logger.info(f"Extracting audio from {video_path}...")
    await asyncio.to_thread(_extract_sync, video_path, audio_path)
    size_kb = os.path.getsize(audio_path) // 1024
    logger.info(f"Audio extraction complete: {audio_path} ({size_kb} KB)")
    return audio_path
