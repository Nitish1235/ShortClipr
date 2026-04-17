"""
caption_generator.py — Burn word-level animated karaoke captions onto vertical video.

Subtitle approach:
  - Words are grouped into small caption blocks (3 words each).
  - The entire group is shown together for the duration of the group.
  - The currently spoken word is highlighted teal (#14B8A6); others remain white.
  - Each caption block → exactly ONE ASS Dialogue event per word highlight phase.
  - Times are relative to the clip (not the original video).
  - ASS color reset is scoped correctly per-word via inline override tags.

ASS color encoding (little-endian BGR):
  White  #FFFFFF → BGR: FF FF FF → &H00FFFFFF&  (with &H prefix, no alpha byte in \\c)
  Teal   #14B8A6 → BGR: A6 B8 14 → &H00A6B814&
"""
import asyncio
import logging
import os
import ffmpeg

logger = logging.getLogger(__name__)

# ─── ASS header ──────────────────────────────────────────────────────────────
# PlayRes matches our target output: 1080×1920
# Alignment=2 → bottom-center
# MarginV=160 → keeps captions above the bottom tag
ASS_HEADER = """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,60,60,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# ASS teal color in \c format — 6-digit BBGGRR (NO alpha prefix in inline \c tags)
# Teal  #14B8A6 → BGR bytes: 0xA6, 0xB8, 0x14 → &HA6B814&
# White #FFFFFF → BGR bytes: 0xFF, 0xFF, 0xFF → &HFFFFFF&
TEAL_COLOR  = "&HA6B814&"
WHITE_COLOR = "&HFFFFFF&"


def _ts(seconds: float) -> str:
    """Convert float seconds to ASS timestamp: h:mm:ss.cc"""
    seconds  = max(0.0, seconds)
    hours    = int(seconds // 3600)
    minutes  = int((seconds % 3600) // 60)
    secs     = int(seconds % 60)
    centisec = int(round((seconds - int(seconds)) * 100))
    if centisec >= 100:
        centisec = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisec:02d}"


def _build_ass_content(
    words:           list[dict],
    clip_start:      float,
    clip_end:        float,
    words_per_group: int = 3,
) -> str:
    """
    Build complete ASS file content for a single clip.

    Each group of N words produces one Dialogue event per word-highlight phase.
    The event text contains the full group with inline \\c color tags so only
    the active word is teal, and the reset to white is scoped correctly.

    All timestamps are relative to the clip start (0 = start of clip).
    """
    if not words:
        return ASS_HEADER

    clip_dur  = clip_end - clip_start
    # Keep words strictly within the clip window (small tolerance at end)
    clip_words = [
        w for w in words
        if w.get("start", 0) >= clip_start - 0.05
        and w.get("end",   0) <= clip_end   + 0.5
    ]

    if not clip_words:
        return ASS_HEADER

    lines = [ASS_HEADER.rstrip()]

    for i in range(0, len(clip_words), words_per_group):
        group      = clip_words[i : i + words_per_group]
        group_end  = min(clip_dur, group[-1]["end"] - clip_start)

        for j, active_word in enumerate(group):
            # ── Time window for this highlight phase ──────────────────────
            t_start = max(0.0, active_word["start"] - clip_start)
            # This highlight lasts until next word starts (or end of group)
            if j + 1 < len(group):
                t_end = max(t_start + 0.05, group[j + 1]["start"] - clip_start)
            else:
                t_end = group_end
            t_end = min(clip_dur, t_end)

            if t_end <= t_start:
                continue

            # ── Build text: each word individually colored ─────────────────
            # Pattern: white{word1} teal{activeword}white{word3}
            # \\c without argument resets to the style's PrimaryColour (white).
            word_texts = []
            for k, w in enumerate(group):
                raw = w.get("word", "").strip()
                if not raw:
                    continue
                if k == j:
                    # Active word → teal, then reset to white for next word
                    word_texts.append(f"{{\\c{TEAL_COLOR}}}{raw}{{\\c{WHITE_COLOR}}}")
                else:
                    word_texts.append(raw)

            text = " ".join(word_texts)

            lines.append(
                f"Dialogue: 0,{_ts(t_start)},{_ts(t_end)},"
                f"Default,,0,0,0,,{text}"
            )

    return "\n".join(lines) + "\n"


def _burn_sync(video_path: str, ass_path: str, output_path: str) -> str:
    """
    Burn ASS subtitles into video using FFmpeg's subtitles filter.

    The subtitles filter requires:
      - Forward slashes on all OS
      - Colons in Windows drive letters escaped as \\:  (e.g. C\\:/tmp/...)
    Audio is copied (no re-encode needed since only video filter is applied).
    """
    # Normalize path for FFmpeg subtitle filter
    safe_path = ass_path.replace("\\", "/").replace(":", "\\:")

    try:
        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                vf=f"subtitles={safe_path}",
                vcodec="libx264",
                acodec="copy",          # audio is unchanged
                video_bitrate="4500k",
                preset="fast",
                movflags="+faststart",
            )
            .overwrite_output()
            .global_args('-nostdin')
            .run(quiet=True)
        )
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode(errors="ignore") if exc.stderr else ""
        logger.warning(f"Caption burn failed: {stderr[:300]}")
        logger.warning("Caption fallback: copying video unchanged.")
        # If subtitle burn fails, just pass the video through unchanged
        (
            ffmpeg
            .input(video_path)
            .output(output_path, vcodec="copy", acodec="copy", movflags="+faststart")
            .overwrite_output()
            .global_args('-nostdin')
            .run(quiet=True)
        )

    return output_path


async def add_captions(
    video_path: str,
    work_dir:   str,
    clip_index: int,
    clip_start: float,
    clip_end:   float,
    words:      list[dict],
) -> str:
    """
    Add word-level teal karaoke captions to a vertical 1080×1920 clip.
    Returns path to the captioned MP4.
    """
    ass_path    = os.path.join(work_dir, f"clip_{clip_index}.ass")
    output_path = os.path.join(work_dir, f"clip_{clip_index}_captioned.mp4")

    ass_content = _build_ass_content(words, clip_start, clip_end)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    logger.info(f"Burning captions for clip {clip_index} ({clip_start:.1f}s→{clip_end:.1f}s)...")
    await asyncio.to_thread(_burn_sync, video_path, ass_path, output_path)
    logger.info(f"Captions burned: {output_path}")
    return output_path
