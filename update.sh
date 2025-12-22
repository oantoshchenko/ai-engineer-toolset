#!/bin/bash
# Tools Update Script
# Idempotent: handles both fresh setup and updates
#
# Usage:
#   ./update.sh              # Full update (clone/pull, build, start)
#   ./update.sh --no-start   # Update only, don't start services
#   ./update.sh --pull-only  # Just pull vendor repos, no build

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
NO_START=false
PULL_ONLY=false
for arg in "$@"; do
    case $arg in
        --no-start) NO_START=true ;;
        --pull-only) PULL_ONLY=true ;;
    esac
done

echo "=== Tools Update ==="
echo "Directory: $SCRIPT_DIR"
echo ""

# --- Step 1: Check/create .env ---
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env from template."
        echo ""
        echo "⚠️  Please edit .env with your secrets, then run this script again."
        echo "   Required: ELEVENLABS_API_KEY, OBSIDIAN_API_KEY"
        echo ""
        exit 0
    else
        echo "ERROR: .env.example not found"
        exit 1
    fi
fi

# --- Step 2: Clone or update vendor repos ---
echo ">>> Updating vendor repositories..."
mkdir -p vendor

clone_or_pull() {
    local name="$1"
    local url="$2"
    local ref="$3"  # Optional: branch, tag, or commit to checkout
    local dir="vendor/$name"

    if [ ! -d "$dir" ]; then
        echo "    Cloning $name..."
        git clone "$url" "$dir"
        if [ -n "$ref" ]; then
            cd "$dir"
            git checkout "$ref"
            cd "$SCRIPT_DIR"
        fi
    else
        echo "    Updating $name..."
        cd "$dir"
        git fetch origin
        if [ -n "$ref" ]; then
            # If pinned to a ref, just checkout that ref
            git checkout "$ref"
        else
            # Otherwise try to fast-forward
            git pull --ff-only origin main 2>/dev/null || git pull --ff-only origin master 2>/dev/null || {
                echo "    ⚠️  Could not fast-forward $name (local changes?)"
            }
        fi
        cd "$SCRIPT_DIR"
    fi
}

# OpenMemory: pinned to v1.2.3 because later versions removed dashboard source
# TODO: Update when upstream fixes dashboard or switch to hosted dashboard
clone_or_pull "OpenMemory" "https://github.com/CaviraOSS/OpenMemory.git" "v1.2.3"
clone_or_pull "piper-tts-mcp" "https://github.com/CryptoDappDev/piper-tts-mcp.git"

# --- Step 2b: Apply patches ---
echo ">>> Applying patches..."
if [ -d patches ]; then
    for patch in patches/*.patch; do
        if [ -f "$patch" ]; then
            # Extract repo name from patch filename (e.g., piper-tts-mcp.patch -> piper-tts-mcp)
            repo_name=$(basename "$patch" .patch)
            if [ -d "vendor/$repo_name" ]; then
                echo "    Applying $patch to vendor/$repo_name..."
                cd "vendor/$repo_name"
                # Check if patch is already applied
                if git apply --check "$SCRIPT_DIR/$patch" 2>/dev/null; then
                    git apply "$SCRIPT_DIR/$patch"
                    echo "    ✅ Patch applied"
                else
                    echo "    ⚠️  Patch already applied or conflicts"
                fi
                cd "$SCRIPT_DIR"
            fi
        fi
    done
fi

echo ""

if [ "$PULL_ONLY" = true ]; then
    echo "=== Pull complete (--pull-only) ==="
    exit 0
fi

# --- Step 3: Install Python dependencies for MCP servers ---
echo ">>> Installing piper-tts-mcp dependencies..."
if command -v uv &> /dev/null; then
    cd vendor/piper-tts-mcp && uv sync 2>/dev/null || uv pip install -e . && cd "$SCRIPT_DIR"
else
    echo "    ⚠️  uv not found, skipping piper-tts-mcp deps"
fi
echo ""

# --- Step 4: Build Docker services ---
echo ">>> Building Docker services..."

if [ -f services/openmemory/docker-compose.yml ]; then
    echo "    Building OpenMemory..."
    cd services/openmemory && docker compose build && cd "$SCRIPT_DIR"
fi

if [ -f services/piper-tts/docker-compose.yml ]; then
    echo "    Building Piper TTS..."
    cd services/piper-tts && docker compose build && cd "$SCRIPT_DIR"
fi

echo ""

if [ "$NO_START" = true ]; then
    echo "=== Build complete (--no-start) ==="
    exit 0
fi

# --- Step 5: Start services ---
echo ">>> Starting services..."

if [ -f services/openmemory/docker-compose.yml ]; then
    echo "    Starting OpenMemory..."
    cd services/openmemory && docker compose up -d && cd "$SCRIPT_DIR"
fi

if [ -f services/piper-tts/docker-compose.yml ]; then
    echo "    Starting Piper TTS..."
    cd services/piper-tts && docker compose up -d && cd "$SCRIPT_DIR"
fi

if [ -f services/langfuse/docker-compose.yaml ]; then
    echo "    Starting LangFuse..."
    cd services/langfuse && docker compose up -d && cd "$SCRIPT_DIR"
fi

echo ""

# --- Step 6: Health checks ---
echo ">>> Health checks..."
sleep 3

if curl -sf http://localhost:8787/health > /dev/null 2>&1; then
    echo "    ✅ OpenMemory: http://localhost:8787"
else
    echo "    ⚠️  OpenMemory not responding (may still be starting)"
fi

if curl -sf http://localhost:3737 > /dev/null 2>&1; then
    echo "    ✅ Dashboard: http://localhost:3737"
else
    echo "    ⚠️  Dashboard not responding (may still be starting)"
fi

if curl -sf http://localhost:5847 > /dev/null 2>&1; then
    echo "    ✅ Piper TTS: http://localhost:5847"
else
    echo "    ⚠️  Piper TTS not responding (may still be starting)"
fi

if curl -sf http://localhost:13000 > /dev/null 2>&1; then
    echo "    ✅ LangFuse: http://localhost:13000"
else
    echo "    ⚠️  LangFuse not responding (may still be starting)"
fi

echo ""
echo "=== Update complete ==="

