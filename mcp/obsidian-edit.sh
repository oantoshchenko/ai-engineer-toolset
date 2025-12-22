#!/bin/bash
# Obsidian MCP wrapper (cyanheads version with write support)
# Requires OBSIDIAN_API_KEY in .env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source environment (required for API key)
if [ -f "$REPO_ROOT/.env" ]; then
    source "$REPO_ROOT/.env"
fi

if [ -z "$OBSIDIAN_API_KEY" ]; then
    echo "ERROR: OBSIDIAN_API_KEY not set. Add it to $REPO_ROOT/.env" >&2
    exit 1
fi

export OBSIDIAN_API_KEY
export OBSIDIAN_BASE_URL="${OBSIDIAN_BASE_URL:-http://127.0.0.1:27123}"

exec npx obsidian-mcp-server

