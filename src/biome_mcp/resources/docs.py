from typing import Any

from fastmcp import Context
from fastmcp.exceptions import ResourceError

from biome_mcp.app import app
from biome_mcp.context import services


@app.resource(
    "biome:docs://{section}", name="biome_docs_section", mime_type="application/json"
)
async def get_docs_section(ctx: Context, section: str) -> dict[str, Any]:
    try:
        return await services(ctx).docs.get_section_overview(section)
    except (FileNotFoundError, ValueError) as exc:
        raise ResourceError(str(exc)) from exc


@app.resource(
    "biome:docs://{section}/{command}",
    name="biome_docs_command",
    mime_type="application/json",
)
async def get_docs_command(ctx: Context, section: str, command: str) -> dict[str, Any]:
    try:
        return await services(ctx).docs.get_command_docs(section, command)
    except (FileNotFoundError, ValueError) as exc:
        raise ResourceError(str(exc)) from exc


@app.resource(
    "biome:docs://{section}/{command}/{subsection}",
    name="biome_docs_subsection",
    mime_type="application/json",
)
async def get_docs_subsection(
    ctx: Context, section: str, command: str, subsection: str
) -> dict[str, Any]:
    try:
        return await services(ctx).docs.get_subsection_docs(
            section, command, subsection
        )
    except (FileNotFoundError, ValueError) as exc:
        raise ResourceError(str(exc)) from exc
