"""
orchestrator.py — Main pipeline controller.

Runs all steps in order for a given job:
  1.  Duration validation
  2.  Video download (GCS or YouTube)
  3.  GCS duration probe for direct uploads
  4.  Audio extraction (FFmpeg)
  5.  Transcription (OpenAI Whisper)
  6.  Content analysis → viral clip segments (GPT-4o, template-aware)
  7.  Per-clip loop:
      a. Clip extraction (FFmpeg)
      b. AI reframe to 9:16 (MediaPipe + OpenCV)
      c. Caption burn (ASS word-level subtitles)
      d. Template visual effects + title/tag overlay (FFmpeg)
      e. Thumbnail generation (OpenCV + PIL)
      f. Upload clip + thumbnail to GCS
  8.  Cleanup temp work directory
"""
import asyncio
import logging
import os
import shutil
import uuid
from typing import Callable, List

import ffmpeg
import yt_dlp

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
WORK_BASE_DIR        = "/tmp/shortclipr"   # ephemeral scratch space


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
    Full pipeline. Returns a list of processed clip dicts ready for Firestore.
    Raises ValueError for validation failures, Exception for processing errors.
    """
    work_dir = os.path.join(WORK_BASE_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)

    try:
        # ─── Step 1: Duration Validation ─────────────────────────────────────
        await status_callback("Validating video duration", 5)
        if youtube_url:
            def _get_yt_duration():
                with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                    return ydl.extract_info(youtube_url, download=False).get("duration", 0)
            try:
                yt_duration = await asyncio.to_thread(_get_yt_duration)
                if yt_duration > MAX_DURATION_SECONDS:
                    raise ValueError(
                        f"Video exceeds 150-minute limit ({yt_duration / 60:.1f} min)."
                    )
                logger.info(f"[{job_id}] YouTube duration: {yt_duration / 60:.1f} min — OK")
            except Exception as e:
                if "150-minute limit" in str(e):
                    raise
                logger.warning(f"[{job_id}] Could not pre-validate YouTube duration: {e}")

        # ─── Step 2: Download ─────────────────────────────────────────────────
        await status_callback("Downloading video", 12)
        local_video = await downloader.download(
            job_id=job_id,
            youtube_url=youtube_url,
            video_url=video_url,
            work_dir=work_dir,
        )

        # ─── Step 3: GCS file duration probe ─────────────────────────────────
        if video_url and not youtube_url:
            def _probe_duration():
                return float(ffmpeg.probe(local_video)["format"]["duration"])
            file_duration = await asyncio.to_thread(_probe_duration)
            if file_duration > MAX_DURATION_SECONDS:
                raise ValueError(
                    f"Uploaded file exceeds 150-minute limit ({file_duration / 60:.1f} min)."
                )
            logger.info(f"[{job_id}] File duration: {file_duration / 60:.1f} min — OK")

        # ─── Step 4: Audio Extraction ─────────────────────────────────────────
        await status_callback("Extracting audio", 18)
        audio_path = await audio_extractor.extract(local_video, work_dir)

        # ─── Step 5: Transcription ────────────────────────────────────────────
        await status_callback("Transcribing audio (Whisper)", 25)
        transcript_result = await transcriber.transcribe(audio_path)
        full_text = transcript_result["text"]
        word_timestamps = transcript_result["words"]
        logger.info(f"[{job_id}] Transcript: {len(full_text.split())} words")

        # ─── Step 6: Content Analysis (GPT-4o, template-aware) ───────────────
        await status_callback("Analyzing content for viral hooks", 35)
        clip_segments = await content_analyzer.analyze(
            transcript=full_text,
            options=options,
            template_id=template_id,
        )
        if not clip_segments:
            logger.warning(f"[{job_id}] GPT returned no segments. Using single full-video clip.")
            def _total_duration():
                return float(ffmpeg.probe(local_video)["format"]["duration"])
            total_dur = await asyncio.to_thread(_total_duration)
            clip_segments = [{
                "start": 0.0,
                "end": min(60.0, total_dur),
                "top_title": "Watch This",
                "bottom_tag": "🔥 Viral",
                "reasoning": "Fallback: no segments detected",
            }]

        logger.info(f"[{job_id}] {len(clip_segments)} clip segments identified")

        # ─── Step 7: Per-clip processing loop ────────────────────────────────
        clips = []
        total_clips = len(clip_segments)

        for idx, segment in enumerate(clip_segments):
            clip_id      = str(uuid.uuid4())
            start        = float(segment["start"])
            end          = float(segment["end"])
            top_title    = segment.get("top_title", "")
            bottom_tag   = segment.get("bottom_tag", "")
            duration     = end - start
            progress_base = 35 + int(55 * (idx / total_clips))

            logger.info(f"[{job_id}] Processing clip {idx + 1}/{total_clips}: {start:.1f}s → {end:.1f}s")

            # a. Clip extraction
            await status_callback(f"Extracting clip {idx + 1}/{total_clips}", progress_base + 2)
            raw_clip = await clip_extractor.extract(
                source_path=local_video,
                work_dir=work_dir,
                clip_index=idx,
                start=start,
                end=end,
            )

            # b. AI Reframe to 9:16
            await status_callback(f"Reframing clip {idx + 1} to 9:16", progress_base + 5)
            vertical_clip = await reframer.reframe_to_vertical(
                video_path=raw_clip,
                work_dir=work_dir,
                clip_index=idx,
            )

            # c. Caption burn
            await status_callback(f"Burning captions for clip {idx + 1}", progress_base + 7)
            captioned_clip = await caption_generator.add_captions(
                video_path=vertical_clip,
                work_dir=work_dir,
                clip_index=idx,
                clip_start=start,
                clip_end=end,
                words=word_timestamps,
            )

            # d. Template visual effects + text overlay
            await status_callback(f"Applying '{template_id}' template to clip {idx + 1}", progress_base + 9)
            rendered_clip = await template_renderer.render(
                video_path=captioned_clip,
                work_dir=work_dir,
                clip_index=idx,
                template_id=template_id,
                top_title=top_title,
                bottom_tag=bottom_tag,
                duration=duration,
            )

            # e. Thumbnail generation
            await status_callback(f"Generating thumbnail for clip {idx + 1}", progress_base + 10)
            thumb_path = await thumbnail_generator.generate(
                video_path=rendered_clip,
                work_dir=work_dir,
                clip_index=idx,
                top_title=top_title,
            )

            # f. Upload to GCS
            await status_callback(f"Uploading clip {idx + 1}", progress_base + 11)
            clip_url  = await gcs_uploader.upload_clip(rendered_clip, user_id, job_id, clip_id)
            thumb_url = await gcs_uploader.upload_thumbnail(thumb_path, user_id, job_id, clip_id)

            clips.append({
                "clip_id":            clip_id,
                "clip_url":           clip_url,
                "thumbnail_url":      thumb_url,
                "duration":           duration,
                "start_time":         start,
                "end_time":           end,
                "transcript_snippet": " ".join(
                    [w["word"] for w in word_timestamps if start <= w["start"] <= end]
                )[:200],
                "viral_score":        float(90 - idx * 4),
                "top_title":          top_title,
                "bottom_tag":         bottom_tag,
                "template_id":        template_id,
            })

        await status_callback("Finalizing", 97)

        # ─── Step 8: Delete original GCS source video ─────────────────────────
        # Only applies to direct GCS uploads (not YouTube downloads).
        # Non-fatal: a failure here must not undo the completed clips.
        if video_url and not youtube_url:
            try:
                await gcs_uploader.delete_source_video(video_url)
                logger.info(f"[{job_id}] Source video deleted from GCS.")
            except Exception as del_exc:
                logger.warning(f"[{job_id}] Source video deletion failed (non-fatal): {del_exc}")

        logger.info(f"[{job_id}] Pipeline complete. {len(clips)} clips generated.")
        return clips

    finally:
        # Always clean up the local temp directory
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
            logger.info(f"[{job_id}] Cleaned up temp dir: {work_dir}")
