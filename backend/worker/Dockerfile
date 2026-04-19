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
    unzip \
    libglib2.0-0 \
    libnss3 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libusb-1.0-0 \
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig \
    libcurl4-openssl-dev \
    libssl-dev \
    ca-certificates \
    && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

# ── Python venv from builder ──────────────────────────────────────────────────
COPY --from=builder /opt/venv /opt/venv

# ── Force yt-dlp nightly and curl_cffi extra ──────────────────────────────────
RUN . /opt/venv/bin/activate \
    && pip install -U "yt-dlp[default,curl-cffi]"

# ── bgutil-pot Rust binary (pre-downloaded, no network call needed) ───────────
COPY ./binaries/bgutil-pot /usr/local/bin/bgutil-pot
RUN chmod +x /usr/local/bin/bgutil-pot

# ── Sanity checks (run as root, guaranteed PATH) ──────────────────────────────
RUN bgutil-pot --version \
    && deno --version \
    && python -c "import yt_dlp; print('yt-dlp OK')" \
    && python -c "import cv2; print('opencv OK')" \
    && python -c "import mediapipe; print('mediapipe OK')" \
    && python -c "import curl_cffi; print('curl_cffi OK')" \
    && /opt/venv/bin/yt-dlp --list-impersonate-targets

# ── Non-root user setup ───────────────────────────────────────────────────────
RUN addgroup --system workergroup \
    && adduser --system --ingroup workergroup workeruser

RUN mkdir -p /tmp/shortclipr /tmp/yt-dlp-cache \
    && chown -R workeruser:workergroup /tmp/shortclipr /tmp/yt-dlp-cache

COPY ./app /app/app
COPY ./start.sh /app/start.sh

RUN chmod +x /app/start.sh \
    && chown -R workeruser:workergroup /app /opt/venv

USER workeruser

CMD ["/bin/bash", "/app/start.sh"]
