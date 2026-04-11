# ── Stage 1: Python deps builder ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools
RUN pip install --no-cache-dir --prefer-binary --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    # Suppress MediaPipe noisy logs
    GLOG_minloglevel=2 \
    TF_CPP_MIN_LOG_LEVEL=3

# ── System deps: FFmpeg, OpenCV, MediaPipe, fonts ────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # FFmpeg (video processing core)
    ffmpeg \
    # OpenCV headless runtime libs
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    # Font stack for FFmpeg drawtext
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig \
    # yt-dlp needs these for merging streams
    python3-pip \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN addgroup --system workergroup && adduser --system --ingroup workergroup workeruser

# Scratch dir for temp files
RUN mkdir -p /tmp/shortclipr && chown workeruser:workergroup /tmp/shortclipr

COPY ./app /app/app

USER workeruser

# Worker is a continuous polling loop — no HTTP port needed
CMD ["python", "-u", "app/main.py"]
