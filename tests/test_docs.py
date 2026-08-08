import pytest

from biome_mcp.docs import (
    CacheManager,
    parse_cli_documentation,
    parse_linter_documentation,
)

CLI_HTML = """
<div class="sl-markdown-content">
  <div class="sl-heading-wrapper level-h1"><h1>Command summary</h1></div>
  <div class="sl-heading-wrapper level-h2"><h2>biome check</h2></div>
  <p>Check project files.</p>
  <p>Usage: biome check PATH</p>
  <p>Available options:</p>
  <ul><li>--write - Apply fixes.</li></ul>
</div>
"""

LINTER_HTML = """
<div class="sl-markdown-content">
  <div class="sl-heading-wrapper level-h2"><h2>correctness</h2></div>
  <table><tr><th>Rule name</th><th>Description</th><th>Properties</th></tr>
    <tr><td><a href="/linter/rules/no-foo">noFoo</a></td><td>Disallow foo.</td>
      <td><span class="inline-icon" title="This rule is recommended"></span></td></tr>
  </table>
</div>
"""


def test_documentation_parsers_extract_cli_and_rules() -> None:
    cli = parse_cli_documentation(CLI_HTML)
    assert cli["elements"][0]["name"] == "biome check"
    assert cli["elements"][0]["description"] == "Check project files."
    assert cli["elements"][0]["documentation"][0]["title"] == "Usage"

    linter = parse_linter_documentation(LINTER_HTML)
    assert linter["elements"][0]["name"] == "noFoo"
    assert linter["elements"][0]["documentation"][0]["content"] == ["correctness"]


@pytest.mark.anyio
async def test_cache_manager_round_trip_and_search(tmp_path) -> None:
    manager = CacheManager(cache_dir=tmp_path)
    await manager.update_version({"version": "1.0"})
    await manager.update_section(
        "cli",
        {
            "elements": [
                {
                    "name": "biome check",
                    "description": "Check files.",
                    "documentation": [{"title": "Usage", "content": ["biome check"]}],
                }
            ]
        },
    )

    assert await manager.get_cached_version() == {"version": "1.0"}
    results = await manager.search("check")
    assert results[0]["path"] == "biome:docs://cli/biome-check"

    await manager.clear_cache()
    assert not (tmp_path / "version.json").exists()
