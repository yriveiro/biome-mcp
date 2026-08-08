import biome_mcp.resources  # noqa: F401
import biome_mcp.tools  # noqa: F401
from biome_mcp.app import app as mcp

__all__ = ["mcp"]


if __name__ == "__main__":
    mcp.run()
