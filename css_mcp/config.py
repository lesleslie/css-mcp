"""Configuration for CSS MCP Server."""

from __future__ import annotations

import os
from contextlib import suppress
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

import yaml
from oneiric.core.config import OneiricMCPConfig
from pydantic import BaseModel, Field


class CSSMCPSettings(OneiricMCPConfig):
    """CSS MCP Server configuration extending OneiricMCPConfig.

    Loaded in priority order (highest to lowest):
    1. Environment variables (CSS_MCP_*)
    2. settings/local.yaml (gitignored, developer overrides)
    3. settings/css-mcp.yaml (checked into repo)
    4. Defaults defined below
    """

    model_config = {  # type: ignore[reportUnknownMemberType]
        "env_prefix": "CSS_MCP_",
        "env_file": ".env",
        "extra": "ignore",
    }

    server_name: str = "css-mcp"

    # HTTP server
    http_host: str = Field(default="localhost", description="HTTP server host")
    http_port: int = Field(default=3050, description="HTTP server port")

    # Cache settings
    cache_ttl: int = Field(default=86400, description="Cache TTL in seconds (24 hours)")

    # MDN settings
    mdn_base_url: str = Field(
        default="https://developer.mozilla.org/en-US/docs/Web/CSS",
        description="MDN CSS documentation base URL",
    )
    mdn_timeout: float = Field(default=10.0, description="MDN fetch timeout in seconds")

    # Analysis settings
    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Max CSS file size in bytes (10MB)"
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
        default=False, description="Enable FastBlocks style adapter integration"
    )
    fastblocks_path: str | None = Field(
        default=None, description="Path to FastBlocks project for integration"
    )

    LEGACY_ENV_PREFIX: ClassVar[str] = "CSS_MCP"

    @classmethod
    def load(
        cls,
        server_name: str = "css-mcp",
        config_path: Path | None = None,
        env_prefix: str | None = None,
    ) -> CSSMCPSettings:
        """Load settings with layered configuration.

        Backward-compatible with the MCPBaseSettings.load() signature. Reads
        YAML files in priority order, then applies environment variable
        overrides using the provided env_prefix.

        Priority (highest to lowest):
        1. Explicit config_path (if provided)
        2. Environment variables ({env_prefix}_{FIELD})
        3. settings/local.yaml (gitignored)
        4. settings/{server_name}.yaml
        5. Defaults defined below

        Args:
            server_name: Server identifier (default: 'css-mcp')
            config_path: Optional explicit config file path
            env_prefix: Environment variable prefix (default: 'CSS_MCP')
        """
        if env_prefix is None:
            env_prefix = cls.LEGACY_ENV_PREFIX

        data: dict[str, Any] = {"server_name": server_name}

        # Layer 1: settings/{server_name}.yaml
        server_yaml = Path("settings") / f"{server_name}.yaml"
        if server_yaml.exists():
            with server_yaml.open() as f:
                yaml_data = yaml.safe_load(f)
            if isinstance(yaml_data, dict):
                data.update(yaml_data)

        # Layer 2: settings/local.yaml
        local_yaml = Path("settings") / "local.yaml"
        if local_yaml.exists():
            with local_yaml.open() as f:
                local_data = yaml.safe_load(f)
            if isinstance(local_data, dict):
                data.update(local_data)

        # Layer 3: Environment variables
        for field_name in cls.model_fields:
            env_var = f"{env_prefix}_{field_name.upper()}"
            if env_var in os.environ:
                env_value: str | Path | None = os.environ[env_var]
                field_def = cls.model_fields[field_name]
                field_type = field_def.annotation
                field_args = ()
                with suppress(Exception):
                    from typing import get_args as _get_args

                    field_args = _get_args(field_type)
                if field_type is Path or (field_args and Path in field_args):
                    env_value = Path(env_value) if env_value else None
                data[field_name] = env_value

        # Layer 4: Explicit config path (highest priority)
        if config_path is not None and config_path.exists():
            with config_path.open() as f:
                explicit_data = yaml.safe_load(f)
            if isinstance(explicit_data, dict):
                data.update(explicit_data)

        return cls.model_validate(data)


# Backward-compatible alias — existing imports of CSSMCPConfig continue to work
CSSMCPConfig = CSSMCPSettings


class AnalysisOptions(BaseModel):
    """Options for CSS analysis."""

    include_metrics: bool = Field(default=True, description="Include complexity metrics")
    include_specificity: bool = Field(default=True, description="Include specificity analysis")
    include_compatibility: bool = Field(default=True, description="Include browser compatibility")
    include_suggestions: bool = Field(default=True, description="Include optimization suggestions")
    max_results: int = Field(default=100, description="Maximum results per category")


class CompatibilityLevel(StrEnum):
    """Browser compatibility levels."""

    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"
    UNKNOWN = "unknown"


class PropertyCategory(StrEnum):
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
