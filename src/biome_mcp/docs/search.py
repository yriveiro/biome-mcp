from collections.abc import Awaitable, Callable
from difflib import get_close_matches
from typing import Any

from biome_mcp.docs.constants import DOCUMENTATION_SECTIONS
from biome_mcp.docs.parsing import DocumentationElement
from biome_mcp.docs.text import slugify

_MAX_RESULTS = 3
_MIN_SCORE = 0.25


def build_resources(
    elements: list[DocumentationElement], section: str
) -> list[dict[str, Any]]:
    """Flatten cached documentation into searchable resources."""
    resources: list[dict[str, Any]] = []
    for element in elements:
        name = element["name"]
        content = " ".join(
            str(item)
            for doc in element.get("documentation", [])
            for item in doc.get("content", [])[:3]
        )
        resources.append(
            {
                "path": f"biome:docs://{section}/{slugify(name)}",
                "name": name,
                "description": element["description"],
                "search_text": f"{name} {element['description']} {content}",
                "section": section,
            }
        )
    return resources


def score_resource(resource: dict[str, Any], keywords: list[str]) -> float:
    """Score a resource against search keywords."""
    score = 0.0
    name = resource["name"].lower()
    section = resource["section"].lower()
    search_text = resource["search_text"].lower()
    for keyword in keywords:
        if keyword == section:
            score += 3.0
        elif keyword in section:
            score += 2.0
        if keyword == name:
            score += 2.0
        elif keyword in name:
            score += 1.0
        if f" {keyword} " in f" {search_text} ":
            score += 0.75
        elif keyword in search_text:
            score += 0.5
    if score < 1.0:
        score += sum(
            0.25
            for keyword in keywords
            if get_close_matches(keyword, [name, section], n=1, cutoff=0.6)
        )
    return score


async def search_sections(
    load_section: Callable[[str], Awaitable[dict[str, Any]]], query: str
) -> list[dict[str, str]]:
    """Search all cached sections and return the best matching resources."""
    keywords = query.lower().split()
    resources = [
        resource
        for section in DOCUMENTATION_SECTIONS
        for resource in build_resources(
            (await load_section(section)).get("elements", []), section
        )
    ]
    ranked = sorted(
        ((score_resource(resource, keywords), resource) for resource in resources),
        key=lambda item: item[0],
        reverse=True,
    )
    return [
        {
            "path": resource["path"],
            "name": resource["name"],
            "description": resource["description"],
        }
        for score, resource in ranked
        if score > _MIN_SCORE
    ][:_MAX_RESULTS]
