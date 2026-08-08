from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP

from biome_mcp import __version__
from biome_mcp.context import ServerContext
from biome_mcp.docs import CacheManager
from biome_mcp.runner import ToolRunner
from biome_mcp.settings import Settings, configure_logging


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[ServerContext]:
    """Build shared services for the lifetime of the server."""
    settings = Settings()
    configure_logging(settings)
    docs = CacheManager(
        cache_dir=Path(settings.cache_dir) if settings.cache_dir else None
    )
    await docs.initialize()
    yield ServerContext(
        runner=ToolRunner(
            command_prefix=settings.command_prefix,
            command_timeout=settings.command_timeout,
        ),
        docs=docs,
        project_dir=(
            Path(settings.project_dir).resolve() if settings.project_dir else Path.cwd()
        ),
    )


app = FastMCP(
    "biome-mcp",
    instructions=(
        "Run Biome on TypeScript and web projects with token-efficient output. "
        "Use biome_check for formatting, linting, and assist diagnostics, "
        "biome_lint for lint-only diagnostics, and biome_format to verify "
        "formatting without modifying files. Prefer changed_only=true for "
        "fast feedback on recently edited files, and browse the cached Biome "
        "documentation resources for CLI and configuration questions."
    ),
    version=__version__,
    lifespan=lifespan,
)
