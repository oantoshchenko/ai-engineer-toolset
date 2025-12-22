# Tools

MCP infrastructure for AI assistants. Syncs across machines via Git.

## Structure

```
tools/
├── mcp/           # MCP wrapper scripts (sourced by IDE/agent)
├── services/      # Docker Compose configs (committed)
├── vendor/        # Third-party repos (gitignored, cloned by update.sh)
├── patches/       # Patches applied to vendor repos
└── update.sh      # Idempotent setup script
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

The script:
1. Clones/updates vendor repos (OpenMemory pinned to v1.2.3)
2. Applies patches
3. Builds Docker images
4. Starts all services

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
./scripts/langfuse-maintenance.sh --help    # See options
./scripts/langfuse-maintenance.sh --setup   # First-time optimization
./scripts/langfuse-maintenance.sh           # Regular cleanup
```

## Notes

- OpenMemory pinned to v1.2.3 because later versions removed dashboard source
- Run `./update.sh` after pulling to sync vendor deps

