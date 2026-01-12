---
description: Add a new service to the AI Agent Toolset. Use when the user wants to create a new Docker-based service, add a tool to the tools repo, or extend the toolset with a new backend service. Guides through creating service.yaml, docker-compose.yml, update.sh, and optionally an MCP wrapper.
name: add-service
# Augment code rule
type: "agent_requested" 
---

# Add Service to AI Agent Toolset

This skill guides the creation of a new service in the tools repository. Services are Docker-based backends that provide functionality to AI agents via MCP servers.

## Prerequisites

Before starting, gather from the user:
1. **Service name** (lowercase, hyphenated, e.g., `my-service`)
2. **Purpose** - What does this service do?
3. **Port(s)** - Which port(s) will it expose?
4. **Vendor repo** (optional) - Is there an upstream repo to clone?
5. **Environment variables** - Any required configuration?

## File Structure

A complete service requires these files in `services/<name>/`:

```
services/<name>/
├── service.yaml         # Required: CLI metadata
├── docker-compose.yml   # Required: Container definition
├── update.sh            # Required: Installation script
└── .env                 # Optional: Environment variables (gitignored)
```

## Step 1: Create service.yaml

The `service.yaml` file enables CLI discovery and management.

```yaml
name: Service Name
description: Brief description of what this service does
category: optional  # core | optional | experimental

# Optional: upstream repository
vendor:
  url: https://github.com/org/repo.git
  ref: main  # tag, branch, or commit

ports:
  - name: API
    port: 8080
    health_endpoint: /health  # Optional: for health checks

env_vars:
  - name: API_KEY
    required: true
    secret: true
    description: API key for authentication
  - name: PORT
    required: false
    default: "8080"
    description: Port to listen on

dependencies:
  system:
    - docker
    - docker-compose
  services: []  # Other tools services this depends on

# Optional: custom lifecycle commands (defaults to docker-compose)
lifecycle:
  start: docker compose up -d
  stop: docker compose down
  restart: docker compose restart
  install: ./update.sh
  logs: docker compose logs
  status: docker compose ps --quiet | grep -q . && exit 0 || exit 1
```

## Step 2: Create docker-compose.yml

Define the container configuration:

```yaml
services:
  <service-name>:
    image: <image>:<tag>
    # Or build from Dockerfile:
    # build:
    #   context: .
    #   dockerfile: Dockerfile
    ports:
      - "${PORT:-8080}:8080"
    environment:
      - API_KEY=${API_KEY}
    volumes:
      - data:/app/data
    restart: unless-stopped

volumes:
  data:
```

## Step 3: Create update.sh

The installation script handles the full lifecycle:

```bash
#!/bin/bash
set -e
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVICE_DIR"

echo "=== Service Name ==="

# If using a vendor repo:
TOOLS_ROOT="$(cd "$SERVICE_DIR/../.." && pwd)"
VENDOR_DIR="$TOOLS_ROOT/vendor"

if [ ! -d "$VENDOR_DIR/<repo-name>" ]; then
    git clone <repo-url> "$VENDOR_DIR/<repo-name>"
fi
cd "$VENDOR_DIR/<repo-name>"
git fetch --tags
git checkout <ref>

cd "$SERVICE_DIR"

# Build or pull
docker compose pull  # or: docker compose build

# Start
docker compose up -d

# Health check
sleep 3
curl -sf http://localhost:<port>/health > /dev/null && \
    echo "  ✅ Service Name: http://localhost:<port>" || \
    echo "  ⚠️  Service started but health check failed"
```

Make executable: `chmod +x services/<name>/update.sh`

## Step 4: Optional - Create MCP Wrapper

If the service exposes an MCP endpoint, create `mcp/<name>.sh`:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$REPO_ROOT/.env" ]; then
    source "$REPO_ROOT/.env"
fi

# Option A: HTTP MCP proxy
exec npx -y mcp-remote "http://localhost:<port>/mcp"

# Option B: Run Python MCP server
# cd "$REPO_ROOT/vendor/<repo>"
# exec uv run server.py
```

Make executable: `chmod +x mcp/<name>.sh`

## Step 5: Test

1. Run `uv run tools` - service should appear in the list
2. Press `i` to install the service
3. Press `s` to start it
4. Verify health check passes

## Validation Checklist

- [ ] `service.yaml` has name, description, category
- [ ] `service.yaml` ports match docker-compose.yml
- [ ] `docker-compose.yml` uses environment variables from service.yaml
- [ ] `update.sh` is executable and handles vendor repo (if applicable)
- [ ] Health endpoint returns 200 when service is running
- [ ] Service appears in CLI (`uv run tools`)

## Reference

- Full service.yaml spec: `docs/service-yaml-spec.md`
- CLI architecture: `docs/cli-architecture.md`
- Existing services for examples: `services/openmemory/`, `services/piper-tts/`

