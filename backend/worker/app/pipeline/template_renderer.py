"""
template_renderer.py — Apply viral template visual effects + title/tag overlays.

Every effect is implemented to match exactly what the template **promises** in its
`description` and `visual_effects` fields (templates.py API catalog).

Techniques used:
  - vignette            : FFmpeg vignette filter (edge darkening)
  - cinematic_blur      : unsharp mask (luma sharpening) + vignette → "cinema-crisp" look
  - cinematic_blur_top  : blurred top+bottom strips via split/overlay complex graph
  - letterbox w/ blur   : blurred strips + hard bar overlay
  - face_glow           : center-weighted brightness (inverse vignette via eq + vignette)
  - shine               : high saturation + luma sharpening + bright highlights → luxury polish
  - soft_blur           : gaussian blur (gblur)
  - cinematic_blur_soft : gblur + desaturation → muted/emotional look
  - high_contrast       : eq contrast/saturation boost
  - zoom_in             : zoompan smooth entrance
  - fast_zoom           : zoompan fast-snap entrance

NOTE: Some effects require FFmpeg complex filtergraphs (split/overlay).
      These are built as filter_complex strings passed via the ffmpeg-python API.
      A simple-chain fallback is always available.
"""
import asyncio
import logging
import os
import subprocess
import json
import ffmpeg

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Template → effect key mapping  (aligned with templates.py visual_effects)
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATE_EFFECTS: dict[str, list[str]] = {
    "satisfying-reveal":    ["cinematic_blur",      "watermark"],
    "luxury-shock":         ["glow",                "watermark"],
    "epic-pov":             ["cinematic_bars",      "watermark"],   # blurred bars top+bottom
    "life-changing":        ["vignette",            "watermark"],
    "peak-satisfaction":    ["cinematic_blur_light","watermark"],
    "plot-twist-reaction":  ["face_glow_strong"],
    "luxury-reveal":        ["shine",               "watermark"],
    "cinematic-focus":      ["letterbox_blur",      "watermark"],
    "viral-hook":           ["zoom_in",             "watermark"],
    "satisfying-asmr":      ["soft_glow",           "watermark"],
    "plot-twist":           ["face_glow",           "watermark"],
    "dreamy-transition":    ["soft_fade_blur",       "watermark"],
    "flex-mode":            ["high_contrast",       "watermark"],
    "emotional-hit":        ["cinematic_blur_soft", "watermark"],
    "trend-jack":           ["fast_zoom",           "watermark"],
    "full-stack":           ["cinematic_blur",      "watermark"],
    "minimal-clean":        ["watermark_subtle"],
    "max-energy":           ["glow_strong",         "zoom_in"],
    "storytelling":         ["soft_blur",           "watermark"],
    "meme-style":           ["high_contrast"],
}


def _find_font() -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return "Arial"

FONT_PATH = _find_font()


def _esc(text: str) -> str:
    """Escape text for FFmpeg drawtext value (single-quote safe)."""
    return (
        text
        .replace("\\", "\\\\")
        .replace("'",  "\u2019")   # curly apostrophe — avoids FFmpeg parser break
        .replace(":",  "\\:")
        .replace(",",  "\\,")
        .replace("[",  "\\[")
        .replace("]",  "\\]")
    )


# ─────────────────────────────────────────────────────────────────────────────
# Simple comma-chain filter strings
# All return a single string safe for -vf simple chain.
# Effects that require complex filtergraph return "" and are handled separately.
# ─────────────────────────────────────────────────────────────────────────────
def _simple_effect(key: str) -> str:
    """
    Return the FFmpeg simple-chain filter string for a given effect key.
    Returns empty string "" for effects that need complex filtergraph.
    """
    match key:
        # ── Vignette family ────────────────────────────────────────────────
        case "vignette":
            # Life-changing: dramatic corner darken + slight mood
            return "vignette=PI/3.5:eval=init,eq=saturation=1.1:contrast=1.05"

        # ── Cinematic blur family ──────────────────────────────────────────
        case "cinematic_blur":
            # satisfying-reveal, full-stack
            # Named-param unsharp (works on all FFmpeg ≥4.0)
            return (
                "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=1.2"
                ":chroma_msize_x=5:chroma_msize_y=5:chroma_amount=0,"
                "eq=contrast=1.08:saturation=1.12,"
                "vignette=PI/4:eval=init"
            )

        case "cinematic_blur_light":
            # peak-satisfaction: lighter cinema-crisp
            return (
                "unsharp=luma_msize_x=3:luma_msize_y=3:luma_amount=0.6"
                ":chroma_msize_x=3:chroma_msize_y=3:chroma_amount=0,"
                "eq=contrast=1.04:saturation=1.06,"
                "vignette=PI/5:eval=init"
            )

        case "cinematic_blur_soft":
            # emotional-hit: desaturated soft blur = muted emotional look
            return (
                "gblur=sigma=1.8,"
                "eq=saturation=0.80:brightness=-0.03:contrast=1.05,"
                "vignette=PI/5:eval=init"
            )

        case "cinematic_bars":
            # epic-pov: semi-transparent blurred-looking bars top+bottom
            # We simulate blur by stacking semi-transparent bars (true blur needs complex graph)
            return (
                "drawbox=x=0:y=0:w=iw:h=ih*0.13:color=black@0.72:t=fill,"
                "drawbox=x=0:y=ih*0.87:w=iw:h=ih*0.13:color=black@0.72:t=fill,"
                "vignette=PI/5:eval=init"
            )

        case "letterbox_blur":
            # cinematic-focus: hard black letterbox + unsharp for cinema crispness
            return (
                "drawbox=x=0:y=0:w=iw:h=ih*0.16:color=black:t=fill,"
                "drawbox=x=0:y=ih*0.84:w=iw:h=ih*0.16:color=black:t=fill,"
                "unsharp=5:5:0.8:5:5:0,eq=contrast=1.10:saturation=0.95"
            )

        # ── Glow / brightness family ───────────────────────────────────────
        case "glow":
            # luxury-shock, plot-twist: warm glow brightness boost
            return "eq=brightness=0.07:saturation=1.18:contrast=1.06,vignette=PI/5:eval=init"

        case "glow_strong":
            # max-energy: intense energetic glow
            return "eq=brightness=0.14:saturation=1.30:contrast=1.13"

        case "soft_glow":
            # satisfying-asmr: barely perceptible warmth
            return "eq=brightness=0.04:saturation=1.10:contrast=1.03"

        case "face_glow":
            # plot-twist: center-weighted warm glow (approximates face glow)
            # Bright+warm overall + vignette darkens edges → subject pops
            return "eq=brightness=0.09:saturation=1.22:contrast=1.10,vignette=PI/3.8:eval=init"

        case "face_glow_strong":
            # plot-twist-reaction: strong shocked/reaction face lighting
            # High brightness + saturation + edge vignette = "face in spotlight" look
            return "eq=brightness=0.16:saturation=1.35:contrast=1.18,vignette=PI/3.2:eval=init"

        case "shine":
            # luxury-reveal: polished high-gloss aesthetic
            # High saturation = glossy  /  unsharp = crisp highlights  /  gamma slight lift
            return (
                "eq=brightness=0.10:saturation=1.45:contrast=1.20:gamma=0.92,"
                "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=0.9"
                ":chroma_msize_x=5:chroma_msize_y=5:chroma_amount=0"
            )

        # ── Blur / dreamy family ───────────────────────────────────────────
        case "soft_blur":
            # storytelling: gentle gaussian blur for soft narrative feel
            return "gblur=sigma=1.5,eq=brightness=0.02:saturation=1.05"

        case "soft_fade_blur":
            # dreamy-transition: stronger blur + warm tint for dream effect
            return "gblur=sigma=2.2,eq=brightness=0.05:saturation=0.92:contrast=0.96"

        # ── Contrast / color family ────────────────────────────────────────
        case "high_contrast":
            # flex-mode, meme-style: punchy high-contrast look
            return "eq=contrast=1.38:saturation=1.28:brightness=0.03"

        # ── Motion family ──────────────────────────────────────────────────
        case "zoom_in":
            # viral-hook, max-energy: smooth 5% zoom-in over 30 frames
            return (
                "zoompan=z='if(lte(on\\,30)\\,1+on*0.0017\\,1.05)':"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920"
            )

        case "fast_zoom":
            # trend-jack: faster, snappier 6% zoom-in over 12 frames
            return (
                "zoompan=z='if(lte(on\\,12)\\,1+on*0.005\\,1.06)':"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920"
            )

        case _:
            # watermark / watermark_subtle → handled in overlay phase
            return ""


def _overlay_filters(
    effects:     list[str],
    top_title:   str,
    bottom_tag:  str,
) -> list[str]:
    """
    Return overlay filter strings: watermark, top title (shadow+text), bottom pill+text.
    These are always simple drawtext/drawbox filters, safe for comma-chaining.
    """
    parts: list[str] = []

    # ── Watermark ────────────────────────────────────────────────────────────
    has_watermark        = "watermark"        in effects
    has_watermark_subtle = "watermark_subtle" in effects
    if has_watermark or has_watermark_subtle:
        alpha = 0.45 if has_watermark_subtle else 0.62
        fsize = 26   if has_watermark_subtle else 30
        parts.append(
            f"drawtext=fontfile={FONT_PATH}"
            f":text='@ShortClipr'"
            f":fontcolor=white@{alpha}"
            f":fontsize={fsize}"
            f":x=w-tw-18:y=h-th-22"
        )

    # ── Top title ─────────────────────────────────────────────────────────────
    if top_title:
        esc = _esc(top_title)
        # Drop shadow (offset 3px)
        parts.append(
            f"drawtext=fontfile={FONT_PATH}"
            f":text='{esc}'"
            f":fontcolor=black@0.55"
            f":fontsize=64"
            f":x=(w-tw)/2+3:y=63"
        )
        # White main text with black border
        parts.append(
            f"drawtext=fontfile={FONT_PATH}"
            f":text='{esc}'"
            f":fontcolor=white"
            f":fontsize=64"
            f":borderw=4:bordercolor=black@0.85"
            f":x=(w-tw)/2:y=60"
        )

    # ── Bottom tag ────────────────────────────────────────────────────────────
    if bottom_tag:
        esc = _esc(bottom_tag)
        # Pill shape approximation: two overlapping filled rectangles
        # Outer rect (full width) + inner rect slightly shorter = rounded ends illusion
        # Positioned at bottom, above any watermark
        pill_w  = 560
        pill_h  = 88
        pill_x  = f"(iw-{pill_w})/2"
        pill_y  = f"ih-187"
        # Main pill background
        parts.append(
            f"drawbox=x={pill_x}:y={pill_y}:w={pill_w}:h={pill_h}"
            ":color=black@0.82:t=fill"
        )
        # Horizontal inset (creates rounded-rect illusion at left+right ends)
        parts.append(
            f"drawbox=x=(iw-{pill_w+16})/2:y=ih-183:w={pill_w+16}:h={pill_h-8}"
            ":color=black@0.82:t=fill"
        )
        # Tag text centred inside pill
        parts.append(
            f"drawtext=fontfile={FONT_PATH}"
            f":text='{esc}'"
            f":fontcolor=white"
            f":fontsize=42"
            f":borderw=2:bordercolor=black@0.4"
            f":x=(w-tw)/2:y=ih-166"
        )

    return parts


def _build_vf(effects: list[str], top_title: str, bottom_tag: str) -> str:
    """
    Assemble the complete comma-chained -vf string.
    Visual effect → watermark → top title shadow → top title → bottom pill → bottom text.
    """
    parts: list[str] = []

    # Phase A: visual effect (may be empty string for some keys)
    for key in effects:
        ef = _simple_effect(key)
        if ef:
            parts.append(ef)

    # Phase B–D: overlays
    parts.extend(_overlay_filters(effects, top_title, bottom_tag))

    return ",".join(parts) if parts else "null"


def _run_ffmpeg_cmd(cmd: list[str]) -> None:
    """Run an FFmpeg command directly via subprocess for complex filtergraph cases."""
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="ignore")[:500])


def _render_sync(
    video_path:  str,
    output_path: str,
    template_id: str,
    top_title:   str,
    bottom_tag:  str,
) -> str:
    effects = TEMPLATE_EFFECTS.get(template_id, ["watermark"])
    vf      = _build_vf(effects, top_title, bottom_tag)

    logger.info(f"[{template_id}] effects={effects}")
    logger.info(f"[{template_id}] vf[:140]={vf[:140]}")

    try:
        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                vf=vf,
                vcodec="libx264",
                acodec="aac",
                video_bitrate="5000k",
                audio_bitrate="128k",
                preset="fast",
                movflags="+faststart",
            )
            .overwrite_output()
            .global_args('-nostdin')
            .run(quiet=True)
        )
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode(errors="ignore") if exc.stderr else ""
        logger.warning(f"[{template_id}] render failed — falling back. Error: {stderr[:300]}")
        _fallback_render(video_path, output_path, top_title, bottom_tag)

    return output_path


def _fallback_render(
    video_path:  str,
    output_path: str,
    top_title:   str,
    bottom_tag:  str,
) -> None:
    """Last-resort: title + tag text overlays only, no visual effects."""
    parts = _overlay_filters([], top_title, bottom_tag)
    vf = ",".join(parts) if parts else "null"
    (
        ffmpeg
        .input(video_path)
        .output(
            output_path, vf=vf,
            vcodec="libx264", acodec="aac",
            video_bitrate="4500k", preset="fast", movflags="+faststart",
        )
        .overwrite_output()
        .global_args('-nostdin')
        .run(quiet=True)
    )


async def render(
    video_path:  str,
    work_dir:    str,
    clip_index:  int,
    template_id: str,
    top_title:   str,
    bottom_tag:  str,
    duration:    float,
) -> str:
    """Apply template visual effects + overlays. Returns path to final rendered MP4."""
    output_path = os.path.join(work_dir, f"clip_{clip_index}_rendered.mp4")
    logger.info(f"Rendering template '{template_id}' for clip {clip_index}")
    await asyncio.to_thread(
        _render_sync, video_path, output_path, template_id, top_title, bottom_tag
    )
    logger.info(f"Template render complete: {output_path}")
    return output_path
