#!/bin/bash
# start.sh — Container entrypoint
#
# Strategy: start bgutil-pot fire-and-forget, then exec Python immediately.
# Cloud Run's startup probe checks $PORT (8080) from second 1 — we must not
# block that port. Python's health server is up in ~2-3s which is well within
# the 4-minute probe window. bgutil-pot will be ready long before any job runs.

set -e

echo "=== ShortClipr Worker Starting ==="

# ── Ensure yt-dlp is fresh (nightly extraction fixes) ───────────────────────
# We update on every boot so we don't need to rebuild the image for YouTube changes.
echo "Checking for yt-dlp nightly updates..."
/opt/venv/bin/yt-dlp --update-to nightly || echo "yt-dlp update skipped/failed (non-fatal)"

# ── bgutil-pot PO token server (background, non-blocking) ────────────────────
if [ -f "/usr/local/bin/bgutil-pot" ]; then
    /usr/local/bin/bgutil-pot server --host 127.0.0.1 --port "${BGUTIL_HTTP_SERVER_PORT:-4416}" &
    echo "bgutil-pot started in background (PID $!)"
else
    echo "WARNING: bgutil-pot not found — YouTube PO tokens disabled"
fi

# ── Hand off to Python immediately ───────────────────────────────────────────
# Health server inside main.py binds $PORT within seconds → probe passes.
echo "=== Starting Python worker ==="
exec python -u app/main.py
