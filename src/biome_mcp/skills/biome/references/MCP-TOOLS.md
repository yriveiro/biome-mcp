# biome-mcp Tool Catalog

All tools run through the biome-mcp server. Argument names match the MCP tool
signatures exactly. All check tools are **read-only** — they never write to
source files, never apply fixes, and do not modify the project. Check tools run
in the project working directory; use `paths` or `changed_only` to scope the
targets.

## Checks (`check` domain)

| Tool | Signature | Behavior |
|---|---|---|
| `biome_check` | `biome_check(paths?: list[str], changed_only?: bool)` | Run Biome formatting, lint, and assist checks (read-only) |
| `biome_lint` | `biome_lint(paths?: list[str], level: "all"\|"error"\|"warning", changed_only?: bool)` | Run lint diagnostics, filtered by severity (read-only) |
| `biome_format` | `biome_format(paths?: list[str], changed_only?: bool)` | Format-only check (`--linter-enabled=false --assist-enabled=false`) (read-only) |

Check notes:

- Every result includes `exit_code`, `output`, `issues`, `fixable`, `warnings`,
  `saved_tokens`, and `savings_percent`. `exit_code == 0` means clean; inspect
  it, never trust the presence of output alone.
- `issues` counts findings (lint issues or unformatted files, depending on the
  tool); `fixable` is best-effort because Biome JSON lacks a reliable explicit
  fixable field.
- `paths` accepts files, directories, or glob patterns (e.g.
  `paths=["src/**/*.ts"]`). Empty `paths` checks the whole project.
- `changed_only=true` targets staged, unstaged, and untracked web files in the
  current Git repository, and takes precedence over `paths`. When no modified
  web files exist, the check succeeds with `No modified web files found.`
- `biome_lint(level=...)` filters diagnostics after the run; the exit code is
  unchanged. `"all"` shows every level, `"error"` only errors, `"warning"`
  errors and warnings.

## Docs and self (`docs_tools` domain)

| Tool | Signature | Behavior |
|---|---|---|
| `search_documentation` | `search_documentation(query: str)` | Search cached Biome docs (read-only) |
| `update_cache` | `update_cache(force?: bool)` | Refresh cached CLI, configuration, and linter docs |

## Resources

| Resource | Contents |
|---|---|
| `biome:docs://{section}` | Overview of a docs section (`cli`, `configuration`, `linter`) |
| `biome:docs://{section}/{command}` | Docs for one command or rule in a section |
| `biome:docs://{section}/{command}/{subsection}` | Subsection of a command or rule |

Sections: `cli`, `configuration`, `linter`. Resources return JSON with the
parsed documentation elements.

## Prompt

| Prompt | Signature | Behavior |
|---|---|---|
| `summarize_docs` | `summarize_docs(section?)` | Build a summary prompt over the cached Biome docs |
