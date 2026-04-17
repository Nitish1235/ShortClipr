# ── Stage 1: Python deps builder ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip wheel setuptools
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    # Suppress MediaPipe noisy logs
    GLOG_minloglevel=2 \
    TF_CPP_MIN_LOG_LEVEL=3

# ── System deps: FFmpeg, OpenCV, MediaPipe, fonts, yt-dlp runtime ────────────
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
    # Node.js — required by yt-dlp to solve YouTube's n-challenge (JS encryption)
    # Without this, yt-dlp cannot decrypt stream URLs and downloads fail silently
    nodejs \
    npm \
    # curl_cffi runtime deps — required for yt-dlp --impersonate chrome TLS spoofing
    libcurl4 \
    libssl3 \
    ca-certificates \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN addgroup --system workergroup && adduser --system --ingroup workergroup workeruser

# Scratch dir for temp files
RUN mkdir -p /tmp/shortclipr && chown workeruser:workergroup /tmp/shortclipr

COPY ./app /app/app

USER workeruser

# Worker is a continuous polling loop — no HTTP port needed
CMD ["python", "-u", "app/main.py"]
