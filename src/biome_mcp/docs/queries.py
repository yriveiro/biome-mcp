from typing import Any

from biome_mcp.docs.constants import CLI_PREFIX
from biome_mcp.docs.parsing import DocumentationElement
from biome_mcp.docs.text import slugify


def section_overview(section: str, cached: dict[str, Any]) -> dict[str, Any]:
    """Build the resource payload listing a documentation section."""
    elements = cached.get("elements", [])
    if not elements:
        raise FileNotFoundError(
            f"Documentation for '{section}' is not cached; run update_cache first"
        )
    return {
        "type": "section",
        "name": section,
        "commands": [
            {
                "name": element["name"],
                "description": element["description"],
                "uri": f"biome:docs://{section}/{slugify(element['name'])}",
            }
            for element in elements
        ],
    }


def find_element(
    section: str, command: str, cached: dict[str, Any]
) -> DocumentationElement:
    """Find a documented element by name within a cached section."""
    elements = cached.get("elements", [])
    if not elements:
        raise FileNotFoundError(
            f"Documentation for '{section}' is not cached; run update_cache first"
        )
    candidates = [command]
    if section == "cli" and not command.lower().startswith(CLI_PREFIX):
        candidates.append(f"{CLI_PREFIX}{command}")
    for candidate in candidates:
        for element in elements:
            if element["name"].lower() == candidate.lower():
                return element
    raise ValueError(f"Command '{command}' not found in section '{section}'")


def command_docs(section: str, command: str, cached: dict[str, Any]) -> dict[str, Any]:
    """Build metadata and subsection links for a documentation element."""
    element = find_element(section, command, cached)
    return {
        "type": "command",
        "name": element["name"],
        "description": element["description"],
        "sections": [
            {
                "title": doc["title"],
                "uri": (
                    f"biome:docs://{section}/{slugify(element['name'])}"
                    f"/{slugify(doc['title'])}"
                ),
            }
            for doc in element.get("documentation", [])
        ],
    }


def subsection_docs(
    section: str, command: str, subsection: str, cached: dict[str, Any]
) -> dict[str, Any]:
    """Build the detailed content of a documentation subsection."""
    element = find_element(section, command, cached)
    wanted = subsection.replace("-", " ").lower()
    for doc in element.get("documentation", []):
        if doc["title"].lower() == wanted:
            return {
                "type": "section",
                "command": element["name"],
                "section": doc["title"],
                "content": doc.get("content", []),
            }
    raise ValueError(f"Section '{subsection}' not found in command '{element['name']}'")
