from fastmcp import Context

from biome_mcp.app import app
from biome_mcp.context import ServerContext
from biome_mcp.models import CheckLevel, CheckResult
from biome_mcp.runner import ToolResult, changed_web_files, resolve_paths
from biome_mcp.tools.common import READ_ONLY, services

_NO_CHANGES = "No modified web files found."


def _result(result: ToolResult) -> CheckResult:
    metrics = result.metrics
    return CheckResult(
        output=result.output,
        exit_code=result.exit_code,
        issues=result.issues,
        fixable=result.fixable,
        warnings=result.warnings,
        saved_tokens=metrics.saved_tokens if metrics else 0,
        savings_percent=metrics.savings_percent if metrics else 0,
    )


def _targets(
    paths: list[str] | None, changed_only: bool, server: ServerContext
) -> list[str] | None:
    if changed_only:
        changed = changed_web_files(server.project_dir)
        return changed or None
    return resolve_paths(paths or [], server.project_dir)


@app.tool(name="biome_check", annotations=READ_ONLY)
def biome_check(
    ctx: Context, paths: list[str] | None = None, changed_only: bool = False
) -> CheckResult:
    """Run Biome formatting, linting, and assist checks without writing files."""
    server = services(ctx)
    targets = _targets(paths, changed_only, server)
    if targets is None:
        return CheckResult(output=_NO_CHANGES, exit_code=0)
    return _result(server.runner.biome_check(targets, server.project_dir))


@app.tool(name="biome_lint", annotations=READ_ONLY)
def biome_lint(
    ctx: Context,
    paths: list[str] | None = None,
    level: CheckLevel = "all",
    changed_only: bool = False,
) -> CheckResult:
    """Run Biome lint diagnostics without modifying files."""
    server = services(ctx)
    targets = _targets(paths, changed_only, server)
    if targets is None:
        return CheckResult(output=_NO_CHANGES, exit_code=0)
    return _result(server.runner.biome_lint(targets, level, server.project_dir))


@app.tool(name="biome_format", annotations=READ_ONLY)
def biome_format(
    ctx: Context, paths: list[str] | None = None, changed_only: bool = False
) -> CheckResult:
    """Check Biome formatting without modifying files."""
    server = services(ctx)
    targets = _targets(paths, changed_only, server)
    if targets is None:
        return CheckResult(output=_NO_CHANGES, exit_code=0)
    return _result(server.runner.biome_format_check(targets, server.project_dir))
