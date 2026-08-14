"""CSS MCP Server - CSS analysis and documentation for FastBlocks ecosystem."""

from __future__ import annotations

from importlib.metadata import version as _importlib_version

__version__ = _importlib_version("css-mcp")
__author__ = "Les Leslie"

from css_mcp.analyzer import CSSAnalyzer, CSSMetrics, CSSProperty
from css_mcp.config import CSSMCPConfig, CSSMCPSettings

__all__ = [
    "CSSAnalyzer",
    "CSSMetrics",
    "CSSMCPConfig",
    "CSSMCPSettings",
    "CSSProperty",
]
