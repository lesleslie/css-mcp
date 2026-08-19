"""CSS MCP Server - CSS Analysis and Documentation."""

from __future__ import annotations

import asyncio
from typing import Any

from mcp_common.fastmcp import FastMCP
from oneiric.core.logging import get_logger

from css_mcp.config import CSSMCPSettings

logger = get_logger(__name__)

# Global instances
_mcp: FastMCP | None = None


def _run_async_safely(coro: Any) -> Any:
    """Run an async coroutine from a sync context, tolerating a running loop.

    Bridges to the async ``create_app`` via ``asyncio.run`` when no loop
    is running (CLI startup, ``__main__.py``). Falls back to a private
    thread executor when a loop is already running (pytest-asyncio tests
    that instantiate the class).

    Tool profile dispatch is async because the W0 helper from
    mcp-common 0.18.0 (``_apply_tool_profile``) is async. Per the
    W2b.3 lesson, the sync ``apply_tool_profile`` wrapper raises
    ``RuntimeError`` when called from inside a running event loop, so
    the async path is the only correct entry point for any async caller.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Loop already running (pytest-asyncio test). Run the coroutine in a
    # private thread with its own fresh loop, mirroring the W3.4 unifi-mcp
    # pattern that avoids blocking the test's loop.
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def create_server(settings: CSSMCPSettings) -> FastMCP:
    """Create and configure the MCP server (sync wrapper).

    Bridges to the async ``create_app`` via ``_run_async_safely``. Used
    by the existing ``test_health_route.py`` test and the CLI startup
    path. Tests that exercise the real async startup should call
    ``await create_app(...)`` directly so any W2b.3-style regression in
    the production dispatch path is caught.
    """
    return _run_async_safely(create_app(settings))


async def create_app(settings: CSSMCPSettings) -> FastMCP:
    """Create and configure the MCP server (async production path).

    Async because the W0 tool profile dispatch helper is async.
    Callers from sync contexts (CLI startup, ``get_app``, ``create_server``)
    wrap with ``asyncio.run(create_app(...))``. Tests that exercise the
    real async startup should call ``await create_app(...)`` directly so
    any W2b.3-style regression in the production dispatch path is caught.
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

    # Apply tool profile dispatch (CSS_TOOL_PROFILE env var).
    #
    # Replaces the previous direct ``register_tools(mcp, settings)`` call.
    # The W0 helper from mcp-common 0.18.0+ dispatches by group name and
    # always registers the ``discover_tools`` meta-tool. The default
    # (no env var) remains FULL = all 9 css-mcp tools — the previous
    # behavior is preserved.
    #
    # Per the W2b.3 keystone: this MUST be the async helper, NOT the
    # sync ``apply_tool_profile`` wrapper (which raises RuntimeError in
    # event loops and would silently break any test that runs
    # ``create_app`` under an async context).
    #
    # The caller-supplied ``settings`` instance is forwarded through to
    # the registration paths so test-injected configuration overrides
    # are preserved (the W4.1 round-1 reviewer fix — caller-supplied
    # settings were silently discarded before).
    from css_mcp.tools.profiles import apply_css_tool_profile

    await apply_css_tool_profile(mcp, settings)

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
        transport="streamable-http",
        host=settings.http_host,
        port=settings.http_port,
    )


def get_app() -> FastMCP:
    """Get or create the FastMCP server instance (lazy init for uvicorn compatibility)."""
    global _mcp
    if _mcp is None:
        settings = CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP")
        _mcp = create_server(settings)
    return _mcp


def __getattr__(name: str) -> Any:
    """Lazy attribute access for uvicorn compatibility."""
    if name == "app":
        return get_app()
    if name == "http_app":
        return get_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
