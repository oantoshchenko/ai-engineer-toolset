#!/bin/bash
# OpenMemory service update script
# Clones/updates vendor repo, builds, and starts the service

set -e

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_ROOT="$(cd "$SERVICE_DIR/../.." && pwd)"
VENDOR_DIR="$TOOLS_ROOT/vendor"
VENDOR_NAME="OpenMemory"
VENDOR_URL="https://github.com/CaviraOSS/OpenMemory.git"
# Pinned to v1.2.3 because later versions removed dashboard source
VENDOR_REF="v1.2.3"

echo "=== OpenMemory ==="

# --- Clone or update vendor repo ---
mkdir -p "$VENDOR_DIR"

if [ ! -d "$VENDOR_DIR/$VENDOR_NAME" ]; then
    echo "  Cloning $VENDOR_NAME..."
    git clone "$VENDOR_URL" "$VENDOR_DIR/$VENDOR_NAME"
    cd "$VENDOR_DIR/$VENDOR_NAME"
    git checkout "$VENDOR_REF"
    cd "$SERVICE_DIR"
else
    echo "  Updating $VENDOR_NAME..."
    cd "$VENDOR_DIR/$VENDOR_NAME"
    git fetch origin
    git checkout "$VENDOR_REF"
    cd "$SERVICE_DIR"
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

if curl -sf http://localhost:8787/health > /dev/null 2>&1; then
    echo "  ✅ API: http://localhost:8787"
else
    echo "  ⚠️  API not responding (may still be starting)"
fi

if curl -sf http://localhost:3737 > /dev/null 2>&1; then
    echo "  ✅ Dashboard: http://localhost:3737"
else
    echo "  ⚠️  Dashboard not responding (may still be starting)"
fi

echo ""

