from pathlib import Path

import pytest
from typer.testing import CliRunner

from biome_mcp.cli import app
from biome_mcp.cli.skills import bundled_skill_names, install_skill

runner = CliRunner()


def test_bundled_skill_names_include_biome() -> None:
    assert "biome" in bundled_skill_names()


def test_install_skill_copies_to_agents_layout(tmp_path: Path) -> None:
    destination, files = install_skill("biome", tmp_path)
    assert destination == tmp_path / ".agents" / "skills" / "biome"
    assert (destination / "SKILL.md").is_file()
    contents = (destination / "SKILL.md").read_text(encoding="utf-8")
    assert "name: biome" in contents
    assert "`biome_check`" in contents
    assert files == [
        "SKILL.md",
        "references/MCP-TOOLS.md",
        "references/PROJECT-SETUP.md",
        "references/TROUBLESHOOTING.md",
    ]


def test_install_skill_requires_force_for_existing(tmp_path: Path) -> None:
    install_skill("biome", tmp_path)
    with pytest.raises(ValueError, match="already installed"):
        install_skill("biome", tmp_path)
    install_skill("biome", tmp_path, force=True)


def test_skill_install_via_cli(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["skill", "install", "biome", "--target", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert (tmp_path / ".agents" / "skills" / "biome" / "SKILL.md").is_file()
