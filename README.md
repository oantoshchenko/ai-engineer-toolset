# AI Agent Toolset

An open-source, plugin-based toolkit for working with AI agents. Provides MCP servers, services, and agent configuration files that work with any MCP-compatible AI assistant (Claude, Cursor, Augment, etc.).

## What's Included

- **CLI** — Interactive TUI for managing services (start/stop/install/configure)
- **MCP Servers** — Wrapper scripts that expose tools to AI agents via MCP protocol
- **Services** — Docker-based backend services (memory, TTS, observability, etc.)
- **Agent Files** — Reusable agent instructions and skills (`AGENT.md`, skills/)

## Quick Start

```bash
# Clone
git clone git@github.com:oantoshchenko/tools.git ~/ws/tools
cd ~/ws/tools

# Install CLI (requires Python 3.11+ and uv)
uv sync

# Launch the interactive manager
uv run tools
```

The TUI lets you install, start, stop, and configure services with keyboard shortcuts.

Alternatively, use the legacy script to install all services at once:
```bash
./update.sh
```

## Project Structure

```
tools/
├── cli/                  # Interactive TUI (Textual-based)
├── mcp/                  # MCP wrapper scripts for IDE/agent integration
├── services/             # Docker-based services with service.yaml metadata
│   ├── openmemory/       # Persistent memory for agents
│   ├── piper-tts/        # Local text-to-speech
│   ├── langfuse/         # LLM observability
│   └── languagetool/     # Grammar checking
├── ai-assistant/         # Agent configuration files
│   ├── AGENT.md          # Base agent instructions
│   └── skills/           # Reusable skill definitions
├── vendor/               # Third-party repos (gitignored)
├── docs/                 # Architecture documentation
└── pyproject.toml        # Python package config
```

## CLI Usage

```bash
# Launch interactive TUI
uv run tools

# Keyboard shortcuts in TUI:
#   ↑↓  Navigate services
#   s   Start selected service
#   S   Stop selected service
#   R   Restart selected service
#   i   Install/update selected service
#   l   View logs
#   c   Configure environment variables
#   r   Refresh status
#   q   Quit
```

## MCP Configuration

Point your IDE/agent MCP config to scripts in `mcp/`:

| Script | Purpose |
|--------|---------|
| `mcp/openmemory.sh` | Persistent memory with semantic search |
| `mcp/piper-tts.sh` | Local text-to-speech (Piper) |
| `mcp/elevenlabs-tts.sh` | Cloud text-to-speech (ElevenLabs) |
| `mcp/obsidian-edit.sh` | Obsidian vault access |

Example MCP config (for Claude Desktop, Cursor, etc.):
```json
{
  "mcpServers": {
    "openmemory": {
      "command": "/path/to/tools/mcp/openmemory.sh"
    },
    "speak": {
      "command": "/path/to/tools/mcp/piper-tts.sh"
    }
  }
}
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| OpenMemory API | 8787 | Persistent memory layer for agents |
| OpenMemory Dashboard | 3737 | Web UI for memory inspection |
| Piper TTS | 5847 | Local text-to-speech |
| LanguageTool | 8010 | Grammar and spell checking |
| LangFuse | 13000 | LLM observability and tracing |

## Agent Files

The `ai-assistant/` directory contains reusable agent configuration:

- **`AGENT.md`** — Base instructions for AI agents (coding style, protocols, tool usage)
- **`skills/`** — Modular skill definitions that agents can follow

These files are designed to be included in your IDE's agent configuration or referenced by MCP-compatible assistants.

---

## Adding a New Tool

The toolset is designed to be extensible. There are two types of additions:

### Adding a New Service

Services are Docker-based backends that provide functionality to MCP servers.

1. **Create the service directory:**
   ```bash
   mkdir -p services/<name>
   ```

2. **Create `service.yaml`** (required for CLI discovery):
   ```yaml
   name: My Service
   description: What this service does
   category: optional  # core | optional | experimental

   # Optional: vendor repo to clone
   vendor:
     url: https://github.com/org/repo.git
     ref: main  # tag, branch, or commit

   # Ports exposed by the service
   ports:
     - name: API
       port: 8080
       health_endpoint: /health  # for health checks

   # Environment variables
   env_vars:
     - name: API_KEY
       required: true
       secret: true
       description: API key for the service

   # Optional: custom lifecycle commands (defaults to docker-compose)
   lifecycle:
     start: docker compose up -d
     stop: docker compose down
     install: ./update.sh
   ```

3. **Create `docker-compose.yml`:**
   ```yaml
   services:
     myservice:
       image: myimage:latest
       ports:
         - "8080:8080"
       environment:
         - API_KEY=${API_KEY}
   ```

4. **Create `update.sh`** (installation script):
   ```bash
   #!/bin/bash
   set -e
   SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   cd "$SERVICE_DIR"

   echo "=== My Service ==="

   # If using a vendor repo:
   TOOLS_ROOT="$(cd "$SERVICE_DIR/../.." && pwd)"
   VENDOR_DIR="$TOOLS_ROOT/vendor"
   if [ ! -d "$VENDOR_DIR/myrepo" ]; then
       git clone https://github.com/org/repo.git "$VENDOR_DIR/myrepo"
   fi
   cd "$VENDOR_DIR/myrepo" && git pull

   cd "$SERVICE_DIR"
   docker compose pull  # or: docker compose build
   docker compose up -d

   sleep 3
   curl -sf http://localhost:8080/health > /dev/null && echo "  ✅ My Service: http://localhost:8080"
   ```

5. **Make executable and test:**
   ```bash
   chmod +x services/<name>/update.sh
   uv run tools  # Service should appear in the list
   ```

### Adding a New MCP Server

MCP servers expose tools to AI agents. They typically wrap a service or external API.

1. **Create the wrapper script** in `mcp/`:
   ```bash
   #!/bin/bash
   # mcp/myserver.sh
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

   # Source environment
   if [ -f "$REPO_ROOT/.env" ]; then
       source "$REPO_ROOT/.env"
   fi

   # Option A: Proxy to HTTP MCP endpoint
   exec npx -y mcp-remote "http://localhost:8080/mcp"

   # Option B: Run a Python MCP server
   # cd "$REPO_ROOT/vendor/my-mcp-server"
   # exec uv run server.py
   ```

2. **Make executable:**
   ```bash
   chmod +x mcp/myserver.sh
   ```

3. **Add to your IDE's MCP config** (see MCP Configuration section above)

### Service YAML Reference

See `docs/service-yaml-spec.md` for the complete `service.yaml` specification, including:
- Custom lifecycle commands (for non-Docker services)
- Health check configuration
- Dependency declarations

---

## Data Persistence

| Data | Location |
|------|----------|
| OpenMemory | Docker volume `openmemory_data` |
| Piper models | `services/piper-tts/models/` (gitignored) |
| LangFuse | Docker volumes `ai-agent_langfuse_*` |

## Notes

- OpenMemory pinned to v1.2.3 (later versions removed dashboard source)
- Run `./update.sh` after pulling to sync vendor dependencies
- Requires Docker, Python 3.11+, and uv
