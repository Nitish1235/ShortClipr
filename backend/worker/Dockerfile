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
    PATH="/opt/venv/bin:/usr/local/bin:$PATH" \
    GLOG_minloglevel=2 \
    TF_CPP_MIN_LOG_LEVEL=3 \
    BGUTIL_HTTP_SERVER_PORT=4416

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig \
    python3-pip \
    libcurl4 \
    libssl3 \
    ca-certificates \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# ── bgutil-pot Rust binary ────────────────────────────────────────────────────
# Pre-compiled Rust binary — no Node.js, no git clone, no npm needed.
# The pip plugin (bgutil-ytdlp-pot-provider in requirements.txt) calls this
# binary's HTTP server on port 4416 to get YouTube PO tokens.
RUN curl -fsSL \
    https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest/download/bgutil-pot-linux-x86_64 \
    -o /usr/local/bin/bgutil-pot \
    && chmod +x /usr/local/bin/bgutil-pot \
    && bgutil-pot --version \
    && echo "bgutil-pot binary OK"

# ── Python venv from builder ──────────────────────────────────────────────────
COPY --from=builder /opt/venv /opt/venv

# ── Non-root user setup ───────────────────────────────────────────────────────
RUN addgroup --system workergroup && adduser --system --ingroup workergroup workeruser

RUN mkdir -p /tmp/shortclipr /tmp/yt-dlp-cache \
    && chown -R workeruser:workergroup /tmp/shortclipr /tmp/yt-dlp-cache

COPY ./app /app/app
COPY ./start.sh /app/start.sh

RUN chmod +x /app/start.sh \
    && chown -R workeruser:workergroup /app

USER workeruser

# Sanity check — fail build early if something is broken
RUN bgutil-pot --version && python -c "import yt_dlp; print('yt-dlp OK')"

CMD ["/bin/bash", "/app/start.sh"]
