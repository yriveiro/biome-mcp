# Configuration

biome-mcp is configured through environment variables and the way your MCP
client launches it. There is no config file.

## Environment Variables

All variables are optional and prefixed with `BIOME_MCP_`.

| Variable | Default | Purpose |
|---|---|---|
| `BIOME_MCP_LOG_LEVEL` | `INFO` | Logging level for stderr (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `BIOME_MCP_PROJECT_DIR` | server working directory | Root directory checks run against |
| `BIOME_MCP_COMMAND_PREFIX` | `bunx @biomejs/biome` | How Biome is invoked; empty means `biome` from `PATH` |
| `BIOME_MCP_COMMAND_TIMEOUT` | none | Timeout in seconds for each Biome command |
| `BIOME_MCP_CACHE_DIR` | `~/.cache/biome-mcp/docs` | Where the documentation cache is stored |

Example:

```sh
BIOME_MCP_LOG_LEVEL=DEBUG \
BIOME_MCP_PROJECT_DIR=/path/to/project \
BIOME_MCP_COMMAND_TIMEOUT=120 \
uv run biome-mcp
```

### `BIOME_MCP_COMMAND_PREFIX` in detail

The prefix is split on whitespace, so it can be a full command line:

| Value | Effect |
|---|---|
| `bunx @biomejs/biome` (default) | Runs Biome through bun, resolving a project-local or cached package |
| *(empty string)* | Runs `biome` directly from `PATH` |
| `npx @biomejs/biome` | Uses npm's runner instead of bun's |
| `node_modules/.bin/biome` | Uses a locally installed binary |

If the command is missing, tools fail with a `ToolNotFoundError` that tells
the model to install Biome or change the prefix.

## Client Setup

Point your MCP client at the `biome-mcp` command. Because `uvx` may not be on
the client's `PATH` in every environment, launching via `uv run` from the
project directory is the more predictable option.

### opencode

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

### Claude Desktop

```json
{
  "mcpServers": {
    "biome-mcp": {
      "command": "uvx",
      "args": ["biome-mcp"]
    }
  }
}
```

### Generic stdio

```json
{
  "command": "uvx",
  "args": ["biome-mcp"],
  "cwd": "/path/to/project"
}
```

Setting `cwd` (or `BIOME_MCP_PROJECT_DIR`) anchors checks to the project root,
which keeps reported paths relative and readable.

## Agent Skill

If your agent discovers skills in `.agents/skills`, install the bundled
`biome` skill so the model knows when and how to use the server:

```sh
uvx biome-mcp skill install biome --target .
```

This copies `SKILL.md` and its references into
`.agents/skills/biome/`. Re-run with `--force` to overwrite.

See `biome-mcp skill --help` for details.

## Prerequisites

- **Biome** — the server needs a working `bunx @biomejs/biome` (or your
  configured prefix). Install per project: `bun add --dev @biomejs/biome`.
- **Python 3.14+** and `uv` (or a virtualenv with the project installed).
- **Network on first run** — the documentation cache fetches biomejs.dev
  pages once; afterwards it is served from disk.

## Failure Modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `Executable not found: bunx` | bun is not installed | Install bun, or set `BIOME_MCP_COMMAND_PREFIX` to a local binary |
| Checks always target the wrong project | Server started in the wrong `cwd` | Set `BIOME_MCP_PROJECT_DIR` or client `cwd` |
| `No matching documentation resources found.` | Cache not initialized (no network at startup) | Call `update_cache`, then retry |
| Command times out | `BIOME_MCP_COMMAND_TIMEOUT` too low | Raise the timeout |

Next: [Tools & Resources](tools.md) — the full catalog.
