#!/usr/bin/env python3
"""CSS MCP Server - CSS Analysis and Documentation.

Provides MCP tools for CSS analysis, MDN documentation, and browser
compatibility checking. Designed for analyzing programmatically generated
CSS from FastBlocks style adapters.

Usage:
    python -m css_mcp.server
    css-mcp

Environment Variables:
    CSS_MCP_HTTP_PORT: Server port (default: 3050)
    CSS_MCP_HTTP_HOST: Server host (default: localhost)
    CSS_MCP_DEBUG: Enable debug mode (default: false)
"""

from __future__ import annotations

import atexit
import logging
from typing import Any

from fastmcp import FastMCP

from css_mcp.config import CSSMCPConfig
from css_mcp.tools import register_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
_mcp: FastMCP | None = None
_config: CSSMCPConfig | None = None
_mdn_fetcher: Any = None


def get_config() -> CSSMCPConfig:
    """Get or create configuration."""
    global _config
    if _config is None:
        _config = CSSMCPConfig()
    return _config


def create_server(config: CSSMCPConfig) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        config: Server configuration

    Returns:
        Configured FastMCP server instance
    """
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

    # HTTP health endpoint for Claude Code compatibility
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Any) -> Any:
        """HTTP health check endpoint for Claude Code `mcp list` compatibility."""
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok", "service": "css", "version": "0.1.0"})

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz_check(request: Any) -> Any:
        """Kubernetes-style health check endpoint."""
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok"})

    # Register all tools
    register_tools(mcp, config)

    return mcp


async def cleanup() -> None:
    """Cleanup resources on shutdown."""
    global _mdn_fetcher

    if _mdn_fetcher is not None:
        try:
            await _mdn_fetcher.close()
            logger.info("MDN fetcher closed")
        except Exception as e:
            logger.warning(f"Error closing MDN fetcher: {e}")


def main() -> None:
    """Main entry point for the CSS MCP server."""
    global _mcp

    try:
        # Load configuration
        config = get_config()

        # Create server
        _mcp = create_server(config)

        # Register cleanup
        atexit.register(lambda: None)  # Placeholder for sync cleanup

        # Display startup message
        logger.info("=" * 60)
        logger.info("CSS MCP Server v0.1.0")
        logger.info("=" * 60)
        logger.info(f"  Endpoint: http://{config.http_host}:{config.http_port}/mcp")
        logger.info(f"  Debug mode: {config.debug}")
        logger.info("")
        logger.info("  Features:")
        logger.info("    • CSS analysis with 150+ metrics")
        logger.info("    • MDN documentation fetching")
        logger.info("    • Browser compatibility checking")
        logger.info("    • Project-wide CSS analysis")
        logger.info("    • FastBlocks style adapter integration")
        logger.info("=" * 60)

        # Run server
        _mcp.run(
            transport="http",
            host=config.http_host,
            port=config.http_port,
        )

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def get_app() -> FastMCP:
    """Get or create the FastMCP server instance (lazy initialization)."""
    global _mcp
    if _mcp is None:
        config = get_config()
        _mcp = create_server(config)
    return _mcp


def __getattr__(name: str) -> Any:
    """Lazy attribute access for uvicorn compatibility.

    Enables `uvicorn css_mcp.server:http_app --factory` pattern.
    """
    if name == "app":
        return get_app()
    if name == "http_app":
        return get_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


if __name__ == "__main__":
    main()
