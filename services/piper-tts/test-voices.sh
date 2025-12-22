#!/bin/bash
# Test different Piper TTS voices
# Usage: ./test-voices.sh [voice-name]
# Example: ./test-voices.sh en_US-amy-medium

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VOICE="${1:-en_GB-alba-medium}"
TEST_TEXT="${2:-Hello Sasha! This is a test of the Piper text to speech system.}"

echo "Testing voice: $VOICE"
echo "Text: $TEST_TEXT"
echo ""

# Restart container with new voice (no rebuild needed!)
echo "Starting container with voice: $VOICE..."
PIPER_VOICE="$VOICE" docker compose up -d

# Wait for service to be ready (first download may take a moment)
echo "Waiting for service (downloading voice if needed)..."
sleep 3

# Poll until ready or timeout
for i in {1..30}; do
  if curl -s -f "http://localhost:5847/" > /dev/null 2>&1; then
    break
  fi
  echo "  Waiting... ($i/30)"
  sleep 2
done

# Test the voice
echo "Generating audio..."
curl -s -X POST "http://localhost:5847/" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TEST_TEXT\"}" \
  --output /tmp/piper-voice-test.wav

echo "Playing audio..."
afplay /tmp/piper-voice-test.wav

echo ""
echo "Done! Voice $VOICE tested."
echo "To keep this voice running: PIPER_VOICE=$VOICE docker compose up -d"
echo "To try another: ./test-voices.sh <voice-name>"

