import asyncio
import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import httpx

from biome_mcp.docs.constants import (
    DOCS_URLS,
    DOCUMENTATION_SECTIONS,
    HTTP_TIMEOUT,
    NPM_BIOME_URL,
    VERSION_FILE,
    Section,
)
from biome_mcp.docs.parsing import SECTION_SPECS, SectionPayload, parse_section
from biome_mcp.docs.queries import command_docs, section_overview, subsection_docs
from biome_mcp.docs.search import search_sections

logger = logging.getLogger(__name__)


async def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return {}


async def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    def write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(temporary, path)

    await asyncio.to_thread(write)


async def _fetch_text(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=HTTP_TIMEOUT) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


class CacheManager:
    """Fetch, store, and query cached Biome documentation."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        if cache_dir is None:
            root = Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache")))
            cache_dir = root / "biome-mcp" / "docs"
        self.cache_dir = cache_dir
        self.version_file = cache_dir / VERSION_FILE

    async def initialize(self) -> None:
        """Initialize the cache without making startup depend on the network."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self.version_file.exists():
            return
        try:
            await self.update_version(await self.fetch_current_version())
            for section in DOCUMENTATION_SECTIONS:
                await self.update_section(section, await self.fetch_section(section))
        except Exception:
            logger.exception("Failed to initialize documentation cache")
            if not self.version_file.exists():
                await self.update_version({"version": "unknown"})

    async def get_cached_version(self) -> dict[str, str]:
        return await _read_json(self.version_file)

    async def update_version(self, version_info: dict[str, str]) -> None:
        await _write_json(self.version_file, version_info)

    def get_section_cache_path(self, section: str) -> Path:
        return self.cache_dir / f"{section}.json"

    async def get_cached_section(self, section: str) -> dict[str, Any]:
        return await _read_json(self.get_section_cache_path(section))

    async def update_section(
        self, section: str, content: dict[str, Any] | SectionPayload
    ) -> None:
        await _write_json(self.get_section_cache_path(section), content)

    async def clear_cache(self) -> None:
        await asyncio.gather(
            *(asyncio.to_thread(path.unlink) for path in self.cache_dir.glob("*.json"))
        )

    async def fetch_current_version(self) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(NPM_BIOME_URL)
            try:
                response.raise_for_status()
                return {"version": str(response.json()["version"])}
            except httpx.HTTPError, KeyError, ValueError:
                return {"version": "unknown"}

    async def is_cache_valid(self) -> bool:
        try:
            return (await self.get_cached_version()).get("version") == (
                await self.fetch_current_version()
            ).get("version")
        except Exception:
            logger.exception("Failed to check documentation cache validity")
            return False

    async def fetch_section(self, section: str) -> SectionPayload:
        name = cast(Section, section)
        return parse_section(await _fetch_text(DOCS_URLS[name]), SECTION_SPECS[name])

    async def get_section_overview(self, section: str) -> dict[str, Any]:
        return section_overview(section, await self.get_cached_section(section))

    async def get_command_docs(self, section: str, command: str) -> dict[str, Any]:
        return command_docs(section, command, await self.get_cached_section(section))

    async def get_subsection_docs(
        self, section: str, command: str, subsection: str
    ) -> dict[str, Any]:
        return subsection_docs(
            section, command, subsection, await self.get_cached_section(section)
        )

    async def search(self, query: str) -> list[dict[str, str]]:
        return await search_sections(self.get_cached_section, query)
