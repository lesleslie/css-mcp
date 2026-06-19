"""CLI entry point for CSS MCP Server using mcp-common factory pattern."""

from __future__ import annotations

import contextlib
from typing import cast

from mcp_common import MCPServerCLIFactory, RuntimeHealthSnapshot

from css_mcp.config import CSSMCPSettings


def _health_probe(settings: CSSMCPSettings) -> RuntimeHealthSnapshot:
    pid_path = settings.pid_path()
    pid: int | None = None
    if pid_path.exists():
        with contextlib.suppress(ValueError, OSError):
            pid = int(pid_path.read_text().strip())
    return RuntimeHealthSnapshot(
        orchestrator_pid=pid,
        watchers_running=pid is not None,
    )


def create_css_mcp_cli() -> MCPServerCLIFactory:
    settings = cast("CSSMCPSettings", CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP"))

    def start_handler() -> None:
        from css_mcp.server import run_server

        run_server(settings)

    return MCPServerCLIFactory(
        server_name=settings.server_name,
        settings=settings,
        start_handler=start_handler,
        health_probe_handler=lambda: _health_probe(settings),
    )


def main() -> None:
    create_css_mcp_cli().create_app()()
