# Tools & Resources

Every tool, resource, and prompt exposed by the server, with exact signatures.
All check tools are **read-only**: they never write files, apply fixes, or
modify the project.

## Check Tools

| Tool | Signature | Runs |
|---|---|---|
| `biome_check` | `biome_check(paths?: list[str], changed_only?: bool)` | `biome check` — formatting, linting, and assist |
| `biome_lint` | `biome_lint(paths?: list[str], level: "all"\|"error"\|"warning", changed_only?: bool)` | `biome lint`, filtered by severity |
| `biome_format` | `biome_format(paths?: list[str], changed_only?: bool)` | `biome check` with linter and assist disabled |

### Arguments

| Argument | Meaning |
|---|---|
| `paths` | Files, directories, or glob patterns (`paths=["src/**/*.ts"]`). Empty checks the whole project. |
| `changed_only` | Check only staged, unstaged, and untracked web files in git. Takes precedence over `paths`. |
| `level` | `"all"` shows every severity, `"error"` only errors, `"warning"` errors and warnings. |

### Result fields

Every check tool returns:

| Field | Meaning |
|---|---|
| `output` | Compact diagnostics, ready to read |
| `exit_code` | Biome's real exit code — `0` means clean |
| `issues` | Number of findings (lint issues or unformatted files) |
| `fixable` | Findings with an available fix (best-effort) |
| `warnings` | Warning-level diagnostics |
| `saved_tokens` / `savings_percent` | Estimated output reduction |

Inspect `exit_code`, never rely on the presence of output: a severity filter
can produce empty output while the underlying check still failed.

### Notes

- `biome_lint(level=...)` filters after the run; the `exit_code` is
  unchanged.
- `changed_only` with no modified web files returns
  `No modified web files found.` with `exit_code=0`.
- Formatting is only *reported*, never applied — apply fixes through the
  project's editing workflow, then re-check.

## Documentation Tools

| Tool | Signature | Behavior |
|---|---|---|
| `search_documentation` | `search_documentation(query: str)` | Search the cached Biome docs; returns the best-matching resources |
| `update_cache` | `update_cache(force?: bool)` | Refresh the cached docs from biomejs.dev |

`update_cache` reports what it refreshed:

```
Documentation cache updated:
- Cli: 80 elements
- Configuration: 45 elements
- Linter: 300 elements
```

It skips the refresh (unless `force=true`) when the cached version matches
the current npm-published Biome version.

## Resources

| Resource | Contents |
|---|---|
| `biome:docs://{section}` | Overview of a docs section |
| `biome:docs://{section}/{command}` | One command or rule in a section |
| `biome:docs://{section}/{command}/{subsection}` | One subsection of a command |

Sections: `cli`, `configuration`, `linter`. Resources return structured JSON
(`type`, `name`, `description`, and content or links).

## Prompt

| Prompt | Signature | Behavior |
|---|---|---|
| `summarize_docs` | `summarize_docs(section?: str)` | Builds a summary prompt over the cached docs, optionally scoped to one section |

## Skill

The bundled `biome` skill (in `src/biome_mcp/skills/biome/`) packages this
catalog as an installable Agent Skill:

```sh
uvx biome-mcp skill install biome --target .
```

It lands in `.agents/skills/biome/` with `SKILL.md` and references covering
the tool catalog, project setup, and troubleshooting.

Next: [Development](development.md) — layout, tests, and contributing.
