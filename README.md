# biome-mcp

A Model Context Protocol (MCP) server for running [Biome](https://biomejs.dev/)
on TypeScript and web projects with token-efficient output.

## Overview

biome-mcp gives LLMs direct access to Biome's formatting, linting, and assist
checks without shelling out to the CLI. Diagnostic output is parsed
structurally and reduced to compact, grouped results before it reaches the
model, so long check runs stay readable and cheap.

The server also caches the Biome CLI, configuration, and JavaScript linter
documentation and exposes it as searchable resources.

## Features

- **biome_check** - Run formatting, linting, and assist checks in one pass
- **biome_lint** - Lint-only diagnostics with an `all` / `error` / `warning` severity filter
- **biome_format** - Verify formatting without modifying files
- **Structured parsing** - `json-pretty` output avoids fragile parsing of human-readable text
- **Adaptive aggregation** - large result sets include rule/file rollups before flat diagnostics
- **changed_only** - Check only staged, unstaged, and untracked web files (`*.ts`, `*.tsx`, `*.js`, ...)
- **Documentation cache** - Searchable, version-aware cache of Biome docs
- **Bundled Agent Skill** - Install `biome-mcp` skill into `.agents/skills` with one command

## How It Works

biome-mcp implements the [Model Context Protocol](https://modelcontextprotocol.io)
to expose Biome through read-only tools. Every check tool returns a
`CheckResult` with compact `output` text and the underlying `exit_code`; it
never writes to source files.

| Tool | What it runs |
|---|---|
| `biome_check(paths?, changed_only?)` | `biome check` (format + lint + assist) |
| `biome_lint(paths?, level?, changed_only?)` | `biome lint`, filtered by severity |
| `biome_format(paths?, changed_only?)` | `biome check` with linter and assist disabled |
| `search_documentation(query)` | Search the cached Biome docs |
| `update_cache(force?)` | Refresh the cached docs from biomejs.dev |

## Usage

To start the server:

```bash
uvx biome-mcp
```

Or from a checkout:

```bash
uv run biome-mcp
```

Configure an MCP client to launch the server in the project directory to check,
e.g. for opencode:

```json
{
  "mcp": {
    "biome-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["biome-mcp"]
    }
  }
}
```

The server checks the project in its working directory. To target another
directory, set `BIOME_MCP_PROJECT_DIR`.

Biome is invoked through `bunx @biomejs/biome` by default. Set
`BIOME_MCP_COMMAND_PREFIX` to use another project-local invocation (see
`docs/configuration.md`).

### Agent Skill

Install the bundled `biome` skill in a project when the agent client discovers
skills from `.agents/skills`:

```bash
uvx biome-mcp skill install biome --target .
```

The skill directs agents to the server's read-only tools and the cached
documentation resources.

## Configuration

Environment variables, all optional:

| Variable | Default | Purpose |
|---|---|---|
| `BIOME_MCP_LOG_LEVEL` | `INFO` | Logging level (stderr) |
| `BIOME_MCP_PROJECT_DIR` | server working directory | Project directory to check |
| `BIOME_MCP_COMMAND_PREFIX` | `bunx @biomejs/biome` | Invocation for Biome; empty string uses binaries from `PATH` |
| `BIOME_MCP_COMMAND_TIMEOUT` | none | Optional per-command timeout in seconds |
| `BIOME_MCP_CACHE_DIR` | `~/.cache/biome-mcp/docs` | Documentation cache location |

## Documentation

See the [docs](docs/README.md) for the full picture:

- [Architecture](docs/architecture.md) - components, request flow, and output processing
- [Configuration](docs/configuration.md) - environment variables and client setup
- [Tools & resources](docs/tools.md) - complete catalog with signatures
- [Development](docs/development.md) - layout, tests, and contributing

## Development

This project is built with [FastMCP](https://github.com/PrefectHQ/fastmcp) and
[uv](https://github.com/astral-sh/uv).

```bash
uv sync --extra dev
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest
```
