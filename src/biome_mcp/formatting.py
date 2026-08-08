import json
import re
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from typing import Any, cast

from biome_mcp.models import BiomeError, CheckLevel, DiagnosticLevel, TokenMetrics

__all__ = [
    "AGGREGATE_MIN_FILES",
    "AGGREGATE_MIN_ISSUES",
    "MAX_DETAIL_LINES",
    "calculate_metrics",
    "estimate_tokens",
    "filter_biome_level",
    "format_biome_check",
    "format_biome_format",
    "parse_biome_check",
    "parse_biome_format",
]

AGGREGATE_MIN_ISSUES = 25
AGGREGATE_MIN_FILES = 6
MAX_DETAIL_LINES = 50

_CONCISE = re.compile(
    r"^([^:]+):(\d+):(\d+)\s+([^\s]+)(?:\s+FIXABLE)?\s+[─━]",
    re.MULTILINE,
)

_FIXABLE_HINTS = ("Safe fix", "Unsafe fix", "safe fix", "unsafe fix")


def estimate_tokens(text: str) -> int:
    """Estimate the token count of a text using the plugin's heuristic."""
    if not text:
        return 0

    total = 0

    for segment in re.findall(r"\s+|[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text):
        if re.fullmatch(r"\s+|[A-Za-z0-9_]+", segment):
            total += max(1, -(-len(segment) // 4))
        else:
            total += len(segment)

    return total


def calculate_metrics(raw_output: str, processed_output: str) -> TokenMetrics:
    """
    Estimate the token savings of the processed output versus raw output.

    Args:
        raw_output: Output the model would have seen without processing.
        processed_output: Compact output the model actually sees.

    Returns:
        Token metrics for the run.
    """
    raw_tokens = estimate_tokens(raw_output)
    processed_tokens = estimate_tokens(processed_output)
    saved_tokens = raw_tokens - processed_tokens

    return TokenMetrics(
        raw_tokens=raw_tokens,
        processed_tokens=processed_tokens,
        saved_tokens=saved_tokens,
        savings_percent=(
            round((saved_tokens / raw_tokens) * 100) if raw_tokens > 0 else 0
        ),
    )


def parse_biome_check(output: str) -> list[BiomeError]:
    """
    Parse Biome ``json-pretty`` output into findings.

    Falls back to the concise text format when the reporter is unavailable.

    Args:
        output: The command's stdout.

    Returns:
        Parsed findings, or ``[]`` when nothing was found.
    """
    try:
        payload = json.loads(output)
        diagnostics = payload.get("diagnostics", [])
        return [
            BiomeError(
                file=item["location"]["path"],
                line=_start_line(item),
                col=_start_column(item),
                level=cast(DiagnosticLevel, item.get("severity", "error")),
                code=item["category"],
                message=item["message"],
                fixable=_has_fix_hint(item),
            )
            for item in diagnostics
        ]
    except json.JSONDecodeError, KeyError, TypeError:
        return [
            BiomeError(
                file=match[1],
                line=int(match[2]),
                col=int(match[3]),
                level="error",
                code=match[4],
                message=match[4],
            )
            for match in _CONCISE.finditer(output)
        ]


def parse_biome_format(output: str) -> list[str]:
    """
    Extract the files needing formatting from ``json-pretty`` output.

    Args:
        output: The command's stdout.

    Returns:
        The unformatted file paths, in diagnostic order.
    """
    files: list[str] = []
    try:
        payload = json.loads(output)
        for item in payload.get("diagnostics", []):
            if item.get("category") == "format":
                files.append(item["location"]["path"])
    except json.JSONDecodeError, KeyError, TypeError:
        pass

    return list(dict.fromkeys(files))


def _start_line(item: dict[str, Any]) -> int:
    start = item.get("location", {}).get("start") or {}
    return int(start.get("line") or 0)


def _start_column(item: dict[str, Any]) -> int:
    start = item.get("location", {}).get("start") or {}
    return int(start.get("column") or 0)


def _has_fix_hint(item: dict[str, Any]) -> bool:
    for advice in item.get("advices", []):
        text = advice.get("text", "")
        if any(hint in text for hint in _FIXABLE_HINTS):
            return True
    return False


def filter_biome_level(errors: list[BiomeError], level: CheckLevel) -> list[BiomeError]:
    """
    Filter Biome diagnostics by severity.

    Args:
        errors: Parsed diagnostics.
        level: ``error`` keeps errors, ``warning`` keeps warnings and errors,
            ``all`` keeps everything.

    Returns:
        The filtered diagnostics.
    """
    match level:
        case "error":
            return [error for error in errors if error.level == "error"]
        case "warning":
            return [error for error in errors if error.level in ("error", "warning")]
        case _:
            return errors


def format_biome_check(errors: list[BiomeError]) -> str:
    """Format Biome findings compactly, aggregated for large result sets."""
    if not errors:
        return "No issues found."
    if _use_aggregate(errors):
        return _format_biome_aggregate(errors)

    return _format_grouped(
        header=_biome_header(errors),
        errors=errors,
        lines=lambda err: [
            f"  L{err.line}:{err.col} "
            f"[{_level_mark(err.level)}{'*' if err.fixable else ''}:"
            f"{err.code}] {err.message}"
        ],
    )


def format_biome_format(files: list[str]) -> str:
    """Format the list of unformatted files compactly."""
    if not files:
        return "All files properly formatted."

    lines = [f"biome format: {len(files)} files need formatting", ""]
    lines.extend(f"  {f}" for f in sorted(files))

    return "\n".join(lines).strip()


def _use_aggregate(errors: Sequence[Any]) -> bool:
    """True when the result set is large enough to warrant rollups."""
    return (
        len(errors) >= AGGREGATE_MIN_ISSUES
        or len({err.file for err in errors}) >= AGGREGATE_MIN_FILES
    )


def _format_grouped(
    header: str,
    errors: Sequence[Any],
    lines: Callable[[Any], list[str]],
) -> str:
    """Format findings grouped by file, the plugin's compact layout."""
    by_file: dict[str, list[Any]] = {}

    for err in sorted(errors, key=lambda error: (error.file, error.line)):
        by_file.setdefault(err.file, []).append(err)

    out = [header, ""]

    for file in sorted(by_file):
        out.append(f"## {file}")

        for err in by_file[file]:
            out.extend(lines(err))
        out.append("")

    return "\n".join(out).strip()


def _biome_header(errors: list[BiomeError]) -> str:
    """Build the compact header line for a Biome result."""
    fixable = sum(1 for error in errors if error.fixable)
    files = len({error.file for error in errors})
    header = f"biome: {len(errors)} issues in {files} files"

    return f"{header} ({fixable} fixable)" if fixable else header


def _level_mark(level: str) -> str:
    """Map a diagnostic level to its one-letter marker."""
    match level:
        case "error":
            return "E"
        case "warning":
            return "W"
        case _:
            return "I"


def _format_biome_aggregate(errors: list[BiomeError]) -> str:
    """Large-result layout: rule/file rollups plus flat diagnostic lines."""
    out = [_biome_header(errors), ""]
    out.append("Top rules:")

    for code, count in _ranked_counts(error.code for error in errors):
        out.append(f"  {code} ({count}x)")

    out.append("")
    out.append("Top files:")
    by_file: dict[str, list[BiomeError]] = {}

    for error in errors:
        by_file.setdefault(error.file, []).append(error)

    for file, file_errors in _ranked_groups(by_file):
        out.append(f"  {file} ({len(file_errors)} issues)")

        for code, count in _ranked_counts(err.code for err in file_errors):
            out.append(f"    {code} ({count})")

    out.append("")
    out.append("Violations:")
    details = sorted(errors, key=lambda error: (error.file, error.line, error.col))

    for err in details[:MAX_DETAIL_LINES]:
        out.append(
            f"  {err.file}:{err.line}:{err.col} "
            f"[{_level_mark(err.level)}:{err.code}] {err.message}"
        )

    _append_omission(out, len(details), "issues")

    return "\n".join(out).strip()


def _ranked_counts(values: Iterable[str]) -> list[tuple[str, int]]:
    """Return deterministic descending counts for an iterable of strings."""
    counts = Counter(values)

    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def _ranked_groups[T](groups: dict[str, list[T]]) -> list[tuple[str, list[T]]]:
    """Return groups ranked by size, then name."""
    return sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))


def _append_omission(lines: list[str], total: int, noun: str) -> None:
    """Add a compact pointer when detail lines were intentionally capped."""
    remaining = total - MAX_DETAIL_LINES

    if remaining > 0:
        lines.append(f"  ... +{remaining} more {noun}")
