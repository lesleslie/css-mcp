"""Tool profile registration groups for css-mcp MCP server.

Maps ``ToolProfile`` levels to specific ``register_<group>_tools()`` call
lists, controlling which tools are exposed at startup based on the
``CSS_TOOL_PROFILE`` environment variable.

Profile tiers (Tier-A trivial — single register fn, 3-tier with STANDARD=FULL):

    MINIMAL:  No MCP-registered tool groups (only the ``/health`` HTTP route
              registered via ``mcp_common.health.register_http_health_route``
              and the ``discover_tools`` meta-tool from the W0 helper).
              Useful for control-plane / health-probe-only deployments.
    STANDARD: All 9 css-mcp tools (analyze_css, analyze_css_summary,
              get_docs, get_browser_compatibility, search_properties,
              get_properties_by_category, analyze_project_css,
              list_capabilities, health_check).
    FULL:     Same as STANDARD (css-mcp is a small Tier-A server — STANDARD
              and FULL are intentionally identical).

The dispatch surface (``PROFILE_REGISTRATIONS`` + ``REGISTRATION_MAP`` +
``register_all_tool_groups`` + ``apply_css_tool_profile``) is consumed by
``css_mcp.server.create_app`` which delegates to
``mcp_common.tools.dispatch._apply_tool_profile``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_common.tools import ToolProfile
from mcp_common.tools.dispatch import ALL_TOOLS

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastmcp import FastMCP

# Canonical list of every register_<group>_tools group key + the matching
# attribute name on ``css_mcp.tools``. The order matches the pre-refactor
# decorator registration order in ``css_mcp.tools.register_tools`` and is
# preserved across all three call sites
# (FULL_REGISTRATIONS, _build_registration_map, register_all_tool_groups)
# so adding a new group requires editing only this constant.
_GROUP_REGISTRY: list[tuple[str, str]] = [
    ("analysis_tools", "register_tools"),
]

MINIMAL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = []

FULL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = [
    key for key, _ in _GROUP_REGISTRY
]

PROFILE_REGISTRATIONS: dict[
    ToolProfile,
    list[str | Callable[[FastMCP], Awaitable[None] | None]] | type[ALL_TOOLS],
] = {
    ToolProfile.MINIMAL: MINIMAL_REGISTRATIONS,
    # Tier-A trivial: STANDARD and FULL both register everything via the
    # per-item loop. ALL_TOOLS sentinel is only honored at the FULL key.
    ToolProfile.STANDARD: FULL_REGISTRATIONS,
    ToolProfile.FULL: ALL_TOOLS,
}


def _build_registration_map() -> dict[str, Callable[[FastMCP], Awaitable[None] | None]]:
    """Build the {group_key: register_fn(app)} map.

    Local imports keep ``css_mcp.tools.profiles`` importable without forcing
    ``css_mcp.tools`` to resolve at module import time. Called by
    ``apply_css_tool_profile`` (not eagerly at import).

    The single ``register_tools(app, config)`` function takes 2 arguments
    (mcp + settings). The W0 helper expects single-arg callables, so we
    bind ``settings`` via the default-argument capture trick (the W3.1
    graphics-mcp lesson):
        ``lambda app, _cfg=settings: register_tools(app, _cfg)``
    The ``_cfg=settings`` default prevents the classic late-binding bug.
    """
    from css_mcp.config import CSSMCPSettings
    from css_mcp.tools import register_tools

    settings: CSSMCPSettings = CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP")

    # default-arg capture avoids late-binding bugs (W3.1 lesson)
    return {"analysis_tools": lambda app, _fn=register_tools, _cfg=settings: _fn(app, _cfg)}


def register_all_tool_groups(server: FastMCP) -> None:
    """Bulk register every css-mcp tool group (called at FULL/STANDARD profile).

    Used as ``register_all_fn`` for the W0 helper. Calls each
    ``register_<group>_tools`` directly so that adding a new group
    requires editing only the ``_GROUP_REGISTRY`` constant — the canonical
    source of truth (matches the W2a Crackerjack pattern).
    """
    from css_mcp.config import CSSMCPSettings
    from css_mcp.tools import register_tools

    settings: CSSMCPSettings = CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP")
    for _key, attr_name in _GROUP_REGISTRY:
        if attr_name == "register_tools":
            register_tools(server, settings)


async def apply_css_tool_profile(server: FastMCP) -> None:
    """Apply the CSS_TOOL_PROFILE dispatch to ``server`` at startup.

    Async because the W0 helper is async; called from
    ``css_mcp.server.create_app`` via ``await apply_css_tool_profile(app)``.
    The sync ``apply_tool_profile`` wrapper raises ``RuntimeError`` in any
    async context, so this async path is the only correct entry point —
    the W2b.3 spline lesson is the keystone of this rule.

    No tools are mandatory at any profile level for css-mcp — every tool
    group is opt-in per profile. The ``/health`` HTTP route is registered
    via ``mcp_common.health.register_http_health_route`` which lives
    OUTSIDE the W0 dispatch (always available regardless of profile), and
    the MCP ``health_check`` tool is part of the standard analysis_tools
    group (not load-bearing on its own). The MANDATORY_GROUPS /
    MANDATORY_TOOLS invariants are therefore vacuous; we pass empty sets
    explicitly to opt out of the subset check (matches the W3.2 lesson's
    accurate justification).
    """
    from mcp_common.tools.dispatch import _apply_tool_profile

    await _apply_tool_profile(
        server,
        profile_env_var="CSS_TOOL_PROFILE",
        registrations=PROFILE_REGISTRATIONS,
        registration_map=_build_registration_map(),
        register_all_fn=register_all_tool_groups,
        mandatory_groups=set(),
        essential_tool_names=set(),
    )


__all__ = [
    "FULL_REGISTRATIONS",
    "MINIMAL_REGISTRATIONS",
    "PROFILE_REGISTRATIONS",
    "_GROUP_REGISTRY",
    "_build_registration_map",
    "apply_css_tool_profile",
    "register_all_tool_groups",
]
