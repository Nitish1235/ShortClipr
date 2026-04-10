"""
thumbnail_generator.py — Extract the best frame from a clip and return as JPEG.

Strategy:
  1. Sample ~10 frames evenly across the clip duration
  2. Score frames by brightness variance (sharpest, most interesting frames score higher)
  3. Save the best-scoring frame as a JPEG thumbnail
  4. Overlay the template's top_title text using PIL for a rich preview image
"""
import asyncio
import logging
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

THUMBNAIL_WIDTH  = 540   # Half-resolution (1080 / 2) for smaller file size
THUMBNAIL_HEIGHT = 960   # 9:16 ratio


def _score_frame(frame: np.ndarray) -> float:
    """
    Score a frame by its Laplacian variance (edges = sharpness).
    Higher = more interesting/sharp frame.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _extract_best_frame_sync(video_path: str, num_samples: int = 10) -> np.ndarray:
    """Sample frames evenly and return the sharpest one."""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count  = max(1, total_frames)

    sample_positions = np.linspace(
        int(frame_count * 0.1),       # skip first 10% (often blurry/black)
        int(frame_count * 0.85),      # skip last 15% (often fade-out)
        num=num_samples,
        dtype=int,
    )

    best_frame = None
    best_score = -1.0

    for pos in sample_positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
        ret, frame = cap.read()
        if not ret:
            continue
        score = _score_frame(frame)
        if score > best_score:
            best_score = score
            best_frame = frame.copy()

    cap.release()

    if best_frame is None:
        # Fallback: just grab first frame
        cap = cv2.VideoCapture(video_path)
        _, best_frame = cap.read()
        cap.release()

    return best_frame


def _overlay_thumbnail_text(
    frame_bgr: np.ndarray,
    top_title: str,
) -> np.ndarray:
    """Use PIL to overlay the top_title text on the thumbnail frame."""
    # Convert BGR → RGB → PIL
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb).resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)

    if not top_title:
        return np.array(img)

    draw = ImageDraw.Draw(img)

    # Try to load a bold font; fall back to PIL default
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    font = None
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size=36)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    # Word-wrap for long titles
    max_chars_per_line = 22
    words = top_title.split()
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars_per_line:
            current = f"{current} {w}".strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    # Draw semi-transparent background strip
    line_h  = 44
    bg_h    = len(lines) * line_h + 24
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rectangle([(0, 0), (THUMBNAIL_WIDTH, bg_h)], fill=(0, 0, 0, 160))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        y = 12 + i * line_h
        # Shadow
        draw.text((14, y + 2), line, font=font, fill=(0, 0, 0, 200))
        # Main text
        draw.text((12, y), line, font=font, fill=(255, 255, 255, 255))

    return np.array(img)


def _generate_sync(
    video_path: str,
    output_path: str,
    top_title: str,
) -> str:
    frame = _extract_best_frame_sync(video_path)
    composited = _overlay_thumbnail_text(frame, top_title)
    # Convert numpy → PIL → JPEG
    pil_img = Image.fromarray(composited).resize(
        (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS
    )
    pil_img.save(output_path, "JPEG", quality=88, optimize=True)
    return output_path


async def generate(
    video_path: str,
    work_dir: str,
    clip_index: int,
    top_title: str = "",
) -> str:
    """
    Generate a thumbnail JPEG for a clip.
    Returns the path to the thumbnail file.
    """
    output_path = os.path.join(work_dir, f"clip_{clip_index}_thumb.jpg")
    logger.info(f"Generating thumbnail for clip {clip_index}...")
    await asyncio.to_thread(_generate_sync, video_path, output_path, top_title)
    logger.info(f"Thumbnail generated: {output_path}")
    return output_path
