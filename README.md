# Tools

MCP infrastructure for AI assistants. Syncs across machines via Git.

## Structure

```
tools/
├── mcp/              # MCP wrapper scripts (sourced by IDE/agent)
├── services/         # Each service has its own update.sh
│   ├── openmemory/   # docker-compose.yml, update.sh
│   ├── piper-tts/    # docker-compose.yml, update.sh, patches/
│   └── langfuse/     # docker-compose.yaml, update.sh, maintenance.sh
├── vendor/           # Third-party repos (gitignored)
└── update.sh         # Runs all services/*/update.sh
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| OpenMemory API | 8787 | Cross-project memory for agents |
| OpenMemory Dashboard | 3737 | Web UI for memory inspection |
| Piper TTS | 5847 | Local text-to-speech |
| LangFuse Web | 13000 | LLM observability UI |
| LangFuse Worker | 13030 | Background trace processing |
| LangFuse Postgres | 15433 | LangFuse database |
| LangFuse ClickHouse | 18123 | Analytics database |
| LangFuse MinIO | 19090 | S3-compatible storage |
| LangFuse Redis | 16379 | Cache |

## Setup

```bash
# Clone and run
git clone git@github.com:oantoshchenko/tools.git ~/ws/tools
cd ~/ws/tools
./update.sh
```

The master script runs each service's `update.sh`, which handles:
- Cloning/updating vendor repos
- Applying patches (if any)
- Building Docker images
- Starting containers

## MCP Configuration

Point your IDE/agent MCP config to scripts in `mcp/`:

- `mcp/openmemory.sh` - OpenMemory MCP server
- `mcp/piper-tts.sh` - Piper TTS MCP server
- `mcp/elevenlabs-tts.sh` - ElevenLabs TTS (cloud)
- `mcp/obsidian-edit.sh` - Obsidian vault access

## Data Persistence

- OpenMemory data: Docker volume `openmemory_data` (survives updates)
- Piper models: `services/piper-tts/models/` (gitignored)
- LangFuse data: Docker volumes `ai-agent_langfuse_*` (external, shared)

## LangFuse

Login: `admin@aiagent.local` / `admin123`

API keys (pre-configured):
- Public: `pk-lf-ai-agent-public-key`
- Secret: `sk-lf-ai-agent-secret-key`

Maintenance (ClickHouse can bloat):
```bash
./services/langfuse/maintenance.sh --help    # See options
./services/langfuse/maintenance.sh --setup   # First-time optimization
./services/langfuse/maintenance.sh           # Regular cleanup
```

## Adding a New Service

1. Create `services/<name>/` directory
2. Add `docker-compose.yml` with your service config
3. Create `update.sh` that handles the full lifecycle:

```bash
#!/bin/bash
set -e
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVICE_DIR"  # IMPORTANT: cd before docker compose commands

echo "=== <Name> ==="

# If using a vendor repo:
TOOLS_ROOT="$(cd "$SERVICE_DIR/../.." && pwd)"
VENDOR_DIR="$TOOLS_ROOT/vendor"
# Clone/update vendor repo here...

# If patches needed, put them in patches/ subdirectory

docker compose build  # or 'docker compose pull' for pre-built images
docker compose up -d

# Health check
sleep 3
curl -sf http://localhost:<port> > /dev/null && echo "  ✅ <Name>: http://localhost:<port>"
```

4. Make executable: `chmod +x services/<name>/update.sh`
5. Update this README (Services table, Data Persistence if applicable)
6. Run `./update.sh` to test

The master `update.sh` auto-discovers and runs all `services/*/update.sh` scripts.

## Notes

- OpenMemory pinned to v1.2.3 because later versions removed dashboard source
- Run `./update.sh` after pulling to sync vendor deps
