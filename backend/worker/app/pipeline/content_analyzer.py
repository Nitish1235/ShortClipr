import os
import json
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────────────────────────────────────
# Template catalog (mirrors backend/api/app/routers/templates.py)
# Kept here so the worker is fully self-contained and has zero API dependency.
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATE_RULES: dict[str, dict] = {
    "satisfying-reveal": {
        "top_text_style": "Bold, large white font. A satisfying or shocking reveal statement about the clip.",
        "bottom_tag_style": "Black rounded pill tag with a trophy emoji 🏆. Short punchy label like 'Most Satisfying'.",
    },
    "luxury-shock": {
        "top_text_style": "Elegant serif-style bold white text. A luxury or wealth shock statement.",
        "bottom_tag_style": "Dark rounded pill tag with sparkle emoji ✨. Label like 'Luxury Shock' or similar.",
    },
    "epic-pov": {
        "top_text_style": "Bold 'POV:' prefix followed by a relatable scenario based on the clip.",
        "bottom_tag_style": "White rounded pill tag with mountain emoji ⛰️. Short impactful label.",
    },
    "life-changing": {
        "top_text_style": "Bold inspiring white text. A statement about the life-changing insight in the clip.",
        "bottom_tag_style": "Dark rounded pill tag with mountain emoji ⛰️. Label like 'Life Changing'.",
    },
    "peak-satisfaction": {
        "top_text_style": "Bold white uppercase text. A satisfying or completion-themed statement.",
        "bottom_tag_style": "Rounded pill tag with upward arrow emoji 🔝. Label 'Peak Satisfaction'.",
    },
    "plot-twist-reaction": {
        "top_text_style": "Bold/italic white text. Captures the shocking moment or unexpected turn in the clip.",
        "bottom_tag_style": "Rounded pill tag with surprised emoji 😱. Label like 'Plot Twist' or 'Nobody Expected This'.",
    },
    "luxury-reveal": {
        "top_text_style": "Elegant thin white text. A luxury, wealth, or exclusive reveal statement.",
        "bottom_tag_style": "Gold-black rounded pill tag with diamond emoji 💎. Label 'Luxury Reveal'.",
    },
    "cinematic-focus": {
        "top_text_style": "Bold centered white uppercase title. A dramatic, movie-style statement about the clip.",
        "bottom_tag_style": "Minimal small rounded tag. Just a single word or short phrase, no emoji.",
    },
    "viral-hook": {
        "top_text_style": "Big bold white question or hook statement to grab attention instantly.",
        "bottom_tag_style": "Rounded pill tag with a trending emoji combo 🔥💯. A trending phrase.",
    },
    "satisfying-asmr": {
        "top_text_style": "Soft italic white text starting with 'The most satisfying part...' contextualised for the clip.",
        "bottom_tag_style": "Soft white rounded pill tag. Label '🎧 ASMR Moment'.",
    },
    "plot-twist": {
        "top_text_style": "Bold white text. Describes the plot twist moment as captured in the clip transcript.",
        "bottom_tag_style": "Rounded pill tag with shocked emoji 😲. Label 'Plot Twist'.",
    },
    "dreamy-transition": {
        "top_text_style": "Poetic, softer white italic text. An atmospheric or dreamy statement inspired by the clip.",
        "bottom_tag_style": "Soft rounded pill tag with cloud/moon emoji 🌙☁️. Label 'Dream Mode'.",
    },
    "flex-mode": {
        "top_text_style": "Bold uppercase white text. An aspirational flex-style statement about the clip content.",
        "bottom_tag_style": "Rounded pill tag with flex/money emoji 💰💪. Label 'Flex Mode'.",
    },
    "emotional-hit": {
        "top_text_style": "Emotionally resonant bold white text. Captures the feeling or lesson of the clip.",
        "bottom_tag_style": "Soft rounded pill tag with heart or tear emoji 💔❤️. Label 'Emotional Hit'.",
    },
    "trend-jack": {
        "top_text_style": "Bold white text with a trending phrase or meme format adapted to the clip content.",
        "bottom_tag_style": "Rounded pill tag with trending emoji combination 🚀🔥. A snappy trending label.",
    },
    "full-stack": {
        "top_text_style": "Bold white top title. A strong hook statement for the clip.",
        "bottom_tag_style": "Rounded pill tag with relevant emoji. A supporting label beneath the main hook.",
    },
    "minimal-clean": {
        "top_text_style": "Simple, large bold white text. The cleanest possible title statement for the clip.",
        "bottom_tag_style": "No tag. Only a subtle watermark at the bottom. Return empty string for bottom_tag.",
    },
    "max-energy": {
        "top_text_style": "All-caps energetic bold white text. Maximum hype statement that grabs attention.",
        "bottom_tag_style": "Wide rounded pill tag with multiple high-energy emojis 🔥💥⚡. A hype label.",
    },
    "storytelling": {
        "top_text_style": "Elegant chapter-style white title. Frames the clip as part of a larger story.",
        "bottom_tag_style": "Rounded pill tag with '📖 Part 1' style label indicating episode or chapter number.",
    },
    "meme-style": {
        "top_text_style": "Impact-font style bold white text. A meme-worthy phrase or caption for the clip.",
        "bottom_tag_style": "Rounded pill tag with meme-style phrase and trending emojis 💀😭🤣. Keep it relatable.",
    },
}

_FALLBACK_RULES = TEMPLATE_RULES["viral-hook"]


async def analyze(transcript: str, options: dict, template_id: str = "viral-hook") -> list[dict]:
    """
    Analyzes a video transcript to identify highly engaging viral hooks and segments.
    Uses the selected template to shape the top title and bottom tag text for each clip.
    Returns a list of clip segment dicts with start, end, top_title, bottom_tag, reasoning.
    """
    if not transcript:
        logger.warning("Empty transcript provided to content_analyzer")
        return []

    # Resolve template rules
    rules = TEMPLATE_RULES.get(template_id, _FALLBACK_RULES)
    top_style = rules["top_text_style"]
    bottom_style = rules["bottom_tag_style"]

    try:
        prompt = f"""You are an expert short-form video editor and viral content strategist for TikTok, Reels, and YouTube Shorts.

The user has selected the visual template: "{template_id}".

=== TEMPLATE OVERLAY RULES ===
TOP TITLE STYLE  : {top_style}
BOTTOM TAG STYLE : {bottom_style}

=== CONTENT RULES (strictly follow) ===
- top_title and bottom_tag MUST be written based on what is ACTUALLY said in the transcript.
- Do NOT use generic placeholders. Use the real subject, emotion, or event from the clip.
- Emojis in bottom_tag must match the clip topic and emotion:
  sports → 🏆⚽  finance/money → 💰📈  travel → ✈️🌍  heartbreak → 💔
  tech → 💻⚡  food → 🍔🔥  fitness → 💪🏋️  motivation → 🚀🔥  scandal → 😱💣
- top_title: complete punchy sentence, max 10 words.
- bottom_tag: max 5 words + 1–2 relevant emojis.

=== TASK ===
Find the most viral-worthy segments. Each needs: strong hook, cohesive point, natural conclusion.
Clip length: 15–60 seconds. Return 2–5 clips.

=== TRANSCRIPT ===
{transcript}

Return strictly valid JSON with a "clips" array. Each object MUST have:
- "start":      (float) Start time in seconds
- "end":        (float) End time in seconds
- "top_title":  (string) TOP overlay — content-specific, follows TOP TITLE STYLE
- "bottom_tag": (string) BOTTOM tag + emojis — content-specific, follows BOTTOM TAG STYLE
- "reasoning":  (string) Why this segment is viral (1 sentence)
"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a JSON-centric AI editor. Always output a valid JSON object "
                        "with a top-level 'clips' array. Never add markdown or extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        response_data = json.loads(response.choices[0].message.content)
        clips = response_data.get("clips", [])

        formatted_segments = []
        for clip in clips:
            if "start" in clip and "end" in clip:
                formatted_segments.append({
                    "start": float(clip["start"]),
                    "end": float(clip["end"]),
                    "top_title": str(clip.get("top_title", "")),
                    "bottom_tag": str(clip.get("bottom_tag", "")),
                    "reasoning": str(clip.get("reasoning", "")),
                })

        logger.info(
            f"GPT API returned {len(formatted_segments)} viral segments for template '{template_id}'."
        )
        return formatted_segments

    except Exception as e:
        logger.error(f"Error during content analysis with GPT API: {e}")
        return []
