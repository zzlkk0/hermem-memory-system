---
name: hierarchical-memory
description: "Three-tier memory system: global facts, session files, searchable history. Load references for details."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [memory, organization, notes, productivity]
    related_skills: [hermes-agent, obsidian]
---

# Hierarchical Memory System

Three-tier memory: global facts → session files → searchable history.

## When to Use

- Before calling `memory(action='add')` — follow the decision tree
- MEMORY.md cleanup needed
- User corrects memory habits
- Starting substantive work → create session memory (see `references/session-memory.md`)
- Error fixed → log to errors.md
- Major task completed → update timeline.md

Don't use for: routine tool calls, code editing.

## The Three Tiers

```
TIER 1: MEMORY.md (Global, ~2200 char cap)
  One-line facts. No IDs. No details.
  "Has a Telegram bot configured"
  "Prefers Python 3.11+"

TIER 2: notes/sessions/<date>-<topic>/ (Per-session, unlimited)
  4 files: overview / timeline / errors / reference
  Survives token compression — see references/session-memory.md

TIER 3: session_search() (SQLite FTS5)
  session_search(query="telegram setup") → past conversations
```

## Decision Tree: Where to Save

```
Found a fact worth keeping.
│
├─ Will this matter in an unrelated conversation NEXT MONTH?
│  ├─ YES → Is it one sentence?
│  │        ├─ YES → MEMORY.md (memory tool, concise!)
│  │        └─ NO  → notes/<file>.md, then add ONE reference line to MEMORY.md
│  └─ NO  → Is it configuration details / logs / raw data?
│           ├─ YES → notes/<file>.md (write_file)
│           └─ NO  → session_search will find it — don't save
```

## MEMORY.md Rules

**DO:** One-liners like "Has a Telegram bot (see notes/setup-log.md)"
**DON'T:** Raw IDs, tokens, multi-paragraph blocks, task progress

## notes/ Directory

```
~/.hermes/notes/
├── setup-log.md              # System config diary
├── project-index.md          # User project catalog
├── environment.md            # Installed software
├── sessions/<date>-<topic>/  # Per-session memory (→ references/session-memory.md)
└── permanent-knowledge.md    # Distilled from errors (auto-generated)
```

## Reference Documents

Load these on-demand with `skill_view(name='hierarchical-memory', file_path='references/<file>')`:

| File | When to load |
|------|-------------|
| `references/session-memory.md` | Creating/updating session files, naming, cleanup |
| `references/project-tracking.md` | Managing project-index, environment, MCP integrity tools |
| `references/backup-and-distillation.md` | Backup/restore, knowledge distillation, context briefing |

## MCP Tools (Quick Reference)

| Tool | Purpose |
|------|---------|
| `check_project_paths` | Verify project paths exist |
| `check_environment` | Verify tools on PATH |
| `list_projects` | List all tracked projects |
| `get_project_health` | Git status + freshness + file stats |
| `backup_notes` | Create tar.gz backup |
| `list_backups` | View backups |
| `restore_backups` | Restore (safety backup first) |
| `prune_backups` | Delete old backups |
| `distill_knowledge` | Cross-session error pattern extraction |
| `context_brief("topic")` | Focused context for a project |

## Cron Jobs

- **02:00 daily** — backup notes/ + prune
- **09:00 daily** — integrity check (paths + environment)
- **10:00 Sun** — knowledge distillation

## Common Pitfalls

1. **IDs to MEMORY.md** — put in notes/ instead
2. **Task progress to MEMORY.md** — use session_search
3. **Overwriting notes files** — use `patch` to append
4. **No reference line** — if you move details to notes/, add a one-liner to MEMORY.md
5. **Not creating session files** — token compression WILL erase context
6. **Duplicating data** — MEMORY.md = index, session files = archive
7. **Overwriting existing session dir** — always check first, RESUME if same-day
8. **Stale sessions pile up** — archive >30-day directories to `.archive/`
9. **Forgetting context_brief** — before project work, get focused briefing to save tokens
