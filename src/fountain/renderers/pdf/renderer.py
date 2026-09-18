# ABOUTME: PDFRenderer, which ties PageGeometry and LayoutProfile together via fpdf2 to produce PDF bytes.
# Writer-only tools are omitted; dual dialogue flattens to two sequential blocks; page breaks start a new page.
from typing import TYPE_CHECKING, cast

from fountain.document import FountainDocument
from fountain.elements import ElementType, FountainElement
from fountain.renderers.pdf._deps import require_fpdf
from fountain.renderers.pdf.geometry import LETTER, PageGeometry
from fountain.renderers.pdf.profile import SCREENPLAY, ElementLayout, LayoutProfile

if TYPE_CHECKING:
    from fpdf import FPDF

_OMITTED_TYPES = frozenset(
    {
        ElementType.NOTE,
        ElementType.SECTION,
        ElementType.SYNOPSIS,
        ElementType.BONEYARD,
    }
)

_BLANK_LINE_HEIGHT_IN = 0.15


class PDFRenderer:
    """Renders a :class:`FountainDocument` to PDF bytes via fpdf2.

    PDFRenderer consumes a :class:`~fountain.renderers.pdf.geometry.PageGeometry`
    (page size, margins, binding offset) and a
    :class:`~fountain.renderers.pdf.profile.LayoutProfile` (font and
    per-element-type indent/width) and writes each document element at its
    profile position within the geometry's text block. Writer-only tools
    (notes, sections, synopses, boneyard) are omitted, matching the other
    renderers' contract. Requires the ``[pdf]`` extra; raises ``ImportError``
    at construction time if fpdf2 is not installed.

    Args:
        geometry: Page size, margins, and binding offset. Defaults to LETTER.
        profile: Font and per-element-type layout. Defaults to SCREENPLAY.

    Raises:
        ImportError: If fpdf2 is not installed (see :func:`require_fpdf`).
    """

    def __init__(self, geometry: PageGeometry = LETTER, profile: LayoutProfile = SCREENPLAY) -> None:
        self._pdf_class = cast("type[FPDF]", require_fpdf().FPDF)
        self.geometry = geometry
        self.profile = profile

    def render_bytes(self, document: FountainDocument) -> bytes:
        """Render a document to PDF bytes.

        Args:
            document: The parsed document to render.

        Returns:
            The rendered PDF, as bytes.

        Raises:
            ValueError: If ``self.geometry.text_width_in`` is not positive,
                which would otherwise lay text out with a zero or negative
                width.
        """
        if self.geometry.text_width_in <= 0:
            raise ValueError(
                f"geometry.text_width_in must be positive, got {self.geometry.text_width_in} "
                "(margins and binding offset leave no room for text)"
            )

        pdf = self._new_document()
        for element in document.elements:
            self._render_element(pdf, element)
        return bytes(pdf.output())

    def _new_document(self) -> "FPDF":
        """Build an fpdf document sized and margined per ``self.geometry``.

        Returns:
            A fresh, single-page fpdf document with the profile font already
            selected.
        """
        pdf = self._pdf_class(orientation="P", unit="in", format=(self.geometry.width_in, self.geometry.height_in))
        pdf.set_margins(
            left=self.geometry.margin_in + self.geometry.binding_offset_in,
            top=self.geometry.margin_in,
            right=self.geometry.margin_in,
        )
        pdf.set_auto_page_break(auto=True, margin=self.geometry.margin_in)
        pdf.add_page()
        pdf.set_font(self.profile.font_name, size=self.profile.font_size_pt)
        return pdf

    def _render_element(self, pdf: "FPDF", element: FountainElement) -> None:
        """Write one element's text block, or take its structural action.

        Args:
            pdf: The in-progress fpdf document.
            element: The Fountain element to render.
        """
        if element.type in _OMITTED_TYPES:
            return
        if element.type == ElementType.PAGE_BREAK:
            pdf.add_page()
            return
        if element.type == ElementType.DUAL_DIALOGUE:
            self._render_dual_dialogue(pdf, element)
            return
        self._write_text_block(pdf, element.type, element.text)

    def _render_dual_dialogue(self, pdf: "FPDF", element: FountainElement) -> None:
        """Write a DUAL_DIALOGUE element as the left side's block followed by the right's.

        Single-column stacking, matching :class:`~fountain.renderers.plaintext.PlainTextRenderer`.

        Args:
            pdf: The in-progress fpdf document.
            element: A DUAL_DIALOGUE element carrying left/right character
                and dialogue metadata.
        """
        metadata = element.metadata
        if not metadata:
            return

        for character_key, dialogue_key in (("left_character", "left_dialogue"), ("right_character", "right_dialogue")):
            character = cast(FountainElement, metadata[character_key])
            self._write_text_block(pdf, character.type, character.text)
            dialogue = cast("list[FountainElement]", metadata[dialogue_key])
            for dialogue_element in dialogue:
                self._write_text_block(pdf, dialogue_element.type, dialogue_element.text)

    def _write_text_block(self, pdf: "FPDF", element_type: ElementType, text: str) -> None:
        """Write one wrapped text block at its profile indent/width, then a blank line.

        Args:
            pdf: The in-progress fpdf document.
            element_type: The element type, used to look up its layout.
            text: The text to write.
        """
        layout = self._layout_for(element_type)
        pdf.set_x(self.geometry.margin_in + self.geometry.binding_offset_in + layout.left_indent_in)
        pdf.multi_cell(w=layout.width_in, text=text, align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(_BLANK_LINE_HEIGHT_IN)

    def _layout_for(self, element_type: ElementType) -> ElementLayout:
        """Look up an element type's layout, falling back to the full text width.

        Args:
            element_type: The element type to look up.

        Returns:
            The profile's layout for this type, or a zero-indent,
            full-text-width default for types the profile does not cover.
        """
        return self.profile.element_layout.get(
            element_type, ElementLayout(left_indent_in=0.0, width_in=self.geometry.text_width_in)
        )
