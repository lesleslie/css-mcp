# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For a shorter, tool-neutral bootstrap document, start with `AGENTS.md`.

## Project Overview

CSS MCP Server is an MCP (Model Context Protocol) server for CSS analysis and documentation, designed for the FastBlocks ecosystem. It provides 9 tools for analyzing programmatically generated CSS from style adapters like Kelp UI and WebAwesome.

## Development Commands

```bash
# Install dependencies
uv sync --group dev

# Run tests
pytest

# Type check
mypy css_mcp

# Lint
ruff check css_mcp

# Run the server locally
css-mcp
# or
python -m css_mcp.server
```

## Architecture

The server is built on FastMCP and follows a modular architecture:

```
css_mcp/
├── server.py      # MCP server entry point, async create_app + sync wrapper
├── tools/         # Tool implementations
│   ├── __init__.py # Pydantic input models + register_tools (all 9 tools) + register_health_tool (health probe)
│   └── profiles.py # Tool profile dispatch (W4.1, mcp-common>=0.18.0)
├── analyzer.py    # Core CSS analysis engine (~150 derived metrics over 78 CSSMetrics fields)
├── mdn_fetcher.py # MDN Web Docs documentation fetcher
├── compat.py      # Browser compatibility checker
├── config.py      # Configuration with environment variable support
├── cli.py         # Console-script entry (css-mcp) wired to mcp-common factory
├── __main__.py    # `python -m css_mcp` entry point
└── __init__.py    # Package metadata (CSSAnalyzer, CSSMetrics, CSSMCPSettings exports)
```

### Key Components

**CSSAnalyzer** (`analyzer.py`): The core analysis engine that parses CSS using tinycss2 and computes ~150 derived metrics (78 `CSSMetrics` fields plus selector/property counters) including:

- Complexity scores (0-100)
- Specificity analysis with distribution
- Selector patterns (ID, class, element, universal)
- Property categorization (layout, typography, flexbox, grid, etc.)
- Quality metrics (duplicates, empty rules, !important usage)

**MDNFetcher** (`mdn_fetcher.py`): Fetches CSS property documentation from MDN Web Docs with built-in fallback metadata for common properties.

**BrowserCompatChecker** (`compat.py`): Built-in browser compatibility data for major CSS properties across Chrome, Firefox, Safari, and Edge.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `analyze_css` | Full CSS analysis with ~150 derived metrics |
| `analyze_css_summary` | Quick summary (faster) |
| `get_docs` | MDN documentation for CSS properties |
| `get_browser_compatibility` | Browser support checking |
| `search_properties` | Search CSS properties |
| `get_properties_by_category` | Properties by category |
| `analyze_project_css` | Project-wide CSS analysis |
| `list_capabilities` | List available tools |
| `health_check` | Server health status |

## Tool Profile System

css-mcp adopts the W0 tool profile dispatch from `mcp-common>=0.18.0` with
a Tier-A trivial 3-tier mapping (see `docs/architecture/tool-profile-rationale.md`
for the full rationale):

| Profile | Tools | Env var |
|------------|--------------------------------------|-------------------------------|
| `MINIMAL` | `health_check` + `discover_tools` | `CSS_TOOL_PROFILE=minimal` |
| `STANDARD` | All 9 tools + `discover_tools` | `CSS_TOOL_PROFILE=standard` |
| `FULL` | All 9 tools + `discover_tools` | `CSS_TOOL_PROFILE=full` (default) |

The `/health` HTTP route is registered **inside `register_health_tool`**
alongside the MCP `health_check` tool. It is available whenever
`health_check` is — every profile that includes `health_tools`
(MINIMAL, STANDARD, FULL). The route is load-bearing for the launchd
wrapper that supervises this server; the pre-existing
`tests/unit/test_health_route.py` test pins this invariant.

### Dispatch surface

- `css_mcp/tools/profiles.py` — `PROFILE_REGISTRATIONS`,
  `_GROUP_REGISTRY` (single source of truth — drives the registration
  map AND the bulk registration loop), `apply_css_tool_profile`
  (async, the W2b.3 keystone entry point)
- `css_mcp/tools/__init__.py::register_health_tool` — the canonical
  health probe callable (registers the MCP `health_check` tool + the
  HTTP `/health` route). Required for the W4.1 `MINIMAL=health` mapping.
- `css_mcp/server.py::create_app` — async production entry point;
  threads caller-supplied `settings` through to the registration paths
- `css_mcp/server.py::create_server` — sync wrapper via `_run_async_safely`
  (works from both sync CLI startup and async test contexts)
- `tests/unit/test_tool_profile.py` — 28 wiring tests including:
  - AST guard that structurally checks for
    `await apply_css_tool_profile(server, settings)` (NOT just call
    count — counting `ast.Call` would be a tautology that passes even
    if `await` is removed)
  - Two regression tests that monkey-patch `CSSMCPSettings.load` to
    fail if any registration path silently re-loads settings from the
    environment (the W4.1 round-1 regression)
  - Strict-equality assertions on the registered tool set at each
    profile (`tool_names == expected`, not `<=`)

## Configuration

Environment variables (prefix: `CSS_MCP_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `CSS_MCP_HTTP_PORT` | 3050 | Server port |
| `CSS_MCP_HTTP_HOST` | localhost | Server host |
| `CSS_MCP_DEBUG` | false | Enable debug mode |

## Dependencies

- **fastmcp**: MCP server framework
- **tinycss2**: CSS parsing (covers both selector parsing and AST analysis)
- **httpx**: Async HTTP for MDN fetching
- **pydantic**: Data validation
- **mcp-common**: Shared MCP utilities
- **oneiric**: Configuration management

## FastBlocks Integration

This server is designed for analyzing CSS generated by FastBlocks style adapters:

- Kelp UI (custom lightweight framework)
- WebAwesome (Font Awesome components)
- Vanilla (minimal semantic styling)

When analyzing generated CSS, use `CSSAnalyzer` directly:

```python
from css_mcp.analyzer import CSSAnalyzer

analyzer = CSSAnalyzer()
metrics = analyzer.analyze(css_content)
suggestions = analyzer.get_suggestions()
```
