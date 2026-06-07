# Project & Environment Tracking

## project-index.md

Catalog of ALL user projects at `~/.hermes/notes/project-index.md`. Update proactively when:
- User mentions a new project path
- User creates a new directory for work
- User asks "where is project X?"
- A project is deleted or moved (mark as ARCHIVED)

Format: markdown tables grouped by category with project name, path, type, and notes.

## environment.md

Catalog of installed software at `~/.hermes/notes/environment.md`. Update when:
- User installs new software (pip install, npm install, apt install, etc.)
- User mentions a tool or version
- User asks "what version of X do I have?"

Format: markdown tables grouped by category.

## Directory Integrity MCP

Server at `~/.hermes/notes/mcp-servers/directory-integrity/server.py` provides these tools:

### Integrity Tools

| Tool | Purpose |
|------|---------|
| `check_project_paths` | Verify all paths in project-index.md exist |
| `check_environment` | Verify all tools in environment.md are available on PATH |
| `list_projects` | List all tracked projects with live status |
| `get_project_health` | Git status, freshness (>180d = abandoned), file count/size |

### When to Use

- Before starting work on a project → `check_project_paths` + `get_project_health`
- After installing software → `check_environment`
- User asks "what projects do I have?" → `list_projects`
- Periodically assess project portfolio → `get_project_health()`
