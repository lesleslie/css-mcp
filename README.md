# CSS MCP Server

Universal CSS Analysis and Documentation MCP Server. Analyze any CSS with 150+ metrics for complexity, specificity, and quality.

## Features

- **CSS Analysis**: 150+ metrics for CSS complexity, specificity, and quality
- **MDN Documentation**: Fetch CSS property docs from MDN Web Docs
- **Browser Compatibility**: Check cross-browser support for CSS properties
- **Project Analysis**: Analyze all CSS files in a project

## Installation

```bash
# Using uv
uv pip install css-mcp

# Using pip
pip install css-mcp
```

## Usage

### Start Server

```bash
# Via CLI
css-mcp

# Via Python module
python -m css_mcp.server
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CSS_MCP_HTTP_PORT` | 3050 | Server port |
| `CSS_MCP_HTTP_HOST` | localhost | Server host |
| `CSS_MCP_DEBUG` | false | Enable debug mode |

## Available Tools

| Tool | Description |
|------|-------------|
| `analyze_css` | Full CSS analysis with 150+ metrics |
| `analyze_css_summary` | Quick CSS summary (faster) |
| `get_docs` | MDN documentation for CSS properties |
| `get_browser_compatibility` | Check browser support for properties |
| `search_properties` | Search for CSS properties |
| `get_properties_by_category` | Get properties by category |
| `analyze_project_css` | Analyze all CSS in a project |
| `list_capabilities` | List available capabilities |
| `health_check` | Check server health |

## Programmatic Usage

Use the analyzer directly in Python for any CSS:

### Example: Analyze Any CSS

```python
from css_mcp.analyzer import CSSAnalyzer

# Analyze any CSS content
analyzer = CSSAnalyzer()
metrics = analyzer.analyze(css_content)

# Get complexity score
print(f"Complexity: {metrics.complexity_score}/100")

# Get optimization suggestions
suggestions = analyzer.get_suggestions()
```

## Metrics

The analyzer provides 150+ metrics including:

### Basic Metrics
- Total rules, selectors, properties
- File size (bytes, gzipped)
- Lines of code

### Selector Metrics
- ID, class, element, universal selectors
- Pseudo-classes and pseudo-elements
- Combinators (descendant, child, sibling)
- Selector depth

### Specificity Metrics
- Average, min, max specificity
- High specificity rules
- Specificity distribution

### Property Metrics
- Unique properties
- Category distribution (layout, typography, etc.)
- Vendor prefixes
- `!important` usage
- CSS custom properties

### Quality Metrics
- Duplicate selectors
- Duplicate properties
- Empty rules
- Complexity score
- Efficiency scores

## Browser Compatibility

Built-in compatibility data for common CSS properties across:
- Chrome
- Firefox
- Safari
- Edge

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
pytest

# Type check
mypy css_mcp

# Lint
ruff check css_mcp
```

## License

BSD-3-Clause
