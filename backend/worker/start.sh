#!/bin/bash
# start.sh — Container entrypoint
# 1. Starts the bgutil Node.js PO token server in the background
# 2. Waits for it to be ready on port 4416
# 3. Launches the Python worker process

set -e

PORT="${BGUTIL_HTTP_SERVER_PORT:-4416}"

# Find bgutil server JS entry point from npm global install
BGUTIL_ROOT="$(npm root -g 2>/dev/null)/bgutil-ytdlp-pot-provider"
BGUTIL_SERVER="${BGUTIL_ROOT}/build/server.js"

if [ -f "$BGUTIL_SERVER" ]; then
    echo "[startup] Starting bgutil PO token server (port ${PORT})..."
    node "$BGUTIL_SERVER" &
    BGUTIL_PID=$!

    # Wait up to 20 seconds for the server to bind to the port
    READY=0
    for i in $(seq 1 20); do
        if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1', ${PORT})); s.close()" 2>/dev/null; then
            echo "[startup] bgutil server ready on port ${PORT} (pid=${BGUTIL_PID})"
            READY=1
            break
        fi
        sleep 1
    done

    if [ "$READY" -eq 0 ]; then
        echo "[startup] WARNING: bgutil server did not start within 20s — continuing without PO tokens"
    fi
else
    echo "[startup] WARNING: bgutil server not found at ${BGUTIL_SERVER}"
    echo "[startup] npm global root: $(npm root -g 2>/dev/null || echo 'unknown')"
    echo "[startup] Continuing without PO tokens (yt-dlp may fail on datacenter IPs)"
fi

# Hand off to Python worker
echo "[startup] Starting ShortClipr worker..."
exec python -u app/main.py
