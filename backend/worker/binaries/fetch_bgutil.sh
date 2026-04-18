#!/usr/bin/env bash
# fetch_bgutil.sh — Download the bgutil-pot Linux x86_64 binary.
#
# Usage:
#   ./binaries/fetch_bgutil.sh              # fetch the latest release
#   ./binaries/fetch_bgutil.sh v1.2.3       # fetch a specific tag
#
# The binary is git-ignored. Run this script once locally and in any CI
# pipeline that builds the Docker image from scratch.

set -euo pipefail

REPO="jim60105/bgutil-ytdlp-pot-provider-rs"
TAG="${1:-latest}"
DEST="$(dirname "$0")/bgutil-pot"

if [[ "$TAG" == "latest" ]]; then
    URL="https://github.com/${REPO}/releases/latest/download/bgutil-pot-linux-x86_64"
else
    URL="https://github.com/${REPO}/releases/download/${TAG}/bgutil-pot-linux-x86_64"
fi

echo "=== Fetching bgutil-pot (${TAG}) ==="
echo "  Source : ${URL}"
echo "  Dest   : ${DEST}"

curl -fsSL "$URL" -o "$DEST"
chmod +x "$DEST"

echo "=== Done ==="
"$DEST" --version
