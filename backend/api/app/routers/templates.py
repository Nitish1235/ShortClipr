"""
Templates Router — list all pre-built viral style templates
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/templates", tags=["Templates"])


class TemplateDefinition(BaseModel):
    id: str
    name: str
    description: str
    # Individual text slot descriptions so GPT knows what to generate
    top_text_style: str
    bottom_tag_style: str
    # Visual effects description (used by renderer later)
    visual_effects: List[str]
    thumbnail_url: str  # Path served from Next.js public folder


# ─────────────────────────────────────────────
# Master catalog of 20 viral style templates
# ─────────────────────────────────────────────
TEMPLATES: List[TemplateDefinition] = [
    TemplateDefinition(
        id="satisfying-reveal",
        name="Satisfying Reveal",
        description="Bold top title with a black rounded tag and trophy emoji, subtle cinematic blur, YouTube Shorts watermark.",
        top_text_style="Bold, large white font. A satisfying or shocking reveal statement about the clip.",
        bottom_tag_style="Black rounded pill tag with a trophy emoji 🏆. Short punchy label like 'Most Satisfying'.",
        visual_effects=["cinematic_blur", "watermark"],
        thumbnail_url="/templates/satisfying-reveal.jpg",
    ),
    TemplateDefinition(
        id="luxury-shock",
        name="Luxury Shock",
        description="Bold luxury-style top text with a sparkle bottom tag, glow effect, and watermark.",
        top_text_style="Elegant serif-style bold white text. A luxury or wealth shock statement.",
        bottom_tag_style="Dark rounded pill tag with sparkle emoji ✨. Label like 'Luxury Shock' or similar.",
        visual_effects=["glow", "watermark"],
        thumbnail_url="/templates/luxury-shock.jpg",
    ),
    TemplateDefinition(
        id="epic-pov",
        name="Epic POV",
        description="Top 'POV:' title, subtle middle subtitle, bottom white rounded tag with mountain emoji, cinematic letterbox blur.",
        top_text_style="Bold 'POV:' prefix followed by a relatable scenario based on the clip.",
        bottom_tag_style="White rounded pill tag with mountain emoji ⛰️. Short impactful label.",
        visual_effects=["cinematic_blur_top", "cinematic_blur_bottom"],
        thumbnail_url="/templates/epic-pov.jpg",
    ),
    TemplateDefinition(
        id="life-changing",
        name="Life Changing",
        description="Bold top statement, mountain emoji rounded tag at bottom, soft vignette, watermark.",
        top_text_style="Bold inspiring white text. A statement about the life-changing insight in the clip.",
        bottom_tag_style="Dark rounded pill tag with mountain emoji ⛰️. Label like 'Life Changing'.",
        visual_effects=["vignette", "watermark"],
        thumbnail_url="/templates/life-changing.jpg",
    ),
    TemplateDefinition(
        id="peak-satisfaction",
        name="Peak Satisfaction",
        description="Bold top text, arrow emoji rounded tag at bottom, light cinematic blur, watermark.",
        top_text_style="Bold white uppercase text. A satisfying or completion-themed statement.",
        bottom_tag_style="Rounded pill tag with upward arrow emoji 🔝. Label 'Peak Satisfaction'.",
        visual_effects=["cinematic_blur_light", "watermark"],
        thumbnail_url="/templates/peak-satisfaction.jpg",
    ),
    TemplateDefinition(
        id="plot-twist-reaction",
        name="Plot Twist Reaction",
        description="Top 'When the plot twist hits' style text, surprised emoji rounded tag, strong face glow.",
        top_text_style="Bold/italic white text. Captures the shocking moment or unexpected turn in the clip.",
        bottom_tag_style="Rounded pill tag with surprised emoji 😱. Label like 'Plot Twist' or 'Nobody Expected This'.",
        visual_effects=["face_glow_strong"],
        thumbnail_url="/templates/plot-twist-reaction.jpg",
    ),
    TemplateDefinition(
        id="luxury-reveal",
        name="Luxury Reveal",
        description="Elegant top text, gold/black rounded diamond tag, subtle shine animation, watermark.",
        top_text_style="Elegant thin white text. A luxury, wealth, or exclusive reveal statement.",
        bottom_tag_style="Gold-black rounded pill tag with diamond emoji 💎. Label 'Luxury Reveal'.",
        visual_effects=["shine_animation", "watermark"],
        thumbnail_url="/templates/luxury-reveal.jpg",
    ),
    TemplateDefinition(
        id="cinematic-focus",
        name="Cinematic Focus",
        description="Strong top and bottom cinematic blur (letterbox), bold centered title, minimal bottom tag, watermark.",
        top_text_style="Bold centered white uppercase title. A dramatic, movie-style statement about the clip.",
        bottom_tag_style="Minimal small rounded tag. Just a single word or short phrase, no emoji.",
        visual_effects=["letterbox_blur_strong", "watermark"],
        thumbnail_url="/templates/cinematic-focus.jpg",
    ),
    TemplateDefinition(
        id="viral-hook",
        name="Viral Hook",
        description="Big bold question or statement at top, trending emoji rounded tag, fast zoom-in effect, watermark.",
        top_text_style="Big bold white question or hook statement to grab attention instantly.",
        bottom_tag_style="Rounded pill tag with a trending emoji combo 🔥💯. A trending phrase.",
        visual_effects=["zoom_in_fast", "watermark"],
        thumbnail_url="/templates/viral-hook.jpg",
    ),
    TemplateDefinition(
        id="satisfying-asmr",
        name="Satisfying ASMR",
        description="Top 'The most satisfying part...' text, ASMR Moment rounded tag, soft glow, watermark.",
        top_text_style="Soft italic white text starting with 'The most satisfying part...' contextualised for the clip.",
        bottom_tag_style="Soft white rounded pill tag. Label '🎧 ASMR Moment'.",
        visual_effects=["soft_glow", "watermark"],
        thumbnail_url="/templates/satisfying-asmr.jpg",
    ),
    TemplateDefinition(
        id="plot-twist",
        name="Plot Twist",
        description="Top 'When the plot twist hits' text, shocked emoji rounded tag, face glow effect, watermark.",
        top_text_style="Bold white text. Describes the plot twist moment as captured in the clip transcript.",
        bottom_tag_style="Rounded pill tag with shocked emoji 😲. Label 'Plot Twist'.",
        visual_effects=["face_glow", "watermark"],
        thumbnail_url="/templates/plot-twist.jpg",
    ),
    TemplateDefinition(
        id="dreamy-transition",
        name="Dreamy Transition",
        description="Poetic top text, dreamy cloud/moon emoji rounded tag, soft fade blur, watermark.",
        top_text_style="Poetic, softer white italic text. An atmospheric or dreamy statement inspired by the clip.",
        bottom_tag_style="Soft rounded pill tag with cloud/moon emoji 🌙☁️. Label 'Dream Mode'.",
        visual_effects=["soft_fade_blur", "watermark"],
        thumbnail_url="/templates/dreamy-transition.jpg",
    ),
    TemplateDefinition(
        id="flex-mode",
        name="Flex Mode",
        description="Top 'This is the sound of luxury' style text, flex emoji rounded tag, strong contrast, watermark.",
        top_text_style="Bold uppercase white text. An aspirational flex-style statement about the clip content.",
        bottom_tag_style="Rounded pill tag with flex/money emoji 💰💪. Label 'Flex Mode'.",
        visual_effects=["high_contrast", "watermark"],
        thumbnail_url="/templates/flex-mode.jpg",
    ),
    TemplateDefinition(
        id="emotional-hit",
        name="Emotional Hit",
        description="Emotional top statement, heart or tear emoji rounded tag, soft cinematic blur, watermark.",
        top_text_style="Emotionally resonant bold white text. Captures the feeling or lesson of the clip.",
        bottom_tag_style="Soft rounded pill tag with heart or tear emoji 💔❤️. Label 'Emotional Hit'.",
        visual_effects=["cinematic_blur_soft", "watermark"],
        thumbnail_url="/templates/emotional-hit.jpg",
    ),
    TemplateDefinition(
        id="trend-jack",
        name="Trend Jack",
        description="Trending phrase at top, trending emoji combination rounded tag, fast animation, watermark.",
        top_text_style="Bold white text with a trending phrase or meme format adapted to the clip content.",
        bottom_tag_style="Rounded pill tag with trending emoji combination 🚀🔥. A snappy trending label.",
        visual_effects=["fast_animation", "watermark"],
        thumbnail_url="/templates/trend-jack.jpg",
    ),
    # ─── Bonus Advanced Combos ───
    TemplateDefinition(
        id="full-stack",
        name="Full Stack",
        description="Top title + middle subtitle + bottom emoji rounded tag + cinematic blur + watermark. The complete package.",
        top_text_style="Bold white top title. A strong hook statement for the clip.",
        bottom_tag_style="Rounded pill tag with relevant emoji. A supporting label beneath the main hook.",
        visual_effects=["cinematic_blur", "watermark", "middle_subtitle"],
        thumbnail_url="/templates/full-stack.jpg",
    ),
    TemplateDefinition(
        id="minimal-clean",
        name="Minimal Clean",
        description="Only bold top title + subtle bottom watermark. No rounded tag — pure minimalism.",
        top_text_style="Simple, large bold white text. The cleanest possible title statement for the clip.",
        bottom_tag_style="No tag. Only a subtle watermark at the bottom.",
        visual_effects=["watermark_subtle"],
        thumbnail_url="/templates/minimal-clean.jpg",
    ),
    TemplateDefinition(
        id="max-energy",
        name="Max Energy",
        description="Big bold top text, multiple bottom emojis, glow, zoom-in effect. Maximum hype.",
        top_text_style="All-caps energetic bold white text. Maximum hype statement that grabs attention.",
        bottom_tag_style="Wide rounded pill tag with multiple high-energy emojis 🔥💥⚡. A hype label.",
        visual_effects=["glow", "zoom_in_fast"],
        thumbnail_url="/templates/max-energy.jpg",
    ),
    TemplateDefinition(
        id="storytelling",
        name="Storytelling",
        description="Top chapter-style title, 'Part 1/5' bottom rounded tag, soft blur. Perfect for series.",
        top_text_style="Elegant chapter-style white title. Frames the clip as part of a larger story.",
        bottom_tag_style="Rounded pill tag with '📖 Part 1' style label indicating episode or chapter number.",
        visual_effects=["soft_blur"],
        thumbnail_url="/templates/storytelling.jpg",
    ),
    TemplateDefinition(
        id="meme-style",
        name="Meme Style",
        description="Top text + bottom rounded tags with popular meme-style phrases and trending emojis.",
        top_text_style="Impact-font style bold white text. A meme-worthy phrase or caption for the clip.",
        bottom_tag_style="Rounded pill tag with meme-style phrase and trending emojis 💀😭🤣. Keep it relatable.",
        visual_effects=["high_contrast"],
        thumbnail_url="/templates/meme-style.jpg",
    ),
]

# Lookup map for worker pipeline access
TEMPLATE_MAP = {t.id: t for t in TEMPLATES}


@router.get("", response_model=List[TemplateDefinition], summary="List all available viral style templates")
async def list_templates():
    """
    Returns the full catalog of pre-built viral style templates.
    The frontend uses this to build the template selector UI in the dashboard.
    """
    return TEMPLATES


@router.get("/{template_id}", response_model=TemplateDefinition, summary="Get a specific template by ID")
async def get_template(template_id: str):
    from fastapi import HTTPException
    template = TEMPLATE_MAP.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    return template
