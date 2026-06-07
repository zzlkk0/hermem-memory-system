# Contributing

Contributions are welcome! Here's how:

## Ways to Contribute

- **Bug reports** — Open an issue with steps to reproduce
- **Feature ideas** — Open an issue describing the use case
- **Code** — PRs for MCP tools, skill improvements, documentation
- **Examples** — Share your session memory structures

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/hermes-memory-system.git
cd hermes-memory-system
pip install -e ".[dev]"
```

## Testing the MCP Server

```bash
python3 mcp/directory-integrity/server.py &
# The server starts in stdio mode — it's tested through Hermes's MCP client
```

## Skill Guidelines

- Keep SKILL.md concise (4-5K chars max)
- Put detailed docs in `references/`
- Follow the [skill authoring guide](https://hermes-agent.nousresearch.com/docs/)

## PR Checklist

- [ ] MCP server passes syntax check: `python3 -c "import py_compile; py_compile.compile('mcp/directory-integrity/server.py', doraise=True)"`
- [ ] Skill validates: YAML frontmatter parses, `name` and `description` present
- [ ] README updated if adding new features
