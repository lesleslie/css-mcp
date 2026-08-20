# css-mcp Tool Profile Adoption (W4.1)

**Wave**: 4 (Tier-A adoption across 10 repos)
**Status**: Adopted 2026-08-18 (round 1 fixes applied 2026-08-18)
**Author**: Claude (W4.1 subagent)
**W0 helper**: `mcp-common>=0.18.0`

## Summary

css-mcp adopts the W0 tool profile dispatch (`mcp_common.tools.dispatch._apply_tool_profile`)
with the W4.1 canonical 3-tier mapping:

| Profile | Tools | Use case |
|------------|------------------------------------------------|---------------------------------------|
| `MINIMAL` | `health_check` + `discover_tools` | Health-probe-only / control-plane |
| `STANDARD` | All 9 css-mcp tools + `discover_tools` | Daily development |
| `FULL` | All 9 css-mcp tools + `discover_tools` | Same as STANDARD (css-mcp is Tier-A small) |

The pre-existing `/health` HTTP route (registered via
`mcp_common.health.register_http_health_route`) lives **inside**
`register_health_tool` (not separately) so the W0 dispatch can guarantee
`health_check` is exposed at every profile that includes `health_tools`.
The HTTP route is therefore always available whenever `health_check` is —
both at MINIMAL and at STANDARD/FULL.

## Rationale

### Why MINIMAL = `["health_tools"]` (canonical W4.1 mapping)

The W4.1 plan explicitly requires `MINIMAL=health`. The brief notes that
"the fact that an HTTP `/health` route exists outside MCP dispatch does
NOT supersede that requirement" — implementing the spec means
registering the **MCP** `health_check` tool at MINIMAL, not just relying
on the HTTP route.

To make this possible, `css_mcp/tools/__init__.py` exposes two separate
callables:

| Function | Registers |
|----------|-----------|
| `register_health_tool(mcp, config)` | The MCP `health_check` tool + the HTTP `/health` route |
| `register_tools(mcp, config)` | Everything: `register_health_tool` first, then the 8 analysis tools |

The split is the W4.1 round-1 reviewer fix: a single combined function
(`register_tools`) cannot selectively expose the health probe at MINIMAL.
Now `register_health_tool` can be registered independently via the
W0 dispatch.

### Why 3 tiers when STANDARD == FULL

The brief mandates the 3-tier mapping for Tier-A repos. css-mcp's tool
count (9) is small enough that splitting STANDARD from FULL adds no
value, but the canonical schema requires both. We set:

- `STANDARD` → `FULL_REGISTRATIONS` (a list of group keys; the dispatch
  loop iterates them)
- `FULL` → `ALL_TOOLS` (the sentinel that triggers `register_all_fn`)

The `ALL_TOOLS` sentinel is **only honored at the FULL key** — at any
other key the dispatch loop tries to iterate it as a list and fails
(`TypeError: 'type' object is not iterable`). Putting it at STANDARD breaks
iteration.

### Why async `create_app` (and sync `create_server` wrapper)

The W0 helper `_apply_tool_profile` is async. Per the W2b.3 spline
lesson, calling the sync wrapper `apply_tool_profile` from inside a
running event loop raises `RuntimeError`. Therefore:

- The **production path** (`css_mcp/server.py::create_app`) is `async def`
  and uses `await apply_css_tool_profile(server, settings)`.
- The **sync wrapper** (`css_mcp/server.py::create_server`) bridges via
  `_run_async_safely(create_app(settings))` so `get_app()`, the CLI
  startup, and the existing `test_health_route.py` test continue to
  work without modification.
- `_run_async_safely` uses `asyncio.run` from sync contexts and falls
  back to a `ThreadPoolExecutor(max_workers=1)` bridge when a loop is
  already running (matches the W3.4 unifi-mcp pattern).

The `tests/unit/test_tool_profile.py::test_server_awaits_apply_css_tool_profile`
AST guard structurally checks for
`ast.Await(value=ast.Call(func=ast.Name(id="apply_css_tool_profile")))`
(NOT just call count — counting `ast.Call` would be a tautology that
passes even when `await` is removed; this is the W3.2 round-1 fix).

### Why caller-supplied `settings` is preserved (W4.1 round-1 fix)

`apply_css_tool_profile(server, settings)` forwards the caller-supplied
`settings` through to:

- `_build_registration_map(settings)` — captures `settings` via
  default-argument in each lambda (the W3.1 lesson)
- `register_all_tool_groups` — called via
  `register_all_fn=lambda server: register_all_tool_groups(server, settings)`

The W4.1 round-1 reviewer found that registration paths were
**re-loading** `CSSMCPSettings.load(...)` from the environment, silently
discarding any test-injected overrides. The fix threads `settings`
through every registration call so production tests with custom
configuration (e.g. a sentinel `server_name`) reach the registration
callbacks unchanged. Two regression tests
(`test_caller_supplied_settings_are_preserved` and
`test_register_all_tool_groups_does_not_reload_settings`) monkey-patch
`CSSMCPSettings.load` to track calls; if a registration path re-loads
settings, the tests fail loud.

### Why `_GROUP_REGISTRY` is the actual single source of truth

The W3.2 lesson: `FULL_REGISTRATIONS` and the registration map can drift
out of sync if maintained independently. `_GROUP_REGISTRY` is a
`list[tuple[str, str]]` of `(group_key, attr_name)` pairs. Both
`FULL_REGISTRATIONS` and the registration map / bulk registration derive
from it via `getattr(css_mcp.tools, attr_name)`:

```python
_GROUP_REGISTRY: list[tuple[str, str]] = [
    ("health_tools", "register_health_tool"),
    ("analysis_tools", "register_tools"),
]

def _build_registration_map(settings):
    from css_mcp import tools as _tools_module
    mapping = {}
    for key, attr_name in _GROUP_REGISTRY:
        register_fn = getattr(_tools_module, attr_name)
        mapping[key] = lambda server, _fn=register_fn, _cfg=settings: _fn(server, _cfg)
    return mapping

def register_all_tool_groups(server, settings):
    from css_mcp import tools as _tools_module
    for _key, attr_name in _GROUP_REGISTRY:
        getattr(_tools_module, attr_name)(server, settings)
```

The W4.1 round-1 reviewer found that the previous implementation had a
name-specific `if attr_name == "register_tools":` conditional in
`register_all_tool_groups` and a hard-coded `"analysis_tools"` key in
`_build_registration_map`. The round-1 fix removes both — adding a new
group requires editing only `_GROUP_REGISTRY`.

### Why default-argument capture for the lambda binding

Each `register_<group>_tools(mcp, config)` function takes 2 arguments.
The W0 helper expects single-arg callables. Following the W3.1
graphics-mcp lesson, each registration map entry uses default-argument
capture to prevent the classic late-binding bug:

```python
mapping[key] = lambda server, _fn=register_fn, _cfg=settings: _fn(server, _cfg)
```

The `_fn=register_fn` and `_cfg=settings` defaults bind the values at
lambda-creation time, not at call time.

### Why `essential_tool_names={"health_check"}`

The W0 helper's subset check asserts that all tool names in
`essential_tool_names` are present after dispatch. Setting
`essential_tool_names={"health_check"}` enforces the W4.1 canonical
MINIMAL=health invariant — if a future refactor accidentally drops
`health_tools` from MINIMAL_REGISTRATIONS, the subset check raises
`ValueError` at startup (fail-loud). The
`test_essential_tool_names_subset_check_enforced` test asserts the
source passes this exact set.

## Files changed

| File | Change |
|------|--------|
| `css_mcp/tools.py` | **RENAMED** → `css_mcp/tools/__init__.py` (converted from module to package) |
| `css_mcp/tools/__init__.py` | **MODIFIED** — split out `register_health_tool(mcp, config)` from `register_tools(mcp, config)` so the health probe is registerable independently |
| `css_mcp/tools/profiles.py` | **REWRITTEN** — added `health_tools` registry entry, MINIMAL=health, settings threaded through all registration paths, no name-specific conditionals |
| `css_mcp/server.py` | **MODIFIED** — `await apply_css_tool_profile(mcp, settings)` (forwards caller settings; was `apply_css_tool_profile(mcp)`) |
| `pyproject.toml` | **MODIFIED** — bumped `mcp-common>=0.17.0` → `>=0.18.0` |
| `uv.lock` | **MODIFIED** — reflects the mcp-common pin bump |
| `tests/unit/test_tool_profile.py` | **REWRITTEN** — 28 wiring tests, strict-equality tool set assertions, monkeypatch fixture, settings-preservation regression tests |
| `tests/unit/test_health_route.py` | **MODIFIED** — auto-formatted by `ruff format` (no behavioral change) |
| `tests/test_version_sync.py` | **MODIFIED** — auto-formatted by `ruff format` (no behavioral change) |
| `CLAUDE.md` | **MODIFIED** — added "Tool Profile System" subsection + updated architecture block |

## Pre-flight verification

```bash
$ grep -nE 'def register_|@mcp\.tool\(' css_mcp/tools/*.py
css_mcp/tools/__init__.py:94:def register_health_tool(mcp: FastMCP, config: CSSMCPSettings) -> None:
css_mcp/tools/__init__.py:130:def register_tools(mcp: FastMCP, config: CSSMCPSettings) -> None:
css_mcp/tools/__init__.py:110:    @mcp.tool()   # health_check (in register_health_tool)
css_mcp/tools/__init__.py:143:    @mcp.tool()   # analyze_css
css_mcp/tools/__init__.py:181:    @mcp.tool()   # analyze_css_summary
css_mcp/tools/__init__.py:207:    @mcp.tool()   # get_docs
css_mcp/tools/__init__.py:239:    @mcp.tool()   # get_browser_compatibility
css_mcp/tools/__init__.py:278:    @mcp.tool()   # search_properties
css_mcp/tools/__init__.py:309:    @mcp.tool()   # get_properties_by_category
css_mcp/tools/__init__.py:354:    @mcp.tool()   # analyze_project_css
css_mcp/tools/__init__.py:450:    @mcp.tool()   # list_capabilities
```

**Total: 2 register functions (`register_health_tool`, `register_tools`) +
9 `@mcp.tool()` decorators** = 9 tools (1 in `register_health_tool` +
8 in `register_tools`). The MINIMAL=health spec is implementable.

## Behavioral parity

| Configuration | Pre-refactor | Post-refactor | Match? |
|----------------------------------|--------------------|--------------------------------|---------|
| No env var | 9 tools | 9 + `discover_tools` = 10 | additive — meta-tool required by W0 spec |
| `CSS_TOOL_PROFILE=minimal` | (no profile system)| `health_check` + `discover_tools` = 2 | new — Tier-A canonical MINIMAL=health |
| `CSS_TOOL_PROFILE=standard` | (no profile system)| 9 + `discover_tools` = 10 | new — explicit |
| `CSS_TOOL_PROFILE=full` | (no profile system)| 9 + `discover_tools` = 10 | new — explicit |
| `CSS_TOOL_PROFILE=bogus` | (no profile system)| `InvalidProfileError` | new — fail-loud |

The `/health` HTTP route is preserved at every profile that includes
`health_tools` (MINIMAL, STANDARD, FULL) — verified by the pre-existing
`tests/unit/test_health_route.py` which is unchanged.

## Notes for the next W4 wave (excalidraw-mcp)

1. **Tier-A trivial pattern is reusable.** Two `register_<group>_tools`
   functions (one for health, one for everything else) →
   `_GROUP_REGISTRY = [(<key1>, <attr1>), (<key2>, <attr2>)]`,
   MINIMAL=`[<key1>]`, STANDARD/FULL via `register_all_fn`.

1. **If `excalidraw_mcp/tools/` is not yet a package**, convert
   `tools.py` → `tools/__init__.py` BEFORE creating `tools/profiles.py`.
   Python won't import `css_mcp.tools.profiles` if `css_mcp/tools.py`
   already exists as a module file.

1. **AST guard for `await apply_<repo>_tool_profile(app)` must be
   structural** — `ast.Await(value=ast.Call(func=ast.Name(id=...)))`,
   not call-count. The latter is a tautology that would pass even when
   `await` is removed (the W3.2 round-1 fix). Verified by manually
   mutating css-mcp's server.py — guard failed correctly.

1. **The `_run_async_safely` helper from unifi-mcp / css-mcp is the
   pattern to copy** if excalidraw-mcp's main entrypoint is sync but
   the W0 dispatch is async. ThreadPoolExecutor bridge avoids the
   `RuntimeError` from `asyncio.run()` inside a running event loop.

1. **Thread `settings` through every registration path.** The W4.1
   round-1 regression was re-loading `CSSMCPSettings.load(...)` inside
   registration callbacks, discarding caller-supplied overrides. Pass
   `settings` to `apply_<repo>_tool_profile(server, settings)`,
   forward it to `_build_registration_map(settings)` and
   `register_all_tool_groups(server, settings)`, and bind via
   default-argument capture in each lambda. Write a regression test
   that monkey-patches `<settings>.load` and fails if it gets called.

1. **STANDARD must use a list, not `ALL_TOOLS` sentinel.** The W0
   dispatch loop iterates the value as a list; `ALL_TOOLS` is only
   honored at the FULL key. If STANDARD == FULL, both can use
   `FULL_REGISTRATIONS` (a list) OR the FULL key alone can use
   `ALL_TOOLS` — pick one consistently.

1. **MINIMAL = `<health_key>` with `essential_tool_names={"<health_tool>"}`**
   is the canonical pattern for the W4.1 spec. Empty `mandatory_groups`
   (the per-profile registration walk already handles MINIMAL).
   `essential_tool_names` enforces the subset check that catches
   accidental health-tool drift.

1. **`_GROUP_REGISTRY` must drive BOTH the registration map AND the
   bulk registration loop.** Avoid name-specific conditionals like
   `if attr_name == "register_tools":` — they break the SSOT invariant.
   Use `getattr(<module>, attr_name)` uniformly.

1. **Lambda binding for 2-arg register fns uses default-argument
   capture** (W3.1 lesson):
   `lambda app, _fn=register_fn, _cfg=settings: _fn(app, _cfg)`
   The `_fn=...` and `_cfg=...` defaults bind at lambda-creation time.

1. **Strict-equality tool set assertions** in production-path tests
   (W2b.1 lesson). Use `tool_names == expected` so unreported extra
   tools fail loud — `expected <= tool_names` masks bugs.

1. **Use the standard `monkeypatch` pytest fixture**, not manual
   `pytest.MonkeyPatch()` lifecycle (`monkeypatch = MonkeyPatch()` +
   try/finally + `monkeypatch.undo()`). The fixture handles teardown
   automatically.

1. **The mcp-common pin bump to `>=0.18.0` is mandatory** — the
   `apply_tool_profile` and `_apply_tool_profile` helpers were
   introduced in 0.18.0. The `test_pyproject_bumps_mcp_common_to_0_18`
   test enforces this.
