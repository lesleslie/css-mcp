"""Regression test pinning the /health HTTP route response shape.

The launch_with_healthcheck.sh wrapper script used by launchd to supervise
Bodai MCP servers polls GET /health after starting the server. The wrapper
expects a JSON body with status == "ok", service == "<service name>", and a
non-empty version. If css-mcp only exposed the MCP-tool health_check (POST
/mcp), the wrapper would time out and crash-cycle restart the server, so
the existence and shape of GET /health is load-bearing.

If this test fails, the launchd wrapper will silently kill the css-mcp
server on every restart. Fix css_mcp/tools.py::register_tools() before
merging.
"""

from __future__ import annotations

from starlette.testclient import TestClient

from css_mcp.config import CSSMCPSettings
from css_mcp.server import create_server


def _build_client() -> TestClient:
    """Build a fresh FastMCP server wrapped in a Starlette TestClient."""
    settings = CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP")
    mcp = create_server(settings)
    return TestClient(mcp.http_app())


def test_health_route_is_registered() -> None:
    """The FastMCP ASGI app must expose a GET /health route."""
    client = _build_client()

    paths = {route.path for route in client.app.routes if hasattr(route, "path")}
    assert "/health" in paths, (
        f"Expected GET /health route on css-mcp ASGI app; found paths: {sorted(paths)}"
    )


def test_health_route_returns_expected_shape() -> None:
    """GET /health must return JSON with status=ok, service=css-mcp, non-empty version."""
    client = _build_client()

    response = client.get("/health")

    assert response.status_code == 200, f"GET /health returned {response.status_code}; expected 200"

    body = response.json()
    assert body["status"] == "ok", f"status should be 'ok', got {body.get('status')!r}"
    assert body["service"] == "css-mcp", f"service should be 'css-mcp', got {body.get('service')!r}"
    assert isinstance(body.get("version"), str) and body["version"], (
        f"version should be a non-empty string, got {body.get('version')!r}"
    )
