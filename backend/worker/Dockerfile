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
    gnupg \
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

# ── Node.js 20 LTS via NodeSource ────────────────────────────────────────────
# Debian's apt repo ships nodejs v12 — yt-dlp requires v18+ for JS challenge solving.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version \
    && npm --version

# ── bgutil JS server (npm) ────────────────────────────────────────────────────
# Installs the Node.js server that generates YouTube PO tokens.
# The pip package (bgutil-ytdlp-pot-provider in requirements.txt) is the yt-dlp
# plugin that talks to this server. Both are required.
#   - npm package → runs the HTTP server on port 4416
#   - pip package → registers as yt-dlp plugin, calls the server for PO tokens
RUN npm install -g bgutil-ytdlp-pot-provider \
    && echo "bgutil installed at: $(npm root -g)/bgutil-ytdlp-pot-provider"

# ── Python venv from builder ──────────────────────────────────────────────────
COPY --from=builder /opt/venv /opt/venv

# ── Non-root user setup ───────────────────────────────────────────────────────
RUN addgroup --system workergroup && adduser --system --ingroup workergroup workeruser

# Scratch dirs for yt-dlp and temp files
RUN mkdir -p /tmp/shortclipr /tmp/yt-dlp-cache \
    && chown -R workeruser:workergroup /tmp/shortclipr /tmp/yt-dlp-cache

# Copy app + startup script
COPY ./app /app/app
COPY ./start.sh /app/start.sh

# Make startup script executable and fix ownership
RUN chmod +x /app/start.sh \
    && chown -R workeruser:workergroup /app

# Expose npm global bin to workeruser (Node 20 installs to /usr/local/bin)
RUN ls /usr/local/lib/node_modules/bgutil-ytdlp-pot-provider/build/server.js \
    && echo "bgutil server.js verified"

USER workeruser

# Use start.sh as entrypoint — boots bgutil server then launches Python worker
CMD ["/bin/bash", "/app/start.sh"]
