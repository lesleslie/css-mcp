"""CSS MCP Server - CSS Analysis and Documentation."""

from __future__ import annotations

from typing import Any, cast

from fastmcp import FastMCP
from oneiric.core.logging import get_logger

from css_mcp.config import CSSMCPSettings
from css_mcp.tools import register_tools

logger = get_logger(__name__)

# Global instances
_mcp: FastMCP | None = None


def create_server(settings: CSSMCPSettings) -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="CSS MCP Server",
        instructions="""CSS Analysis and Documentation Server

Provides tools for analyzing CSS, fetching MDN documentation, and checking
browser compatibility. Designed for analyzing programmatically generated CSS
from FastBlocks style adapters (Kelp, WebAwesome, etc.).

Available tools:
- analyze_css: Full CSS analysis with 150+ metrics
- analyze_css_summary: Quick CSS summary
- get_docs: MDN documentation for CSS properties
- get_browser_compatibility: Check browser support
- search_properties: Search for CSS properties
- get_properties_by_category: Get properties by category
- analyze_project_css: Analyze all CSS in a project
- list_capabilities: List available capabilities
- health_check: Check server health
""",
    )

    register_tools(mcp, settings)
    return mcp


def run_server(settings: CSSMCPSettings) -> None:
    """Start the CSS MCP server. Called by cli.start_handler."""
    global _mcp

    _mcp = create_server(settings)
    logger.info(
        "CSS MCP Server starting",
        endpoint=f"http://{settings.http_host}:{settings.http_port}/mcp",
    )

    _mcp.run(
        transport="http",
        host=settings.http_host,
        port=settings.http_port,
    )


def get_app() -> FastMCP:
    """Get or create the FastMCP server instance (lazy init for uvicorn compatibility)."""
    global _mcp
    if _mcp is None:
        settings = cast("CSSMCPSettings", CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP"))
        _mcp = create_server(settings)
    return _mcp


def __getattr__(name: str) -> Any:
    """Lazy attribute access for uvicorn compatibility."""
    if name == "app":
        return get_app()
    if name == "http_app":
        return get_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
