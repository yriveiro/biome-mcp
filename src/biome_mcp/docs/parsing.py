from dataclasses import dataclass
from typing import Literal, TypedDict

from bs4 import BeautifulSoup, Tag

from biome_mcp.docs.constants import Section
from biome_mcp.docs.text import clean_code, clean_text


class SubSection(TypedDict):
    title: str
    content: list[str]


class DocumentationElement(TypedDict):
    name: str
    description: str
    documentation: list[SubSection]


class SectionPayload(TypedDict):
    type: Literal["documentation_section"]
    section: Section
    elements: list[DocumentationElement]


@dataclass(frozen=True, slots=True)
class SectionSpec:
    name: Section
    handle_usage: bool = False
    handle_options: bool = False
    handle_settings: bool = False
    handle_rules: bool = False
    handle_default: bool = False
    handle_examples: bool = False


SECTION_SPECS: dict[Section, SectionSpec] = {
    "cli": SectionSpec("cli", handle_usage=True, handle_options=True),
    "configuration": SectionSpec(
        "configuration", handle_settings=True, handle_default=True, handle_examples=True
    ),
    "linter": SectionSpec("linter", handle_rules=True),
}


def parse_section(html: str, spec: SectionSpec) -> SectionPayload:
    """Parse one Biome documentation page into structured elements."""
    content = _content_root(html)
    if content is None:
        return {"type": "documentation_section", "section": spec.name, "elements": []}
    if spec.handle_rules:
        elements = _parse_rules(content)
    else:
        elements = _parse_heading_elements(content, spec)
    return {"type": "documentation_section", "section": spec.name, "elements": elements}


def parse_cli_documentation(html: str) -> SectionPayload:
    """Parse the Biome CLI reference page."""
    return parse_section(html, SECTION_SPECS["cli"])


def parse_configuration_documentation(html: str) -> SectionPayload:
    """Parse the Biome configuration reference page."""
    return parse_section(html, SECTION_SPECS["configuration"])


def parse_linter_documentation(html: str) -> SectionPayload:
    """Parse the Biome JavaScript linter rules page."""
    return parse_section(html, SECTION_SPECS["linter"])


def _content_root(html: str) -> Tag | None:
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one(".sl-markdown-content") or soup.select_one(".md-content")


def _parse_heading_elements(
    content: Tag, spec: SectionSpec
) -> list[DocumentationElement]:
    elements: list[DocumentationElement] = []
    current: DocumentationElement | None = None
    active: SubSection | None = None
    description_pending = False
    pending_group: str | None = None

    for node in content.children:
        if not isinstance(node, Tag):
            continue
        if _is_heading_wrapper(node):
            heading = node.find(["h1", "h2", "h3", "h4"])
            if heading is None:
                continue
            level = heading.name
            if level == "h1":
                current = None
                active = None
                continue
            if spec.name == "cli" and level == "h2":
                current = _new_element(heading)
                elements.append(current)
                active = None
                description_pending = True
                pending_group = None
                continue
            if spec.name == "configuration" and level in ("h2", "h3"):
                current = _new_element(heading)
                elements.append(current)
                active = None
                description_pending = True
                pending_group = None
                continue
            if current is not None and level in ("h3", "h4"):
                active = {"title": _heading_text(heading), "content": []}
                current["documentation"].append(active)
            continue

        if current is None:
            continue
        if node.name == "p":
            text = clean_text(node.get_text(" ", strip=True))
            if not text:
                continue
            if description_pending:
                current["description"] = text
                description_pending = False
                continue
            if spec.handle_usage and text.startswith("Usage:"):
                active = _append_section(current, "Usage", [text])
                continue
            if spec.handle_options:
                pending_group = text
                continue
            _append_general(current, active, text)
            continue
        if node.name == "ul":
            items = _list_items(node)
            if spec.handle_options:
                active = _append_section(current, pending_group or "Options", items)
                pending_group = None
            elif items:
                _append_general(
                    current, active, "\n".join(f"- {item}" for item in items)
                )
            continue
        if spec.handle_default and node.name == "blockquote":
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                active = _append_section(current, "Default", [text])
            continue
        if spec.handle_examples and _has_class(node, "expressive-code"):
            code = _example(node)
            if code:
                active = _append_section(current, "Examples", [code])
            continue

    return [element for element in elements if element["name"]]


def _parse_rules(content: Tag) -> list[DocumentationElement]:
    elements: list[DocumentationElement] = []
    wrappers = content.find_all("div", class_="sl-heading-wrapper")
    for wrapper in wrappers:
        heading = wrapper.find("h2")
        if heading is None:
            continue
        domain = clean_text(heading.get_text(" ", strip=True))
        table = wrapper.find_next_sibling("table")
        if table is None:
            continue
        for row in table.find_all("tr"):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 2:
                continue
            name = clean_text(cells[0].get_text(" ", strip=True))
            description = clean_text(cells[1].get_text(" ", strip=True))
            if not name:
                continue
            documentation: list[SubSection] = [
                SubSection(title="Domain", content=[domain]),
            ]
            if len(cells) > 2:
                properties = [
                    clean_text(title)
                    for icon in cells[2].find_all("span", class_="inline-icon")
                    if (title := str(icon.get("title", "")))
                ]
                if properties:
                    documentation.append(
                        SubSection(title="Properties", content=properties)
                    )
            elements.append(
                {
                    "name": name,
                    "description": description,
                    "documentation": documentation,
                }
            )
    return elements


def _new_element(heading: Tag) -> DocumentationElement:
    return {"name": _heading_text(heading), "description": "", "documentation": []}


def _heading_text(heading: Tag) -> str:
    return clean_text(heading.get_text(" ", strip=True))


def _is_heading_wrapper(node: Tag) -> bool:
    return "sl-heading-wrapper" in (node.get("class") or [])


def _has_class(node: Tag, class_name: str) -> bool:
    return class_name in (node.get("class") or [])


def _list_items(list_tag: Tag) -> list[str]:
    return [
        text
        for item in list_tag.find_all("li", recursive=False)
        if (text := clean_text(item.get_text(" ", strip=True)))
    ]


def _example(container: Tag) -> str | None:
    pre = container.find("pre")
    if pre is None:
        return None
    code = pre.find("code")
    return clean_code((code or pre).get_text("\n", strip=True))


def _append_section(
    element: DocumentationElement, title: str, content: list[str]
) -> SubSection:
    section = next(
        (item for item in element["documentation"] if item["title"] == title), None
    )
    if section is None:
        section = SubSection(title=title, content=[])
        element["documentation"].append(section)
    section["content"].extend(item for item in content if item)
    return section


def _append_general(
    element: DocumentationElement, active: SubSection | None, text: str
) -> None:
    if active is not None:
        active["content"].append(text)
    else:
        _append_section(element, "General", [text])
