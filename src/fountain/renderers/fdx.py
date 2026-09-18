# ABOUTME: Final Draft (FDX) XML renderer built on the stdlib xml.etree.ElementTree only.
# Maps element types to <Paragraph Type="..."> blocks and title-page metadata to FDX TitlePage; writer tools omitted.
import xml.etree.ElementTree as ET
from typing import cast

from fountain.document import FountainDocument
from fountain.elements import ElementType, FountainElement

_OMITTED_TYPES = frozenset(
    {
        ElementType.NOTE,
        ElementType.SECTION,
        ElementType.SYNOPSIS,
        ElementType.BONEYARD,
    }
)

# Element type to FDX <Paragraph Type="..."> mapping. CENTERED and LYRICS map to the
# nearest FDX paragraph type (Action and Dialogue respectively); FDX carries alignment
# separately via _ALIGNMENTS.
_PARAGRAPH_TYPES: dict[ElementType, str] = {
    ElementType.SCENE_HEADING: "Scene Heading",
    ElementType.ACTION: "Action",
    ElementType.CHARACTER: "Character",
    ElementType.PARENTHETICAL: "Parenthetical",
    ElementType.DIALOGUE: "Dialogue",
    ElementType.TRANSITION: "Transition",
    ElementType.CENTERED: "Action",
    ElementType.LYRICS: "Dialogue",
}

_ALIGNMENTS: dict[ElementType, str] = {
    ElementType.CENTERED: "Center",
}

# Title page metadata key to FDX title-page paragraph type. Only the fields FDX's
# TitlePage structure recognizes are mapped; unrecognized metadata keys are skipped.
_TITLE_PAGE_PARAGRAPH_TYPES: dict[str, str] = {
    "title": "Title",
    "credit": "Credit",
    "author": "Author",
    "authors": "Author",
    "source": "Source",
    "draft date": "Draft Date",
    "contact": "Contact",
}


class FDXRenderer:
    """Renders a :class:`FountainDocument` as Final Draft (.fdx) interchange XML.

    Built entirely on :mod:`xml.etree.ElementTree` from the standard library, so
    FDX export adds zero runtime dependencies. Writer-only tools (notes,
    sections, synopses, boneyard) are omitted, matching the HTML and
    plain-text renderers' contract. Dual dialogue is emitted as a single
    ``<Paragraph><DualDialogue>`` wrapper containing both characters' cue and
    dialogue paragraphs.

    Example:
        Rendering a minimal document::

            >>> from fountain.document import FountainDocument
            >>> from fountain.elements import ElementType, FountainElement
            >>> elements = [
            ...     FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            ...     FountainElement(ElementType.ACTION, "John enters.", [], 2),
            ... ]
            >>> document = FountainDocument(elements)
            >>> output = FDXRenderer().render(document)
            >>> "<FinalDraft" in output
            True
    """

    def render(self, document: FountainDocument) -> str:
        """Render a document to Final Draft XML.

        Args:
            document: The parsed document to render.

        Returns:
            The FDX XML document as a string, rooted at ``<FinalDraft>``.
        """
        root = ET.Element("FinalDraft", {"DocumentType": "Script", "Template": "No", "Version": "1"})
        content = ET.SubElement(root, "Content")
        for element in document.elements:
            self._render_element(content, element)
        if document.metadata:
            self._render_title_page(root, document.metadata)
        return ET.tostring(root, encoding="unicode")

    def _render_element(self, parent: ET.Element, element: FountainElement) -> None:
        """Append the FDX representation of one element to its parent, if any.

        Args:
            parent: The XML element to append to (the ``<Content>`` element).
            element: The Fountain element to render.
        """
        if element.type in _OMITTED_TYPES:
            return
        if element.type == ElementType.DUAL_DIALOGUE:
            self._render_dual_dialogue(parent, element)
            return

        # Types with no _PARAGRAPH_TYPES entry (PAGE_BREAK; TITLE_PAGE, which never
        # appears in document.elements) have no FDX paragraph representation and are
        # silently skipped, same as the omitted writer tools.
        paragraph_type = _PARAGRAPH_TYPES.get(element.type)
        if paragraph_type is None:
            return
        self._append_paragraph(parent, paragraph_type, element.text, alignment=_ALIGNMENTS.get(element.type))

    def _append_paragraph(
        self, parent: ET.Element, paragraph_type: str, text: str, alignment: str | None = None
    ) -> ET.Element:
        """Append a ``<Paragraph Type="...">`` with a ``<Text>`` child.

        Args:
            parent: The XML element to append the paragraph to.
            paragraph_type: The FDX ``Type`` attribute value.
            text: The paragraph's text content.
            alignment: Optional ``Alignment`` attribute value.

        Returns:
            The created ``<Paragraph>`` element.
        """
        attributes = {"Type": paragraph_type}
        if alignment is not None:
            attributes["Alignment"] = alignment
        paragraph = ET.SubElement(parent, "Paragraph", attributes)
        text_element = ET.SubElement(paragraph, "Text")
        text_element.text = text
        return paragraph

    def _render_dual_dialogue(self, parent: ET.Element, element: FountainElement) -> None:
        """Append a dual-dialogue block as a ``<Paragraph><DualDialogue>`` wrapper.

        Args:
            parent: The XML element to append to.
            element: A DUAL_DIALOGUE element carrying left/right character and
                dialogue metadata.
        """
        metadata = element.metadata
        if not metadata:
            return

        left_character = cast(FountainElement, metadata["left_character"])
        left_dialogue = cast("list[FountainElement]", metadata["left_dialogue"])
        right_character = cast(FountainElement, metadata["right_character"])
        right_dialogue = cast("list[FountainElement]", metadata["right_dialogue"])

        wrapper = ET.SubElement(parent, "Paragraph")
        dual_dialogue = ET.SubElement(wrapper, "DualDialogue")
        for character, dialogue in ((left_character, left_dialogue), (right_character, right_dialogue)):
            self._append_paragraph(dual_dialogue, "Character", character.text)
            for dialogue_element in dialogue:
                # _process_dual_dialogue only ever collects DIALOGUE and PARENTHETICAL
                # elements here, both present in _PARAGRAPH_TYPES.
                self._append_paragraph(dual_dialogue, _PARAGRAPH_TYPES[dialogue_element.type], dialogue_element.text)

    def _render_title_page(self, root: ET.Element, metadata: dict[str, str]) -> None:
        """Append the FDX ``<TitlePage>`` structure built from title page metadata.

        Args:
            root: The ``<FinalDraft>`` root element.
            metadata: The document's title page metadata (lowercase keys).
        """
        title_page = ET.SubElement(root, "TitlePage")
        content = ET.SubElement(title_page, "Content")
        for key, paragraph_type in _TITLE_PAGE_PARAGRAPH_TYPES.items():
            if key in metadata:
                self._append_paragraph(content, paragraph_type, metadata[key])
