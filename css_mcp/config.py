"""Configuration for CSS MCP Server."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CSSMCPConfig(BaseModel):
    """Configuration for CSS MCP Server.

    This configuration follows the mcp-common patterns for settings
    with environment variable support and validation.
    """

    # Server settings
    http_port: int = Field(default=3050, description="HTTP server port")
    http_host: str = Field(default="localhost", description="HTTP server host")
    debug: bool = Field(default=False, description="Enable debug mode")
    enable_http_transport: bool = Field(
        default=True, description="Enable HTTP transport"
    )

    # Cache settings
    cache_dir: str = Field(default=".css_mcp_cache", description="Cache directory")
    cache_ttl: int = Field(default=86400, description="Cache TTL in seconds (24 hours)")

    # MDN settings
    mdn_base_url: str = Field(
        default="https://developer.mozilla.org/en-US/docs/Web/CSS",
        description="MDN CSS documentation base URL",
    )
    mdn_timeout: float = Field(default=10.0, description="MDN fetch timeout in seconds")

    # Analysis settings
    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Max CSS file size (10MB)"
    )
    complexity_threshold: int = Field(
        default=80, description="Complexity score threshold for warnings"
    )
    specificity_threshold: int = Field(
        default=100, description="Specificity threshold for warnings"
    )

    # Browser compatibility settings
    target_browsers: list[str] = Field(
        default=["chrome", "firefox", "safari", "edge"],
        description="Target browsers for compatibility checks",
    )
    browser_versions: dict[str, str] = Field(
        default={
            "chrome": "last 2 versions",
            "firefox": "last 2 versions",
            "safari": "last 2 versions",
            "edge": "last 2 versions",
        },
        description="Browser version requirements",
    )

    # Integration settings
    fastblocks_integration: bool = Field(
        default=True, description="Enable FastBlocks style adapter integration"
    )
    fastblocks_path: str | None = Field(
        default=None, description="Path to FastBlocks project for integration"
    )

    model_config = {
        "env_prefix": "CSS_MCP_",
        "extra": "ignore",
    }


class AnalysisOptions(BaseModel):
    """Options for CSS analysis."""

    include_metrics: bool = Field(
        default=True, description="Include complexity metrics"
    )
    include_specificity: bool = Field(
        default=True, description="Include specificity analysis"
    )
    include_compatibility: bool = Field(
        default=True, description="Include browser compatibility"
    )
    include_suggestions: bool = Field(
        default=True, description="Include optimization suggestions"
    )
    max_results: int = Field(default=100, description="Maximum results per category")


class CompatibilityLevel(str):
    """Browser compatibility levels."""

    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"
    UNKNOWN = "unknown"


class PropertyCategory(str):
    """CSS property categories for organization."""

    LAYOUT = "layout"
    TYPOGRAPHY = "typography"
    COLORS = "colors"
    SPACING = "spacing"
    SIZING = "sizing"
    TRANSFORMS = "transforms"
    ANIMATIONS = "animations"
    TRANSITIONS = "transitions"
    FLEXBOX = "flexbox"
    GRID = "grid"
    POSITIONING = "positioning"
    EFFECTS = "effects"
    BACKGROUNDS = "backgrounds"
    BORDERS = "borders"
    INTERACTIVITY = "interactivity"
    UNKNOWN = "unknown"
