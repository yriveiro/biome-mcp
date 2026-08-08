import glob
import logging
import os
import shlex
import subprocess
from pathlib import Path

from pydantic import BaseModel

from biome_mcp.errors import ToolNotFoundError
from biome_mcp.formatting import (
    calculate_metrics,
    filter_biome_level,
    format_biome_check,
    format_biome_format,
    parse_biome_check,
    parse_biome_format,
)
from biome_mcp.models import BiomeError, CheckLevel, TokenMetrics

logger = logging.getLogger(__name__)


class ProcessResult(BaseModel):
    """Raw stdout, stderr, and exit code from a subprocess."""

    output: str
    stderr: str = ""
    exit_code: int


class ToolResult(BaseModel):
    """Formatted result returned by one tool execution."""

    output: str
    exit_code: int
    issues: int = 0
    fixable: int = 0
    warnings: int = 0
    metrics: TokenMetrics | None = None


class ToolRunner:
    """
    Execute Biome using the project's configured invocation.

    Args:
        command_prefix: Prefix for tool invocations, usually
            ``"bunx @biomejs/biome"``.
        command_timeout: Timeout in seconds for each command.
    """

    def __init__(
        self,
        command_prefix: str = "bunx @biomejs/biome",
        command_timeout: float | None = None,
    ):
        self.command_prefix = shlex.split(command_prefix) or ["biome"]
        self.command_timeout = command_timeout

    def biome_check(self, paths: list[str], cwd: str | Path) -> ToolResult:
        """Run biome check (lint, format, and assist) and compact its JSON."""
        command = [
            *self.command_prefix,
            "check",
            "--reporter=json-pretty",
            "--max-diagnostics=none",
            *paths,
        ]
        result = self._run(command, cwd)
        all_errors = parse_biome_check(result.output)
        _relativize_paths(all_errors, cwd)
        output = format_biome_check(all_errors)

        if result.exit_code != 0 and not all_errors:
            output = (
                result.stderr.strip() or result.output[:2000] or "Biome check failed."
            )

        raw = _biome_concise(all_errors)
        metrics = calculate_metrics(raw, output)

        return ToolResult(
            output=output,
            exit_code=result.exit_code,
            issues=len(all_errors),
            fixable=sum(error.fixable for error in all_errors),
            warnings=sum(error.level == "warning" for error in all_errors),
            metrics=metrics,
        )

    def biome_lint(
        self,
        paths: list[str],
        level: CheckLevel,
        cwd: str | Path,
    ) -> ToolResult:
        """Run biome lint with the json-pretty reporter and filter by severity."""
        command = [
            *self.command_prefix,
            "lint",
            "--reporter=json-pretty",
            "--max-diagnostics=none",
            *paths,
        ]
        result = self._run(command, cwd)
        all_errors = parse_biome_check(result.output)
        _relativize_paths(all_errors, cwd)
        errors = filter_biome_level(all_errors, level)
        output = format_biome_check(errors)

        if result.exit_code != 0 and not all_errors:
            output = (
                result.stderr.strip() or result.output[:2000] or "Biome lint failed."
            )

        raw = _biome_concise(all_errors)
        metrics = calculate_metrics(raw, output)

        return ToolResult(
            output=output,
            exit_code=result.exit_code,
            issues=len(errors),
            fixable=sum(error.fixable for error in errors),
            warnings=sum(error.level == "warning" for error in errors),
            metrics=metrics,
        )

    def biome_format_check(self, paths: list[str], cwd: str | Path) -> ToolResult:
        """Run format-only checking and list the files needing formatting."""
        command = [
            *self.command_prefix,
            "check",
            "--linter-enabled=false",
            "--assist-enabled=false",
            "--reporter=json-pretty",
            "--max-diagnostics=none",
            *paths,
        ]
        result = self._run(command, cwd)
        files = parse_biome_format(result.output)
        output = format_biome_format(files)

        if result.exit_code != 0 and not files:
            output = (
                result.stderr.strip()
                or result.output[:2000]
                or "Biome format check failed."
            )

        return ToolResult(
            output=output,
            exit_code=result.exit_code,
            issues=len(files),
            metrics=calculate_metrics(result.output, output),
        )

    def _run(self, command: list[str], cwd: str | Path) -> ProcessResult:
        """Run a command and capture output without raising on exit codes."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(cwd),
                timeout=self.command_timeout,
            )
        except FileNotFoundError as e:
            raise ToolNotFoundError(
                f"Executable not found: {command[0]}. "
                "Install Biome or set BIOME_MCP_COMMAND_PREFIX to the project tooling."
            ) from e
        except subprocess.TimeoutExpired as e:
            logger.error(
                "command timed out after %s seconds: %s",
                self.command_timeout,
                command,
            )
            raise ToolNotFoundError(
                f"Command timed out after {self.command_timeout} seconds: "
                f"{' '.join(command)}"
            ) from e
        return ProcessResult(
            output=result.stdout.strip(),
            stderr=result.stderr.strip(),
            exit_code=result.returncode,
        )


_TS_PATTERNS = (
    "*.ts",
    "*.tsx",
    "*.mts",
    "*.cts",
    "*.js",
    "*.jsx",
    "*.mjs",
    "*.cjs",
    "*.json",
    "*.jsonc",
    "*.css",
    "*.html",
    "*.graphql",
    "*.vue",
    "*.astro",
    "*.svelte",
)


def changed_web_files(cwd: str | Path) -> list[str]:
    """List staged, unstaged, and untracked web files in a git repository."""
    tracked = _run_git(["git", "diff", "--name-only", "HEAD", "--", *_TS_PATTERNS], cwd)
    if tracked is None:
        return []

    files = tracked.splitlines()
    untracked = _run_git(
        ["git", "ls-files", "--others", "--exclude-standard", *_TS_PATTERNS], cwd
    )
    if untracked:
        files.extend(untracked.splitlines())

    return list(dict.fromkeys(file for file in files if file))


def resolve_paths(paths: list[str], cwd: str | Path) -> list[str]:
    """Expand glob patterns into concrete paths."""

    resolved: list[str] = []

    for pattern in paths:
        if any(char in pattern for char in "*?["):
            resolved.extend(glob.glob(pattern, root_dir=str(cwd), recursive=True))
        elif pattern:
            resolved.append(pattern)

    return resolved


def _run_git(command: list[str], cwd: str | Path) -> str | None:
    """Run a git command, returning stdout or ``None`` when it fails."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(cwd),
        )
    except FileNotFoundError, OSError:
        return None

    return result.stdout if result.returncode == 0 else None


def _relativize_paths(errors: list[BiomeError], cwd: str | Path) -> None:
    """Make absolute diagnostic paths relative to the checked project."""
    root = Path(cwd).resolve()

    for error in errors:
        path = Path(error.file)

        if path.is_absolute():
            try:
                error.file = os.fspath(path.resolve().relative_to(root))
            except ValueError:
                error.file = os.fspath(path)


def _biome_concise(errors: list[BiomeError]) -> str:
    """Reconstruct concise Biome output for savings comparison."""
    lines = [
        f"{error.file}:{error.line}:{error.col} "
        f"{error.code}{'*' if error.fixable else ''} {error.message}"
        for error in errors
    ]

    if errors:
        lines.append(f"Found {len(errors)} issues.")

    return "\n".join(lines)
