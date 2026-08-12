# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-08-12

### Added

- Register /health HTTP route for launchd wrapper

### Fixed

- Address crackerjack + test failures

### Testing

- Pin /health HTTP route response shape

### Internal

- Adopt register_http_health_route from mcp-common
- css-mcp: Remove unnecessary model_config type: ignore
- Migrate MCPBaseSettings → OneiricMCPConfig, bump fastmcp to >=3.4.0,<4
- Use __version__ instead of hardcoded version literal

## [0.2.0] - 2026-06-19

### Internal

- gitignore: Add backup file patterns to silence checkpoint tool artifacts

## [0.1.2] - 2026-02-25

### Changed

- Update config, core, docs
