"""MCP Tools for CSS Analysis Server.

Provides tools for:
- CSS analysis with 150+ metrics
- MDN documentation fetching
- Browser compatibility checking
- Project-wide CSS analysis
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from oneiric.core.logging import get_logger
from pydantic import BaseModel, Field, field_validator

from css_mcp.analyzer import CSSAnalyzer
from css_mcp.compat import BrowserCompatChecker
from css_mcp.mdn_fetcher import get_mdn_fetcher

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from css_mcp.config import CSSMCPSettings

logger = get_logger(__name__)


# Input models for tool validation
class CSSInput(BaseModel):
    """Input for CSS analysis."""

    css: str = Field(
        ...,
        min_length=1,
        max_length=10 * 1024 * 1024,  # 10MB max
        description="CSS content to analyze",
    )

    @field_validator("css")
    @classmethod
    def validate_css(cls, v: str) -> str:
        """Validate CSS content."""
        return v.strip()


class PropertyInput(BaseModel):
    """Input for property documentation."""

    property_name: str = Field(..., min_length=1, max_length=100, description="CSS property name")

    @field_validator("property_name")
    @classmethod
    def validate_property(cls, v: str) -> str:
        """Validate and normalize property name."""
        return v.lower().strip().replace(" ", "-")


class CompatibilityInput(BaseModel):
    """Input for compatibility check."""

    properties: list[str] = Field(
        ..., min_length=1, max_length=50, description="List of CSS properties to check"
    )
    target_browsers: list[str] | None = Field(
        default=None,
        description="Target browsers (e.g., ['chrome', 'firefox', 'safari', 'edge'])",
    )


class ProjectInput(BaseModel):
    """Input for project-wide analysis."""

    path: str = Field(..., description="Path to project directory or CSS file")
    include_patterns: list[str] | None = Field(
        default=["**/*.css"], description="Glob patterns for CSS files"
    )
    exclude_patterns: list[str] | None = Field(
        default=["**/node_modules/**", "**/.venv/**", "**/vendor/**"],
        description="Patterns to exclude",
    )


class SearchInput(BaseModel):
    """Input for property search."""

    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")


def register_tools(mcp: FastMCP, config: CSSMCPSettings) -> None:
    """Register all CSS analysis tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        config: Server configuration
    """

    @mcp.tool()
    async def analyze_css(input_data: CSSInput) -> dict[str, Any]:
        """Analyze CSS content and return comprehensive metrics.

        Provides 150+ metrics including:
        - Complexity score (0-100)
        - Specificity analysis
        - Selector patterns
        - Property usage
        - Color analysis
        - Optimization suggestions

        Args:
            input_data: CSS content to analyze

        Returns:
            Dictionary with metrics and suggestions
        """
        try:
            analyzer = CSSAnalyzer()
            metrics = analyzer.analyze(input_data.css)
            suggestions = analyzer.get_suggestions()

            return {
                "status": "success",
                "metrics": metrics.model_dump(),
                "summary": metrics.to_summary(),
                "suggestions": suggestions,
                "rules_count": len(analyzer.get_rules()),
            }

        except Exception as e:
            logger.exception("CSS analysis failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
            }

    @mcp.tool()
    async def analyze_css_summary(input_data: CSSInput) -> dict[str, Any]:
        """Get a quick summary of CSS analysis (faster than full analysis).

        Args:
            input_data: CSS content to analyze

        Returns:
            Summary with key metrics
        """
        try:
            analyzer = CSSAnalyzer()
            metrics = analyzer.analyze(input_data.css)

            return {
                "status": "success",
                "summary": metrics.to_summary(),
            }

        except Exception as e:
            logger.exception("CSS summary failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
            }

    @mcp.tool()
    async def get_docs(input_data: PropertyInput) -> dict[str, Any]:
        """Get MDN documentation for a CSS property.

        Fetches documentation from MDN Web Docs including:
        - Property summary
        - Syntax
        - Initial value
        - Browser compatibility

        Args:
            input_data: CSS property name

        Returns:
            Documentation for the property
        """
        try:
            fetcher = await get_mdn_fetcher()
            docs = await fetcher.get_property_docs(input_data.property_name)

            return {
                "status": "success",
                "documentation": docs.model_dump(),
            }

        except Exception as e:
            logger.exception("Failed to get docs", prop=input_data.property_name, error=str(e))
            return {
                "status": "error",
                "error": str(e),
            }

    @mcp.tool()
    async def get_browser_compatibility(
        input_data: CompatibilityInput,
    ) -> dict[str, Any]:
        """Check browser compatibility for CSS properties.

        Checks support across major browsers:
        - Chrome
        - Firefox
        - Safari
        - Edge

        Args:
            input_data: Properties and target browsers

        Returns:
            Compatibility information for each property
        """
        try:
            checker = BrowserCompatChecker(
                target_browsers=input_data.target_browsers,
            )

            results = checker.check_properties(input_data.properties)
            summary = checker.get_compatibility_summary(input_data.properties)

            return {
                "status": "success",
                "properties": {prop: result.to_dict() for prop, result in results.items()},
                "summary": summary,
            }

        except Exception as e:
            logger.exception("Compatibility check failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
            }

    @mcp.tool()
    async def search_properties(input_data: SearchInput) -> dict[str, Any]:
        """Search for CSS properties by name or description.

        Args:
            input_data: Search query and options

        Returns:
            List of matching properties
        """
        try:
            fetcher = await get_mdn_fetcher()
            results = await fetcher.search_properties(
                input_data.query,
                input_data.limit,
            )

            return {
                "status": "success",
                "query": input_data.query,
                "results": results,
                "count": len(results),
            }

        except Exception as e:
            logger.exception("Property search failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
            }

    @mcp.tool()
    async def get_properties_by_category(category: str) -> dict[str, Any]:
        """Get CSS properties organized by category.

        Categories include:
        - layout
        - typography
        - colors
        - spacing
        - sizing
        - flexbox
        - grid
        - transforms
        - animations
        - transitions
        - effects
        - backgrounds
        - borders

        Args:
            category: Category name

        Returns:
            List of properties in the category
        """
        try:
            fetcher = await get_mdn_fetcher()
            properties = await fetcher.get_properties_by_category(category)

            return {
                "status": "success",
                "category": category,
                "properties": properties,
                "count": len(properties),
            }

        except Exception as e:
            logger.exception(
                "Failed to get properties for category", category=category, error=str(e)
            )
            return {
                "status": "error",
                "error": str(e),
            }

    @mcp.tool()
    async def analyze_project_css(input_data: ProjectInput) -> dict[str, Any]:
        """Analyze all CSS files in a project.

        Scans project for CSS files and provides:
        - Combined metrics
        - File-by-file analysis
        - Duplicate detection
        - Overall complexity

        Args:
            input_data: Project path and options

        Returns:
            Comprehensive project analysis
        """
        try:
            project_path = Path(input_data.path)

            if not project_path.exists():
                return {
                    "status": "error",
                    "error": f"Path does not exist: {input_data.path}",
                }

            # Find CSS files
            css_files = []
            if project_path.is_file() and project_path.suffix == ".css":
                css_files = [project_path]
            else:
                include_patterns = input_data.include_patterns or ["**/*.css"]
                exclude_patterns = input_data.exclude_patterns or []

                for pattern in include_patterns:
                    for file_path in project_path.glob(pattern):
                        # Check exclusions
                        excluded = False
                        for exclude in exclude_patterns:
                            if exclude.replace("**/", "") in str(file_path):
                                excluded = True
                                break

                        if not excluded:
                            css_files.append(file_path)

            if not css_files:
                return {
                    "status": "error",
                    "error": "No CSS files found",
                }

            # Analyze each file
            file_results = []
            combined_css = ""
            total_bytes = 0

            for css_file in css_files[:100]:  # Limit to 100 files
                try:
                    content = css_file.read_text()
                    combined_css += content + "\n"
                    total_bytes += len(content.encode("utf-8"))

                    analyzer = CSSAnalyzer()
                    metrics = analyzer.analyze(content)

                    file_results.append(
                        {
                            "file": str(css_file.relative_to(project_path)),
                            "metrics": metrics.to_summary(),
                        }
                    )

                except Exception as e:
                    logger.warning("Failed to analyze CSS file", file=str(css_file), error=str(e))

            # Analyze combined CSS
            combined_analyzer = CSSAnalyzer()
            combined_metrics = combined_analyzer.analyze(combined_css)

            return {
                "status": "success",
                "project_path": str(project_path),
                "files_analyzed": len(file_results),
                "total_bytes": total_bytes,
                "combined_metrics": combined_metrics.to_summary(),
                "suggestions": combined_analyzer.get_suggestions(),
                "files": file_results,
            }

        except Exception as e:
            logger.exception("Project analysis failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
            }

    @mcp.tool()
    async def list_capabilities() -> dict[str, Any]:
        """List available CSS analysis capabilities.

        Returns:
            Dictionary of available tools and their descriptions
        """
        return {
            "status": "success",
            "capabilities": [
                {
                    "name": "analyze_css",
                    "description": "Full CSS analysis with 150+ metrics",
                    "use_case": "Analyze CSS complexity, specificity, and quality",
                },
                {
                    "name": "analyze_css_summary",
                    "description": "Quick CSS summary (faster)",
                    "use_case": "Get key metrics without full analysis",
                },
                {
                    "name": "get_docs",
                    "description": "MDN documentation for CSS properties",
                    "use_case": "Learn about CSS properties and values",
                },
                {
                    "name": "get_browser_compatibility",
                    "description": "Check browser support for properties",
                    "use_case": "Ensure cross-browser compatibility",
                },
                {
                    "name": "search_properties",
                    "description": "Search for CSS properties",
                    "use_case": "Find properties by name or description",
                },
                {
                    "name": "get_properties_by_category",
                    "description": "Get properties by category",
                    "use_case": "Explore CSS property categories",
                },
                {
                    "name": "analyze_project_css",
                    "description": "Analyze all CSS in a project",
                    "use_case": "Project-wide CSS analysis and optimization",
                },
            ],
            "version": "0.1.0",
            "metrics_count": 150,
        }

    @mcp.tool()
    async def health_check() -> dict[str, Any]:
        """Check server health status.

        Returns:
            Health status information
        """
        return {
            "status": "healthy",
            "version": "0.1.0",
            "capabilities": [
                "css_analysis",
                "mdn_documentation",
                "browser_compatibility",
                "project_analysis",
            ],
        }

    logger.info("Registered CSS analysis tools", count=9)
