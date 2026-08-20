---
description: Analyze an inline CSS snippet with full metrics, quick summary, or MDN context for any property encountered.
argument-hint: <css-snippet-or-file>
allowed-tools: mcp__css__analyze_css, mcp__css__analyze_css_summary, mcp__css__get_docs
---

# /css-analyze

Analyze an inline CSS snippet for complexity, specificity, and quality.

## Usage

`/css-analyze <css-snippet-or-file>`

## What it does

1. If the input resolves to a readable file path, read its contents first; otherwise treat the input as raw CSS.
2. Short input (< 1 KB or fewer than 20 selectors): calls `mcp__css__analyze_css_summary` for a fast overview.
3. Otherwise: calls `mcp__css__analyze_css` for the full ~150-metric report.
4. If the report surfaces unusual or non-standard properties, follows up with `mcp__css__get_docs` for each one to attach the relevant MDN context to the answer.

## Example

`/css-analyze .btn { display: grid; gap: 0.5rem; }`
