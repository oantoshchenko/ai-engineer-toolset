#!/bin/bash
# ElevenLabs TTS MCP wrapper
# Requires ELEVENLABS_API_KEY in .env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source environment (required for API key)
if [ -f "$REPO_ROOT/.env" ]; then
    source "$REPO_ROOT/.env"
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "ERROR: ELEVENLABS_API_KEY not set. Add it to $REPO_ROOT/.env" >&2
    exit 1
fi

export ELEVENLABS_API_KEY

# Suppress "Speaking:" output to avoid interfering with LLM responses
export MCP_TTS_SUPPRESS_SPEAKING_OUTPUT="true"

# Enforce sequential TTS (prevent concurrent speech)
export MCP_TTS_ALLOW_CONCURRENT="false"

# Use mcp-tts from Go bin (installed via: go install github.com/...)
# Falls back to PATH if not in standard location
if [ -x "$HOME/go/bin/mcp-tts" ]; then
    exec "$HOME/go/bin/mcp-tts"
else
    exec mcp-tts
fi

