# MCP Servers

This directory contains wrapper scripts for Model Context Protocol (MCP) servers used with AI assistants.

You do not have to use these scripts. Those are just one-line MCP configurations that avoid setting up more complicated setups and avoid doing that in multiple agent tools. 

## Available MCP Servers

### obsidian-edit.sh
**Purpose:** Interact with Obsidian vault via REST API  
**Package:** `obsidian-mcp-server` (npm)  
**Prerequisites:**
- Obsidian with Local REST API plugin installed and enabled
- API key generated in plugin settings

**Configuration (.env):**
```bash
OBSIDIAN_API_KEY=your-api-key-here
OBSIDIAN_BASE_URL=http://127.0.0.1:27123  # Default HTTP endpoint
```

**Setup:**
1. Install Local REST API plugin in Obsidian (Settings → Community Plugins)
2. Enable the plugin and generate an API key
3. Enable "Non-encrypted (HTTP) Server" in plugin settings
4. Add API key to `.env`

---

### openmemory.sh
**Purpose:** Persistent memory storage for AI conversations  
**Package:** `mcp-remote` (npm)  
**Prerequisites:**
- OpenMemory service running (via CLI tool)

**Configuration (.env):**
```bash
OPENMEMORY_URL=http://localhost:8787  # Default
```

**Setup:**
- Start OpenMemory service: `./cli/app.py start openmemory`

---

### piper-tts.sh
**Purpose:** Text-to-speech using Piper  
**Package:** Local vendor package (`vendor/piper-tts-mcp`)  
**Prerequisites:**
- Piper TTS service running (via Docker)
- uv package manager

**Configuration (.env):**
```bash
PIPER_TTS_URL=http://localhost:5847  # Default
```

**Setup:**
- Start Piper TTS service: `./cli/app.py start piper-tts`

---

### elevenlabs-tts.sh
**Purpose:** Text-to-speech using ElevenLabs API  
**Package:** `mcp-tts` (Go binary)  
**Prerequisites:**
- ElevenLabs API key
- Go binary installed: `go install github.com/metoro-io/mcp-tts@latest`

**Configuration (.env):**
```bash
ELEVENLABS_API_KEY=your-api-key-here
```

**Setup:**
1. Get API key from ElevenLabs
2. Install mcp-tts: `go install github.com/metoro-io/mcp-tts@latest`
3. Add API key to `.env`

---

## Usage

These scripts are meant to be referenced in your MCP client configuration (e.g., Augment, Claude Desktop).

Example configuration:
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "/path/to/tools/mcp/obsidian-edit.sh"
    }
  }
}
```

## Environment Variables

All scripts source `.env` from the repository root. Create `.env` by copying `.env.example` (in root of the repo):
```shell
cp .env.example .env
```
Set the variable for the MCPs you are using
