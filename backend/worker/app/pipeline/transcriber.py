"""
transcriber.py — Transcribe audio to text using OpenAI Whisper API.
Returns full transcript text and word-level timestamps.

Speed optimisations vs naïve impl:
  1. Parallel chunk transcription via asyncio.gather — all chunks are sent
     to the Whisper API simultaneously instead of one-at-a-time.
  2. Low-bitrate MP3 (32kbps mono 16kHz) — speech-only content; Whisper
     doesn't need music quality. Cuts upload payload ~4× vs 128kbps.
  3. Pre-compute chunk durations in parallel before transcribing so probing
     doesn't serialise the transcription loop.
"""
import asyncio
import logging
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Default: OpenAI Whisper API
# To switch to Groq (faster + cheaper), set GROQ_API_KEY env var.
_GROQ_KEY = os.getenv("GROQ_API_KEY", "")
if _GROQ_KEY:
    client = AsyncOpenAI(api_key=_GROQ_KEY, base_url="https://api.groq.com/openai/v1")
    MODEL_NAME = "whisper-large-v3"
    logger.info("Transcriber: using Groq Whisper Large v3")
else:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    MODEL_NAME = "whisper-1"

# Whisper API hard limit is 25 MB. We stay safely below it.
MAX_FILE_SIZE_BYTES = 24 * 1024 * 1024  # 24 MB


# ── Public API ────────────────────────────────────────────────────────────────

async def transcribe(audio_path: str) -> dict:
    """
    Transcribe an audio file using OpenAI Whisper (or Groq if configured).

    Returns:
        {
            "text":  str,              # full transcript
            "words": [                 # word-level timestamps
                {"word": str, "start": float, "end": float},
                ...
            ]
        }
    """
    file_size = os.path.getsize(audio_path)
    logger.info(f"Transcribing audio: {audio_path} ({file_size // 1024} KB)")

    if file_size <= MAX_FILE_SIZE_BYTES:
        return await _transcribe_single(audio_path)
    else:
        return await _transcribe_chunked(audio_path)


# ── Word-parsing helper ───────────────────────────────────────────────────────

def _parse_word(w) -> dict:
    """
    Handle OpenAI SDK word response format differences:
    - Newer SDK (≥1.x): plain dict  → w["word"], w["start"], w["end"]
    - Older SDK:         object     → w.word,     w.start,   w.end
    """
    if isinstance(w, dict):
        return {"word": w["word"].strip(), "start": w["start"], "end": w["end"]}
    return {"word": w.word.strip(), "start": w.start, "end": w.end}


# ── Single-file transcription ─────────────────────────────────────────────────

async def _transcribe_single(audio_path: str) -> dict:
    """Transcribe one audio file (must be ≤ 24 MB)."""
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model=MODEL_NAME,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    words = []
    if hasattr(response, "words") and response.words:
        words = [_parse_word(w) for w in response.words]

    logger.info(
        f"Chunk transcribed: {len(response.text.split())} words, "
        f"{len(words)} timestamps — {os.path.basename(audio_path)}"
    )
    return {"text": response.text, "words": words}


# ── Chunked transcription (parallel) ─────────────────────────────────────────

async def _transcribe_chunked(audio_path: str) -> dict:
    """
    Split audio into chunks and transcribe ALL chunks in parallel.

    Sequential (old):   chunk1 → wait → chunk2 → wait → chunk3 → ...
    Parallel  (new):    chunk1 ┐
                        chunk2 ├─ all sent to Whisper simultaneously
                        chunk3 ┘
                        → merge results with time offsets
    """
    import ffmpeg

    logger.info("Audio file exceeds 25MB — splitting into chunks for parallel transcription.")
    chunk_dir = os.path.join(os.path.dirname(audio_path), "chunks")
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_pattern = os.path.join(chunk_dir, "chunk_%03d.mp3")

    # ── Step 1: Split audio into chunks ──────────────────────────────────────
    def _split():
        (
            ffmpeg
            .input(audio_path)
            .output(
                chunk_pattern,
                segment_time=600,    # 10 minutes per chunk
                f="segment",
                acodec="libmp3lame",
                audio_bitrate="32k", # 32kbps is plenty for speech — cuts upload 4×
                ar=16000,            # 16 kHz — Whisper's native sample rate
                ac=1,                # mono
            )
            .overwrite_output()
            .global_args("-nostdin")
            .run(quiet=True)
        )

    await asyncio.to_thread(_split)

    chunk_files = sorted([
        os.path.join(chunk_dir, f)
        for f in os.listdir(chunk_dir)
        if f.startswith("chunk_") and f.endswith(".mp3")
    ])
    logger.info(f"Split into {len(chunk_files)} chunks — transcribing in parallel")

    # ── Step 2: Pre-compute durations for ALL chunks in parallel ─────────────
    def _probe_duration(path: str) -> float:
        return float(ffmpeg.probe(path)["format"]["duration"])

    duration_tasks = [asyncio.to_thread(_probe_duration, p) for p in chunk_files]
    durations = await asyncio.gather(*duration_tasks)

    # ── Step 3: Transcribe ALL chunks in parallel ─────────────────────────────
    transcription_tasks = [_transcribe_single(p) for p in chunk_files]
    results = await asyncio.gather(*transcription_tasks)

    # ── Step 4: Merge with cumulative time offsets ────────────────────────────
    all_words:       list[dict] = []
    full_text_parts: list[str]  = []
    time_offset = 0.0

    for result, duration in zip(results, durations):
        full_text_parts.append(result["text"])
        for w in result["words"]:
            all_words.append({
                "word":  w["word"],
                "start": round(w["start"] + time_offset, 3),
                "end":   round(w["end"]   + time_offset, 3),
            })
        time_offset += duration

    logger.info(
        f"Parallel transcription complete: {len(chunk_files)} chunks, "
        f"{len(all_words)} words total"
    )
    return {
        "text":  " ".join(full_text_parts),
        "words": all_words,
    }
