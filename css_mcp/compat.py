"""Browser Compatibility Checker for CSS Properties.

Provides browser support information for CSS properties and values,
helping developers ensure cross-browser compatibility.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SupportLevel(StrEnum):
    """Browser support level."""

    FULL = "full"  # Fully supported
    PARTIAL = "partial"  # Partial support / prefixed
    NONE = "none"  # Not supported
    UNKNOWN = "unknown"  # No data available


@dataclass
class BrowserSupport:
    """Browser support information for a feature."""

    browser: str
    version_added: str | None = None
    version_removed: str | None = None
    prefix: str | None = None
    support_level: SupportLevel = SupportLevel.UNKNOWN
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "browser": self.browser,
            "version_added": self.version_added,
            "version_removed": self.version_removed,
            "prefix": self.prefix,
            "support_level": self.support_level.value,
            "notes": self.notes,
        }


class CompatibilityResult(BaseModel):
    """Result of a compatibility check."""

    model_config = {"arbitrary_types_allowed": True}

    property_name: str = Field(..., description="CSS property name")
    overall_support: SupportLevel = Field(
        default=SupportLevel.UNKNOWN, description="Overall support level"
    )
    browsers: dict[str, BrowserSupport] = Field(
        default_factory=dict, description="Per-browser support details"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Compatibility recommendations"
    )
    prefixes_needed: list[str] = Field(
        default_factory=list, description="Vendor prefixes that may be needed"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with serialized browser support."""
        return {
            "property_name": self.property_name,
            "overall_support": self.overall_support.value,
            "browsers": {
                k: v.to_dict() if isinstance(v, BrowserSupport) else v
                for k, v in self.browsers.items()
            },
            "recommendations": self.recommendations,
            "prefixes_needed": self.prefixes_needed,
        }


class BrowserCompatChecker:
    """Checks CSS property browser compatibility.

    Uses built-in compatibility data for common CSS properties.
    Can be extended to use MDN compatibility data or other sources.
    """

    # Browser compatibility data for CSS properties
    # Format: property -> {browser -> (version_added, prefix)}
    COMPAT_DATA: dict[str, dict[str, dict[str, Any]]] = {
        # Flexbox
        "display": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "flex": {
            "chrome": {"version": "29", "support": "full"},
            "firefox": {"version": "20", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "flex-direction": {
            "chrome": {"version": "29", "support": "full"},
            "firefox": {"version": "20", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "flex-wrap": {
            "chrome": {"version": "29", "support": "full"},
            "firefox": {"version": "28", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "justify-content": {
            "chrome": {"version": "29", "support": "full"},
            "firefox": {"version": "20", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "align-items": {
            "chrome": {"version": "29", "support": "full"},
            "firefox": {"version": "20", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "gap": {
            "chrome": {"version": "84", "support": "full"},
            "firefox": {"version": "63", "support": "full"},
            "safari": {"version": "14.1", "support": "full"},
            "edge": {"version": "84", "support": "full"},
        },
        # Grid
        "grid-template-columns": {
            "chrome": {"version": "57", "support": "full"},
            "firefox": {"version": "52", "support": "full"},
            "safari": {"version": "10.1", "support": "full"},
            "edge": {"version": "16", "support": "full"},
        },
        "grid-template-rows": {
            "chrome": {"version": "57", "support": "full"},
            "firefox": {"version": "52", "support": "full"},
            "safari": {"version": "10.1", "support": "full"},
            "edge": {"version": "16", "support": "full"},
        },
        "grid-template-areas": {
            "chrome": {"version": "57", "support": "full"},
            "firefox": {"version": "52", "support": "full"},
            "safari": {"version": "10.1", "support": "full"},
            "edge": {"version": "16", "support": "full"},
        },
        # Layout
        "position": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "position:sticky": {
            "chrome": {"version": "56", "support": "full"},
            "firefox": {"version": "32", "support": "full"},
            "safari": {"version": "13", "support": "full", "prefix": "-webkit-"},
            "edge": {"version": "16", "support": "full"},
        },
        # Sizing
        "aspect-ratio": {
            "chrome": {"version": "88", "support": "full"},
            "firefox": {"version": "89", "support": "full"},
            "safari": {"version": "15", "support": "full"},
            "edge": {"version": "88", "support": "full"},
        },
        # Typography
        "font-size": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "line-height": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        # Colors
        "color": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "opacity": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        # Background
        "background": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "background-clip": {
            "chrome": {"version": "1.0", "support": "full", "prefix": "-webkit-"},
            "firefox": {"version": "4.0", "support": "full"},
            "safari": {"version": "3.0", "support": "full", "prefix": "-webkit-"},
            "edge": {"version": "12", "support": "full"},
        },
        # Border
        "border": {
            "chrome": {"version": "1.0", "support": "full"},
            "firefox": {"version": "1.0", "support": "full"},
            "safari": {"version": "1.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "border-radius": {
            "chrome": {"version": "5.0", "support": "full"},
            "firefox": {"version": "4.0", "support": "full"},
            "safari": {"version": "5.0", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        # Effects
        "box-shadow": {
            "chrome": {"version": "10.0", "support": "full"},
            "firefox": {"version": "4.0", "support": "full"},
            "safari": {"version": "5.1", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "filter": {
            "chrome": {"version": "53", "support": "full"},
            "firefox": {"version": "35", "support": "full"},
            "safari": {"version": "9.1", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        "backdrop-filter": {
            "chrome": {"version": "76", "support": "full"},
            "firefox": {"version": "103", "support": "full"},
            "safari": {"version": "9", "support": "full", "prefix": "-webkit-"},
            "edge": {"version": "17", "support": "full"},
        },
        # Transform
        "transform": {
            "chrome": {"version": "36", "support": "full"},
            "firefox": {"version": "16", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        # Animation
        "animation": {
            "chrome": {"version": "43", "support": "full"},
            "firefox": {"version": "16", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        # Transition
        "transition": {
            "chrome": {"version": "26", "support": "full"},
            "firefox": {"version": "16", "support": "full"},
            "safari": {"version": "9", "support": "full"},
            "edge": {"version": "12", "support": "full"},
        },
        # CSS Custom Properties
        "--*": {
            "chrome": {"version": "49", "support": "full"},
            "firefox": {"version": "31", "support": "full"},
            "safari": {"version": "9.1", "support": "full"},
            "edge": {"version": "15", "support": "full"},
        },
        # Container Queries
        "container-type": {
            "chrome": {"version": "105", "support": "full"},
            "firefox": {"version": "110", "support": "full"},
            "safari": {"version": "16", "support": "full"},
            "edge": {"version": "105", "support": "full"},
        },
        "container": {
            "chrome": {"version": "105", "support": "full"},
            "firefox": {"version": "110", "support": "full"},
            "safari": {"version": "16", "support": "full"},
            "edge": {"version": "105", "support": "full"},
        },
        # Logical Properties
        "margin-inline": {
            "chrome": {"version": "87", "support": "full"},
            "firefox": {"version": "66", "support": "full"},
            "safari": {"version": "14.1", "support": "full"},
            "edge": {"version": "87", "support": "full"},
        },
        "padding-inline": {
            "chrome": {"version": "87", "support": "full"},
            "firefox": {"version": "66", "support": "full"},
            "safari": {"version": "14.1", "support": "full"},
            "edge": {"version": "87", "support": "full"},
        },
        # Scroll Snap
        "scroll-snap-type": {
            "chrome": {"version": "69", "support": "full"},
            "firefox": {"version": "68", "support": "full"},
            "safari": {"version": "11", "support": "full"},
            "edge": {"version": "79", "support": "full"},
        },
        # Overscroll Behavior
        "overscroll-behavior": {
            "chrome": {"version": "63", "support": "full"},
            "firefox": {"version": "59", "support": "full"},
            "safari": {"version": "16", "support": "full"},
            "edge": {"version": "18", "support": "full"},
        },
    }

    # Default target browsers
    DEFAULT_BROWSERS = ["chrome", "firefox", "safari", "edge"]

    def __init__(
        self,
        target_browsers: list[str] | None = None,
        browser_versions: dict[str, str] | None = None,
    ) -> None:
        """Initialize compatibility checker.

        Args:
            target_browsers: List of browsers to check (default: chrome, firefox, safari, edge)
            browser_versions: Minimum browser versions to support
        """
        self.target_browsers = target_browsers or self.DEFAULT_BROWSERS.copy()
        self.browser_versions = browser_versions or {}

    def check_property(self, property_name: str) -> CompatibilityResult:
        """Check browser compatibility for a CSS property.

        Args:
            property_name: CSS property name

        Returns:
            CompatibilityResult with browser support details
        """
        prop = property_name.lower().strip()

        # Handle custom properties
        if prop.startswith("--"):
            return self._check_custom_property(prop)

        result = CompatibilityResult(property_name=prop)

        # Get compatibility data
        compat_data = self.COMPAT_DATA.get(prop)

        if compat_data is None:
            # Unknown property
            result.overall_support = SupportLevel.UNKNOWN
            result.recommendations.append(
                f"No compatibility data available for '{prop}'"
            )
            return result

        # Check each target browser
        support_levels = []
        for browser in self.target_browsers:
            browser_data = compat_data.get(browser)

            if browser_data is None:
                support = BrowserSupport(
                    browser=browser,
                    support_level=SupportLevel.UNKNOWN,
                )
                result.browsers[browser] = support
                support_levels.append(SupportLevel.UNKNOWN)
                continue

            support_level = SupportLevel(browser_data.get("support", "full"))
            prefix = browser_data.get("prefix")

            support = BrowserSupport(
                browser=browser,
                version_added=browser_data.get("version"),
                support_level=support_level,
                prefix=prefix,
            )

            # Check against minimum version
            min_version = self.browser_versions.get(browser)
            if min_version and support.version_added:
                # Simple version comparison (works for major.minor)
                try:
                    required = float(min_version.split()[0])
                    available = float(support.version_added)
                    if available > required:
                        support.notes.append(
                            f"Requires version {support.version_added}+ (target: {min_version})"
                        )
                except (ValueError, IndexError):
                    pass

            result.browsers[browser] = support
            support_levels.append(support_level)

            if prefix:
                result.prefixes_needed.append(f"{prefix}{prop}")

        # Calculate overall support
        if all(s == SupportLevel.FULL for s in support_levels):
            result.overall_support = SupportLevel.FULL
        elif any(s == SupportLevel.NONE for s in support_levels):
            result.overall_support = SupportLevel.NONE
        elif any(s == SupportLevel.UNKNOWN for s in support_levels):
            result.overall_support = SupportLevel.UNKNOWN
        else:
            result.overall_support = SupportLevel.PARTIAL

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _check_custom_property(self, prop: str) -> CompatibilityResult:
        """Check compatibility for CSS custom properties."""
        result = CompatibilityResult(property_name=prop)

        custom_prop_data = self.COMPAT_DATA.get("--*", {})

        for browser in self.target_browsers:
            browser_data = custom_prop_data.get(browser, {})
            support = BrowserSupport(
                browser=browser,
                version_added=browser_data.get("version"),
                support_level=SupportLevel(browser_data.get("support", "full")),
            )
            result.browsers[browser] = support

        result.overall_support = SupportLevel.FULL
        result.recommendations.append(
            "CSS custom properties are well-supported in modern browsers"
        )

        return result

    def _generate_recommendations(self, result: CompatibilityResult) -> list[str]:
        """Generate compatibility recommendations."""
        recommendations = []

        if result.overall_support == SupportLevel.FULL:
            recommendations.append(
                f"'{result.property_name}' is fully supported in all target browsers"
            )
        elif result.overall_support == SupportLevel.PARTIAL:
            unsupported = [
                b
                for b, s in result.browsers.items()
                if s.support_level in (SupportLevel.NONE, SupportLevel.UNKNOWN)
            ]
            if unsupported:
                recommendations.append(
                    f"'{result.property_name}' may not work in: {', '.join(unsupported)}"
                )
        elif result.overall_support == SupportLevel.NONE:
            recommendations.append(
                f"'{result.property_name}' is not supported in target browsers"
            )
            recommendations.append("Consider using a fallback or alternative approach")

        if result.prefixes_needed:
            recommendations.append(
                f"Add vendor prefixes: {', '.join(result.prefixes_needed)}"
            )

        return recommendations

    def check_properties(
        self,
        properties: list[str],
    ) -> dict[str, CompatibilityResult]:
        """Check compatibility for multiple properties.

        Args:
            properties: List of CSS property names

        Returns:
            Dictionary mapping property names to compatibility results
        """
        return {prop: self.check_property(prop) for prop in properties}

    def get_compatibility_summary(
        self,
        properties: list[str],
    ) -> dict[str, Any]:
        """Get a summary of compatibility for multiple properties.

        Args:
            properties: List of CSS property names

        Returns:
            Summary with overall support and issues
        """
        results = self.check_properties(properties)

        summary = {
            "total_properties": len(properties),
            "fully_supported": 0,
            "partially_supported": 0,
            "not_supported": 0,
            "unknown": 0,
            "issues": [],
            "prefixes_needed": [],
        }

        for prop, result in results.items():
            if result.overall_support == SupportLevel.FULL:
                summary["fully_supported"] += 1
            elif result.overall_support == SupportLevel.PARTIAL:
                summary["partially_supported"] += 1
                summary["issues"].append(
                    {
                        "property": prop,
                        "browsers": [
                            b
                            for b, s in result.browsers.items()
                            if s.support_level != SupportLevel.FULL
                        ],
                    }
                )
            elif result.overall_support == SupportLevel.NONE:
                summary["not_supported"] += 1
                summary["issues"].append(
                    {
                        "property": prop,
                        "browsers": list(result.browsers.keys()),
                    }
                )
            else:
                summary["unknown"] += 1

            if result.prefixes_needed:
                summary["prefixes_needed"].extend(result.prefixes_needed)

        return summary


# Singleton instance
_checker: BrowserCompatChecker | None = None


def get_compat_checker(
    target_browsers: list[str] | None = None,
    browser_versions: dict[str, str] | None = None,
) -> BrowserCompatChecker:
    """Get or create compatibility checker instance."""
    global _checker
    if _checker is None or target_browsers or browser_versions:
        _checker = BrowserCompatChecker(target_browsers, browser_versions)
    return _checker
