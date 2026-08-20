---
description: Check cross-browser compatibility for one or more CSS properties and pull supporting MDN documentation.
argument-hint: <property> [<property> ...] [--browser chrome,firefox,safari,edge]
allowed-tools: mcp__css__get_browser_compatibility, mcp__css__get_docs, mcp__css__search_properties, mcp__css__list_capabilities
---

# /css-check-compat

Verify cross-browser support for one or more CSS properties and follow up with MDN documentation when the result is partial or unknown.

## Usage

`/css-check-compat <property> [<property> ...] [--browser chrome,firefox,safari,edge]`

## What it does

1. Calls `mcp__css__list_capabilities` to confirm the server is healthy and to surface the canonical property list (used to disambiguate user typos).
2. If a property name does not appear in the canonical list, falls back to `mcp__css__search_properties` for a fuzzy match and presents the closest candidates before proceeding.
3. Calls `mcp__css__get_browser_compatibility` with the resolved property names plus the requested target browsers (defaults: chrome, firefox, safari, edge).
4. For any property the compatibility report marks as `partial` or `unknown`, follows up with `mcp__css__get_docs` so the user gets the relevant MDN context (baseline support, caveats, fallback strategies) in the same response.

## Example

`/css-check-compat container-type subgrid --browser chrome,firefox,safari`
