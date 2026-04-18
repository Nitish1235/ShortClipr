#!/bin/bash
# start.sh — Container entrypoint
# 1. Starts the bgutil Node.js HTTP server (generates YouTube PO tokens)
# 2. Waits for it to be ready on port 4416
# 3. Launches the Python worker

set -e

PORT="${BGUTIL_HTTP_SERVER_PORT:-4416}"

echo "=== Starting bgutil PO token server ==="

# Resolve the server entry point from the installed npm package
BGUTIL_SERVER=$(node -e "require.resolve('@imputnet/bgutil-ytdlp-pot-provider-server')" 2>/dev/null || echo "")

if [ -z "$BGUTIL_SERVER" ]; then
    echo "WARNING: bgutil server module not found — continuing without PO tokens"
else
    node "$BGUTIL_SERVER" &
    BGUTIL_PID=$!
    echo "bgutil server started (PID $BGUTIL_PID)"

    # Wait up to 30s for it to respond
    for i in $(seq 1 30); do
        if curl -sf "http://localhost:${PORT}/token" > /dev/null 2>&1; then
            echo "bgutil ready after ${i}s"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo "WARNING: bgutil did not respond in 30s — continuing anyway"
        fi
        sleep 1
    done
fi

echo "=== Starting ShortClipr worker ==="
exec python -u app/main.py
