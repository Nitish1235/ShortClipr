"""
clip_extractor.py — Extract a precise clip from the source video using FFmpeg.
Uses stream-copy for speed where possible, re-encodes if needed.
"""
import asyncio
import logging
import os
import ffmpeg

logger = logging.getLogger(__name__)


def _extract_sync(
    source_path: str,
    output_path: str,
    start: float,
    end: float,
) -> str:
    """Blocking FFmpeg clip extraction."""
    duration = end - start
    (
        ffmpeg
        .input(source_path, ss=start, t=duration)
        .output(
            output_path,
            vcodec="libx264",
            acodec="aac",
            video_bitrate="4000k",
            audio_bitrate="128k",
            preset="fast",
            movflags="+faststart",
        )
        .overwrite_output()
        .global_args('-nostdin')
        .run(quiet=True)
    )
    return output_path


async def extract(
    source_path: str,
    work_dir: str,
    clip_index: int,
    start: float,
    end: float,
) -> str:
    """
    Extract a clip from source_path between start and end seconds.
    Returns path to the extracted raw clip MP4.
    """
    output_path = os.path.join(work_dir, f"clip_{clip_index}_raw.mp4")
    logger.info(f"Extracting clip {clip_index}: {start:.2f}s → {end:.2f}s from {source_path}")
    await asyncio.to_thread(_extract_sync, source_path, output_path, start, end)
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    logger.info(f"Clip {clip_index} extracted: {output_path} ({size_mb:.1f} MB)")
    return output_path
