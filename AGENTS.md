# Repository Guidelines

## Project Structure & Module Organization

- `css_mcp/` contains the MCP server package, including tool implementations, parsing or analysis helpers, and server entrypoints.
- Tests should live under `tests/`, mirroring package structure when practical.
- Root files such as `pyproject.toml`, `uv.lock`, and `README.md` define packaging, dependency, and operator guidance; keep behavioral documentation there rather than scattering it across scripts.
- Generated output in `dist/` or coverage artifacts should not be edited manually.

## Build, Test, and Development Commands

- `uv sync --group dev` installs development dependencies.
- `uv run pytest` runs the full test suite.
- `uv run mypy css_mcp` validates typing.
- `uv run ruff check css_mcp tests` and `uv run ruff format css_mcp tests` cover linting and formatting.
- Run the MCP server with the repo's documented local command before validating tool behavior.

## Coding Style & Naming Conventions

- Use explicit type hints, small focused modules, and structured tool inputs and outputs.
- Keep module names snake_case and classes PascalCase.
- Prefer extending existing CSS analysis or documentation helpers rather than adding parallel tool paths.

## Testing Guidelines

- Add tests with each tool or parser change, especially around CSS analysis edge cases and response formatting.
- Prefer deterministic fixture inputs over live or generated CSS blobs unless the case requires end-to-end validation.
- Review coverage locally after larger changes.

## Commit & Pull Request Guidelines

- Use focused commits such as `fix(parser): handle nested rule output`.
- PRs should describe changed tools, commands run for validation, and any user-facing output differences.

## Security & Configuration Tips

- Validate file paths and CSS inputs rigorously.
- Keep secrets and machine-specific paths out of version control.
