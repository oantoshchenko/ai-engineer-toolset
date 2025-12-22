#!/bin/bash
# Piper TTS service update script
# Clones/updates vendor repo, applies patches, builds, and starts the service

set -e

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_ROOT="$(cd "$SERVICE_DIR/../.." && pwd)"
VENDOR_DIR="$TOOLS_ROOT/vendor"
VENDOR_NAME="piper-tts-mcp"
VENDOR_URL="https://github.com/CryptoDappDev/piper-tts-mcp.git"

echo "=== Piper TTS ==="

# --- Clone or update vendor repo ---
mkdir -p "$VENDOR_DIR"

if [ ! -d "$VENDOR_DIR/$VENDOR_NAME" ]; then
    echo "  Cloning $VENDOR_NAME..."
    git clone "$VENDOR_URL" "$VENDOR_DIR/$VENDOR_NAME"
else
    echo "  Updating $VENDOR_NAME..."
    cd "$VENDOR_DIR/$VENDOR_NAME"
    git fetch origin
    git pull --ff-only origin main 2>/dev/null || git pull --ff-only origin master 2>/dev/null || {
        echo "  ⚠️  Could not fast-forward (local changes?)"
    }
    cd "$SERVICE_DIR"
fi

# --- Apply patches ---
if [ -d "$SERVICE_DIR/patches" ]; then
    for patch in "$SERVICE_DIR/patches"/*.patch; do
        if [ -f "$patch" ]; then
            echo "  Applying $(basename "$patch")..."
            cd "$VENDOR_DIR/$VENDOR_NAME"
            if git apply --check "$patch" 2>/dev/null; then
                git apply "$patch"
                echo "  ✅ Patch applied"
            else
                echo "  ⚠️  Patch already applied or conflicts"
            fi
            cd "$SERVICE_DIR"
        fi
    done
fi

# --- Install Python dependencies ---
if command -v uv &> /dev/null; then
    echo "  Installing Python dependencies..."
    cd "$VENDOR_DIR/$VENDOR_NAME"
    uv sync 2>/dev/null || uv pip install -e .
    cd "$SERVICE_DIR"
else
    echo "  ⚠️  uv not found, skipping Python deps"
fi

# --- Build ---
echo "  Building..."
docker compose build

# --- Start ---
echo "  Starting..."
docker compose up -d

# --- Health check ---
echo "  Checking health..."
sleep 3

if curl -sf http://localhost:5847 > /dev/null 2>&1; then
    echo "  ✅ Piper TTS: http://localhost:5847"
else
    echo "  ⚠️  Not responding (may still be starting)"
fi

echo ""

