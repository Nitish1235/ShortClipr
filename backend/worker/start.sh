#!/bin/bash
# start.sh — Container entrypoint
# 1. Starts bgutil-pot Rust server in background (generates YouTube PO tokens)
# 2. Waits for it to be ready on port 4416
# 3. Launches the Python worker

set -e

PORT="${BGUTIL_HTTP_SERVER_PORT:-4416}"

echo "=== Starting bgutil-pot PO token server ==="

if ! command -v bgutil-pot &>/dev/null; then
    echo "WARNING: bgutil-pot binary not found — continuing without PO tokens"
else
    bgutil-pot server --host 127.0.0.1 --port "$PORT" &
    BGUTIL_PID=$!
    echo "bgutil-pot started (PID $BGUTIL_PID)"

    # Wait up to 30s for the server to respond
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${PORT}/token" > /dev/null 2>&1; then
            echo "bgutil-pot ready after ${i}s"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "WARNING: bgutil-pot did not respond in 30s — continuing anyway"
        fi
        sleep 1
    done
fi

echo "=== Starting ShortClipr worker ==="
exec python -u app/main.py
