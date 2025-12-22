#!/bin/bash
# Piper TTS MCP wrapper
# Runs the MCP server with uv, pointing to local Docker service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PIPER_TTS_URL="${PIPER_TTS_URL:-http://localhost:5847}"

cd "$REPO_ROOT/vendor/piper-tts-mcp"
exec uv run server.py

