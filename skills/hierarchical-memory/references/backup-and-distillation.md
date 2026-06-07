# Backup, Knowledge Distillation & Context Briefing

## Backup System

The directory-integrity MCP provides full backup lifecycle:

| Tool | Purpose |
|------|---------|
| `backup_notes` | Create tar.gz backup of `notes/` → `~/.hermes/backups/` |
| `list_backups` | List all backups with size, date, age |
| `restore_backups` | Restore from a backup (creates safety backup first) |
| `prune_backups` | Keep only last N backups (default: 10) |

**Cron:** Daily at 2:00 AM — auto-backup + prune old backups.

**Restore safety:** `restore_backups` always creates a safety backup of current notes first. Never possible to lose data.

## Knowledge Distillation

`distill_knowledge` scans all `sessions/*/errors.md` files across ALL past sessions and identifies recurring error patterns. This turns scattered error logs into permanent knowledge.

**How it works:**
1. Reads every `errors.md` in every session directory
2. Extracts keywords from error titles and bodies
3. Groups by recurring keywords appearing across ≥2 sessions
4. Outputs a report: pattern name, occurrence count, which sessions, examples

**Cron:** Weekly Sunday 10:00 AM — auto-distill + agent writes findings to `notes/permanent-knowledge.md`.

## Context Briefing (Token Optimization)

`context_brief("topic")` returns a focused briefing for a specific project/topic, loading ONLY what's relevant:

```
Before (no briefing):           After (context_brief):
  All MEMORY.md                     MEMORY.md (tiny)
  All session files                 Only 1-5 relevant sessions
  All project entries               Only matching projects
  All errors                        Only topic-related errors
  ~8K token overhead                ~1K token overhead
```

**What it returns:**
1. Relevant sessions (by topic match) with overview summaries
2. Matching project entries from project-index.md
3. Top 5 errors from matching sessions

**When to use:**
- Before starting work on a specific project — load only that project's context
- When user says "continue work on X" — find the relevant session history
