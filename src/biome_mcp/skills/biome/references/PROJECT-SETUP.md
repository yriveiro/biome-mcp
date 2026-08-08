# Biome Project Setup Reference

## Install Biome

```bash
npm install --save-dev @biomejs/biome
# or with bun
bun add --dev @biomejs/biome
# or globally
npm install -g @biomejs/biome
```

biome-mcp invokes `bunx @biomejs/biome` by default. To use a different
project-local invocation, set `BIOME_MCP_COMMAND_PREFIX`:

```bash
export BIOME_MCP_COMMAND_PREFIX="bunx @biomejs/biome"
```

## Initialize a Config File

```bash
bunx @biomejs/biome init
```

Generates `biome.json` in the project root with recommended defaults. Override
rules, formatter, and linter settings there.

## Configure the Server

```bash
BIOME_MCP_LOG_LEVEL=INFO \      # logging on stderr (default INFO)
BIOME_MCP_PROJECT_DIR=/path/to/project \  # project root (default: CWD)
BIOME_MCP_COMMAND_PREFIX="bunx @biomejs/biome" \  # biome invocation
BIOME_MCP_COMMAND_TIMEOUT=120 \ # per-command timeout in seconds
BIOME_MCP_CACHE_DIR=/custom/cache \  # docs cache location
uv run biome-mcp
```

The server runs checks in the project directory and relativizes diagnostic
paths to it.

## Target Checks

- Whole project: omit `paths`
- Specific files or globs: `paths=["src/**/*.ts"]`
- Only modified files: `changed_only=true` (staged, unstaged, and untracked
  web files in the current Git repository; takes precedence over `paths`)
