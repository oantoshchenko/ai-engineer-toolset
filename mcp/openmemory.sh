#!/bin/bash
# OpenMemory MCP stdio proxy
# Forwards MCP requests to the running OpenMemory backend via HTTP

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source environment if available
if [ -f "$REPO_ROOT/.env" ]; then
    source "$REPO_ROOT/.env"
fi

BACKEND_URL="${OPENMEMORY_URL:-http://localhost:8787}"

# Use npx to run the mcp-remote package which proxies HTTP MCP to stdio
exec npx -y mcp-remote "$BACKEND_URL/mcp"

