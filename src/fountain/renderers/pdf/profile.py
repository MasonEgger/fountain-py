# ABOUTME: Layout profile data for PDF export: font and per-element-type indent/width.
# Pure data, no fpdf import; separate from page geometry so font/indent choices vary independently of page size.
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType

from fountain.elements import ElementType


@dataclass(frozen=True)
class ElementLayout:
    """Left indent and column width for one element type, in inches.

    Args:
        left_indent_in: Distance from the page's text-block left edge to
            where this element's text starts, in inches.
        width_in: Width of this element's text column, in inches.

    Attributes:
        left_indent_in: Distance from the page's text-block left edge to
            where this element's text starts, in inches.
        width_in: Width of this element's text column, in inches.
    """

    left_indent_in: float
    width_in: float


@dataclass(frozen=True)
class LayoutProfile:
    """Font and per-element-type layout for PDF export.

    LayoutProfile is pure data the PDF renderer consumes: it carries no
    rendering behavior of its own. It is orthogonal to :class:`~fountain.renderers.pdf.geometry.PageGeometry`,
    which governs page size and margins; a profile's indents are relative
    to the geometry's text block.

    Args:
        font_name: PDF font family name.
        font_size_pt: Font size in points.
        element_layout: Mapping of :class:`~fountain.elements.ElementType` to its
            :class:`ElementLayout`.

    Attributes:
        font_name: PDF font family name.
        font_size_pt: Font size in points.
        element_layout: Mapping of :class:`~fountain.elements.ElementType` to its
            :class:`ElementLayout`.

    Example:
        Reading the SCREENPLAY profile's character-cue indent::

            >>> from fountain.elements import ElementType
            >>> from fountain.renderers.pdf.profile import SCREENPLAY
            >>> SCREENPLAY.element_layout[ElementType.CHARACTER].left_indent_in
            2.5
    """

    font_name: str
    font_size_pt: int
    element_layout: MappingProxyType[ElementType, ElementLayout] = field(default_factory=lambda: MappingProxyType({}))


SCREENPLAY = LayoutProfile(
    font_name="Courier",
    font_size_pt=12,
    element_layout=MappingProxyType(
        {
            ElementType.SCENE_HEADING: ElementLayout(left_indent_in=0.0, width_in=6.0),
            ElementType.ACTION: ElementLayout(left_indent_in=0.0, width_in=6.0),
            ElementType.CHARACTER: ElementLayout(left_indent_in=2.5, width_in=3.0),
            ElementType.PARENTHETICAL: ElementLayout(left_indent_in=2.0, width_in=2.5),
            ElementType.DIALOGUE: ElementLayout(left_indent_in=1.5, width_in=3.5),
            ElementType.TRANSITION: ElementLayout(left_indent_in=4.0, width_in=2.0),
        }
    ),
)
