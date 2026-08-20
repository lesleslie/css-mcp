---
description: Run a project-wide CSS audit, scanning all CSS files for complexity, specificity, and quality metrics.
argument-hint: <project-path> [--include PATTERN] [--exclude PATTERN]
allowed-tools: mcp__css__analyze_project_css, mcp__css__list_capabilities, mcp__css__analyze_css_summary
---

# /css-audit-project

Run a comprehensive CSS audit across a project directory.

## Usage

`/css-audit-project <project-path> [--include PATTERN] [--exclude PATTERN]`

## What it does

1. Calls `mcp__css__list_capabilities` to confirm the server is healthy and surface the available tool set.
2. Calls `mcp__css__analyze_project_css` with the project path and any include/exclude glob patterns.
3. For any file the project scanner flags as a complexity hotspot, falls back to `mcp__css__analyze_css_summary` on the individual file to give the user a quick-mode breakdown without re-walking the directory.
4. Returns per-file metrics plus the project-wide rollup (total rules, average specificity, complexity distribution, top optimization opportunities).

## Example

`/css-audit-project /Users/les/Projects/my-app --include '**/*.css' --exclude '**/dist/**'`
