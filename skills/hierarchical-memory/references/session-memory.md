# Session Memory Management

## When to Create a Session Directory

Create `~/.hermes/notes/sessions/<YYYYMMDD>-<topic-slug>/` when:
- The conversation turns substantive (not just brief Q&A)
- The user states a goal or project
- Work spans 5+ tool calls

## Directory Structure

```
~/.hermes/notes/sessions/<YYYYMMDD>-<topic-slug>/
├── overview.md    — What this conversation is about, goals, key decisions
├── timeline.md    — Chronological: what user asked, what agent did
├── errors.md      — Errors encountered + how they were fixed (patterns to avoid)
└── reference.md   — IDs, tokens, configs, rarely-used but critical data
```

## Naming Convention

`<YYYYMMDD>-<topic-slug>/` — topic-slug: lowercase, hyphens, ≤40 chars. Extract from the user's first substantive request.

Examples: `20260608-hermes-memory-design`, `20260608-fix-auth-bug`.

**Resolving the topic:**
1. Look at the user's FIRST message that starts substantive work
2. Extract 2-5 key words
3. If ambiguous, ask the user: "What should I call this session?" (use clarify tool)
4. If the user has a project name, use it

## Conflict Resolution

```
Does notes/sessions/<date>-<topic>/ exist?
├─ NO  → Create it fresh
└─ YES → Is today's date in the name?
         ├─ YES → Same topic, same day → RESUME: read existing files, append
         └─ NO  → Different day, same topic → create new dir with today's date
```

**Never overwrite** an existing session directory. Always append.

## Discovery

Before creating a new session directory, list existing ones:
```bash
ls ~/.hermes/notes/sessions/
```

## Cleanup

```
For each session directory:
├─ last modified > 30 days ago → archive (move to notes/sessions/.archive/)
├─ overview.md says "completed" + > 14 days ago → archive
└─ otherwise → keep active
```

Use `mv`, not `rm` — nothing is ever deleted, only relocated.

## Proactive Read/Write Rules

**At session start:**
1. Create directory + overview.md (goals, context) + reference.md (IDs/configs)

**Throughout the session:**
- Major action (3+ tool calls, completed task, error fixed) → append to `timeline.md`
- Error fixed → add to `errors.md`: what broke, root cause, fix, pattern to avoid
- IDs/tokens/paths mentioned → update `reference.md`
- Decisions made → update `overview.md`

**Before ending a turn that made progress:**
- Check if timeline/errors/overview need updating

## Forgetting Rules

Apply staleness to prevent bloat:

| Data type | Keep if... | Remove when... |
|-----------|-----------|----------------|
| Timeline entry | Key decision or turning point | Trivial intermediate step |
| Error entry | Root cause unknown or pattern may recur | One-off typo / user mistake |
| Reference data | Still valid config/path/ID | Config has changed |
| Overview goals | Goal is still active | Goal completed or abandoned |

When session directory exceeds ~10KB, review and prune. Mark removed entries with `~~strikethrough~~`.

## Integration with Global Memory

When a session uncovers a fact that matters beyond this conversation:
1. Write the ONE-LINE fact to MEMORY.md (via memory tool)
2. Reference the session: "Has a Telegram bot (see notes/sessions/20260608-...)"
3. Do NOT duplicate — MEMORY.md is the index, session files are the archive
