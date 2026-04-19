#!/bin/bash
# start.sh — Container entrypoint
#
# Strategy: start bgutil-pot fire-and-forget, then exec Python immediately.
# Cloud Run's startup probe checks $PORT (8080) from second 1 — we must not
# block that port. Python's health server is up in ~2-3s which is well within
# the 4-minute probe window. bgutil-pot will be ready long before any job runs.

set -e

echo "=== ShortClipr Worker Starting ==="

# ── Ensure yt-dlp is fresh (background) ───────────────────────
# We update in the background so we don't block the Cloud Run health check.
(
    echo "Background task: Checking for yt-dlp updates..."
    /opt/venv/bin/pip install -U --no-cache-dir "yt-dlp[default,curl-cffi]" > /dev/null 2>&1 || true
    echo "Background task: yt-dlp update check finished"
) &

# ── bgutil-pot PO token server (non-blocking) ───────────────────────────────
echo "=== Checking bgutil-pot binary ==="
ls -la /usr/local/bin/bgutil-pot 2>/dev/null || echo "ERROR: bgutil-pot binary not found"
bgutil-pot --version 2>/dev/null || echo "ERROR: bgutil-pot failed to run"

BGUTIL_PORT="${BGUTIL_HTTP_SERVER_PORT:-4416}"
echo "=== Starting bgutil-pot server on port $BGUTIL_PORT ==="
/usr/local/bin/bgutil-pot server --host 127.0.0.1 --port "$BGUTIL_PORT" &
BGUTIL_PID=$!
echo "bgutil-pot started (PID: $BGUTIL_PID)"

# ── Hand off to Python immediately ───────────────────────────────────────────
# Health server inside main.py binds $PORT within seconds → probe passes.
echo "=== Starting Python worker ==="
exec python -u app/main.py
