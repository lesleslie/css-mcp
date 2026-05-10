"""CSS Analysis Engine for CSS MCP Server.

Provides comprehensive CSS analysis including:
- 150+ complexity and quality metrics
- Specificity analysis
- Selector optimization
- Property categorization
- Browser compatibility scoring
- Optimization suggestions

Designed for analyzing programmatically generated CSS from FastBlocks style adapters.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import tinycss2
from pydantic import BaseModel, Field

from css_mcp.config import PropertyCategory


class SpecificityLevel(StrEnum):
    """Specificity level classification."""

    LOW = "low"  # 0-10
    MEDIUM = "medium"  # 11-50
    HIGH = "high"  # 51-100
    VERY_HIGH = "very_high"  # 100+


class ComplexityLevel(StrEnum):
    """Complexity level classification."""

    SIMPLE = "simple"  # 0-30
    MODERATE = "moderate"  # 31-60
    COMPLEX = "complex"  # 61-80
    VERY_COMPLEX = "very_complex"  # 81+


@dataclass
class CSSProperty:
    """Represents a CSS property with metadata."""

    name: str
    value: str
    line: int = 0
    column: int = 0
    important: bool = False
    category: PropertyCategory = PropertyCategory.UNKNOWN
    vendor_prefixes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "important": self.important,
            "category": self.category.value
            if isinstance(self.category, PropertyCategory)
            else self.category,
            "vendor_prefixes": self.vendor_prefixes,
        }


@dataclass
class CSSSelector:
    """Represents a CSS selector with specificity info."""

    selector: str
    specificity: tuple[int, int, int]
    line: int = 0
    pseudo_classes: list[str] = field(default_factory=list)
    pseudo_elements: list[str] = field(default_factory=list)
    combinators: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    ids: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    elements: list[str] = field(default_factory=list)

    @property
    def specificity_score(self) -> int:
        """Calculate numeric specificity score (0-999)."""
        a, b, c = self.specificity
        return a * 100 + b * 10 + c

    @property
    def specificity_level(self) -> SpecificityLevel:
        """Classify specificity level."""
        score = self.specificity_score
        if score <= 10:
            return SpecificityLevel.LOW
        elif score <= 50:
            return SpecificityLevel.MEDIUM
        elif score <= 100:
            return SpecificityLevel.HIGH
        return SpecificityLevel.VERY_HIGH

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector": self.selector,
            "specificity": self.specificity,
            "specificity_score": self.specificity_score,
            "specificity_level": self.specificity_level.value,
            "line": self.line,
            "pseudo_classes": self.pseudo_classes,
            "pseudo_elements": self.pseudo_elements,
            "combinators": self.combinators,
            "attributes": self.attributes,
            "ids": self.ids,
            "classes": self.classes,
            "elements": self.elements,
        }


@dataclass
class CSSRule:
    """Represents a complete CSS rule (selector + properties)."""

    selectors: list[CSSSelector]
    properties: list[CSSProperty]
    line: int = 0
    end_line: int = 0
    is_media_query: bool = False
    media_query: str | None = None
    is_keyframes: bool = False
    keyframe_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selectors": [s.to_dict() for s in self.selectors],
            "properties": [p.to_dict() for p in self.properties],
            "line": self.line,
            "end_line": self.end_line,
            "is_media_query": self.is_media_query,
            "media_query": self.media_query,
            "is_keyframes": self.is_keyframes,
            "keyframe_name": self.keyframe_name,
        }


class CSSMetrics(BaseModel):
    """Comprehensive CSS metrics (150+ metrics)."""

    # Basic metrics
    total_rules: int = Field(default=0, description="Total number of CSS rules")
    total_selectors: int = Field(default=0, description="Total number of selectors")
    total_properties: int = Field(default=0, description="Total number of properties")
    total_declarations: int = Field(default=0, description="Total declarations")
    total_lines: int = Field(default=0, description="Total lines of CSS")
    total_characters: int = Field(default=0, description="Total characters")
    total_bytes: int = Field(default=0, description="Total bytes")

    # Selector metrics
    selector_count: int = Field(default=0, description="Unique selectors")
    id_selectors: int = Field(default=0, description="ID selectors (#id)")
    class_selectors: int = Field(default=0, description="Class selectors (.class)")
    element_selectors: int = Field(default=0, description="Element selectors (div)")
    universal_selectors: int = Field(default=0, description="Universal selectors (*)")
    attribute_selectors: int = Field(
        default=0, description="Attribute selectors ([attr])"
    )
    pseudo_class_selectors: int = Field(
        default=0, description="Pseudo-class selectors (:hover)"
    )
    pseudo_element_selectors: int = Field(
        default=0, description="Pseudo-element selectors (::before)"
    )
    descendant_combinators: int = Field(
        default=0, description="Descendant combinators (space)"
    )
    child_combinators: int = Field(default=0, description="Child combinators (>)")
    sibling_combinators: int = Field(
        default=0, description="Sibling combinators (+, ~)"
    )
    nested_selectors: int = Field(default=0, description="Nested selectors depth > 3")

    # Specificity metrics
    avg_specificity: float = Field(default=0.0, description="Average specificity score")
    max_specificity: int = Field(default=0, description="Maximum specificity score")
    min_specificity: int = Field(default=0, description="Minimum specificity score")
    high_specificity_rules: int = Field(
        default=0, description="Rules with specificity > 100"
    )
    very_high_specificity_rules: int = Field(
        default=0, description="Rules with specificity > 500"
    )
    specificity_distribution: dict[str, int] = Field(
        default_factory=lambda: {"low": 0, "medium": 0, "high": 0, "very_high": 0},
        description="Distribution of specificity levels",
    )

    # Property metrics
    unique_properties: int = Field(default=0, description="Unique property names")
    property_count: dict[str, int] = Field(
        default_factory=dict, description="Property usage counts"
    )
    vendor_prefixed_properties: int = Field(
        default=0, description="Vendor-prefixed properties"
    )
    important_properties: int = Field(
        default=0, description="Properties with !important"
    )
    custom_properties: int = Field(default=0, description="CSS custom properties (--*)")
    shorthand_properties: int = Field(
        default=0, description="Shorthand properties used"
    )

    # Property category distribution
    layout_properties: int = Field(
        default=0, description="Layout properties (display, position)"
    )
    typography_properties: int = Field(
        default=0, description="Typography properties (font, text)"
    )
    color_properties: int = Field(
        default=0, description="Color properties (color, background)"
    )
    spacing_properties: int = Field(
        default=0, description="Spacing properties (margin, padding)"
    )
    sizing_properties: int = Field(
        default=0, description="Sizing properties (width, height)"
    )
    transform_properties: int = Field(default=0, description="Transform properties")
    animation_properties: int = Field(default=0, description="Animation properties")
    transition_properties: int = Field(default=0, description="Transition properties")
    flexbox_properties: int = Field(default=0, description="Flexbox properties")
    grid_properties: int = Field(default=0, description="Grid properties")
    effect_properties: int = Field(
        default=0, description="Effect properties (shadow, opacity)"
    )

    # Color metrics
    total_colors: int = Field(default=0, description="Total color values")
    unique_colors: int = Field(default=0, description="Unique colors")
    hex_colors: int = Field(default=0, description="Hex color values")
    rgb_colors: int = Field(default=0, description="RGB/RGBA values")
    hsl_colors: int = Field(default=0, description="HSL/HSLA values")
    named_colors: int = Field(default=0, description="Named color values")
    color_variables: int = Field(default=0, description="Color via CSS variables")

    # Value metrics
    values_with_units: int = Field(default=0, description="Values with units")
    px_values: int = Field(default=0, description="Pixel values")
    rem_values: int = Field(default=0, description="REM values")
    em_values: int = Field(default=0, description="EM values")
    percent_values: int = Field(default=0, description="Percentage values")
    viewport_values: int = Field(default=0, description="Viewport units (vw, vh)")
    calc_values: int = Field(default=0, description="Calc() expressions")
    css_functions: int = Field(default=0, description="CSS function calls")

    # Complexity metrics
    complexity_score: int = Field(
        default=0, description="Overall complexity score (0-100)"
    )
    complexity_level: str = Field(
        default="simple", description="Complexity classification"
    )
    avg_selector_length: float = Field(
        default=0.0, description="Average selector length"
    )
    max_selector_length: int = Field(default=0, description="Maximum selector length")
    avg_declarations_per_rule: float = Field(
        default=0.0, description="Average declarations per rule"
    )
    max_declarations_per_rule: int = Field(
        default=0, description="Maximum declarations per rule"
    )

    # Organization metrics
    media_queries: int = Field(default=0, description="Media query count")
    keyframes: int = Field(default=0, description="Keyframe animations")
    font_faces: int = Field(default=0, description="@font-face rules")
    imports: int = Field(default=0, description="@import rules")
    supports_queries: int = Field(default=0, description="@supports queries")
    container_queries: int = Field(default=0, description="Container queries")

    # Quality metrics
    duplicate_selectors: int = Field(default=0, description="Duplicate selectors")
    duplicate_properties: int = Field(
        default=0, description="Duplicate properties in rules"
    )
    empty_rules: int = Field(default=0, description="Empty rules")
    invalid_properties: int = Field(
        default=0, description="Potentially invalid properties"
    )
    redundant_values: int = Field(default=0, description="Redundant property values")

    # Efficiency metrics
    gzipped_size: int = Field(default=0, description="Estimated gzipped size")
    rules_per_line: float = Field(default=0.0, description="Rules per line ratio")
    selector_efficiency: float = Field(
        default=0.0, description="Selector efficiency score"
    )
    property_efficiency: float = Field(
        default=0.0, description="Property efficiency score"
    )

    def to_summary(self) -> dict[str, Any]:
        """Generate a summary of key metrics."""
        return {
            "overview": {
                "total_rules": self.total_rules,
                "total_selectors": self.total_selectors,
                "total_properties": self.total_properties,
                "total_bytes": self.total_bytes,
                "gzipped_size": self.gzipped_size,
            },
            "complexity": {
                "score": self.complexity_score,
                "level": self.complexity_level,
                "avg_specificity": round(self.avg_specificity, 2),
            },
            "selectors": {
                "ids": self.id_selectors,
                "classes": self.class_selectors,
                "elements": self.element_selectors,
                "pseudo_classes": self.pseudo_class_selectors,
            },
            "properties": {
                "unique": self.unique_properties,
                "important": self.important_properties,
                "custom": self.custom_properties,
                "vendor_prefixed": self.vendor_prefixed_properties,
            },
            "quality": {
                "duplicates": self.duplicate_selectors + self.duplicate_properties,
                "empty_rules": self.empty_rules,
                "efficiency": round(self.selector_efficiency, 2),
            },
        }


class CSSAnalyzer:
    """CSS Analysis Engine.

    Provides comprehensive analysis of CSS content with 150+ metrics.
    Designed for analyzing programmatically generated CSS from FastBlocks.
    """

    # Property categories mapping
    PROPERTY_CATEGORIES: dict[str, PropertyCategory] = {
        # Layout
        "display": PropertyCategory.LAYOUT,
        "position": PropertyCategory.LAYOUT,
        "top": PropertyCategory.LAYOUT,
        "right": PropertyCategory.LAYOUT,
        "bottom": PropertyCategory.LAYOUT,
        "left": PropertyCategory.LAYOUT,
        "float": PropertyCategory.LAYOUT,
        "clear": PropertyCategory.LAYOUT,
        "z-index": PropertyCategory.LAYOUT,
        "overflow": PropertyCategory.LAYOUT,
        "visibility": PropertyCategory.LAYOUT,
        "clip": PropertyCategory.LAYOUT,
        # Flexbox
        "flex": PropertyCategory.FLEXBOX,
        "flex-direction": PropertyCategory.FLEXBOX,
        "flex-wrap": PropertyCategory.FLEXBOX,
        "flex-flow": PropertyCategory.FLEXBOX,
        "justify-content": PropertyCategory.FLEXBOX,
        "align-items": PropertyCategory.FLEXBOX,
        "align-content": PropertyCategory.FLEXBOX,
        "align-self": PropertyCategory.FLEXBOX,
        "order": PropertyCategory.FLEXBOX,
        "flex-grow": PropertyCategory.FLEXBOX,
        "flex-shrink": PropertyCategory.FLEXBOX,
        "flex-basis": PropertyCategory.FLEXBOX,
        "gap": PropertyCategory.FLEXBOX,
        "row-gap": PropertyCategory.FLEXBOX,
        "column-gap": PropertyCategory.FLEXBOX,
        # Grid
        "grid": PropertyCategory.GRID,
        "grid-template": PropertyCategory.GRID,
        "grid-template-columns": PropertyCategory.GRID,
        "grid-template-rows": PropertyCategory.GRID,
        "grid-template-areas": PropertyCategory.GRID,
        "grid-column": PropertyCategory.GRID,
        "grid-row": PropertyCategory.GRID,
        "grid-area": PropertyCategory.GRID,
        "grid-gap": PropertyCategory.GRID,
        "place-items": PropertyCategory.GRID,
        "place-content": PropertyCategory.GRID,
        "place-self": PropertyCategory.GRID,
        # Typography
        "font": PropertyCategory.TYPOGRAPHY,
        "font-family": PropertyCategory.TYPOGRAPHY,
        "font-size": PropertyCategory.TYPOGRAPHY,
        "font-weight": PropertyCategory.TYPOGRAPHY,
        "font-style": PropertyCategory.TYPOGRAPHY,
        "font-variant": PropertyCategory.TYPOGRAPHY,
        "line-height": PropertyCategory.TYPOGRAPHY,
        "letter-spacing": PropertyCategory.TYPOGRAPHY,
        "word-spacing": PropertyCategory.TYPOGRAPHY,
        "text-align": PropertyCategory.TYPOGRAPHY,
        "text-decoration": PropertyCategory.TYPOGRAPHY,
        "text-transform": PropertyCategory.TYPOGRAPHY,
        "text-indent": PropertyCategory.TYPOGRAPHY,
        "text-shadow": PropertyCategory.TYPOGRAPHY,
        "white-space": PropertyCategory.TYPOGRAPHY,
        "word-break": PropertyCategory.TYPOGRAPHY,
        "word-wrap": PropertyCategory.TYPOGRAPHY,
        # Colors
        "color": PropertyCategory.COLORS,
        "opacity": PropertyCategory.COLORS,
        # Spacing
        "margin": PropertyCategory.SPACING,
        "margin-top": PropertyCategory.SPACING,
        "margin-right": PropertyCategory.SPACING,
        "margin-bottom": PropertyCategory.SPACING,
        "margin-left": PropertyCategory.SPACING,
        "padding": PropertyCategory.SPACING,
        "padding-top": PropertyCategory.SPACING,
        "padding-right": PropertyCategory.SPACING,
        "padding-bottom": PropertyCategory.SPACING,
        "padding-left": PropertyCategory.SPACING,
        # Sizing
        "width": PropertyCategory.SIZING,
        "height": PropertyCategory.SIZING,
        "min-width": PropertyCategory.SIZING,
        "max-width": PropertyCategory.SIZING,
        "min-height": PropertyCategory.SIZING,
        "max-height": PropertyCategory.SIZING,
        "aspect-ratio": PropertyCategory.SIZING,
        "box-sizing": PropertyCategory.SIZING,
        # Transforms
        "transform": PropertyCategory.TRANSFORMS,
        "transform-origin": PropertyCategory.TRANSFORMS,
        "transform-style": PropertyCategory.TRANSFORMS,
        "perspective": PropertyCategory.TRANSFORMS,
        "perspective-origin": PropertyCategory.TRANSFORMS,
        "backface-visibility": PropertyCategory.TRANSFORMS,
        # Animations
        "animation": PropertyCategory.ANIMATIONS,
        "animation-name": PropertyCategory.ANIMATIONS,
        "animation-duration": PropertyCategory.ANIMATIONS,
        "animation-timing-function": PropertyCategory.ANIMATIONS,
        "animation-delay": PropertyCategory.ANIMATIONS,
        "animation-iteration-count": PropertyCategory.ANIMATIONS,
        "animation-direction": PropertyCategory.ANIMATIONS,
        "animation-fill-mode": PropertyCategory.ANIMATIONS,
        "animation-play-state": PropertyCategory.ANIMATIONS,
        # Transitions
        "transition": PropertyCategory.TRANSITIONS,
        "transition-property": PropertyCategory.TRANSITIONS,
        "transition-duration": PropertyCategory.TRANSITIONS,
        "transition-timing-function": PropertyCategory.TRANSITIONS,
        "transition-delay": PropertyCategory.TRANSITIONS,
        # Backgrounds
        "background": PropertyCategory.BACKGROUNDS,
        "background-color": PropertyCategory.BACKGROUNDS,
        "background-image": PropertyCategory.BACKGROUNDS,
        "background-position": PropertyCategory.BACKGROUNDS,
        "background-size": PropertyCategory.BACKGROUNDS,
        "background-repeat": PropertyCategory.BACKGROUNDS,
        "background-attachment": PropertyCategory.BACKGROUNDS,
        "background-clip": PropertyCategory.BACKGROUNDS,
        "background-origin": PropertyCategory.BACKGROUNDS,
        # Borders
        "border": PropertyCategory.BORDERS,
        "border-width": PropertyCategory.BORDERS,
        "border-style": PropertyCategory.BORDERS,
        "border-color": PropertyCategory.BORDERS,
        "border-radius": PropertyCategory.BORDERS,
        "border-top": PropertyCategory.BORDERS,
        "border-right": PropertyCategory.BORDERS,
        "border-bottom": PropertyCategory.BORDERS,
        "border-left": PropertyCategory.BORDERS,
        "outline": PropertyCategory.BORDERS,
        "outline-offset": PropertyCategory.BORDERS,
        # Effects
        "box-shadow": PropertyCategory.EFFECTS,
        "filter": PropertyCategory.EFFECTS,
        "backdrop-filter": PropertyCategory.EFFECTS,
        "mix-blend-mode": PropertyCategory.EFFECTS,
        # Interactivity
        "cursor": PropertyCategory.INTERACTIVITY,
        "pointer-events": PropertyCategory.INTERACTIVITY,
        "user-select": PropertyCategory.INTERACTIVITY,
        "resize": PropertyCategory.INTERACTIVITY,
    }

    # Shorthand properties
    SHORTHAND_PROPERTIES = {
        "font",
        "background",
        "border",
        "margin",
        "padding",
        "flex",
        "flex-flow",
        "grid",
        "grid-template",
        "grid-gap",
        "transition",
        "animation",
        "transform",
        "columns",
        "list-style",
        "outline",
        "text-decoration",
        "place-items",
        "place-content",
    }

    def __init__(self) -> None:
        """Initialize the CSS analyzer."""
        self._rules: list[CSSRule] = []
        self._metrics: CSSMetrics = CSSMetrics()

    def analyze(self, css_content: str) -> CSSMetrics:
        """Analyze CSS content and return comprehensive metrics.

        Args:
            css_content: Raw CSS content to analyze

        Returns:
            CSSMetrics object with 150+ metrics
        """
        # Reset state
        self._rules = []
        self._metrics = CSSMetrics()

        # Basic metrics
        self._metrics.total_characters = len(css_content)
        self._metrics.total_bytes = len(css_content.encode("utf-8"))
        self._metrics.total_lines = css_content.count("\n") + 1

        # Parse CSS
        try:
            stylesheet = tinycss2.parse_stylesheet(
                css_content, skip_comments=True, skip_whitespace=True
            )
        except Exception:
            # If parsing fails, return basic metrics
            return self._metrics

        # Analyze parsed rules
        self._analyze_rules(stylesheet)

        # Calculate derived metrics
        self._calculate_complexity()
        self._calculate_efficiency()
        self._find_duplicates()
        self._estimate_gzip_size(css_content)

        return self._metrics

    def _analyze_rules(self, rules: list[Any]) -> None:
        """Analyze parsed CSS rules."""
        for rule in rules:
            if rule.type == "qualified-rule":
                # Regular CSS rule
                self._analyze_qualified_rule(rule)
            elif rule.type == "at-rule":
                # At-rules (@media, @keyframes, etc.)
                self._analyze_at_rule(rule)

    def _analyze_qualified_rule(self, rule: Any) -> None:
        """Analyze a qualified CSS rule (selector + declarations)."""
        self._metrics.total_rules += 1

        # Parse selectors
        selector_text = tinycss2.serialize(rule.prelude)
        selectors = self._parse_selectors(selector_text)

        # Parse declarations
        properties = self._parse_declarations(rule.content)

        # Create rule object
        css_rule = CSSRule(
            selectors=selectors,
            properties=properties,
            line=getattr(rule, "source_line", 0),
        )

        self._rules.append(css_rule)
        self._metrics.total_selectors += len(selectors)
        self._metrics.total_properties += len(properties)
        self._metrics.total_declarations += len(properties)

        # Update selector metrics
        for selector in selectors:
            self._update_selector_metrics(selector)

        # Update property metrics
        for prop in properties:
            self._update_property_metrics(prop)

    def _analyze_at_rule(self, rule: Any) -> None:
        """Analyze at-rules like @media, @keyframes, etc."""
        at_keyword = rule.at_keyword.lower()

        if at_keyword == "media":
            self._metrics.media_queries += 1
            if rule.content:
                self._analyze_rules(rule.content)
        elif at_keyword == "keyframes":
            self._metrics.keyframes += 1
        elif at_keyword == "font-face":
            self._metrics.font_faces += 1
        elif at_keyword == "import":
            self._metrics.imports += 1
        elif at_keyword == "supports":
            self._metrics.supports_queries += 1
        elif at_keyword == "container":
            self._metrics.container_queries += 1

    def _parse_selectors(self, selector_text: str) -> list[CSSSelector]:
        """Parse selector list into CSSSelector objects."""
        selectors = []

        # Split by comma for selector lists
        for selector_str in selector_text.split(","):
            selector_str = selector_str.strip()
            if not selector_str:
                continue

            specificity = self._calculate_specificity(selector_str)

            selector = CSSSelector(
                selector=selector_str,
                specificity=specificity,
                pseudo_classes=self._extract_pseudo_classes(selector_str),
                pseudo_elements=self._extract_pseudo_elements(selector_str),
                combinators=self._extract_combinators(selector_str),
                attributes=self._extract_attributes(selector_str),
                ids=re.findall(r"#([a-zA-Z0-9_-]+)", selector_str),
                classes=re.findall(r"\.([a-zA-Z0-9_-]+)", selector_str),
                elements=self._extract_elements(selector_str),
            )
            selectors.append(selector)

        return selectors

    def _calculate_specificity(self, selector: str) -> tuple[int, int, int]:
        """Calculate CSS specificity (a, b, c)."""
        a = selector.count("#")  # ID selectors
        b = (
            selector.count(".")  # Class selectors
            + selector.count("[")  # Attribute selectors
            + len(re.findall(r":(?!:)[a-zA-Z-]+", selector))  # Pseudo-classes
        )
        c = len(
            re.findall(r"(?<![a-zA-Z0-9_-])[a-z]+(?![a-zA-Z0-9_-])", selector.lower())
        )  # Elements

        return (a, b, c)

    def _extract_pseudo_classes(self, selector: str) -> list[str]:
        """Extract pseudo-classes from selector."""
        return re.findall(r":([a-zA-Z-]+)(?!\:)", selector)

    def _extract_pseudo_elements(self, selector: str) -> list[str]:
        """Extract pseudo-elements from selector."""
        return re.findall(r"::([a-zA-Z-]+)", selector)

    def _extract_combinators(self, selector: str) -> list[str]:
        """Extract combinators from selector."""
        combinators = []
        # Match combinators: space, >, +, ~
        tokens = re.split(r"(\s+|>|~|\+)", selector)
        for token in tokens:
            token = token.strip()
            if token in (">", "+", "~"):
                combinators.append(token)
            elif token and " " in token:
                combinators.append(" ")
        return combinators

    def _extract_attributes(self, selector: str) -> list[str]:
        """Extract attribute selectors from selector."""
        return re.findall(r"\[([^\]]+)\]", selector)

    def _extract_elements(self, selector: str) -> list[str]:
        """Extract element names from selector."""
        # Match element names (not preceded by ., #, :, or another letter)
        elements = re.findall(
            r"(?<![.#:\w])([a-z][a-z0-9-]*)(?![a-z0-9-]*\()", selector.lower()
        )
        # Filter out pseudo-classes/elements
        pseudo = {
            "hover",
            "focus",
            "active",
            "before",
            "after",
            "first-child",
            "last-child",
        }
        return [e for e in elements if e not in pseudo]

    def _parse_declarations(self, content: list[Any]) -> list[CSSProperty]:
        """Parse declarations into CSSProperty objects."""
        properties = []

        # Parse the content as a declaration list
        declarations = tinycss2.parse_declaration_list(
            content, skip_comments=True, skip_whitespace=True
        )

        for token in declarations:
            if token.type == "declaration":
                prop_name = token.lower_name
                prop_value = tinycss2.serialize(token.value)

                prop = CSSProperty(
                    name=prop_name,
                    value=prop_value,
                    line=getattr(token, "source_line", 0),
                    important=token.important,
                    category=self._get_property_category(prop_name),
                    vendor_prefixes=self._get_vendor_prefixes(prop_name),
                )
                properties.append(prop)

        return properties

    def _get_property_category(self, property_name: str) -> PropertyCategory:
        """Get the category for a CSS property."""
        # Remove vendor prefix for lookup
        clean_name = property_name
        for prefix in ("-webkit-", "-moz-", "-ms-", "-o-"):
            if property_name.startswith(prefix):
                clean_name = property_name[len(prefix) :]
                break

        return self.PROPERTY_CATEGORIES.get(clean_name, PropertyCategory.UNKNOWN)

    def _get_vendor_prefixes(self, property_name: str) -> list[str]:
        """Extract vendor prefixes from property name."""
        prefixes = []
        for prefix in ("-webkit-", "-moz-", "-ms-", "-o-"):
            if property_name.startswith(prefix):
                prefixes.append(prefix.rstrip("-"))
        return prefixes

    def _update_selector_metrics(self, selector: CSSSelector) -> None:
        """Update metrics based on selector analysis."""
        specificity_score = selector.specificity_score

        # Update specificity metrics
        if self._metrics.max_specificity < specificity_score:
            self._metrics.max_specificity = specificity_score
        if (
            self._metrics.min_specificity == 0
            or specificity_score < self._metrics.min_specificity
        ):
            self._metrics.min_specificity = specificity_score

        # Count selector types
        if selector.ids:
            self._metrics.id_selectors += len(selector.ids)
        if selector.classes:
            self._metrics.class_selectors += len(selector.classes)
        if selector.elements:
            self._metrics.element_selectors += len(selector.elements)
        if "*" in selector.selector:
            self._metrics.universal_selectors += 1
        if selector.attributes:
            self._metrics.attribute_selectors += len(selector.attributes)
        if selector.pseudo_classes:
            self._metrics.pseudo_class_selectors += len(selector.pseudo_classes)
        if selector.pseudo_elements:
            self._metrics.pseudo_element_selectors += len(selector.pseudo_elements)

        # Count combinators
        for combinator in selector.combinators:
            if combinator == " ":
                self._metrics.descendant_combinators += 1
            elif combinator == ">":
                self._metrics.child_combinators += 1
            elif combinator in ("+", "~"):
                self._metrics.sibling_combinators += 1

        # Check selector depth
        depth = (
            selector.selector.count(" ")
            + selector.selector.count(">")
            + selector.selector.count("+")
        )
        if depth > 3:
            self._metrics.nested_selectors += 1

        # Specificity distribution
        level = selector.specificity_level.value
        self._metrics.specificity_distribution[level] = (
            self._metrics.specificity_distribution.get(level, 0) + 1
        )

        if specificity_score > 100:
            self._metrics.high_specificity_rules += 1
        if specificity_score > 500:
            self._metrics.very_high_specificity_rules += 1

        # Selector length
        selector_len = len(selector.selector)
        if selector_len > self._metrics.max_selector_length:
            self._metrics.max_selector_length = selector_len

    def _update_property_metrics(self, prop: CSSProperty) -> None:
        """Update metrics based on property analysis."""
        # Count property usage
        self._metrics.property_count[prop.name] = (
            self._metrics.property_count.get(prop.name, 0) + 1
        )

        # Important count
        if prop.important:
            self._metrics.important_properties += 1

        # Custom properties
        if prop.name.startswith("--"):
            self._metrics.custom_properties += 1

        # Vendor prefixes
        if prop.vendor_prefixes:
            self._metrics.vendor_prefixed_properties += 1

        # Shorthand properties
        if prop.name in self.SHORTHAND_PROPERTIES:
            self._metrics.shorthand_properties += 1

        # Category counts
        category = prop.category
        if category == PropertyCategory.LAYOUT:
            self._metrics.layout_properties += 1
        elif category == PropertyCategory.TYPOGRAPHY:
            self._metrics.typography_properties += 1
        elif category == PropertyCategory.COLORS:
            self._metrics.color_properties += 1
        elif category == PropertyCategory.SPACING:
            self._metrics.spacing_properties += 1
        elif category == PropertyCategory.SIZING:
            self._metrics.sizing_properties += 1
        elif category == PropertyCategory.TRANSFORMS:
            self._metrics.transform_properties += 1
        elif category == PropertyCategory.ANIMATIONS:
            self._metrics.animation_properties += 1
        elif category == PropertyCategory.TRANSITIONS:
            self._metrics.transition_properties += 1
        elif category == PropertyCategory.FLEXBOX:
            self._metrics.flexbox_properties += 1
        elif category == PropertyCategory.GRID:
            self._metrics.grid_properties += 1
        elif category == PropertyCategory.EFFECTS:
            self._metrics.effect_properties += 1

        # Analyze values
        self._analyze_value(prop.value)

    def _analyze_value(self, value: str) -> None:
        """Analyze CSS property value for metrics."""
        # Color values
        if re.search(r"#[0-9a-fA-F]{3,8}", value):
            self._metrics.hex_colors += 1
            self._metrics.total_colors += 1
        if re.search(r"rgba?\(", value, re.IGNORECASE):
            self._metrics.rgb_colors += 1
            self._metrics.total_colors += 1
        if re.search(r"hsla?\(", value, re.IGNORECASE):
            self._metrics.hsl_colors += 1
            self._metrics.total_colors += 1
        if re.search(r"var\(--", value):
            self._metrics.color_variables += 1

        # Unit values
        if re.search(r"\d+px", value):
            self._metrics.px_values += 1
            self._metrics.values_with_units += 1
        if re.search(r"\d+rem", value):
            self._metrics.rem_values += 1
            self._metrics.values_with_units += 1
        if re.search(r"\d+em\b", value):
            self._metrics.em_values += 1
            self._metrics.values_with_units += 1
        if re.search(r"\d+%", value):
            self._metrics.percent_values += 1
            self._metrics.values_with_units += 1
        if re.search(r"\d+v[wh]", value):
            self._metrics.viewport_values += 1
            self._metrics.values_with_units += 1

        # Functions
        if "calc(" in value.lower():
            self._metrics.calc_values += 1
            self._metrics.css_functions += 1

    def _calculate_complexity(self) -> None:
        """Calculate overall complexity score."""
        if self._metrics.total_rules == 0:
            return

        # Calculate average specificity
        total_specificity = 0
        total_selectors = 0
        for rule in self._rules:
            for selector in rule.selectors:
                total_specificity += selector.specificity_score
                total_selectors += 1

        if total_selectors > 0:
            self._metrics.avg_specificity = total_specificity / total_selectors

        # Calculate average selector length
        if total_selectors > 0:
            total_length = sum(
                len(s.selector) for rule in self._rules for s in rule.selectors
            )
            self._metrics.avg_selector_length = total_length / total_selectors

        # Calculate declarations per rule
        if self._metrics.total_rules > 0:
            self._metrics.avg_declarations_per_rule = (
                self._metrics.total_properties / self._metrics.total_rules
            )

        # Calculate max declarations per rule
        self._metrics.max_declarations_per_rule = max(
            (len(r.properties) for r in self._rules), default=0
        )

        # Calculate unique properties
        self._metrics.unique_properties = len(self._metrics.property_count)
        self._metrics.selector_count = total_selectors

        # Calculate complexity score (0-100)
        score = 0

        # Factor 1: Average specificity (0-25 points)
        score += min(25, int(self._metrics.avg_specificity / 4))

        # Factor 2: Selector complexity (0-25 points)
        selector_complexity = (
            self._metrics.nested_selectors * 2
            + self._metrics.universal_selectors * 3
            + self._metrics.high_specificity_rules
        )
        score += min(25, selector_complexity)

        # Factor 3: Property complexity (0-25 points)
        property_complexity = (
            self._metrics.important_properties * 2
            + self._metrics.vendor_prefixed_properties
            + self._metrics.duplicate_properties
        )
        score += min(25, property_complexity)

        # Factor 4: Structure complexity (0-25 points)
        structure_complexity = (
            len(self._rules) / 100  # Rules count
            + self._metrics.media_queries * 2
            + self._metrics.keyframes
        )
        score += min(25, int(structure_complexity))

        self._metrics.complexity_score = min(100, score)

        # Set complexity level
        if score <= 30:
            self._metrics.complexity_level = ComplexityLevel.SIMPLE.value
        elif score <= 60:
            self._metrics.complexity_level = ComplexityLevel.MODERATE.value
        elif score <= 80:
            self._metrics.complexity_level = ComplexityLevel.COMPLEX.value
        else:
            self._metrics.complexity_level = ComplexityLevel.VERY_COMPLEX.value

    def _calculate_efficiency(self) -> None:
        """Calculate efficiency scores."""
        if self._metrics.total_rules == 0:
            return

        # Selector efficiency (higher is better)
        # Based on: fewer IDs, fewer universal selectors, less nesting
        selector_issues = (
            self._metrics.universal_selectors * 10
            + self._metrics.nested_selectors * 5
            + self._metrics.id_selectors * 2
        )
        max_issues = self._metrics.total_selectors * 5
        if max_issues > 0:
            self._metrics.selector_efficiency = max(
                0, 100 - (selector_issues / max_issues * 100)
            )

        # Property efficiency (higher is better)
        # Based on: fewer !important, fewer duplicates, fewer vendor prefixes
        property_issues = (
            self._metrics.important_properties * 3
            + self._metrics.duplicate_properties * 2
            + self._metrics.vendor_prefixed_properties
        )
        max_prop_issues = self._metrics.total_properties * 2
        if max_prop_issues > 0:
            self._metrics.property_efficiency = max(
                0, 100 - (property_issues / max_prop_issues * 100)
            )

        # Rules per line
        if self._metrics.total_lines > 0:
            self._metrics.rules_per_line = (
                self._metrics.total_rules / self._metrics.total_lines
            )

    def _find_duplicates(self) -> None:
        """Find duplicate selectors and properties."""
        # Find duplicate selectors
        selector_counts: Counter[str] = Counter()
        for rule in self._rules:
            for selector in rule.selectors:
                selector_counts[selector.selector] += 1

        self._metrics.duplicate_selectors = sum(
            1 for count in selector_counts.values() if count > 1
        )

        # Find duplicate properties within rules
        for rule in self._rules:
            prop_names = [p.name for p in rule.properties]
            if len(prop_names) != len(set(prop_names)):
                self._metrics.duplicate_properties += 1

        # Find empty rules
        self._metrics.empty_rules = sum(
            1 for rule in self._rules if not rule.properties
        )

    def _estimate_gzip_size(self, content: str) -> None:
        """Estimate gzipped size of CSS."""
        import gzip

        try:
            compressed = gzip.compress(content.encode("utf-8"))
            self._metrics.gzipped_size = len(compressed)
        except Exception:
            # Fallback estimate (typically ~70% compression for CSS)
            self._metrics.gzipped_size = int(self._metrics.total_bytes * 0.3)

    def get_rules(self) -> list[CSSRule]:
        """Get parsed CSS rules."""
        return self._rules

    def get_suggestions(self) -> list[dict[str, Any]]:
        """Generate optimization suggestions based on analysis."""
        suggestions = []

        # High specificity warnings
        if self._metrics.high_specificity_rules > 0:
            suggestions.append(
                {
                    "type": "specificity",
                    "severity": "warning",
                    "message": f"{self._metrics.high_specificity_rules} rules with high specificity (>100)",
                    "suggestion": "Consider using BEM or other methodology to reduce specificity",
                }
            )

        # !important warnings
        if self._metrics.important_properties > 5:
            suggestions.append(
                {
                    "type": "maintainability",
                    "severity": "warning",
                    "message": f"{self._metrics.important_properties} uses of !important",
                    "suggestion": "Reduce !important usage by improving selector specificity structure",
                }
            )

        # Duplicate selectors
        if self._metrics.duplicate_selectors > 0:
            suggestions.append(
                {
                    "type": "optimization",
                    "severity": "info",
                    "message": f"{self._metrics.duplicate_selectors} duplicate selectors found",
                    "suggestion": "Consolidate duplicate selectors to reduce CSS size",
                }
            )

        # Empty rules
        if self._metrics.empty_rules > 0:
            suggestions.append(
                {
                    "type": "optimization",
                    "severity": "info",
                    "message": f"{self._metrics.empty_rules} empty rules found",
                    "suggestion": "Remove empty rules to reduce CSS size",
                }
            )

        # Universal selectors
        if self._metrics.universal_selectors > 0:
            suggestions.append(
                {
                    "type": "performance",
                    "severity": "info",
                    "message": f"{self._metrics.universal_selectors} universal selectors (*)",
                    "suggestion": "Universal selectors can impact rendering performance",
                }
            )

        # Complexity warning
        if self._metrics.complexity_score > 80:
            suggestions.append(
                {
                    "type": "complexity",
                    "severity": "warning",
                    "message": f"High complexity score: {self._metrics.complexity_score}/100",
                    "suggestion": "Consider refactoring CSS architecture for better maintainability",
                }
            )

        return suggestions
