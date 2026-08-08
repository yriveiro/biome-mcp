# Development

Guide for working on biome-mcp: setup, layout, conventions, and how to add a
new tool.

## Setup

```sh
uv sync --extra dev
```

This installs the project and dev dependencies (`pytest`, `ruff`, `ty`,
`pyproject-fmt`).

## Quality Gates

Run all three before pushing:

```sh
uv run ruff check          # lint
uv run ruff format --check # formatting
uv run ty check            # type checking
uv run pytest              # tests
```

`pyproject-fmt` keeps `pyproject.toml` tidy:

```sh
uv run pyproject-fmt pyproject.toml
```

## Project Layout

```
src/biome_mcp/
├── __init__.py        # __version__
├── app.py             # FastMCP app + lifespan (ServerContext wiring)
├── cli/               # Typer CLI: `biome-mcp` (server) and `skill install`
├── context.py         # ServerContext dataclass + services(ctx) helper
├── docs/              # documentation cache: fetch, parse, search
├── errors.py          # ToolError, ToolNotFoundError
├── formatting.py      # parse Biome JSON + compact formatting
├── models.py          # Pydantic models (CheckResult, BiomeError, ...)
├── resources/         # biome:docs:// MCP resources
├── runner.py          # ToolRunner subprocess logic + git helpers
├── server.py          # imports tools/resources, exposes `mcp`
├── settings.py        # pydantic-settings BaseSettings
├── skills/            # bundled agent skill
└── tools/             # MCP tool registration (checks, docs)
tests/
├── test_cli.py        # CLI behavior
├── test_docs.py       # docs parsing and cache
├── test_runner.py     # parsing, formatting, runner
└── test_skill_cli.py  # skill install command
```

## How a Tool Is Registered

Tools are plain functions decorated with `@app.tool` (or `@app.resource` /
`@app.prompt`) in `biome_mcp/tools/`. `server.py` imports the package so the
registrations happen on import:

```python
# biome_mcp/tools/checks.py
@app.tool(name="biome_check", annotations=READ_ONLY)
def biome_check(ctx: Context, paths: list[str] | None = None, ...) -> CheckResult:
    server = services(ctx)
    ...
    return _result(server.runner.biome_check(targets, server.project_dir))
```

The `services(ctx)` helper returns the typed `ServerContext` from the
lifespan, so handlers never construct their own runner or resolve the project
directory.

## Adding a New Check Tool

1. Add a method to `ToolRunner` in `runner.py` that builds the command, runs
   it, parses the output, and returns a `ToolResult`.
2. If the output needs new parsing or formatting, extend `formatting.py` and
   its unit tests in `test_runner.py`.
3. Add the `@app.tool` handler in `tools/checks.py` using `services(ctx)`
   and `_result(...)`.
4. Document the tool in `docs/tools.md` and in the skill catalog
   (`src/biome_mcp/skills/biome/references/MCP-TOOLS.md`).

## Conventions

- **Pydantic everywhere.** Request/response shapes are `BaseModel`s; settings
  come from `pydantic-settings` (`BIOME_MCP_*` prefix).
- **Never write to source files.** Check tools are read-only; formatting is
  reported, not applied.
- **Preserve `exit_code`.** Filters may hide diagnostics, but the model must
  always be able to tell a clean run from a failed one.
- **Keep output compact.** The formatting layer is the product — grouped
  layout for small runs, aggregate rollups for large ones.
- **Log to stderr.** stdout carries MCP JSON-RPC; never log there.
