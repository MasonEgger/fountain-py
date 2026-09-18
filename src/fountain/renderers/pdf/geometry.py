# ABOUTME: Page geometry data for PDF export: page size, margins, and binding offset.
# Pure data, no fpdf import; presets plus custom construction, unit-testable without rendering a PDF.
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageGeometry:
    """Page dimensions, margins, and binding offset for PDF export.

    PageGeometry is pure data describing a page's physical size and the
    margins around its text block. ``binding_offset_in`` adds extra space
    on the left margin to leave room for hole-punching or binding, which
    narrows the usable text width without changing the page size.

    Args:
        width_in: Page width in inches.
        height_in: Page height in inches.
        margin_in: Uniform margin in inches applied to all four sides.
        binding_offset_in: Extra left-margin space reserved for binding,
            in inches. Defaults to 0.0 (no binding offset).

    Attributes:
        width_in: Page width in inches.
        height_in: Page height in inches.
        margin_in: Uniform margin in inches applied to all four sides.
        binding_offset_in: Extra left-margin space reserved for binding,
            in inches.

    Example:
        Building a custom geometry and reading its usable text width::

            >>> from fountain.renderers.pdf.geometry import PageGeometry
            >>> geometry = PageGeometry(width_in=6, height_in=9, margin_in=1, binding_offset_in=0.25)
            >>> geometry.text_width_in
            3.75
    """

    width_in: float
    height_in: float
    margin_in: float
    binding_offset_in: float = 0.0

    @property
    def text_width_in(self) -> float:
        """Usable text width in inches, after margins and binding offset.

        Returns:
            The page width minus the left and right margins and the
            binding offset.

        Example:
            Binding offset narrows the usable text width::

                >>> from fountain.renderers.pdf.geometry import PageGeometry
                >>> plain = PageGeometry(width_in=8.5, height_in=11.0, margin_in=1.0)
                >>> bound = PageGeometry(width_in=8.5, height_in=11.0, margin_in=1.0, binding_offset_in=0.5)
                >>> bound.text_width_in < plain.text_width_in
                True
        """
        return self.width_in - (2 * self.margin_in) - self.binding_offset_in


LETTER = PageGeometry(width_in=8.5, height_in=11.0, margin_in=1.0)
A4 = PageGeometry(width_in=210 / 25.4, height_in=297 / 25.4, margin_in=1.0)
HALF_LETTER = PageGeometry(width_in=5.5, height_in=8.5, margin_in=0.5)
