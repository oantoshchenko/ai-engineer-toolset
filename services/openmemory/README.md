# OpenMemory Local

A local deployment of [OpenMemory](https://github.com/OpenMemory/OpenMemory) - a self-hosted AI memory engine that provides persistent memory for AI agents across projects and conversations.

## What is this?

This is a standalone Docker-based deployment that:
- Runs OpenMemory backend on port **8787**
- Runs the dashboard UI on port **3737**
- Uses **Ollama** for local embeddings (no cloud API needed)
- Keeps configuration separate from the source repo for easy updates

## Quick Start

```bash
# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Backend API | http://localhost:8787 | Memory storage and MCP endpoint |
| Dashboard | http://localhost:3737 | Web UI for viewing/managing memories |
| MCP Endpoint | http://localhost:8787/mcp | Model Context Protocol for AI agents |

## Augment Code MCP Configuration

Configure the MCP wrapper script in your IDE. The script is at `mcp/openmemory.sh` in the tools repo.

1. Open Augment Code settings (gear icon)
2. Click **"+ Add MCP"**
3. Fill in:
   - **Name:** `openmemory`
   - **Command:** `<path-to-tools>/mcp/openmemory.sh`
4. Click **Save**

### Verify Connection

After adding the MCP, it should show a green indicator. Start a **new conversation** and ask the agent:

> Do you have access to OpenMemory tools? Run `openmemory_list` to check.

## Available MCP Tools

Once configured, AI agents have access to:

| Tool | Description |
|------|-------------|
| `openmemory_query` | Semantic search across memories |
| `openmemory_store` | Save new memories |
| `openmemory_list` | List recent memories |
| `openmemory_get` | Fetch a specific memory by ID |
| `openmemory_reinforce` | Boost salience of important memories |

### Example Usage

```
# Store a preference
openmemory_store(content="User prefers dark mode", user_id="sasha", tags=["preferences"])

# Query memories
openmemory_query(query="user preferences", user_id="sasha")

# List all memories for a user
openmemory_list(user_id="sasha", limit=10)
```

## Keeping Up-to-Date

Run the update script from the tools root:

```bash
../../update.sh
```

This script:
1. Pulls latest changes from the OpenMemory repository (into vendor/)
2. Rebuilds Docker images with new code
3. Restarts services

## File Structure

```
services/openmemory/
├── docker-compose.yml      # Main Docker Compose configuration
├── Dockerfile.dashboard    # Custom dashboard build
└── README.md               # This file
```

## Configuration

### Environment Variables (docker-compose.yml)

| Variable | Default | Description |
|----------|---------|-------------|
| `OM_EMBEDDINGS` | `ollama` | Embedding provider |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama API URL |
| `OM_TIER` | `hybrid` | Performance tier (hybrid/fast/smart/deep) |
| `OM_API_KEY` | `""` | API key (empty = no auth required) |

### Prerequisites

- Docker and Docker Compose
- Ollama running locally with `nomic-embed-text` model:
  ```bash
  ollama pull nomic-embed-text
  ```

## Troubleshooting

### MCP not connecting

1. Check if backend is running: `curl http://localhost:8787/health`
2. Check MCP endpoint: `curl -X POST http://localhost:8787/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'`

### Dashboard shows 0 memories

The dashboard requires the API key baked in at build time. Rebuild if needed:
```bash
docker compose build dashboard --no-cache
docker compose up -d dashboard
```

### Ollama connection issues

Ensure Ollama is running and the model is available:
```bash
ollama list  # Should show nomic-embed-text
curl http://localhost:11434/api/embeddings -d '{"model":"nomic-embed-text","prompt":"test"}'
```

## Data Persistence

Memory data is stored in a Docker volume `openmemory_data`. To backup:

```bash
docker run --rm -v openmemory_data:/data -v $(pwd):/backup alpine tar czf /backup/openmemory-backup.tar.gz /data
```

To restore:

```bash
docker run --rm -v openmemory_data:/data -v $(pwd):/backup alpine tar xzf /backup/openmemory-backup.tar.gz -C /
```
