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

# --- Check/install uv (Python package manager) ---
if command -v uv &> /dev/null; then
    echo "  uv is installed: $(uv --version)"
else
    echo "  Installing uv..."
    if command -v brew &> /dev/null; then
        brew install uv
    else
        # Fallback to curl installation
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    echo "  Installed: $(uv --version)"
fi

# --- Check/install SDL dependencies (required for pygame) ---
echo "  Checking SDL dependencies..."
if command -v brew &> /dev/null; then
    for dep in sdl2 sdl2_image sdl2_mixer sdl2_ttf pkg-config; do
        if brew list "$dep" &> /dev/null; then
            echo "  ✅ $dep installed"
        else
            echo "  Installing $dep..."
            brew install "$dep"
        fi
    done
else
    echo "  ⚠️  Homebrew not found, SDL dependencies may be missing"
fi

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

    # Set compiler flags for SDL (needed for pygame)
    if command -v brew &> /dev/null; then
        export CFLAGS="-I$(brew --prefix sdl2)/include/SDL2 -I$(brew --prefix)/include"
        export LDFLAGS="-L$(brew --prefix sdl2)/lib -L$(brew --prefix)/lib"
    fi

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

