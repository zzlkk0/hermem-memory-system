#!/usr/bin/env python3
"""MCP server for directory integrity, backup, and project environment management.

Tools:
  - check_project_paths: Verify all paths in project-index.md exist on disk
  - check_environment: Verify all tools in environment.md are available
  - list_projects: Return a summary of all tracked projects
  - backup_notes: Create tar.gz backup of notes/ directory
  - list_backups: List all existing backups with sizes and dates
  - restore_backups: Restore notes/ from a backup (safety: backups current state first)
  - prune_backups: Keep only last N backups, delete older ones
"""

import glob
import os
import re
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HERMES_HOME = os.path.expanduser("~/.hermes")
NOTES_DIR = os.path.join(HERMES_HOME, "notes")
BACKUPS_DIR = os.path.join(HERMES_HOME, "backups")
PROJECT_INDEX = os.path.join(NOTES_DIR, "project-index.md")
ENVIRONMENT_NOTE = os.path.join(NOTES_DIR, "environment.md")
DEFAULT_KEEP = 10

app = FastMCP("directory-integrity")


def expand_path(raw: str) -> str:
    return os.path.expanduser(os.path.expandvars(raw))


def parse_project_paths(content: str) -> list[dict]:
    projects = []
    current_section = ""
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## "):
            current_section = line.replace("## ", "").strip()
        if line.startswith("|") and "~/" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                path = ""
                for p in parts[1:]:
                    if p.startswith("~") or p.startswith("/"):
                        path = p
                        break
                if path:
                    projects.append({"name": name, "path": expand_path(path), "section": current_section})
    return projects


def parse_env_commands(content: str) -> list[dict]:
    commands = []
    current_section = ""
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## "):
            current_section = line.replace("## ", "").strip()
        if line.startswith("|") and "`" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 1:
                match = re.search(r"`([^`]+)`", parts[0])
                if match:
                    commands.append({"command": match.group(1), "section": current_section})
    return commands


def read_file_safe(path: str) -> str | None:
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return None


def format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ── Integrity Tools ──────────────────────────────────────────

@app.tool()
def check_project_paths() -> str:
    """Check if all project paths in project-index.md still exist on disk."""
    content = read_file_safe(PROJECT_INDEX)
    if content is None:
        return f"ERROR: {PROJECT_INDEX} not found. Create it first."

    projects = parse_project_paths(content)
    if not projects:
        return "No project paths found in project-index.md."

    ok, missing, broken = [], [], []
    for proj in projects:
        path = proj["path"]
        if os.path.exists(path):
            if os.path.isdir(path):
                ok.append(proj)
            else:
                broken.append({**proj, "reason": "not a directory"})
        else:
            missing.append({**proj, "reason": "path not found"})

    lines = [f"# Project Integrity Check -- {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    lines.append(f"Total: {len(projects)} | OK: {len(ok)} | Missing: {len(missing)} | Broken: {len(broken)}")

    if ok:
        lines.append("\n## OK")
        for p in ok:
            lines.append(f"  + {p['name']}: {p['path']}")
    if missing:
        lines.append("\n## MISSING")
        for p in missing:
            lines.append(f"  - {p['name']}: {p['path']} -- {p['reason']}")
    if broken:
        lines.append("\n## BROKEN")
        for p in broken:
            lines.append(f"  ! {p['name']}: {p['path']} -- {p['reason']}")
    if not missing and not broken:
        lines.append("\nAll project paths verified.")

    return "\n".join(lines)


@app.tool()
def check_environment() -> str:
    """Check if tools/commands in environment.md are still available on PATH."""
    content = read_file_safe(ENVIRONMENT_NOTE)
    if content is None:
        return f"ERROR: {ENVIRONMENT_NOTE} not found. Create it first."

    commands = parse_env_commands(content)
    if not commands:
        return "No commands found in environment.md."

    ok, missing = [], []
    for entry in commands:
        cmd = entry["command"]
        if shutil.which(cmd):
            ok.append(entry)
        else:
            missing.append(entry)

    lines = [f"# Environment Check -- {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    lines.append(f"Total: {len(commands)} | Available: {len(ok)} | Missing: {len(missing)}")

    if ok:
        lines.append("\n## Available")
        for e in ok:
            lines.append(f"  + {e['command']}: {shutil.which(e['command'])}")
    if missing:
        lines.append("\n## MISSING")
        for e in missing:
            lines.append(f"  - {e['command']}: not found on PATH")

    return "\n".join(lines)


@app.tool()
def list_projects() -> str:
    """Return a summary of all tracked projects from project-index.md."""
    content = read_file_safe(PROJECT_INDEX)
    if content is None:
        return f"ERROR: {PROJECT_INDEX} not found."

    projects = parse_project_paths(content)
    if not projects:
        return "No projects found."

    lines = [f"# Projects ({len(projects)})"]
    current_section = ""
    for p in projects:
        if p["section"] != current_section:
            current_section = p["section"]
            lines.append(f"\n## {current_section}")
        exists = "+" if os.path.exists(p["path"]) else "-"
        lines.append(f"  {exists} {p['name']}: {p['path']}")

    return "\n".join(lines)


# ── Backup Tools ─────────────────────────────────────────────

@app.tool()
def backup_notes() -> str:
    """Create a tar.gz backup of the entire notes/ directory.
    Saves to ~/.hermes/backups/notes-backup-YYYYMMDD-HHMMSS.tar.gz"""
    os.makedirs(BACKUPS_DIR, exist_ok=True)

    if not os.path.isdir(NOTES_DIR):
        return "ERROR: notes/ directory does not exist."

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"notes-backup-{timestamp}.tar.gz"
    backup_path = os.path.join(BACKUPS_DIR, backup_name)

    with tarfile.open(backup_path, "w:gz") as tar:
        tar.add(NOTES_DIR, arcname="notes")

    size = os.path.getsize(backup_path)
    return f"Backup created: {backup_path}\nSize: {format_size(size)}"


@app.tool()
def list_backups() -> str:
    """List all existing backups with size, date, and age."""
    os.makedirs(BACKUPS_DIR, exist_ok=True)

    backups = sorted(
        glob.glob(os.path.join(BACKUPS_DIR, "notes-backup-*.tar.gz")),
        key=os.path.getmtime, reverse=True,
    )

    if not backups:
        return f"No backups found in {BACKUPS_DIR}."

    now = datetime.now()
    lines = [f"# Backups ({len(backups)})"]

    for i, bp in enumerate(backups):
        name = os.path.basename(bp)
        size = format_size(os.path.getsize(bp))
        mtime = datetime.fromtimestamp(os.path.getmtime(bp))
        age = now - mtime
        if age.days > 0:
            age_str = f"{age.days}d ago"
        elif age.seconds > 3600:
            age_str = f"{age.seconds // 3600}h ago"
        else:
            age_str = f"{age.seconds // 60}m ago"
        marker = " (LATEST)" if i == 0 else ""
        lines.append(f"  {name} | {size} | {mtime.strftime('%Y-%m-%d %H:%M')} | {age_str}{marker}")

    return "\n".join(lines)


@app.tool()
def restore_backups(backup_filename: str = "") -> str:
    """Restore notes/ from a backup. Creates a safety backup of current notes first.
    Leave backup_filename empty to restore from the latest backup."""
    os.makedirs(BACKUPS_DIR, exist_ok=True)

    if backup_filename:
        backup_path = os.path.join(BACKUPS_DIR, backup_filename)
        if not os.path.exists(backup_path):
            return f"ERROR: {backup_path} not found. Use list_backups."
    else:
        backups = sorted(
            glob.glob(os.path.join(BACKUPS_DIR, "notes-backup-*.tar.gz")),
            key=os.path.getmtime, reverse=True,
        )
        if not backups:
            return "ERROR: No backups found."
        backup_path = backups[0]
        backup_filename = os.path.basename(backup_path)

    # Safety: backup current notes first
    safety_name = f"notes-safety-before-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
    safety_path = os.path.join(BACKUPS_DIR, safety_name)

    if os.path.isdir(NOTES_DIR):
        with tarfile.open(safety_path, "w:gz") as tar:
            tar.add(NOTES_DIR, arcname="notes")
        safety_note = f"Safety backup: {safety_path}"
    else:
        safety_note = "No existing notes/ to back up."

    # Restore
    if os.path.isdir(NOTES_DIR):
        shutil.rmtree(NOTES_DIR)
    os.makedirs(NOTES_DIR, exist_ok=True)

    with tarfile.open(backup_path, "r:gz") as tar:
        tar.extractall(path=os.path.dirname(NOTES_DIR))

    return f"Restored notes/ from: {backup_filename}\n{safety_note}"


@app.tool()
def prune_backups(keep: int = DEFAULT_KEEP) -> str:
    """Delete old backups, keeping only the most recent N (default: 10)."""
    os.makedirs(BACKUPS_DIR, exist_ok=True)

    backups = sorted(
        glob.glob(os.path.join(BACKUPS_DIR, "notes-backup-*.tar.gz")),
        key=os.path.getmtime, reverse=True,
    )

    if len(backups) <= keep:
        return f"{len(backups)} backups exist, keep={keep}. Nothing to prune."

    to_delete = backups[keep:]
    deleted = []
    for bp in to_delete:
        name = os.path.basename(bp)
        size = format_size(os.path.getsize(bp))
        os.remove(bp)
        deleted.append(f"  Deleted: {name} ({size})")

    kept = backups[:keep]
    lines = [f"Pruned {len(to_delete)} old backups. Keeping {len(kept)} most recent:"]
    for bp in kept:
        lines.append(f"  {os.path.basename(bp)} ({format_size(os.path.getsize(bp))})")
    lines.extend(deleted)
    lines.append(f"\nAuto-prune keeps last {keep} backups.")

    return "\n".join(lines)


# ── Knowledge Distillation ──────────────────────────────────

@app.tool()
def distill_knowledge(min_occurrences: int = 2) -> str:
    """Scan all session errors.md files and extract recurring patterns.
    Groups similar errors across sessions to identify knowledge worth
    preserving permanently.

    Args:
        min_occurrences: Minimum times an error pattern must appear (default: 2)."""
    sessions_dir = os.path.join(NOTES_DIR, "sessions")
    if not os.path.isdir(sessions_dir):
        return "No sessions/ directory found. Nothing to distill."

    # Collect all error entries
    all_errors = []
    session_list = []
    for session_name in sorted(os.listdir(sessions_dir)):
        session_path = os.path.join(sessions_dir, session_name)
        errors_file = os.path.join(session_path, "errors.md")
        if os.path.isfile(errors_file):
            content = Path(errors_file).read_text()
            # Extract numbered error entries: look for "## N. " or "### N. " patterns
            entries = []
            current_entry = None
            for line in content.split("\n"):
                line_stripped = line.strip()
                if line_stripped.startswith("## ") and line_stripped[3].isdigit():
                    if current_entry:
                        entries.append(current_entry)
                    current_entry = {"title": line_stripped, "body": ""}
                elif current_entry:
                    current_entry["body"] += line + "\n"
            if current_entry:
                entries.append(current_entry)

            for e in entries:
                all_errors.append({
                    "session": session_name,
                    "title": e["title"],
                    "body": e["body"].strip(),
                })
            session_list.append(session_name)

    if not all_errors:
        return f"Scanned {len(session_list)} sessions. No errors found to distill."

    # Simple pattern extraction: extract key phrases (2-4 word sequences)
    import collections
    pattern_groups = collections.defaultdict(list)

    for err in all_errors:
        # Extract significant keywords: things in backticks, "Error:", "Failed", etc.
        keywords = set()
        for match in re.finditer(r"`([^`]+)`", err["title"] + " " + err["body"]):
            keywords.add(match.group(1).lower())
        for match in re.finditer(r"(Error|Failed|BUG|FIX|Pattern):\s*([^\n]+)", err["body"]):
            keywords.add(match.group(2).strip().lower())

        # Group by the most specific keyword found
        for kw in keywords:
            if len(kw) > 5:  # meaningful keyword
                pattern_groups[kw].append(err)

    # Filter to patterns that appear across multiple sessions
    distilled = {}
    for pattern, errors in pattern_groups.items():
        sessions_involved = {e["session"] for e in errors}
        if len(sessions_involved) >= min_occurrences:
            distilled[pattern] = {
                "count": len(errors),
                "sessions": sorted(sessions_involved),
                "examples": [e["title"] for e in errors[:2]],
            }

    if not distilled:
        return f"Scanned {len(session_list)} sessions ({len(all_errors)} errors). No patterns with >= {min_occurrences} occurrences found yet. More sessions needed."

    # Build report
    lines = [f"# Knowledge Distillation Report -- {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    lines.append(f"Sessions scanned: {len(session_list)} | Errors found: {len(all_errors)} | Patterns: {len(distilled)}")
    lines.append("")

    for pattern, info in sorted(distilled.items(), key=lambda x: -x[1]["count"]):
        lines.append(f"## Pattern: `{pattern}`")
        lines.append(f"Occurrences: {info['count']} | Sessions: {', '.join(info['sessions'])}")
        lines.append(f"Examples:")
        for ex in info["examples"]:
            lines.append(f"  - {ex}")
        lines.append("")

    suggestion = (
        "SUGGESTION: Save high-value patterns to `notes/permanent-knowledge.md`.\n"
        "The agent should review this report and write distilled knowledge entries."
    )
    lines.append(suggestion)

    return "\n".join(lines)


# ── Context Briefing ────────────────────────────────────────

@app.tool()
def context_brief(topic: str) -> str:
    """Return a compact briefing for a project or topic.
    Finds relevant sessions, project entries, and errors -- only what's needed.
    Use this BEFORE starting work on a project to load focused context.

    Args:
        topic: Project name, topic, or keyword (e.g., 'hermes-memory', 'GPT-SoVITS')."""
    sessions_dir = os.path.join(NOTES_DIR, "sessions")

    lines = [f"# Context Briefing: {topic}"]
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # 1. Find matching sessions
    relevant_sessions = []
    if os.path.isdir(sessions_dir):
        topic_lower = topic.lower()
        for session_name in sorted(os.listdir(sessions_dir), reverse=True):
            if topic_lower in session_name.lower():
                session_path = os.path.join(sessions_dir, session_name)

                # Read overview
                overview_file = os.path.join(session_path, "overview.md")
                overview = ""
                if os.path.isfile(overview_file):
                    overview = Path(overview_file).read_text()[:500]

                relevant_sessions.append({
                    "name": session_name,
                    "path": session_path,
                    "overview": overview,
                    "has_errors": os.path.isfile(os.path.join(session_path, "errors.md")),
                    "has_timeline": os.path.isfile(os.path.join(session_path, "timeline.md")),
                })

    if relevant_sessions:
        lines.append(f"## Relevant Sessions ({len(relevant_sessions)})")
        for s in relevant_sessions[:5]:  # top 5
            lines.append(f"\n### {s['name']}")
            if s["overview"]:
                first_line = s["overview"].split("\n")[0] if s["overview"] else "(no overview)"
                lines.append(f"  {first_line}")
            if s["has_errors"]:
                lines.append(f"  [has errors.md]")
            if s["has_timeline"]:
                lines.append(f"  [has timeline.md]")
        if len(relevant_sessions) > 5:
            lines.append(f"\n  ... and {len(relevant_sessions) - 5} more sessions")
    else:
        lines.append("No matching sessions found.")

    # 2. Find matching projects in project-index
    lines.append("")
    pi_content = read_file_safe(PROJECT_INDEX)
    if pi_content:
        topic_lower = topic.lower()
        matching_projects = []
        for line in pi_content.split("\n"):
            if line.startswith("|") and topic_lower in line.lower():
                matching_projects.append(line.strip())

        if matching_projects:
            lines.append(f"## Matching Projects ({len(matching_projects)})")
            for mp in matching_projects:
                lines.append(f"  {mp}")
        else:
            lines.append("No matching projects in project-index.md.")

    # 3. Known errors related to topic
    if relevant_sessions:
        lines.append("")
        lines.append("## Related Errors")
        error_count = 0
        for s in relevant_sessions[:5]:
            errors_file = os.path.join(s["path"], "errors.md")
            if os.path.isfile(errors_file):
                content = Path(errors_file).read_text()
                # Extract error titles
                for match in re.finditer(r"^## \d+\. (.+)$", content, re.MULTILINE):
                    lines.append(f"  [{s['name']}] {match.group(1)}")
                    error_count += 1
                    if error_count >= 5:
                        break
            if error_count >= 5:
                break
        if error_count == 0:
            lines.append("  No errors recorded for this topic.")

    lines.append("")
    lines.append("NEXT: Read full session files with read_file for detailed context.")
    lines.append(f"  Sessions found: {[s['name'] for s in relevant_sessions[:5]]}")

    return "\n".join(lines)


# ── Project Health ──────────────────────────────────────────

def _get_git_info(project_path: str) -> dict:
    """Get git status for a project directory. Returns {} if not a git repo."""
    import subprocess
    git_dir = os.path.join(project_path, ".git")
    if not os.path.isdir(git_dir):
        return {}

    def run_git(*args):
        try:
            r = subprocess.run(
                ["git", "-C", project_path] + list(args),
                capture_output=True, text=True, timeout=10
            )
            return r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            return ""

    branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    last_commit = run_git("log", "-1", "--format=%ar by %an")
    last_commit_iso = run_git("log", "-1", "--format=%aI")
    status_short = run_git("status", "--short")
    dirty_count = len([l for l in status_short.split("\n") if l.strip()]) if status_short else 0
    behind = run_git("rev-list", "--count", "HEAD..@{u}")
    ahead = run_git("rev-list", "--count", "@{u}..HEAD")

    return {
        "branch": branch or "?",
        "last_commit": last_commit or "no commits",
        "last_commit_iso": last_commit_iso,
        "dirty_files": dirty_count,
        "behind_remote": int(behind) if behind.isdigit() else 0,
        "ahead_remote": int(ahead) if ahead.isdigit() else 0,
    }


def _get_file_stats(project_path: str) -> dict:
    """Get file count and total size for a project directory."""
    total_files = 0
    total_size = 0
    try:
        for root, dirs, files in os.walk(project_path):
            # Skip .git and __pycache__
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
            total_files += len(files)
            for f in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    except Exception:
        pass
    return {"files": total_files, "size_bytes": total_size}


@app.tool()
def get_project_health(project_name_or_path: str = "") -> str:
    """Check the health of a project: git status, freshness, file stats.
    Flags abandoned projects (>6 months untouched).

    Args:
        project_name_or_path: Project name (from project-index) or absolute path.
                             Leave empty to check ALL projects in project-index."""
    projects_to_check = []

    if project_name_or_path:
        # Check if it's a direct path
        expanded = expand_path(project_name_or_path)
        if os.path.isdir(expanded):
            projects_to_check = [{"name": os.path.basename(expanded), "path": expanded}]
        else:
            # Look up in project index
            content = read_file_safe(PROJECT_INDEX)
            if content:
                for proj in parse_project_paths(content):
                    if project_name_or_path.lower() in proj["name"].lower():
                        projects_to_check.append(proj)
            if not projects_to_check:
                return f"Project '{project_name_or_path}' not found. Use list_projects to see tracked projects."
    else:
        # Check ALL projects
        content = read_file_safe(PROJECT_INDEX)
        if content:
            projects_to_check = parse_project_paths(content)

    if not projects_to_check:
        return "No projects to check. Populate project-index.md first."

    now = datetime.now()
    lines = [f"# Project Health Report -- {now.strftime('%Y-%m-%d %H:%M')}"]
    lines.append(f"Projects checked: {len(projects_to_check)}")
    lines.append("")

    healthy, warning, abandoned, missing = [], [], [], []

    for proj in projects_to_check:
        path = proj["path"]
        name = proj["name"]

        if not os.path.isdir(path):
            missing.append({**proj, "reason": "directory not found"})
            continue

        git_info = _get_git_info(path)
        file_stats = _get_file_stats(path)

        # Freshness: use git last commit time or filesystem mtime
        mtime = os.path.getmtime(path)
        mtime_dt = datetime.fromtimestamp(mtime)
        age_days = (now - mtime_dt).days

        # Health assessment
        issues = []
        if git_info:
            if git_info["dirty_files"] > 0:
                issues.append(f"{git_info['dirty_files']} uncommitted changes")
            if git_info["behind_remote"] > 0:
                issues.append(f"{git_info['behind_remote']} commits behind remote")

        status = {
            "name": name,
            "path": path,
            "age_days": age_days,
            "files": file_stats["files"],
            "size": format_size(file_stats["size_bytes"]),
            "git": git_info,
            "issues": issues,
        }

        if age_days > 180:
            abandoned.append(status)
        elif issues:
            warning.append(status)
        else:
            healthy.append(status)

    # Report
    if healthy:
        lines.append("## Healthy")
        for s in healthy:
            git_line = ""
            if s["git"]:
                git_line = f" | git: {s['git']['branch']} ({s['git']['last_commit']})"
            lines.append(f"  + {s['name']}: {s['files']} files, {s['size']}, {s['age_days']}d old{git_line}")
        lines.append("")

    if warning:
        lines.append("## Needs Attention")
        for s in warning:
            git_line = f" | git: {s['git'].get('branch', '?')}" if s["git"] else ""
            lines.append(f"  ! {s['name']}: {', '.join(s['issues'])}{git_line}")
        lines.append("")

    if abandoned:
        lines.append("## Abandoned (>180 days)")
        for s in abandoned:
            lines.append(f"  ~ {s['name']}: {s['age_days']}d since last touch | {s['files']} files | {s['size']}")
            lines.append(f"    Path: {s['path']}")
        lines.append("")
        lines.append("SUGGESTION: Consider archiving abandoned projects or removing them from project-index.")

    if missing:
        lines.append("## Missing")
        for m in missing:
            lines.append(f"  - {m['name']}: {m['path']} -- {m['reason']}")

    if not warning and not abandoned and not missing:
        lines.append("All projects healthy.")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run()
