# ABOUTME: Monospace plain-text renderer producing screenplay-formatted output.
# Column positions (dialogue, parenthetical, cue) are constructor parameters; writer tools are omitted.
import textwrap
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


class PlainTextRenderer:
    """Renders a :class:`FountainDocument` as monospace plain text.

    Column positions for character cues, parentheticals, and dialogue are
    constructor parameters, so callers can retarget the layout to a
    different page width without subclassing. Writer-only tools (notes,
    sections, synopses, boneyard) are omitted, matching the HTML renderer's
    contract.

    Args:
        width: Maximum line width in characters.
        dialogue_indent: Column at which dialogue lines start.
        parenthetical_indent: Column at which parenthetical lines start.
        cue_indent: Column at which character cue lines start.

    Example:
        Rendering a minimal document::

            >>> from fountain.document import FountainDocument
            >>> from fountain.elements import ElementType, FountainElement
            >>> elements = [
            ...     FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            ...     FountainElement(ElementType.ACTION, "John enters.", [], 2),
            ... ]
            >>> document = FountainDocument(elements)
            >>> print(PlainTextRenderer().render(document))
            INT. HOUSE - DAY
            <BLANKLINE>
            John enters.
    """

    def __init__(
        self,
        width: int = 60,
        dialogue_indent: int = 10,
        parenthetical_indent: int = 15,
        cue_indent: int = 22,
    ) -> None:
        self.width = width
        self.dialogue_indent = dialogue_indent
        self.parenthetical_indent = parenthetical_indent
        self.cue_indent = cue_indent

    def render(self, document: FountainDocument) -> str:
        """Render a document to monospace plain text.

        Args:
            document: The parsed document to render.

        Returns:
            The rendered plain-text screenplay, with one blank line between
            blocks.
        """
        blocks = [block for element in document.elements for block in self._render_element(element)]
        return "\n\n".join("\n".join(block) for block in blocks)

    def _render_element(self, element: FountainElement) -> list[list[str]]:
        """Render one element to zero or more blocks of lines.

        Args:
            element: The element to render.

        Returns:
            A list of blocks (each a list of lines). Empty for omitted
            element types and for DUAL_DIALOGUE, whose two child blocks are
            returned separately so they receive their own blank-line
            separation.
        """
        if element.type in _OMITTED_TYPES:
            return []
        if element.type in (ElementType.SCENE_HEADING, ElementType.ACTION, ElementType.CENTERED):
            return [self._indent_and_wrap(element.text, indent=0, wrap_width=self.width)]
        if element.type == ElementType.CHARACTER:
            cue_wrap_width = self.width - self.cue_indent
            return [self._indent_and_wrap(element.text, indent=self.cue_indent, wrap_width=cue_wrap_width)]
        if element.type == ElementType.PARENTHETICAL:
            return [
                self._indent_and_wrap(
                    element.text, indent=self.parenthetical_indent, wrap_width=self.width - self.parenthetical_indent
                )
            ]
        if element.type in (ElementType.DIALOGUE, ElementType.LYRICS):
            dialogue_wrap_width = max(self.width - (2 * self.dialogue_indent), 1)
            return [self._indent_and_wrap(element.text, indent=self.dialogue_indent, wrap_width=dialogue_wrap_width)]
        if element.type == ElementType.TRANSITION:
            wrapped = textwrap.wrap(element.text, width=self.width) or [""]
            return [[line.rjust(self.width) for line in wrapped]]
        if element.type == ElementType.PAGE_BREAK:
            return [["=" * self.width]]
        if element.type == ElementType.DUAL_DIALOGUE:
            return self._render_dual_dialogue(element)
        return [self._indent_and_wrap(element.text, indent=0, wrap_width=self.width)]

    def _render_dual_dialogue(self, element: FountainElement) -> list[list[str]]:
        """Render a DUAL_DIALOGUE element as a left block followed by a right block.

        Single-column stacking: the left character and dialogue render as
        one block, then the right character and dialogue render as a
        second block, per the plan's acceptance for text output.

        Args:
            element: A DUAL_DIALOGUE element carrying left/right character
                and dialogue metadata.

        Returns:
            Zero, one, or two blocks; empty when metadata is missing.
        """
        metadata = element.metadata
        if not metadata:
            return []

        left_character = cast(FountainElement, metadata["left_character"])
        left_dialogue = cast("list[FountainElement]", metadata["left_dialogue"])
        right_character = cast(FountainElement, metadata["right_character"])
        right_dialogue = cast("list[FountainElement]", metadata["right_dialogue"])

        left_lines = self._render_dual_dialogue_side(left_character, left_dialogue)
        right_lines = self._render_dual_dialogue_side(right_character, right_dialogue)
        return [left_lines, right_lines]

    def _render_dual_dialogue_side(self, character: FountainElement, dialogue: list[FountainElement]) -> list[str]:
        """Render one side (character cue plus dialogue lines) of a dual-dialogue pair.

        Args:
            character: The CHARACTER element for this side.
            dialogue: The DIALOGUE (and PARENTHETICAL) elements for this side.

        Returns:
            The flattened lines for this side's single-column block.
        """
        return [line for sub_element in (character, *dialogue) for line in self._render_element(sub_element)[0]]

    def _indent_and_wrap(self, text: str, indent: int, wrap_width: int) -> list[str]:
        """Wrap text to a column width and indent every resulting line.

        The single helper the SCENE_HEADING, ACTION, CHARACTER,
        PARENTHETICAL, DIALOGUE, LYRICS, and CENTERED cases share.

        Args:
            text: The text to wrap.
            indent: Number of leading spaces to prepend to every line.
            wrap_width: Maximum characters per line, excluding the indent.

        Returns:
            One or more indented, wrapped lines. A single blank-indented
            line when text is empty.
        """
        prefix = " " * indent
        wrapped = textwrap.wrap(text, width=max(wrap_width, 1)) or [""]
        return [f"{prefix}{line}" for line in wrapped]
