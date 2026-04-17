"""
transcriber.py — Transcribe audio to text using OpenAI Whisper API.
Returns full transcript text and word-level timestamps.
"""
import asyncio
import logging
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# DEFAULT: Use official OpenAI Whisper API
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "whisper-1"

# FUTURE UPGRADE: Use Groq's ultra-fast Whisper API to save costs
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if GROQ_API_KEY:
#     client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
#     MODEL_NAME = "whisper-large-v3"

# Whisper API has a 25MB file size limit.
# For large audio files, we need to chunk them.
MAX_FILE_SIZE_BYTES = 24 * 1024 * 1024  # 24MB to be safe


async def transcribe(audio_path: str) -> dict:
    """
    Transcribe an audio file using OpenAI Whisper.
    Returns:
        {
            "text": str,                  # full transcript
            "words": [                    # word-level timestamps
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


async def _transcribe_single(audio_path: str) -> dict:
    """Transcribe a single audio file under the 25MB Whisper limit."""
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model=MODEL_NAME,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    words = []
    if hasattr(response, "words") and response.words:
        words = [
            {"word": w.word.strip(), "start": w.start, "end": w.end}
            for w in response.words
        ]

    logger.info(f"Transcription complete: {len(response.text.split())} words, {len(words)} word timestamps")
    return {"text": response.text, "words": words}


async def _transcribe_chunked(audio_path: str) -> dict:
    """
    Chunk large audio files into 10-minute segments and transcribe each.
    Uses FFmpeg to split, then merges results with proper time offsets.
    """
    import ffmpeg

    logger.info("Audio file exceeds 25MB — chunking into 10-minute segments.")
    chunk_dir = os.path.join(os.path.dirname(audio_path), "chunks")
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_pattern = os.path.join(chunk_dir, "chunk_%03d.wav")

    def _split():
        (
            ffmpeg
            .input(audio_path)
            .output(
                chunk_pattern,
                segment_time=600,   # 10 minutes per chunk
                f="segment",
                acodec="pcm_s16le",
                ar=16000,
                ac=1,
            )
            .overwrite_output()
            .global_args('-nostdin')
            .run(quiet=True)
        )

    await asyncio.to_thread(_split)

    chunk_files = sorted([
        os.path.join(chunk_dir, f)
        for f in os.listdir(chunk_dir)
        if f.startswith("chunk_") and f.endswith(".wav")
    ])

    all_words:       list[dict] = []
    full_text_parts: list[str]  = []
    time_offset = 0.0

    def _probe_duration(path: str) -> float:
        """Return duration in seconds for an audio file via ffmpeg.probe."""
        return float(ffmpeg.probe(path)["format"]["duration"])

    for chunk_path in chunk_files:
        result = await _transcribe_single(chunk_path)
        full_text_parts.append(result["text"])
        for w in result["words"]:
            all_words.append({
                "word":  w["word"],
                "start": w["start"] + time_offset,
                "end":   w["end"]   + time_offset,
            })
        time_offset += await asyncio.to_thread(_probe_duration, chunk_path)

    return {
        "text":  " ".join(full_text_parts),
        "words": all_words,
    }
