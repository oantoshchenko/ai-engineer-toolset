# Piper TTS Local

Local deployment of [Piper TTS](https://github.com/rhasspy/piper) as a Docker service with MCP server integration.

## Quick Start

```bash
# Build and start the TTS service
docker compose up -d

# Check logs
docker compose logs -f

# Stop the service
docker compose down
```

## Configuration

- **Port**: The TTS HTTP service runs on port `5847` (mapped from container port 5000)
- **Voice Model**: `en_GB-cori-high` (British English, female voice)

### Changing Voice Models

1. Browse available voices at [Piper Voice Samples](https://rhasspy.github.io/piper-samples/)
2. Edit `Dockerfile` and replace `en_GB-cori-high` with your preferred voice
3. Rebuild: `docker compose build && docker compose up -d`

## Testing the TTS Service

```bash
# Test the TTS service directly
curl -X POST "http://localhost:5847/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test."}' \
  --output test.wav

# Play the audio (macOS)
afplay test.wav
```

## MCP Server Setup

The MCP server is cloned into `vendor/piper-tts-mcp/` by the update script (from [CryptoDappDev/piper-tts-mcp](https://github.com/CryptoDappDev/piper-tts-mcp)).

### MCP Configuration

Use the wrapper script at `mcp/piper-tts.sh`:

```json
{
  "mcpServers": {
    "piper-tts": {
      "command": "<path-to-tools>/mcp/piper-tts.sh"
    }
  }
}
```

### Available Tool

The MCP server provides a `speak` tool with these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | *required* | Text to convert to speech |
| `speaker_id` | int | 0 | Voice speaker ID |
| `length_scale` | float | 1.1 | Speech speed (lower = faster) |
| `noise_scale` | float | 0.667 | Voice variation control |
| `noise_w_scale` | float | 0.333 | Pronunciation variation |
| `volume` | float | 0.15 | Volume level (0.01 to 1.00) |

