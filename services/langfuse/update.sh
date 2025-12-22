#!/bin/bash
# LangFuse service update script
# Pulls latest images and starts the service (no vendor repo needed)

set -e

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVICE_DIR"

echo "=== LangFuse ==="

# --- Pull latest images ---
echo "  Pulling latest images..."
docker compose pull

# --- Start ---
echo "  Starting..."
docker compose up -d

# --- Health check ---
echo "  Checking health..."
sleep 5

if curl -sf http://localhost:13000 > /dev/null 2>&1; then
    echo "  ✅ LangFuse: http://localhost:13000"
else
    echo "  ⚠️  Not responding (may still be starting)"
fi

echo ""

