# Biome Troubleshooting & Resources

## Troubleshooting

- **Executable not found**: Install Biome or set `BIOME_MCP_COMMAND_PREFIX` to
  the project tooling (e.g. `"bunx @biomejs/biome"`).
- **Command timed out**: Increase `BIOME_MCP_COMMAND_TIMEOUT`.
- **No findings but `exit_code != 0`**: The tool falls back to raw stderr
  output; check `output` for the underlying error.
- **Diagnostics missing**: Biome's experimental reporter warning is printed on
  stderr and does not affect JSON parsing from stdout.
- **`No modified web files found.`**: `changed_only=true` found no staged,
  unstaged, or untracked TypeScript/JavaScript/JSON/CSS/HTML files — not an
  error.
- **Fixable count looks off**: Best-effort; Biome JSON lacks a reliable
  explicit fixable field.

## Resources

- Latest docs: `webfetch` → <https://biomejs.dev/reference/cli/>
- Configuration reference: `webfetch` → <https://biomejs.dev/reference/configuration/>
- Linter rules: `webfetch` → <https://biomejs.dev/linter/javascript/rules/>
- Source code: `webfetch` → <https://github.com/biomejs/biome>
