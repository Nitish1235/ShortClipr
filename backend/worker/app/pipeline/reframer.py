"""
reframer.py — AI-powered vertical reframing (16:9 → 9:16) using MediaPipe + OpenCV.

Strategy: "Smart Static Crop"
1. Probe video dimensions and audio track presence
2. Sample frames at ~2fps using OpenCV
3. Run MediaPipe Face Detection on sampled frames
4. EMA-weighted face center over time → stable crop box
5. If no face found → center-top bias (good for talking heads and landscapes)
6. Apply crop + scale + pad via a single FFmpeg command to 1080x1920
7. Handle already-vertical, portrait, and square sources correctly
8. Handle missing audio streams gracefully
"""
import asyncio
import logging
import os
import cv2
import numpy as np
import ffmpeg
import mediapipe as mp

logger = logging.getLogger(__name__)

_mp_face    = mp.solutions.face_detection
TARGET_W    = 1080
TARGET_H    = 1920
TARGET_ASPECT = TARGET_W / TARGET_H   # 9/16 = 0.5625


def _has_audio_stream(video_path: str) -> bool:
    """Return True if the video file has at least one audio stream."""
    try:
        probe = ffmpeg.probe(video_path)
        return any(s["codec_type"] == "audio" for s in probe.get("streams", []))
    except Exception:
        return False


def _sample_face_centers(video_path: str, sample_fps: float = 2.0) -> list[tuple[float, float]]:
    """
    Sample face centers from a video at sample_fps rate.
    Returns list of (cx_ratio, cy_ratio) where each value is in [0, 1].
    Falls back to empty list if OpenCV cannot open the file.
    """
    face_centers: list[tuple[float, float]] = []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"OpenCV could not open: {video_path}")
        return face_centers

    video_fps      = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_interval = max(1, int(video_fps / sample_fps))

    with _mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.45) as detector:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = detector.process(rgb)
                if result.detections:
                    det  = result.detections[0]   # use highest-confidence detection
                    bbox = det.location_data.relative_bounding_box
                    cx   = bbox.xmin + bbox.width  / 2.0
                    cy   = bbox.ymin + bbox.height / 2.0
                    # clamp to [0,1] — bbox can exceed bounds with low-confidence detections
                    face_centers.append((
                        max(0.0, min(1.0, cx)),
                        max(0.0, min(1.0, cy)),
                    ))
            frame_idx += 1

    cap.release()
    logger.info(f"Sampled {len(face_centers)} face detections from {frame_idx} frames")
    return face_centers


def _compute_crop_box(
    face_centers: list[tuple[float, float]],
    frame_w: int,
    frame_h: int,
) -> tuple[int, int, int, int]:
    """
    Compute (x, y, crop_w, crop_h) in pixels for a 9:16 output from a frame of
    size frame_w × frame_h, centered on the detected face (or default position).

    Handles all aspect ratio inputs:
      - Wide (16:9, 4:3, 21:9) → crop width, keep full height
      - Tall / already portrait  → crop height, keep full width
      - Square                   → crop width to 9:16
    """
    # ── Determine face anchor ────────────────────────────────────────────────
    if face_centers:
        # EMA: recent frames weighted heavier
        weights = np.exp(np.linspace(-1.0, 0.0, len(face_centers)))
        weights /= weights.sum()
        arr      = np.array(face_centers)
        cx_ratio = float(np.average(arr[:, 0], weights=weights))
        cy_ratio = float(np.average(arr[:, 1], weights=weights))
    else:
        # Default: horizontal centre, slightly above mid-frame (talking-head bias)
        cx_ratio = 0.5
        cy_ratio = 0.38

    source_aspect = frame_w / frame_h

    if source_aspect >= TARGET_ASPECT:
        # Source is wider than 9:16 → crop WIDTH, keep full height
        crop_h = frame_h
        crop_w = int(frame_h * TARGET_ASPECT)
        crop_w = min(crop_w, frame_w)           # never exceed actual frame width
    else:
        # Source is taller / squarer than 9:16 → crop HEIGHT, keep full width
        crop_w = frame_w
        crop_h = int(frame_w / TARGET_ASPECT)
        crop_h = min(crop_h, frame_h)           # never exceed actual frame height

    # ── Centre box on face anchor ────────────────────────────────────────────
    cx_px = int(cx_ratio * frame_w)
    cy_px = int(cy_ratio * frame_h)

    x = cx_px - crop_w // 2
    y = cy_px - crop_h // 2

    # Clamp to frame bounds
    x = max(0, min(x, frame_w - crop_w))
    y = max(0, min(y, frame_h - crop_h))

    return x, y, crop_w, crop_h


def _reframe_sync(video_path: str, output_path: str) -> str:
    """Full blocking reframe: probe → face detect → FFmpeg crop+scale+pad."""

    # ── 1. Probe video dimensions ────────────────────────────────────────────
    probe = ffmpeg.probe(video_path)
    video_streams = [s for s in probe["streams"] if s["codec_type"] == "video"]
    if not video_streams:
        raise ValueError(f"No video stream in {video_path}")

    vstream   = video_streams[0]
    frame_w   = int(vstream["width"])
    frame_h   = int(vstream["height"])
    has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])

    logger.info(f"Source: {frame_w}x{frame_h}  audio={has_audio}")

    # ── 2. Face detection ────────────────────────────────────────────────────
    face_centers = _sample_face_centers(video_path, sample_fps=2.0)

    # ── 3. Crop box ──────────────────────────────────────────────────────────
    x, y, crop_w, crop_h = _compute_crop_box(face_centers, frame_w, frame_h)
    logger.info(f"Crop box → x={x} y={y} w={crop_w} h={crop_h}")

    # ── 4. FFmpeg: crop → scale (preserve AR) → pad to exact 1080×1920 ───────
    # Using raw vf= string: avoids ffmpeg-python kwarg translation issues.
    vf = (
        f"crop={crop_w}:{crop_h}:{x}:{y},"
        f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2:color=black"
    )

    output_kwargs: dict = {
        "vf":           vf,
        "vcodec":       "libx264",
        "video_bitrate":"4500k",
        "preset":       "fast",
        "movflags":     "+faststart",
    }

    if has_audio:
        output_kwargs["acodec"]       = "aac"
        output_kwargs["audio_bitrate"] = "128k"
    else:
        # No audio track → add silent audio so downstream filters always have an audio stream
        output_kwargs["acodec"]  = "aac"
        output_kwargs["ar"]      = "44100"
        output_kwargs["ac"]      = "2"
        # Generate silent audio via anullsrc
        silent_input = ffmpeg.input("anullsrc=r=44100:cl=stereo", f="lavfi")
        (
            ffmpeg
            .output(
                ffmpeg.input(video_path).video,
                silent_input,
                output_path,
                **output_kwargs,
                shortest=None,
            )
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path

    (
        ffmpeg
        .input(video_path)
        .output(output_path, **output_kwargs)
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path


async def reframe_to_vertical(video_path: str, work_dir: str, clip_index: int) -> str:
    """
    Reframe a clip to 9:16 vertical (1080×1920) using MediaPipe face tracking.
    Returns path to the reframed vertical MP4.
    """
    output_path = os.path.join(work_dir, f"clip_{clip_index}_vertical.mp4")
    logger.info(f"Reframing clip {clip_index} → 9:16...")
    await asyncio.to_thread(_reframe_sync, video_path, output_path)
    logger.info(f"Reframe complete: {output_path}")
    return output_path
