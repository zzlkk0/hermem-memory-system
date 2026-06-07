# Installation

## Prerequisites

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed and running
- Python 3.10+
- `pip install mcp`

## Step 1: Install the Skill

```bash
# Clone the repo
git clone https://github.com/zzlkk0/hermes-memory-system.git
cd hermes-memory-system

# Copy skill to Hermes
mkdir -p ~/.hermes/skills/productivity/hierarchical-memory
cp -r skills/hierarchical-memory/* ~/.hermes/skills/productivity/hierarchical-memory/
```

## Step 2: Install the MCP Server

```bash
# Create MCP directory
mkdir -p ~/.hermes/notes/mcp-servers/directory-integrity

# Copy server
cp mcp/directory-integrity/server.py ~/.hermes/notes/mcp-servers/directory-integrity/server.py

# Make it executable
chmod +x ~/.hermes/notes/mcp-servers/directory-integrity/server.py

# Test it
python3 ~/.hermes/notes/mcp-servers/directory-integrity/server.py &
sleep 2 && kill %1
echo "Server starts OK"
```

## Step 3: Configure Hermes

Add to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  # ... existing servers ...

  directory-integrity:
    command: "python3"
    args:
      - "~/.hermes/notes/mcp-servers/directory-integrity/server.py"
    timeout: 30
```

## Step 4: Create the notes/ Directory

```bash
mkdir -p ~/.hermes/notes/sessions
mkdir -p ~/.hermes/backups
```

## Step 5: Restart Hermes

```bash
# CLI
hermes gateway restart

# Or systemd
systemctl --user restart hermes-gateway
```

## Step 6: Verify

Open a new Hermes session or message your bot:

```
"What are my projects?"
```

The agent should load `hierarchical-memory` skill and use the MCP tools.

## Optional: Set Up Cron Jobs

These cron jobs handle automatic backups, integrity checks, and knowledge distillation. The agent will prompt you to create them during your first session, or you can set them up manually:

```bash
hermes cron create "0 2 * * *" --name "Daily Notes Backup" \
  --prompt "Run backup_notes then prune_backups(keep=10). Report result."

hermes cron create "0 9 * * *" --name "Daily Integrity Check" \
  --prompt "Run check_project_paths and check_environment. Report issues."

hermes cron create "0 10 * * 0" --name "Weekly Knowledge Distillation" \
  --prompt "Run distill_knowledge. If patterns found, write to notes/permanent-knowledge.md."
```

## Troubleshooting

### MCP server not connecting

Check Hermes logs:
```bash
journalctl --user -u hermes-gateway -n 50 | grep -i mcp
```

### Skills not loading

```bash
hermes skills list | grep hierarchical
```

### Tools not appearing

The skill and MCP tools load at startup. Restart Hermes after any changes.

### Python import errors

```bash
pip install mcp
python3 -c "from mcp.server.fastmcp import FastMCP; print('OK')"
```
