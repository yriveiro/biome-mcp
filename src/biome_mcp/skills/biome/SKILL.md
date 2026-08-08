---
name: biome
description: Use when the biome-mcp MCP server is available to run biome_check, biome_lint, or biome_format on TypeScript and web projects. Prefer its compact read-only diagnostics for linting and format verification.
license: Apache-2.0
compatibility: Requires the biome-mcp MCP server connected to the agent.
metadata:
  audience: typescript-developers
  author: Yago Riveiro
  version: "1.0.0"
---

# biome Skill

`biome-mcp` exposes compact, read-only quality checks for TypeScript and web
projects. It does not modify source files or manage JavaScript dependencies.

## Tools

| Need | Tool | Arguments |
| --- | --- | --- |
| Run all Biome checks | `biome_check` | `paths?: list[str]`, `changed_only?: bool` |
| Run lint checks | `biome_lint` | `paths?: list[str]`, `level?: "all"|"error"|"warning"`, `changed_only?: bool` |
| Verify formatting | `biome_format` | `paths?: list[str]`, `changed_only?: bool` |

Use these MCP tools instead of shelling out to Biome when they are in the tool
context. Their output is structured and intentionally compact.

## Fast Feedback

After changing TypeScript or web code:

1. Run `biome_check(changed_only=true)`.
2. Run `biome_format(changed_only=true)`.
3. Fix the reported files and rerun the affected check.

Use `biome_lint(level="all", changed_only=true)` when informational diagnostics
are relevant. Always inspect the returned `exit_code`.

## Target Selection

- Omit `paths` to check the whole project.
- Pass files, directories, or glob patterns such as `paths=["src/**/*.ts"]`.
- Use `changed_only=true` for staged, unstaged, and untracked web files in the
  current Git repository. It takes precedence over `paths`.
- When no modified web files exist, a changed-only check succeeds with
  `No modified web files found.`

## Documentation

Use `search_documentation` for Biome CLI, configuration, and JavaScript linter
questions. Read the returned `biome:docs://` resources for detailed content.

## References

- Full tool catalog with signatures: `references/MCP-TOOLS.md`
- Installing Biome, configuring the server, targeting checks: `references/PROJECT-SETUP.md`
- Error handling and where to look up docs: `references/TROUBLESHOOTING.md`
