#!/bin/bash
# Tools Update Script
# Idempotent: handles both fresh setup and updates
#
# Runs update.sh in each service directory.
# Each service handles its own vendor repos, patches, builds, and starts.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Tools Update ==="
echo "Directory: $SCRIPT_DIR"
echo ""

# --- Check/create .env ---
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

# --- Run each service's update script ---
for service_dir in services/*/; do
    if [ -f "$service_dir/update.sh" ]; then
        "$service_dir/update.sh"
    fi
done

echo "=== Update complete ==="
