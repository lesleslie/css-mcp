"""MDN CSS Documentation Fetcher.

Fetches CSS property documentation from MDN Web Docs for
AI-assisted CSS development and learning.
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from oneiric.core.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class MDNDocumentation(BaseModel):
    """MDN documentation for a CSS property."""

    property_name: str = Field(..., description="CSS property name")
    url: str = Field(..., description="MDN documentation URL")
    summary: str = Field(default="", description="Brief summary of the property")
    syntax: str = Field(default="", description="Formal syntax")
    initial_value: str = Field(default="", description="Initial/default value")
    applies_to: str = Field(default="", description="Elements this applies to")
    inherited: bool = Field(default=False, description="Whether property is inherited")
    computed_value: str = Field(default="", description="Computed value type")
    animation_type: str = Field(default="", description="Animation type")
    examples: list[dict[str, str]] = Field(default_factory=list, description="Code examples")
    browser_compatibility: dict[str, Any] = Field(
        default_factory=dict, description="Browser support"
    )
    related_properties: list[str] = Field(default_factory=list, description="Related properties")
    status: str = Field(default="unknown", description="Fetch status")


class MDNFetcher:
    """Fetches CSS documentation from MDN Web Docs.

    Uses MDN's structured data and content to provide comprehensive
    property documentation for AI-assisted development.
    """

    BASE_URL = "https://developer.mozilla.org/en-US/docs/Web/CSS"
    API_URL = "https://developer.mozilla.org/api/v1"

    # Common CSS property metadata (fallback when MDN unavailable)
    PROPERTY_METADATA: dict[str, dict[str, Any]] = {
        "display": {
            "summary": "Sets whether an element is treated as a block or inline element and the layout used for its children.",
            "initial": "inline",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "display: block | inline | flex | grid | none | ...",
        },
        "flex": {
            "summary": "Shorthand for flex-grow, flex-shrink, and flex-basis.",
            "initial": "0 1 auto",
            "applies_to": "flex items",
            "inherited": False,
            "syntax": "flex: none | <flex-grow> <flex-shrink>? <flex-basis>?",
        },
        "flex-direction": {
            "summary": "Sets how flex items are placed in the flex container.",
            "initial": "row",
            "applies_to": "flex containers",
            "inherited": False,
            "syntax": "flex-direction: row | row-reverse | column | column-reverse",
        },
        "flex-wrap": {
            "summary": "Sets whether flex items are forced onto one line or can wrap onto multiple lines.",
            "initial": "nowrap",
            "applies_to": "flex containers",
            "inherited": False,
            "syntax": "flex-wrap: nowrap | wrap | wrap-reverse",
        },
        "justify-content": {
            "summary": "Defines how the browser distributes space between and around content items.",
            "initial": "flex-start",
            "applies_to": "flex containers",
            "inherited": False,
            "syntax": "justify-content: flex-start | flex-end | center | space-between | space-around | ...",
        },
        "align-items": {
            "summary": "Sets the align-self value on all direct children as a group.",
            "initial": "stretch",
            "applies_to": "flex containers",
            "inherited": False,
            "syntax": "align-items: flex-start | flex-end | center | baseline | stretch",
        },
        "gap": {
            "summary": "Sets the gaps (gutters) between rows and columns in flex, grid, or multi-column layouts.",
            "initial": "normal",
            "applies_to": "multi-column elements, flex containers, grid containers",
            "inherited": False,
            "syntax": "gap: <row-gap> <column-gap>?",
        },
        "grid-template-columns": {
            "summary": "Defines the line names and track sizing functions of the grid columns.",
            "initial": "none",
            "applies_to": "grid containers",
            "inherited": False,
            "syntax": "grid-template-columns: none | <track-list> | <auto-track-list>",
        },
        "grid-template-rows": {
            "summary": "Defines the line names and track sizing functions of the grid rows.",
            "initial": "none",
            "applies_to": "grid containers",
            "inherited": False,
            "syntax": "grid-template-rows: none | <track-list> | <auto-track-list>",
        },
        "color": {
            "summary": "Sets the foreground color value of an element's text and text decorations.",
            "initial": "canvastext",
            "applies_to": "all elements",
            "inherited": True,
            "syntax": "color: <color>",
        },
        "background": {
            "summary": "Shorthand for all background properties.",
            "initial": "see individual properties",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "background: <bg-image> <bg-position>? / <bg-size>? <repeat-style>? ...",
        },
        "background-color": {
            "summary": "Sets the background color of an element.",
            "initial": "transparent",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "background-color: <color>",
        },
        "margin": {
            "summary": "Sets the margin area on all four sides of an element.",
            "initial": "0",
            "applies_to": "all elements except table display types",
            "inherited": False,
            "syntax": "margin: <length> | <percentage> | auto",
        },
        "padding": {
            "summary": "Sets the padding area on all four sides of an element.",
            "initial": "0",
            "applies_to": "all elements except table display types",
            "inherited": False,
            "syntax": "padding: <length> | <percentage>",
        },
        "width": {
            "summary": "Sets an element's width.",
            "initial": "auto",
            "applies_to": "all elements but non-replaced inline elements, table rows, and row groups",
            "inherited": False,
            "syntax": "width: auto | <length> | <percentage> | max-content | min-content | fit-content",
        },
        "height": {
            "summary": "Sets an element's height.",
            "initial": "auto",
            "applies_to": "all elements but non-replaced inline elements, table columns, and column groups",
            "inherited": False,
            "syntax": "height: auto | <length> | <percentage> | max-content | min-content | fit-content",
        },
        "font-size": {
            "summary": "Sets the size of the font.",
            "initial": "medium",
            "applies_to": "all elements",
            "inherited": True,
            "syntax": "font-size: <absolute-size> | <relative-size> | <length> | <percentage>",
        },
        "font-family": {
            "summary": "Specifies a prioritized list of one or more font family names.",
            "initial": "depends on user agent",
            "applies_to": "all elements",
            "inherited": True,
            "syntax": "font-family: <family-name># | <generic-family>#",
        },
        "line-height": {
            "summary": "Sets the height of a line box.",
            "initial": "normal",
            "applies_to": "all elements",
            "inherited": True,
            "syntax": "line-height: normal | <number> | <length> | <percentage>",
        },
        "border": {
            "summary": "Shorthand for border-width, border-style, and border-color.",
            "initial": "see individual properties",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "border: <border-width> <border-style> <border-color>",
        },
        "border-radius": {
            "summary": "Rounds the corners of an element's outer border edge.",
            "initial": "0",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "border-radius: <length-percentage>{1,4} [ / <length-percentage>{1,4} ]?",
        },
        "box-shadow": {
            "summary": "Adds shadow effects around an element's frame.",
            "initial": "none",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "box-shadow: none | <shadow>#",
        },
        "transform": {
            "summary": "Lets you rotate, scale, skew, or translate an element.",
            "initial": "none",
            "applies_to": "transformable elements",
            "inherited": False,
            "syntax": "transform: none | <transform-list>",
        },
        "transition": {
            "summary": "Shorthand for transition-property, transition-duration, transition-timing-function, and transition-delay.",
            "initial": "see individual properties",
            "applies_to": "all elements, ::before and ::after pseudo-elements",
            "inherited": False,
            "syntax": "transition: <property> <duration> <timing-function> <delay>",
        },
        "animation": {
            "summary": "Shorthand for animation-name, animation-duration, animation-timing-function, etc.",
            "initial": "see individual properties",
            "applies_to": "all elements, ::before and ::after pseudo-elements",
            "inherited": False,
            "syntax": "animation: <name> <duration> <timing-function> <delay> <iteration-count> ...",
        },
        "position": {
            "summary": "Sets how an element is positioned in a document.",
            "initial": "static",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "position: static | relative | absolute | fixed | sticky",
        },
        "z-index": {
            "summary": "Sets the z-order of a positioned element and its descendants or flex items.",
            "initial": "auto",
            "applies_to": "positioned elements",
            "inherited": False,
            "syntax": "z-index: auto | <integer>",
        },
        "overflow": {
            "summary": "Sets what happens when an element's content is too big to fit in its block.",
            "initial": "visible",
            "applies_to": "block containers, flex containers, grid containers",
            "inherited": False,
            "syntax": "overflow: visible | hidden | clip | scroll | auto",
        },
        "opacity": {
            "summary": "Sets the opacity of an element.",
            "initial": "1",
            "applies_to": "all elements",
            "inherited": False,
            "syntax": "opacity: <alpha-value>",
        },
        "cursor": {
            "summary": "Sets the mouse cursor to display when the mouse pointer is over an element.",
            "initial": "auto",
            "applies_to": "all elements",
            "inherited": True,
            "syntax": "cursor: <url>? <keyword>",
        },
    }

    def __init__(self, timeout: float = 10.0, cache_ttl: int = 86400) -> None:
        """Initialize MDN fetcher.

        Args:
            timeout: HTTP request timeout in seconds
            cache_ttl: Cache time-to-live in seconds (default 24 hours)
        """
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[str, MDNDocumentation] = {}
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_property_docs(self, property_name: str) -> MDNDocumentation:
        """Fetch documentation for a CSS property.

        Args:
            property_name: CSS property name (e.g., 'flex-direction')

        Returns:
            MDNDocumentation with property information
        """
        # Normalize property name
        prop = property_name.lower().strip()

        # Check cache
        if prop in self._cache:
            return self._cache[prop]

        # Build URL
        url = f"{self.BASE_URL}/{prop}"

        doc = MDNDocumentation(
            property_name=prop,
            url=url,
        )

        # Try to fetch from MDN
        try:
            client = await self._get_client()
            response = await client.get(url, follow_redirects=True)

            if response.status_code == 200:
                doc = await self._parse_mdn_page(prop, url, response.text)
                doc.status = "success"
            else:
                # Use fallback metadata
                doc = self._get_fallback_docs(prop, url)
                doc.status = "fallback"

        except Exception as e:
            logger.warning("Failed to fetch MDN docs", prop=prop, error=str(e))
            doc = self._get_fallback_docs(prop, url)
            doc.status = f"error: {str(e)[:50]}"

        # Cache result
        self._cache[prop] = doc
        return doc

    async def _parse_mdn_page(self, prop: str, url: str, html: str) -> MDNDocumentation:
        """Parse MDN page HTML for documentation."""
        doc = MDNDocumentation(
            property_name=prop,
            url=url,
        )

        # Extract summary from meta description or first paragraph
        summary_match = re.search(r'<meta name="description" content="([^"]+)"', html)
        if summary_match:
            doc.summary = summary_match.group(1)

        # Extract syntax from code blocks
        syntax_match = re.search(
            r'<pre[^>]*class="[^"]*brush:css[^"]*"[^>]*>(.*?)</pre>',
            html,
            re.DOTALL | re.IGNORECASE,
        )
        if syntax_match:
            # Clean HTML entities and tags
            syntax = re.sub(r"<[^>]+>", "", syntax_match.group(1))
            doc.syntax = syntax.strip()

        # Check for inherited status
        if "Inherited: yes" in html or "inherited: yes" in html.lower():
            doc.inherited = True

        return doc

    def _get_fallback_docs(self, prop: str, url: str) -> MDNDocumentation:
        """Get fallback documentation from built-in metadata."""
        doc = MDNDocumentation(
            property_name=prop,
            url=url,
        )

        if prop in self.PROPERTY_METADATA:
            meta = self.PROPERTY_METADATA[prop]
            doc.summary = meta.get("summary", "")
            doc.syntax = meta.get("syntax", "")
            doc.initial_value = meta.get("initial", "")
            doc.applies_to = meta.get("applies_to", "")
            doc.inherited = meta.get("inherited", False)

        return doc

    async def search_properties(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """Search for CSS properties matching a query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching properties with summaries
        """
        query_lower = query.lower()
        results = []

        # Search in built-in metadata
        for prop, meta in self.PROPERTY_METADATA.items():
            if query_lower in prop or query_lower in meta.get("summary", "").lower():
                results.append(
                    {
                        "property": prop,
                        "summary": meta.get("summary", "")[:100],
                        "url": f"{self.BASE_URL}/{prop}",
                    }
                )
                if len(results) >= limit:
                    break

        return results

    async def get_properties_by_category(self, category: str) -> list[str]:
        """Get CSS properties by category.

        Args:
            category: Category name (layout, typography, colors, etc.)

        Returns:
            List of property names in the category
        """
        from css_mcp.analyzer import CSSAnalyzer

        category_lower = category.lower()
        properties = [
            prop_name
            for prop_name, prop_category in CSSAnalyzer.PROPERTY_CATEGORIES.items()
            if prop_category.value == category_lower
        ]
        return sorted(properties)

    def clear_cache(self) -> None:
        """Clear the documentation cache."""
        self._cache.clear()


# Singleton instance for reuse
_fetcher: MDNFetcher | None = None


async def get_mdn_fetcher() -> MDNFetcher:
    """Get or create MDN fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = MDNFetcher()
    return _fetcher


async def get_property_docs(property_name: str) -> MDNDocumentation:
    """Convenience function to get property documentation."""
    fetcher = await get_mdn_fetcher()
    return await fetcher.get_property_docs(property_name)
