# css-mcp Tool Profile Adoption (W4.1)

**Wave**: 4 (Tier-A adoption across 10 repos)
**Status**: Adopted 2026-08-18
**Author**: Claude (W4.1 subagent)
**W0 helper**: `mcp-common>=0.18.0`

## Summary

css-mcp adopts the W0 tool profile dispatch (`mcp_common.tools.dispatch._apply_tool_profile`)
with a Tier-A trivial 3-tier mapping:

| Profile    | Tools                                | Use case                                  |
|------------|--------------------------------------|-------------------------------------------|
| `MINIMAL`  | 0 groups (just `discover_tools`)     | Health-probe-only / control-plane         |
| `STANDARD` | All 9 tools + `discover_tools`       | Daily development                         |
| `FULL`     | All 9 tools + `discover_tools`       | Same as STANDARD (css-mcp is Tier-A small) |

The pre-existing `/health` HTTP route (registered via
`mcp_common.health.register_http_health_route`) lives **outside** the W0
dispatch and is always available regardless of profile — the launchd wrapper
script that supervises css-mcp depends on `GET /health` returning JSON
with `status="ok"`, so this route is load-bearing (see
`tests/unit/test_health_route.py` for the regression test).

## Rationale

### Why MINIMAL = empty (not "health")

The brief's canonical trivial mapping is `MINIMAL=health, STANDARD/FULL=all`.
For css-mcp, "health" is ambiguous:

1. The `/health` HTTP route (registered by `register_http_health_route`)
   is load-bearing for the launchd wrapper and is **always on** — it
   lives outside the W0 dispatch entirely.
2. The MCP `health_check` tool (an `@mcp.tool()` decorator inside
   `register_tools`) is a discoverable meta-tool, not load-bearing.

The W3.4 unifi-mcp precedent (also Tier-A, also has a load-bearing
`/healthz` HTTP route) chose MINIMAL=empty with explicit opt-outs from
both `MANDATORY_GROUPS` and `MANDATORY_TOOLS`. We follow the same pattern:

> **No tools are mandatory at any profile level for css-mcp** — every
> tool group is opt-in per profile. The `/health` HTTP route lives outside
> the W0 dispatch, so it is always available regardless of profile. We
> pass empty sets explicitly to opt out of the MANDATORY_GROUPS /
> MANDATORY_TOOLS subset checks.

This wording is precise (the W3.2 lesson): it does NOT say "no MCP-registered
health tools" (which would be ambiguous given the `/health` HTTP route
exists), it explicitly notes that the route lives outside the dispatch.

### Why 3 tiers when STANDARD == FULL

The brief mandates the 3-tier mapping for Tier-A repos. css-mcp's tool
count (9) is small enough that splitting STANDARD from FULL adds no value,
but the canonical schema requires both. We set both to `ALL_TOOLS`
(via `register_all_fn=register_all_tool_groups`) so adding more tools
later only requires extending `_GROUP_REGISTRY`.

### Why async `create_app` (and sync `create_server` wrapper)

The W0 helper `_apply_tool_profile` is async. Per the W2b.3 spline lesson,
calling the sync wrapper `apply_tool_profile` from inside a running event
loop raises `RuntimeError`. Therefore:

- The **production path** (`css_mcp/server.py::create_app`) is `async def`
  and uses `await apply_css_tool_profile(mcp)`.
- The **sync wrapper** (`css_mcp/server.py::create_server`) bridges via
  `_run_async_safely(create_app(settings))` so `get_app()`, the CLI
  startup, and the existing `test_health_route.py` test continue to work
  without modification.
- `_run_async_safely` uses `asyncio.run` from sync contexts and falls
  back to a `ThreadPoolExecutor(max_workers=1)` bridge when a loop is
  already running (matches the W3.4 unifi-mcp pattern).

The `tests/unit/test_tool_profile.py::test_server_awaits_apply_css_tool_profile`
AST guard structurally checks for
`ast.Await(value=ast.Call(func=ast.Name(id="apply_css_tool_profile")))`
(NOT just call count — counting `ast.Call` would be a tautology that
passes even when `await` is removed; this is the W3.2 round-1 fix).

### Why `_GROUP_REGISTRY` as a single source of truth

The W3.2 lesson: `FULL_REGISTRATIONS` and the docstring can drift out of
sync if they're maintained independently. `_GROUP_REGISTRY` is a
`list[tuple[str, str]]` of `(group_key, attr_name)` pairs. Both
`FULL_REGISTRATIONS` and `_build_registration_map()` derive from it.
Adding a new group requires editing only this constant.

### Why default-argument capture for the lambda binding

css-mcp's `register_tools(app, settings)` takes 2 arguments. The W0
helper expects single-arg callables. Following the W3.1 graphics-mcp
lesson, the registration map entry uses default-argument capture to
prevent the classic late-binding bug:

```python
mapping["analysis_tools"] = lambda app, _fn=register_tools, _cfg=settings: _fn(app, _cfg)
```

The `_fn=register_tools` and `_cfg=settings` defaults bind the values
at lambda-creation time, not at call time.

## Files changed

| File | Change |
|------|--------|
| `css_mcp/tools/profiles.py` | **CREATED** — profile dispatch module |
| `css_mcp/server.py` | **MODIFIED** — added `async def create_app`, refactored `create_server` as sync wrapper via `_run_async_safely` |
| `pyproject.toml` | **MODIFIED** — bumped `mcp-common>=0.17.0` → `>=0.18.0` |
| `tests/unit/test_tool_profile.py` | **CREATED** — 17 wiring tests (AST guards + real production-path tests) |
| `CLAUDE.md` | **MODIFIED** — added "Tool Profile System" subsection |

## Pre-flight verification

```bash
$ grep -nE 'def register_|@mcp\.tool\(' css_mcp/*.py
css_mcp/tools.py:94:def register_tools(mcp: FastMCP, config: CSSMCPSettings) -> None:
css_mcp/tools.py:102:    @mcp.tool()
css_mcp/tools.py:140:    @mcp.tool()
css_mcp/tools.py:166:    @mcp.tool()
css_mcp/tools.py:198:    @mcp.tool()
css_mcp/tools.py:237:    @mcp.tool()
css_mcp/tools.py:268:    @mcp.tool()
css_mcp/tools.py:313:    @mcp.tool()
css_mcp/tools.py:409:    @mcp.tool()
css_mcp/tools.py:459:    @mcp.tool()
```

**Total: 1 `register_tools` function + 9 `@mcp.tool()` decorators** = 9
tools (analyze_css, analyze_css_summary, get_docs, get_browser_compatibility,
search_properties, get_properties_by_category, analyze_project_css,
list_capabilities, health_check) — matches the CLAUDE.md tool table.

## Behavioral parity

| Configuration                    | Pre-refactor        | Post-refactor                  | Match?  |
|----------------------------------|---------------------|--------------------------------|---------|
| No env var                       | 9 tools             | 9 + `discover_tools` = 10      | additive — meta-tool required by W0 spec |
| `CSS_TOOL_PROFILE=minimal`       | (no profile system) | 0 css tools + `discover_tools` = 1 | new — Tier-A profile system |
| `CSS_TOOL_PROFILE=standard`      | (no profile system) | 9 + `discover_tools` = 10      | new — explicit |
| `CSS_TOOL_PROFILE=full`          | (no profile system) | 9 + `discover_tools` = 10      | new — explicit |
| `CSS_TOOL_PROFILE=bogus`         | (no profile system) | `InvalidProfileError`          | new — fail-loud |

The `/health` HTTP route (load-bearing for launchd wrapper) is preserved
at all profiles — verified by `tests/unit/test_health_route.py` which is
unchanged.

## Notes for the next W4 wave (excalidraw-mcp)

1. **Tier-A trivial pattern is reusable.** Single `register_*_tools`
   function → `_GROUP_REGISTRY = [(<key>, <attr_name>)]`, FULL =
   ALL_TOOLS via `register_all_fn`. excalidraw-mcp likely follows the
   same shape.
2. **AST guard for `await apply_<repo>_tool_profile(app)` must be
   structural** — `ast.Await(value=ast.Call(func=ast.Name(id=...)))`,
   not call-count. The latter is a tautology.
3. **The `_run_async_safely` helper from unifi-mcp / css-mcp is the
   pattern to copy** if excalidraw-mcp's main entrypoint is sync but
   the W0 dispatch is async. ThreadPoolExecutor bridge avoids the
   `RuntimeError` from `asyncio.run()` inside a running event loop.
4. **MINIMAL = empty with explicit `mandatory_groups=set()` /
   `essential_tool_names=set()` opt-outs** is the correct pattern when
   the repo's load-bearing health surface is the HTTP `/health` route
   (outside W0 dispatch), NOT an MCP-registered tool.
5. **The mcp-common pin bump to `>=0.18.0` is mandatory** — the
   `apply_tool_profile` and `_apply_tool_profile` helpers were
   introduced in 0.18.0.