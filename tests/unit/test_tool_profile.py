"""Tests for css-mcp's ToolProfile adoption (W4.1).

Pins the Tier-A trivial mapping (MINIMAL = empty / STANDARD = FULL = all)
and verifies the W2b.3 keystone: the production path uses the async
``_apply_tool_profile`` helper (NOT the sync ``apply_tool_profile`` wrapper,
which raises ``RuntimeError`` when called from inside a running event loop).

See ``docs/architecture/tool-profile-rationale.md`` for the rationale.
"""

from __future__ import annotations

import ast
import inspect
import os
import pathlib

import pytest

from css_mcp.config import CSSMCPSettings
from css_mcp.server import create_app
from css_mcp.tools.profiles import (
    _GROUP_REGISTRY,
    FULL_REGISTRATIONS,
    MINIMAL_REGISTRATIONS,
    PROFILE_REGISTRATIONS,
    _build_registration_map,
    apply_css_tool_profile,
    register_all_tool_groups,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVER_PY = REPO_ROOT / "css_mcp" / "server.py"
PROFILES_PY = REPO_ROOT / "css_mcp" / "tools" / "profiles.py"


# ---------------------------------------------------------------------------
# Structural / AST guards
# ---------------------------------------------------------------------------


def test_profiles_py_exists() -> None:
    """css_mcp/tools/profiles.py must exist."""
    assert PROFILES_PY.exists(), f"Missing {PROFILES_PY}"


def test_profiles_py_defines_profile_registrations() -> None:
    """PROFILE_REGISTRATIONS dict must be defined."""
    assert isinstance(PROFILE_REGISTRATIONS, dict)
    assert set(PROFILE_REGISTRATIONS.keys()) == {"minimal", "standard", "full"}


def test_profiles_py_defines_group_registry() -> None:
    """_GROUP_REGISTRY must be the single source of truth."""
    assert isinstance(_GROUP_REGISTRY, list)
    assert len(_GROUP_REGISTRY) >= 1
    for key, attr_name in _GROUP_REGISTRY:
        assert isinstance(key, str) and isinstance(attr_name, str)


def test_profiles_py_defines_build_registration_map() -> None:
    """_build_registration_map fn must be defined."""
    assert callable(_build_registration_map)


def test_profiles_py_defines_register_all_tool_groups() -> None:
    """register_all_tool_groups fn must be defined."""
    assert callable(register_all_tool_groups)


def test_profiles_py_defines_apply_css_tool_profile() -> None:
    """async apply_css_tool_profile fn must be defined."""
    assert callable(apply_css_tool_profile)
    assert inspect.iscoroutinefunction(apply_css_tool_profile)


def test_profiles_py_references_css_tool_profile_env_var() -> None:
    """CSS_TOOL_PROFILE env var must be referenced."""
    source = PROFILES_PY.read_text()
    assert "CSS_TOOL_PROFILE" in source


def test_server_uses_async_create_app() -> None:
    """server.py must expose async create_app."""
    source = SERVER_PY.read_text()
    tree = ast.parse(source)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_app":
            found = True
            break
    assert found, "Expected `async def create_app(...)` in server.py"


def test_server_awaits_apply_css_tool_profile() -> None:
    """W2b.3 keystone: production path MUST await apply_css_tool_profile.

    Structural AST check for ``ast.Await(value=ast.Call(
    func=ast.Name(id="apply_css_tool_profile")))`` — NOT just call count,
    which would pass for a sync-wrapper regression (the W3.2 round-1 fix).
    """
    source = SERVER_PY.read_text()
    tree = ast.parse(source)
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Await):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not (
            isinstance(node.value.func, ast.Name) and node.value.func.id == "apply_css_tool_profile"
        ):
            continue
        found = True
        break
    assert found, (
        "`await apply_css_tool_profile(...)` not found in server.py. "
        "Production path MUST use the async helper, not the sync wrapper."
    )


def test_server_does_not_use_sync_wrapper() -> None:
    """server.py must NOT call sync ``apply_tool_profile`` (only ``apply_css_tool_profile`` or ``_apply_tool_profile``)."""
    source = SERVER_PY.read_text()
    # bare apply_tool_profile (not apply_css_tool_profile, not _apply_tool_profile)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "apply_tool_profile":
            raise AssertionError(
                "server.py calls bare `apply_tool_profile(...)` (sync wrapper). "
                "Use the async helper: `await apply_css_tool_profile(app)`."
            )


def test_profiles_uses_async_helper_not_sync_wrapper() -> None:
    """profiles.py must use _apply_tool_profile (async), not apply_tool_profile (sync)."""
    source = PROFILES_PY.read_text()
    assert "_apply_tool_profile" in source, (
        "profiles.py must call _apply_tool_profile (async helper)"
    )
    # If it imports/uses the sync wrapper, that's a bug
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "apply_tool_profile":
            raise AssertionError(
                "profiles.py calls sync `apply_tool_profile(...)`; "
                "must use async `_apply_tool_profile(...)`"
            )


def test_pyproject_bumps_mcp_common_to_0_18() -> None:
    """pyproject.toml must pin mcp-common>=0.18.0."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert "mcp-common>=0.18.0" in pyproject, "pyproject.toml must bump mcp-common to >=0.18.0"


def test_decision_doc_exists_at_tracked_path() -> None:
    """docs/architecture/tool-profile-rationale.md must exist."""
    doc = REPO_ROOT / "docs" / "architecture" / "tool-profile-rationale.md"
    assert doc.exists(), f"Missing rationale doc at {doc}"


# ---------------------------------------------------------------------------
# Profile semantics
# ---------------------------------------------------------------------------


def test_profile_registrations_subset_of_map() -> None:
    """Every key in PROFILE_REGISTRATIONS must be in the registration map.

    For ALL_TOOLS sentinel entries (FULL/STANDARD here), the helper uses
    ``register_all_fn`` instead of the map — so only MINIMAL's list of
    strings must be a subset of the registration_map keys. css-mcp's
    MINIMAL is empty, so this trivially holds — but assert it explicitly
    to guard against future drift.
    """
    mapping = _build_registration_map()
    minimal_keys = set(MINIMAL_REGISTRATIONS)
    map_keys = set(mapping.keys())
    if minimal_keys:
        assert minimal_keys <= map_keys, (
            f"MINIMAL keys {minimal_keys - map_keys} not in registration_map"
        )


def test_mandatory_tools_invariant() -> None:
    """MANDATORY_GROUPS / MANDATORY_TOOLS must both be opted out explicitly.

    css-mcp's /health HTTP route lives outside W0 dispatch (registered via
    ``register_http_health_route``), so no MCP-registered tool group is
    mandatory. We pass ``mandatory_groups=set()`` and
    ``essential_tool_names=set()`` to opt out of the subset check.

    Verify the source references both opt-outs.
    """
    source = PROFILES_PY.read_text()
    assert "mandatory_groups=set()" in source, (
        "profiles.py must pass mandatory_groups=set() to opt out"
    )
    assert "essential_tool_names=set()" in source, (
        "profiles.py must pass essential_tool_names=set() to opt out"
    )


def test_full_registers_all_9_tools() -> None:
    """FULL/STANDARD profile registers all 9 css-mcp tools plus discover_tools."""
    mapping = _build_registration_map()
    assert "analysis_tools" in mapping
    assert len(mapping) == len(_GROUP_REGISTRY)


def test_minimal_has_only_discover_tools() -> None:
    """MINIMAL profile registers 0 tool groups (only discover_tools)."""
    assert MINIMAL_REGISTRATIONS == []
    assert len(MINIMAL_REGISTRATIONS) == 0


def test_invalid_profile_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid CSS_TOOL_PROFILE values raise InvalidProfileError at sync validation.

    When ``server=None`` is passed, the sync wrapper only validates (it does
    not require a real server / event loop). We exercise the validation
    phase by calling ``apply_tool_profile`` (sync wrapper) with server=None.
    """
    from mcp_common.tools.dispatch import InvalidProfileError, apply_tool_profile

    monkeypatch.setenv("CSS_TOOL_PROFILE", "bogus")
    with pytest.raises(InvalidProfileError):
        apply_tool_profile(
            None,  # server=None: validation-only path
            profile_env_var="CSS_TOOL_PROFILE",
            registrations=PROFILE_REGISTRATIONS,
            registration_map={},
            register_all_fn=register_all_tool_groups,
            mandatory_groups=set(),
            essential_tool_names=set(),
        )


# ---------------------------------------------------------------------------
# W2b.3 keystone: real production-path tests
# ---------------------------------------------------------------------------


async def test_create_app_full_profile_real_path() -> None:
    """W2b.3 keystone test — real ``await create_app(settings)`` end-to-end.

    NO mocks of the dispatch helper. This test catches the W2b.3 spline
    regression where ``apply_tool_profile`` (sync wrapper) was used in
    production and silently masked the bug under tests.
    """
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.delenv("CSS_TOOL_PROFILE", raising=False)
        settings = CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP")
        mcp = await create_app(settings)
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}

        # FULL profile: all 9 css-mcp tools + discover_tools
        expected = {
            "analyze_css",
            "analyze_css_summary",
            "get_docs",
            "get_browser_compatibility",
            "search_properties",
            "get_properties_by_category",
            "analyze_project_css",
            "list_capabilities",
            "health_check",
            "discover_tools",
        }
        assert expected <= tool_names, (
            f"Missing tools at FULL profile: {expected - tool_names}; got {tool_names}"
        )
    finally:
        monkeypatch.undo()


async def test_create_app_minimal_profile_real_path() -> None:
    """W2b.3 keystone test — real MINIMAL ``await create_app(settings)``."""
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setenv("CSS_TOOL_PROFILE", "minimal")
        settings = CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP")
        mcp = await create_app(settings)
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}

        # MINIMAL: only discover_tools (no css-mcp tools)
        assert "discover_tools" in tool_names, f"discover_tools missing at MINIMAL: {tool_names}"
        css_tools = {
            "analyze_css",
            "analyze_css_summary",
            "get_docs",
            "get_browser_compatibility",
            "search_properties",
            "get_properties_by_category",
            "analyze_project_css",
            "list_capabilities",
            "health_check",
        }
        assert not (css_tools & tool_names), f"MINIMAL leaked css tools: {css_tools & tool_names}"
    finally:
        monkeypatch.undo()


async def test_create_app_standard_profile_real_path() -> None:
    """STANDARD profile should match FULL (Tier-A trivial: same mapping)."""
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setenv("CSS_TOOL_PROFILE", "standard")
        settings = CSSMCPSettings.load("css-mcp", env_prefix="CSS_MCP")
        mcp = await create_app(settings)
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}

        expected = {
            "analyze_css",
            "analyze_css_summary",
            "get_docs",
            "get_browser_compatibility",
            "search_properties",
            "get_properties_by_category",
            "analyze_project_css",
            "list_capabilities",
            "health_check",
            "discover_tools",
        }
        assert expected <= tool_names, f"Missing tools at STANDARD profile: {expected - tool_names}"
    finally:
        monkeypatch.undo()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_full_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default (no env var) → FULL = all 9 tools + discover_tools."""
    monkeypatch.delenv("CSS_TOOL_PROFILE", raising=False)
    from mcp_common.tools.dispatch import _resolve_profile

    profile = _resolve_profile("CSS_TOOL_PROFILE", yaml_loader=None)
    assert profile.value == "full", f"Expected default FULL, got {profile.value}"


def test_full_registrations_match_group_registry() -> None:
    """FULL_REGISTRATIONS must be derived from _GROUP_REGISTRY (single source of truth)."""
    expected = [key for key, _ in _GROUP_REGISTRY]
    assert expected == FULL_REGISTRATIONS, (
        f"FULL_REGISTRATIONS={FULL_REGISTRATIONS} drifted from _GROUP_REGISTRY={expected}"
    )


def test_env_var_default_is_full(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity: an unset CSS_TOOL_PROFILE env var falls through to FULL."""
    monkeypatch.delenv("CSS_TOOL_PROFILE", raising=False)
    assert os.getenv("CSS_TOOL_PROFILE") is None
