#!/bin/bash
# LanguageTool service update script
# Pulls the latest image and starts the service

set -e

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVICE_DIR"

echo "=== LanguageTool ==="

# --- Pull latest image ---
echo "  Pulling latest image..."
docker compose pull

# --- Start ---
echo "  Starting..."
docker compose up -d

# --- Health check ---
echo "  Checking health..."
# LanguageTool takes a while to start (JVM + loading language models)
sleep 10

if curl -sf http://localhost:8010/v2/languages > /dev/null 2>&1; then
    echo "  ✅ LanguageTool: http://localhost:8010"
else
    echo "  ⚠️  Not responding (may still be starting - JVM startup can take 30-60s)"
fi

echo ""

