from dataclasses import dataclass
from pathlib import Path
from typing import cast

from fastmcp import Context

from biome_mcp.docs import CacheManager
from biome_mcp.runner import ToolRunner


@dataclass(slots=True)
class ServerContext:
    """Per-server shared services created by the lifespan."""

    runner: ToolRunner
    docs: CacheManager
    project_dir: Path


def services(ctx: Context) -> ServerContext:
    """Return the typed server services from a FastMCP context."""
    return cast(ServerContext, ctx.lifespan_context)
