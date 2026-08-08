# ABOUTME: Core Fountain document element types and data structures.
# Defines ElementType enum, FormatSpan for inline formatting, and FountainElement dataclass.
"""
Core Fountain document element types and data structures.

This module provides the fundamental building blocks for representing parsed Fountain
screenplay elements. Each element has a type, text content, formatting information,
and optional metadata.

Example:
    Creating a simple scene heading element::

        >>> from fountain.elements import ElementType, FountainElement
        >>> element = FountainElement(
        ...     type=ElementType.SCENE_HEADING,
        ...     text="INT. COFFEE SHOP - DAY",
        ...     formatting=[],
        ...     line_number=1
        ... )
        >>> element.type.value
        'scene_heading'
        >>> element.text
        'INT. COFFEE SHOP - DAY'
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, NamedTuple, Union

FormatType = Literal["bold", "italic", "underline", "bold_italic"]
MetadataValue = Union[str, int, bool, list["FountainElement"], "FountainElement", None]


class ElementType(Enum):
    """Enumeration of all supported Fountain screenplay element types.

    The Fountain format supports various types of screenplay elements, each with
    specific formatting rules and purposes. This enum provides a complete catalog
    of all supported element types.

    Attributes:
        TITLE_PAGE: Metadata at the beginning of the script (Title:, Author:, etc.)
        SCENE_HEADING: Location and time indicators (INT./EXT. LOCATION - TIME)
        ACTION: Narrative description of what happens on screen
        CHARACTER: Character name that speaks dialogue
        DIALOGUE: The words spoken by a character
        PARENTHETICAL: Direction within dialogue, enclosed in parentheses
        TRANSITION: Scene transitions like FADE IN:, CUT TO:, etc.
        NOTE: Comments not included in final output [[This is a note]]
        BONEYARD: Commented-out content /*This is boneyard text*/
        SECTION: Hierarchical section headings # Section Name
        SYNOPSIS: Plot summaries = This is a synopsis
        DUAL_DIALOGUE: Special formatting for simultaneous character speech
        PAGE_BREAK: Forced page breaks ===
        CENTERED: Centered text >Centered Text<
        LYRICS: Song lyrics or music ~Lyrics go here~

    Example:
        Checking element types::

            >>> ElementType.SCENE_HEADING.value
            'scene_heading'
            >>> ElementType.CHARACTER.value
            'character'
            >>> len(ElementType)
            15

        Using element types for filtering::

            >>> dialogue_types = {ElementType.CHARACTER, ElementType.DIALOGUE, ElementType.PARENTHETICAL}
            >>> ElementType.DIALOGUE in dialogue_types
            True
            >>> ElementType.ACTION in dialogue_types
            False
    """

    TITLE_PAGE = "title_page"
    SCENE_HEADING = "scene_heading"
    ACTION = "action"
    CHARACTER = "character"
    DIALOGUE = "dialogue"
    PARENTHETICAL = "parenthetical"
    TRANSITION = "transition"
    NOTE = "note"
    BONEYARD = "boneyard"
    SECTION = "section"
    SYNOPSIS = "synopsis"
    DUAL_DIALOGUE = "dual_dialogue"
    PAGE_BREAK = "page_break"
    CENTERED = "centered"
    LYRICS = "lyrics"


class FormatSpan(NamedTuple):
    """Represents an inline formatting span within text content.

    FormatSpan defines a contiguous region of text that has specific formatting
    applied, such as bold, italic, or underline. The span is defined by start
    and end character positions within the parent text.

    Attributes:
        start: Zero-based starting character position (inclusive)
        end: Zero-based ending character position (exclusive)
        format_type: Type of formatting applied ('bold', 'italic', 'underline')

    Note:
        The end position is exclusive, following Python slice conventions.
        For text "Hello **world**!", a bold span on "world" would be
        FormatSpan(start=6, end=11, format_type='bold').

    Example:
        Creating and using format spans::

            >>> text = "This is bold and italic text"
            >>> bold_span = FormatSpan(start=8, end=12, format_type='bold')
            >>> italic_span = FormatSpan(start=17, end=23, format_type='italic')
            >>> text[bold_span.start:bold_span.end]
            'bold'
            >>> text[italic_span.start:italic_span.end]
            'italic'

        Validating span bounds::

            >>> span = FormatSpan(start=5, end=10, format_type='underline')
            >>> span.start < span.end
            True
            >>> span.format_type in ['bold', 'italic', 'underline']
            True
    """

    start: int
    end: int
    format_type: FormatType


@dataclass
class FountainElement:
    """Represents a single structural element in a Fountain screenplay document.

    FountainElement is the core building block of parsed Fountain documents.
    Each element represents one logical piece of the screenplay, such as a
    scene heading, character name, dialogue, or action description.

    Args:
        type: The ElementType classification for this element
        text: The textual content of the element. For most element types the
            emphasis and forcing markers are removed. BONEYARD elements keep
            their /* ... */ delimiters and NOTE elements keep their [[ ... ]]
            delimiters, so their text is verbatim including the delimiters.
        formatting: List of FormatSpan objects describing inline formatting
        line_number: Source line number where this element was found (1-based)
        metadata: Optional dictionary for element-specific metadata

    Attributes:
        type: ElementType enum value indicating the element's role
        text: Text content with Fountain emphasis and forcing markers removed
            for most element types. Two exceptions carry their markup verbatim:
            BONEYARD elements retain their /* ... */ delimiters and NOTE
            elements retain their [[ ... ]] delimiters.
        formatting: Zero or more FormatSpan objects for inline styles
        line_number: Original line number from source document
        metadata: Dictionary containing element-specific data and attributes

    Note:
        The metadata dictionary is automatically initialized to an empty dict
        if None is provided. Different element types may store different
        metadata (e.g., scene numbers, character extensions, etc.).

    Example:
        Creating a basic action element::

            >>> from fountain.elements import ElementType, FountainElement
            >>> action = FountainElement(
            ...     type=ElementType.ACTION,
            ...     text="John walks into the room.",
            ...     formatting=[],
            ...     line_number=5
            ... )
            >>> action.type
            <ElementType.ACTION: 'action'>
            >>> action.text
            'John walks into the room.'
            >>> action.metadata
            {}

        Creating a character element with metadata::

            >>> character = FountainElement(
            ...     type=ElementType.CHARACTER,
            ...     text="SARAH",
            ...     formatting=[],
            ...     line_number=10,
            ...     metadata={"extension": "(O.S.)", "force_character": True}
            ... )
            >>> character.metadata["extension"]
            '(O.S.)'

        Creating dialogue with formatting::

            >>> from fountain.elements import FormatSpan
            >>> dialogue = FountainElement(
            ...     type=ElementType.DIALOGUE,
            ...     text="I am very excited!",
            ...     formatting=[FormatSpan(start=5, end=9, format_type='italic')],
            ...     line_number=11
            ... )
            >>> dialogue.formatting[0].format_type
            'italic'
    """

    type: ElementType
    text: str
    formatting: list[FormatSpan]
    line_number: int
    metadata: dict[str, MetadataValue] | None = None

    def __post_init__(self) -> None:
        """Initialize metadata dictionary if None was provided.

        This ensures that metadata is always available as a dictionary,
        preventing AttributeError when accessing metadata attributes.

        Example:
            Automatic metadata initialization::

                >>> element = FountainElement(
                ...     type=ElementType.ACTION,
                ...     text="Test",
                ...     formatting=[],
                ...     line_number=1,
                ...     metadata=None
                ... )
                >>> isinstance(element.metadata, dict)
                True
                >>> element.metadata
                {}
        """
        if self.metadata is None:
            self.metadata = {}


@dataclass(frozen=True)
class ValidationIssue:
    """Represents a single diagnostic issue found while validating a Fountain document.

    ValidationIssue is emitted by the validation API to report problems detected in
    a Fountain source document, such as an unclosed boneyard comment or an orphaned
    character cue. Instances are frozen (immutable and hashable) so that collections
    of issues can be deduplicated and safely shared.

    Args:
        line_number: Source line number where the issue was detected (1-based)
        severity: Diagnostic severity, either 'error' or 'warning'
        code: Stable machine-readable identifier for the diagnostic (e.g. 'unclosed-boneyard')
        message: Human-readable description of the issue

    Attributes:
        line_number: 1-based source line number the issue points at
        severity: Either 'error' or 'warning'
        code: Stable diagnostic code used to identify the issue programmatically
        message: Human-readable explanation of the issue

    Example:
        Creating and inspecting a validation issue::

            >>> from fountain.elements import ValidationIssue
            >>> issue = ValidationIssue(
            ...     line_number=3,
            ...     severity="error",
            ...     code="unclosed-boneyard",
            ...     message="Boneyard comment opened but never closed",
            ... )
            >>> issue.line_number
            3
            >>> issue.severity
            'error'
            >>> issue.code
            'unclosed-boneyard'

        Issues are immutable and hashable::

            >>> hash(issue) == hash(issue)
            True
    """

    line_number: int
    severity: Literal["error", "warning"]
    code: str
    message: str
