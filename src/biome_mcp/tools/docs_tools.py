from fastmcp import Context

from biome_mcp.app import app
from biome_mcp.docs import DOCUMENTATION_SECTIONS
from biome_mcp.tools.common import services


@app.prompt(name="summarize_docs")
async def summarize_docs(ctx: Context, section: str | None = None) -> str:
    """Generate a prompt for summarizing cached Biome documentation."""
    if section:
        overview = await services(ctx).docs.get_section_overview(section)
        commands = ", ".join(item["name"] for item in overview["commands"])
        target = f"the `{section}` section, covering {commands}"
    else:
        target = "the cached Biome documentation"
    return (
        f"Summarize {target} for a TypeScript developer. Use the available "
        "biome:docs:// resources to read relevant documentation. Explain key "
        "commands, settings, rules, and concise usage examples in Markdown."
    )


@app.tool(name="update_cache")
async def update_cache(ctx: Context, force: bool = False) -> str:
    """Refresh the cached Biome documentation."""
    docs = services(ctx).docs
    if not force and await docs.is_cache_valid():
        return "Documentation cache is up to date with the current Biome version."
    version = await docs.fetch_current_version()
    results: list[str] = []
    for section in DOCUMENTATION_SECTIONS:
        try:
            content = await docs.fetch_section(section)
            await docs.update_section(section, content)
            results.append(f"- {section.title()}: {len(content['elements'])} elements")
        except Exception as exc:
            results.append(f"- {section.title()}: failed ({exc})")
    await docs.update_version(version)
    return "Documentation cache updated:\n" + "\n".join(results)


@app.tool(name="search_documentation")
async def search_documentation(query: str, ctx: Context) -> str:
    """Search cached Biome documentation."""
    results = await services(ctx).docs.search(query)
    if not results:
        return "No matching documentation resources found."
    formatted = "\n\n".join(
        f"Resource: {item['path']}\nName: {item['name']}\n"
        f"Description: {item['description']}"
        for item in results
    )
    return f"Best matching resources:\n\n{formatted}"
