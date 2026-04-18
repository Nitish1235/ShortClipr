"""
orchestrator.py — Main pipeline controller.

Audio-First Pipeline for YouTube URLs:
  1.  Download AUDIO ONLY (~5-30MB vs 1-2GB for full video)
  2.  Transcribe with Whisper
  3.  GPT-4o analysis → viral clip timestamps
  4.  Per-clip loop:
      a. Download specific video segment only (e.g. 120s-165s of a 2hr video)
      b. AI reframe to 9:16 (MediaPipe + OpenCV)
      c. Caption burn (ASS word-level subtitles)
      d. Template visual effects + title/tag overlay (FFmpeg)
      e. Thumbnail generation (OpenCV + PIL)
      f. Upload clip + thumbnail to GCS

GCS Upload Pipeline (user-uploaded files):
  1.  Download full video from GCS (fast — Google internal network)
  2.  Extract audio locally with FFmpeg
  3.  Transcribe → Analyze → Per-clip loop (same as above but clips from local file)
"""
import asyncio
import logging
import os
import shutil
import uuid
from typing import Callable, List

import ffmpeg

from . import (
    content_analyzer,
    downloader,
    audio_extractor,
    transcriber,
    clip_extractor,
    reframer,
    caption_generator,
    template_renderer,
    thumbnail_generator,
    gcs_uploader,
)

logger = logging.getLogger(__name__)

MAX_DURATION_SECONDS = 150 * 60      # 150 minutes hard cap
WORK_BASE_DIR        = "/tmp/shortclipr"


async def run_pipeline(
    job_id: str,
    user_id: str,
    video_url: str | None,
    youtube_url: str | None,
    options: dict,
    template_id: str,
    status_callback: Callable,
) -> List[dict]:
    """
    Full pipeline. Returns a list of processed clip dicts ready for DB insert.
    Raises ValueError for validation failures, Exception for processing errors.
    """
    work_dir = os.path.join(WORK_BASE_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)

    try:
        if youtube_url:
            return await _run_youtube_pipeline(
                job_id, user_id, youtube_url, options, template_id,
                status_callback, work_dir,
            )
        elif video_url:
            return await _run_gcs_pipeline(
                job_id, user_id, video_url, options, template_id,
                status_callback, work_dir,
            )
        else:
            raise ValueError("No video source provided.")

    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
            logger.info(f"[{job_id}] Cleaned up temp dir: {work_dir}")


# ── YouTube Audio-First Pipeline ──────────────────────────────────────────────

async def _run_youtube_pipeline(
    job_id: str,
    user_id: str,
    youtube_url: str,
    options: dict,
    template_id: str,
    status_callback: Callable,
    work_dir: str,
) -> List[dict]:
    """
    Audio-first YouTube pipeline.
    Downloads audio → transcribes → finds moments → downloads only clip segments.
    """

    # ── Step 1: Download audio only ──────────────────────────────────────────
    await status_callback("Downloading audio track", 8)
    audio_path = await downloader.download_audio(
        job_id=job_id,
        youtube_url=youtube_url,
        work_dir=work_dir,
    )

    # ── Step 2: Validate duration from audio ─────────────────────────────────
    await status_callback("Validating video duration", 12)
    def _probe_audio_dur():
        return float(ffmpeg.probe(audio_path)["format"]["duration"])
    audio_duration = await asyncio.to_thread(_probe_audio_dur)

    if audio_duration > MAX_DURATION_SECONDS:
        raise ValueError(
            f"Video exceeds 150-minute limit ({audio_duration / 60:.1f} min)."
        )
    logger.info(f"[{job_id}] Audio duration: {audio_duration / 60:.1f} min — OK")

    # ── Step 3: Transcribe ────────────────────────────────────────────────────
    await status_callback("Transcribing with Whisper", 20)
    transcript_result = await transcriber.transcribe(audio_path)
    full_text      = transcript_result["text"]
    word_timestamps = transcript_result["words"]
    logger.info(f"[{job_id}] Transcript: {len(full_text.split())} words")

    # ── Step 4: GPT-4o content analysis ──────────────────────────────────────
    await status_callback("Analyzing content for viral moments", 32)
    clip_segments = await content_analyzer.analyze(
        transcript=full_text,
        options=options,
        template_id=template_id,
    )
    if not clip_segments:
        logger.warning(f"[{job_id}] GPT returned no segments — using full audio as single clip")
        clip_segments = [{
            "start": 0.0,
            "end": min(60.0, audio_duration),
            "top_title": "Watch This",
            "bottom_tag": "Viral Moment",
            "reasoning": "Fallback: no segments detected",
        }]
    logger.info(f"[{job_id}] {len(clip_segments)} viral moments identified")

    # ── Step 5: Per-clip download + process loop ──────────────────────────────
    clips = []
    total = len(clip_segments)

    for idx, segment in enumerate(clip_segments):
        clip_id    = str(uuid.uuid4())
        start      = float(segment["start"])
        end        = float(segment["end"])
        top_title  = segment.get("top_title", "")
        bottom_tag = segment.get("bottom_tag", "")
        duration   = end - start
        progress_base = 35 + int(55 * (idx / total))

        logger.info(f"[{job_id}] Clip {idx+1}/{total}: {start:.1f}s → {end:.1f}s")

        # a. Download only this specific video segment
        await status_callback(f"Downloading clip {idx+1}/{total} segment", progress_base)
        raw_clip = await downloader.download_clip(
            job_id=job_id,
            youtube_url=youtube_url,
            start=start,
            end=end,
            work_dir=work_dir,
            clip_index=idx,
        )

        clips.extend(await _process_clip(
            job_id=job_id, user_id=user_id, clip_id=clip_id,
            raw_clip=raw_clip, work_dir=work_dir, clip_index=idx,
            total_clips=total, start=start, end=end, duration=duration,
            top_title=top_title, bottom_tag=bottom_tag,
            word_timestamps=word_timestamps, template_id=template_id,
            status_callback=status_callback, progress_base=progress_base,
        ))

    await status_callback("Finalizing", 97)
    logger.info(f"[{job_id}] YouTube pipeline complete. {len(clips)} clips generated.")
    return clips


# ── GCS Upload Pipeline ───────────────────────────────────────────────────────

async def _run_gcs_pipeline(
    job_id: str,
    user_id: str,
    video_url: str,
    options: dict,
    template_id: str,
    status_callback: Callable,
    work_dir: str,
) -> List[dict]:
    """
    GCS video pipeline. Downloads full video → extracts audio → clips locally.
    Used for user-uploaded video files.
    """

    # ── Step 1: Download full video from GCS ─────────────────────────────────
    await status_callback("Downloading uploaded video", 8)
    local_video = await downloader.download_gcs(
        job_id=job_id,
        video_url=video_url,
        work_dir=work_dir,
    )

    # ── Step 2: Duration validation ───────────────────────────────────────────
    await status_callback("Validating duration", 12)
    def _probe():
        return float(ffmpeg.probe(local_video)["format"]["duration"])
    file_duration = await asyncio.to_thread(_probe)
    if file_duration > MAX_DURATION_SECONDS:
        raise ValueError(
            f"Uploaded file exceeds 150-minute limit ({file_duration / 60:.1f} min)."
        )
    logger.info(f"[{job_id}] File duration: {file_duration / 60:.1f} min — OK")

    # ── Step 3: Extract audio ─────────────────────────────────────────────────
    await status_callback("Extracting audio", 18)
    audio_path = await audio_extractor.extract(local_video, work_dir)

    # ── Step 4: Transcribe ────────────────────────────────────────────────────
    await status_callback("Transcribing with Whisper", 25)
    transcript_result = await transcriber.transcribe(audio_path)
    full_text       = transcript_result["text"]
    word_timestamps = transcript_result["words"]
    logger.info(f"[{job_id}] Transcript: {len(full_text.split())} words")

    # ── Step 5: GPT-4o content analysis ──────────────────────────────────────
    await status_callback("Analyzing content for viral moments", 35)
    clip_segments = await content_analyzer.analyze(
        transcript=full_text,
        options=options,
        template_id=template_id,
    )
    if not clip_segments:
        logger.warning(f"[{job_id}] GPT returned no segments — using full video")
        clip_segments = [{
            "start": 0.0,
            "end": min(60.0, file_duration),
            "top_title": "Watch This",
            "bottom_tag": "Viral Moment",
            "reasoning": "Fallback: no segments detected",
        }]
    logger.info(f"[{job_id}] {len(clip_segments)} viral moments identified")

    # ── Step 6: Per-clip extraction + process loop ────────────────────────────
    clips = []
    total = len(clip_segments)

    for idx, segment in enumerate(clip_segments):
        clip_id    = str(uuid.uuid4())
        start      = float(segment["start"])
        end        = float(segment["end"])
        top_title  = segment.get("top_title", "")
        bottom_tag = segment.get("bottom_tag", "")
        duration   = end - start
        progress_base = 38 + int(52 * (idx / total))

        logger.info(f"[{job_id}] Clip {idx+1}/{total}: {start:.1f}s → {end:.1f}s")

        # Extract clip from local GCS video using FFmpeg
        await status_callback(f"Extracting clip {idx+1}/{total}", progress_base)
        raw_clip = await clip_extractor.extract(
            source_path=local_video,
            work_dir=work_dir,
            clip_index=idx,
            start=start,
            end=end,
        )

        clips.extend(await _process_clip(
            job_id=job_id, user_id=user_id, clip_id=clip_id,
            raw_clip=raw_clip, work_dir=work_dir, clip_index=idx,
            total_clips=total, start=start, end=end, duration=duration,
            top_title=top_title, bottom_tag=bottom_tag,
            word_timestamps=word_timestamps, template_id=template_id,
            status_callback=status_callback, progress_base=progress_base,
        ))

    # Delete original GCS source file after processing
    try:
        await gcs_uploader.delete_source_video(video_url)
        logger.info(f"[{job_id}] Source video deleted from GCS.")
    except Exception as e:
        logger.warning(f"[{job_id}] Source deletion failed (non-fatal): {e}")

    await status_callback("Finalizing", 97)
    logger.info(f"[{job_id}] GCS pipeline complete. {len(clips)} clips generated.")
    return clips


# ── Shared clip processing ────────────────────────────────────────────────────

async def _process_clip(
    job_id: str,
    user_id: str,
    clip_id: str,
    raw_clip: str,
    work_dir: str,
    clip_index: int,
    total_clips: int,
    start: float,
    end: float,
    duration: float,
    top_title: str,
    bottom_tag: str,
    word_timestamps: list,
    template_id: str,
    status_callback: Callable,
    progress_base: int,
) -> list:
    """
    Shared clip processing: reframe → captions → template → thumbnail → upload.
    Used by both YouTube and GCS pipelines.
    """
    label = f"{clip_index+1}/{total_clips}"

    # b. AI Reframe to 9:16
    await status_callback(f"Reframing clip {label} to 9:16", progress_base + 3)
    vertical_clip = await reframer.reframe_to_vertical(
        video_path=raw_clip,
        work_dir=work_dir,
        clip_index=clip_index,
    )

    # c. Caption burn
    await status_callback(f"Burning captions for clip {label}", progress_base + 5)
    captioned_clip = await caption_generator.add_captions(
        video_path=vertical_clip,
        work_dir=work_dir,
        clip_index=clip_index,
        clip_start=start,
        clip_end=end,
        words=word_timestamps,
    )

    # d. Template visual effects + text overlay
    await status_callback(f"Applying '{template_id}' template to clip {label}", progress_base + 7)
    rendered_clip = await template_renderer.render(
        video_path=captioned_clip,
        work_dir=work_dir,
        clip_index=clip_index,
        template_id=template_id,
        top_title=top_title,
        bottom_tag=bottom_tag,
        duration=duration,
    )

    # e. Thumbnail
    await status_callback(f"Generating thumbnail for clip {label}", progress_base + 9)
    thumb_path = await thumbnail_generator.generate(
        video_path=rendered_clip,
        work_dir=work_dir,
        clip_index=clip_index,
        top_title=top_title,
    )

    # f. Upload to GCS
    await status_callback(f"Uploading clip {label}", progress_base + 10)
    clip_url  = await gcs_uploader.upload_clip(rendered_clip, user_id, job_id, clip_id)
    thumb_url = await gcs_uploader.upload_thumbnail(thumb_path, user_id, job_id, clip_id)

    return [{
        "clip_id":            clip_id,
        "clip_url":           clip_url,
        "thumbnail_url":      thumb_url,
        "duration":           duration,
        "start_time":         start,
        "end_time":           end,
        "transcript_snippet": " ".join(
            [w["word"] for w in word_timestamps if start <= w.get("start", 0) <= end]
        )[:200],
        "viral_score":        float(90 - clip_index * 4),
        "top_title":          top_title,
        "bottom_tag":         bottom_tag,
        "template_id":        template_id,
    }]
