import json
import subprocess
from pathlib import Path

from biome_mcp.formatting import (
    calculate_metrics,
    filter_biome_level,
    format_biome_check,
    parse_biome_check,
    parse_biome_format,
)
from biome_mcp.models import BiomeError
from biome_mcp.runner import ToolRunner, changed_web_files, resolve_paths


def test_parse_biome_json_preserves_diagnostic_fields() -> None:
    payload = json.dumps(
        {
            "diagnostics": [
                {
                    "severity": "warning",
                    "message": "Variable is unused.",
                    "category": "lint/correctness/noUnusedVariables",
                    "location": {
                        "path": "src/a.ts",
                        "start": {"line": 2, "column": 8},
                    },
                    "advices": [],
                }
            ]
        }
    )

    errors = parse_biome_check(payload)

    assert errors == [
        BiomeError(
            file="src/a.ts",
            line=2,
            col=8,
            level="warning",
            code="lint/correctness/noUnusedVariables",
            message="Variable is unused.",
        )
    ]


def test_parse_biome_format_files() -> None:
    payload = json.dumps(
        {
            "diagnostics": [
                {
                    "category": "format",
                    "location": {"path": "src/a.ts"},
                },
                {
                    "category": "lint/style/noVar",
                    "location": {"path": "src/b.ts"},
                },
                {
                    "category": "format",
                    "location": {"path": "src/a.ts"},
                },
            ]
        }
    )

    assert parse_biome_format(payload) == ["src/a.ts"]


def test_filter_biome_level() -> None:
    errors = [
        BiomeError(file="a.ts", line=1, col=1, level="error", code="E", message="e"),
        BiomeError(file="a.ts", line=2, col=1, level="warning", code="W", message="w"),
        BiomeError(file="a.ts", line=3, col=1, level="info", code="I", message="i"),
    ]

    assert len(filter_biome_level(errors, "error")) == 1
    assert len(filter_biome_level(errors, "warning")) == 2
    assert len(filter_biome_level(errors, "all")) == 3


def test_format_biome_check_groups_by_file() -> None:
    output = format_biome_check(
        [BiomeError(file="a.ts", line=1, col=1, level="error", code="E", message="bad")]
    )

    assert "## a.ts" in output
    assert "L1:1 [E:E] bad" in output


def test_metrics_report_processed_savings() -> None:
    metrics = calculate_metrics("a " * 100, "a")
    assert metrics.saved_tokens > 0
    assert metrics.savings_percent > 0


def test_native_runner_runs_biome_end_to_end(tmp_path: Path) -> None:
    (tmp_path / "bad.ts").write_text("const value=1\n", encoding="utf-8")
    result = ToolRunner(command_prefix="").biome_format_check(["bad.ts"], tmp_path)

    assert result.exit_code == 1
    assert result.issues == 1
    assert "bad.ts" in result.output


def test_resolve_paths_expands_globs(tmp_path: Path) -> None:
    (tmp_path / "a.ts").write_text("const a = 1;\n", encoding="utf-8")
    (tmp_path / "b.ts").write_text("const b = 2;\n", encoding="utf-8")
    assert sorted(resolve_paths(["*.ts"], tmp_path)) == ["a.ts", "b.ts"]


def test_changed_web_files_in_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.dev"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.ts").write_text("const value = 1;\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.ts"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.ts").write_text("const value = 2;\n", encoding="utf-8")
    (tmp_path / "new.ts").write_text("const other = 1;\n", encoding="utf-8")

    assert sorted(changed_web_files(tmp_path)) == ["new.ts", "tracked.ts"]
