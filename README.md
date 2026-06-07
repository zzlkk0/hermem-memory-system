# Hermem Memory System

> Structured, self-improving long-term memory for your [Hermes Agent](https://github.com/NousResearch/hermes-agent).  
> Never repeat yourself across sessions again.
<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/e1d84e16-8947-4169-8b1e-23b6d56531de" />

## The Problem

AI agents forget. Every new session, you explain your project structure, your preferences, your environment — again and again. Long conversations get truncated. Error lessons are lost.

## The Solution

A three-tier memory system that's **transparent** (plain Markdown files you can read/edit), **self-improving** (automatically extracts error patterns across sessions), and **token-efficient** (loads only what's relevant for the current task).

```
┌──────────────────────────────────────────────────────┐
│  TIER 1 — Global Memory (MEMORY.md)                  │
│  One-line facts. No clutter. All sessions see this.  │
│  "Has a Telegram bot configured"                     │
│  "Working on hermes-agent at ~/dev/hermes-agent"     │
└──────────┬───────────────────────────────────────────┘
           │ reference → "see notes/setup-log.md"
           ▼
┌──────────────────────────────────────────────────────┐
│  TIER 2 — Session Memory (notes/sessions/)           │
│  4 files per topic: overview / timeline / errors /   │
│  reference. Survives token compression.              │
└──────────┬───────────────────────────────────────────┘
           │ auto-distilled weekly
           ▼
┌──────────────────────────────────────────────────────┐
│  TIER 3 — Permanent Knowledge (notes/permanent-)     │
│  knowledge.md. Patterns extracted across sessions.   │
│  Agent gets smarter the more you use it.             │
└──────────────────────────────────────────────────────┘
```

## Features

| Feature | What It Does |
|---------|-------------|
| **Hierarchical Memory** | Global facts → session context → searchable history. No bloat. |
| **Per-Session Files** | Each conversation gets 4 files (overview, timeline, errors, reference). Survives token compression. |
| **Project Index** | Catalog of all your projects with paths. Agent knows what you're working on. |
| **Environment Tracking** | Installed software, tools, versions. Agent knows what's available. |
| **Automatic Backups** | Daily tar.gz backups of all notes. Restore with safety backup. |
| **Knowledge Distillation** | Weekly scan of all session errors → extracts recurring patterns → writes permanent knowledge. |
| **Context Briefing** | `context_brief("project-name")` loads only what's relevant. Saves ~80% token overhead. |
| **Project Health** | Git status, freshness, file stats. Flags abandoned projects (>180 days). |
| **Directory Integrity** | Daily check: are all tracked project paths still valid? |
| **Transparent** | Everything is Markdown. You can read, edit, delete any file. |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/zzlkk0/hermem-memory-system.git

# 2. Install the skill
cp -r hermem-memory-system/skills/hierarchical-memory ~/.hermes/skills/productivity/

# 3. Install the MCP server
mkdir -p ~/.hermes/notes/mcp-servers/directory-integrity
cp hermem-memory-system/mcp/directory-integrity/server.py ~/.hermes/notes/mcp-servers/directory-integrity/

# 4. Add to ~/.hermes/config.yaml under mcp_servers:
#   directory-integrity:
#     command: "python3"
#     args: ["~/.hermes/notes/mcp-servers/directory-integrity/server.py"]

# 5. Restart Hermes
hermes gateway restart
```

That's it. Next time you start a conversation with Hermes, it will:
1. Read the hierarchical-memory skill
2. Create per-session memory files
3. Use the decision tree to decide what to save where

## Architecture

```
~/.hermes/
├── memories/
│   ├── MEMORY.md              ← Global one-liners (auto-injected every session)
│   └── USER.md                ← Your preferences + CRITICAL RULES
│
├── notes/                     ← The "diary" — detailed, unlimited
│   ├── setup-log.md           ← System config diary
│   ├── project-index.md       ← All your projects cataloged
│   ├── environment.md         ← Installed software/tools
│   ├── permanent-knowledge.md ← Auto-distilled from errors
│   └── sessions/
│       └── <YYYYMMDD>-<topic>/
│           ├── overview.md    ← What this is about
│           ├── timeline.md    ← What happened when
│           ├── errors.md      ← Errors + how to fix
│           └── reference.md   ← IDs, tokens, paths
│
├── skills/productivity/
│   └── hierarchical-memory/
│       ├── SKILL.md           ← Core philosophy + decision tree
│       └── references/        ← On-demand detailed docs
│
└── state.db                   ← session_search() SQLite FTS5
```

## MCP Tools (10 tools)

| Tool | What It Does |
|------|-------------|
| `check_project_paths` | Verify all tracked project paths exist |
| `check_environment` | Verify all tracked tools are on PATH |
| `list_projects` | List all projects with live status |
| `get_project_health` | Git status, freshness (>180d = abandoned), file stats |
| `backup_notes` | Create tar.gz snapshot of all notes |
| `list_backups` | View existing backups |
| `restore_backups` | Restore from backup (auto safety-backup first) |
| `prune_backups` | Keep last N backups only |
| `distill_knowledge` | Cross-session error pattern extraction |
| `context_brief("topic")` | Focused context — loads only relevant sessions |

## Automated Cron Jobs

| Schedule | What Runs |
|----------|-----------|
| Daily 02:00 | Backup notes + prune old backups |
| Daily 09:00 | Integrity check (paths + environment) |
| Weekly Sun 10:00 | Knowledge distillation (scan all errors for patterns) |

## Demo

```
You: "I got a 'permission denied' error again, same as last week."

Agent: [loads context_brief("permission denied")]
       [finds error in 3 past sessions]
       [calls distill_knowledge — pattern confirmed]
       "This is pattern #3 from permanent-knowledge.md.
        Root cause: Docker socket permissions.
        Fix: sudo usermod -aG docker $USER, then reboot."

You: "Let's work on GPT-SoVITS."

Agent: [calls context_brief("GPT-SoVITS")]
       "GPT-SoVITS: 1 sessions, 8 uncommitted changes.
        Last commit: 2 months ago by you.
        Related error: CUDA OOM on large inputs."
```

## Requirements

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed
- Python 3.10+ with `mcp` package: `pip install mcp`
- Memory enabled in Hermes config: `memory.memory_enabled: true`

## License

MIT — see [LICENSE](LICENSE).

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## Author

Created with [Hermes Agent](https://github.com/NousResearch/hermes-agent) by [@zzlkk0](https://github.com/zzlkk0).
