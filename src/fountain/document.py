# ABOUTME: Fountain document representation and analysis functionality.
# Provides FountainDocument class for managing parsed screenplay documents with metadata.
"""
Fountain document representation and analysis functionality.

This module contains the FountainDocument class, which serves as the primary container
for parsed Fountain screenplay content. It provides methods for document analysis,
statistics generation, format conversion, and character/scene extraction.

Example:
    Basic document creation and analysis::

        >>> from fountain.elements import ElementType, FountainElement
        >>> from fountain.document import FountainDocument
        >>> elements = [
        ...     FountainElement(ElementType.TITLE_PAGE, "Title: My Script", [], 1),
        ...     FountainElement(ElementType.SCENE_HEADING, "INT. OFFICE - DAY", [], 2),
        ...     FountainElement(ElementType.CHARACTER, "JOHN", [], 3),
        ...     FountainElement(ElementType.DIALOGUE, "Hello, world!", [], 4)
        ... ]
        >>> doc = FountainDocument(elements)
        >>> len(doc.elements)
        4
        >>> doc.get_characters()
        ['JOHN']
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Self, TypeGuard, TypeVar, get_args

from fountain.elements import ElementType, FormatSpan, FormatType, FountainElement, MetadataValue, ValidationIssue

_FieldType = TypeVar("_FieldType")

JSON_SCHEMA_VERSION = 1
"""Version of the ``to_dict``/``to_json`` output shape. See :doc:`/reference/json-schema`."""


def _element_to_dict(element: FountainElement) -> dict[str, object]:
    """Convert a single FountainElement to a dictionary, recursing into metadata.

    Metadata values that are themselves FountainElement instances (or lists of
    them, as with dual-dialogue's left/right character and dialogue blocks) are
    serialized through this same helper so the result is entirely JSON-safe.

    Args:
        element: The FountainElement to convert.

    Returns:
        Dictionary with keys type, text, formatting, line_number, and metadata,
        where metadata has been recursively serialized.

    Example:
        Converting a plain element::

            >>> from fountain.elements import ElementType, FountainElement
            >>> element = FountainElement(ElementType.ACTION, "He runs.", [], 1)
            >>> _element_to_dict(element)["type"]
            'action'

        Converting an element whose metadata nests another element::

            >>> character = FountainElement(ElementType.CHARACTER, "BRICK", [], 1)
            >>> parent = FountainElement(
            ...     ElementType.DUAL_DIALOGUE, "", [], 1, {"left_character": character}
            ... )
            >>> _element_to_dict(parent)["metadata"]["left_character"]["type"]
            'character'
    """
    serialized_metadata: dict[str, object] = {}
    for key, value in element.metadata.items():
        if isinstance(value, FountainElement):
            serialized_metadata[key] = _element_to_dict(value)
        elif isinstance(value, list):
            serialized_metadata[key] = [
                _element_to_dict(item) if isinstance(item, FountainElement) else item for item in value
            ]
        else:
            serialized_metadata[key] = value

    return {
        "type": element.type.value,
        "text": element.text,
        "formatting": [
            {
                "start": span.start,
                "end": span.end,
                "format_type": span.format_type,
            }
            for span in element.formatting
        ],
        "line_number": element.line_number,
        "metadata": serialized_metadata,
    }


def _require_field(data: dict[str, object], key: str, expected_type: type[_FieldType]) -> _FieldType:
    """Return ``data[key]``, checking it exists and has the expected type.

    ``from_dict`` reads data that crossed a serialization boundary, so every field is
    checked here rather than trusted.

    Args:
        data: The serialized mapping to read from.
        key: The field to read.
        expected_type: The type the field's value must be.

    Returns:
        The field's value.

    Raises:
        ValueError: If the field is missing or holds a value of another type.

    Example:
        >>> _require_field({"text": "Hi."}, "text", str)
        'Hi.'
        >>> _require_field({"text": 3}, "text", str)
        Traceback (most recent call last):
            ...
        ValueError: Malformed document data: 'text' must be str, got int
    """
    value = data.get(key)
    if not isinstance(value, expected_type):
        raise ValueError(
            f"Malformed document data: {key!r} must be {expected_type.__name__}, got {type(value).__name__}"
        )
    return value


def _is_format_type(value: object) -> TypeGuard[FormatType]:
    """Whether ``value`` is one of the ``FormatType`` literal strings."""
    return value in get_args(FormatType)


def _element_from_dict(data: dict[str, object]) -> FountainElement:
    """Rebuild a single FountainElement from its dictionary form, recursing into metadata.

    This is the inverse of :func:`_element_to_dict`; keep the two symmetric. A dict-valued
    metadata entry is a nested serialized element and becomes a FountainElement again; a
    list-valued entry is a list of nested serialized elements.

    Args:
        data: Dictionary with keys type, text, formatting, line_number, and metadata,
            as produced by :func:`_element_to_dict`.

    Returns:
        The reconstructed FountainElement, with ``type`` an ElementType member and
        ``formatting`` entries FormatSpan instances.

    Raises:
        ValueError: If a field is missing, has the wrong type, or names an unknown
            element type or format type.

    Example:
        Rebuilding a plain element::

            >>> from fountain.elements import ElementType, FountainElement
            >>> element = FountainElement(ElementType.ACTION, "He runs.", [], 1)
            >>> _element_from_dict(_element_to_dict(element)) == element
            True
    """
    formatting: list[FormatSpan] = []
    for span in _require_field(data, "formatting", list):
        if not isinstance(span, dict):
            raise ValueError(f"Malformed document data: formatting span must be dict, got {type(span).__name__}")
        format_type = span.get("format_type")
        if not _is_format_type(format_type):
            raise ValueError(f"Malformed document data: unknown format_type {format_type!r}")
        formatting.append(FormatSpan(_require_field(span, "start", int), _require_field(span, "end", int), format_type))

    metadata: dict[str, MetadataValue] = {}
    for key, value in _require_field(data, "metadata", dict).items():
        if isinstance(value, dict):
            metadata[key] = _element_from_dict(value)
        elif isinstance(value, list):
            if not all(isinstance(item, dict) for item in value):
                raise ValueError(f"Malformed document data: metadata list {key!r} must hold serialized elements")
            metadata[key] = [_element_from_dict(item) for item in value]
        elif value is None or isinstance(value, (str, int)):
            metadata[key] = value
        else:
            raise ValueError(f"Malformed document data: metadata {key!r} has unsupported type {type(value).__name__}")

    return FountainElement(
        type=ElementType(_require_field(data, "type", str)),
        text=_require_field(data, "text", str),
        formatting=formatting,
        line_number=_require_field(data, "line_number", int),
        metadata=metadata,
    )


class FountainDocument:
    """Represents a complete Fountain screenplay document with analysis capabilities.

    FountainDocument is the primary container for parsed Fountain content, providing
    methods for document analysis, statistics generation, and format conversion.
    It contains a list of FountainElement objects and optional document metadata.

    Args:
        elements: List of FountainElement objects representing the document content
        metadata: Optional dictionary containing document-level metadata (title page data)

    Attributes:
        elements: List of all parsed FountainElement objects in document order
        metadata: Dictionary containing document metadata like title, author, etc.

    Example:
        Creating a document with basic elements::

            >>> from fountain.elements import ElementType, FountainElement
            >>> from fountain.document import FountainDocument
            >>> elements = [
            ...     FountainElement(ElementType.SCENE_HEADING, "EXT. PARK - DAY", [], 1),
            ...     FountainElement(ElementType.ACTION, "Birds are singing.", [], 2),
            ...     FountainElement(ElementType.CHARACTER, "ALICE", [], 3),
            ...     FountainElement(ElementType.DIALOGUE, "What a beautiful day!", [], 4)
            ... ]
            >>> doc = FountainDocument(elements)
            >>> len(doc.elements)
            4
            >>> doc.elements[0].type.value
            'scene_heading'

        Creating a document with metadata::

            >>> metadata = {"title": "My Script", "author": "Jane Doe"}
            >>> doc_with_meta = FountainDocument(elements, metadata)
            >>> doc_with_meta.metadata["title"]
            'My Script'
            >>> doc_with_meta.metadata["author"]
            'Jane Doe'
    """

    def __init__(
        self,
        elements: list[FountainElement],
        metadata: dict[str, str] | None = None,
        issues: list[ValidationIssue] | None = None,
    ) -> None:
        """Initialize a FountainDocument with elements and optional metadata.

        Args:
            elements: Ordered list of FountainElement objects
            metadata: Optional dictionary of document metadata
            issues: Optional diagnostics recorded during parsing (unclosed constructs,
                orphan cues, empty document). Empty when the document is well formed.

        Example:
            Basic initialization::

                >>> from fountain.elements import ElementType, FountainElement
                >>> element = FountainElement(ElementType.ACTION, "Test action", [], 1)
                >>> doc = FountainDocument([element])
                >>> len(doc.elements)
                1
                >>> doc.metadata
                {}
                >>> doc.issues
                []
        """
        self.elements = elements
        self.metadata = metadata or {}
        self.issues = issues or []

    def to_dict(self) -> dict[str, object]:
        """Convert the entire document to a dictionary representation.

        Creates a dictionary representation of the document,
        including all metadata and element details. This format is useful
        for serialization, debugging, and integration with other tools.

        Returns:
            Dictionary containing 'schema_version', 'metadata', and 'elements' keys,
            where elements is a list of dictionaries representing each FountainElement
            with all its properties including type, text, formatting, line_number, and
            metadata. See :doc:`/reference/json-schema` for the full documented shape.

        Example:
            Converting a simple document to dictionary::

                >>> from fountain.elements import ElementType, FountainElement, FormatSpan
                >>> from fountain.document import FountainDocument
                >>> elements = [
                ...     FountainElement(ElementType.CHARACTER, "JANE", [], 1),
                ...     FountainElement(
                ...         ElementType.DIALOGUE,
                ...         "Hello there!",
                ...         [FormatSpan(0, 5, 'bold')],
                ...         2
                ...     )
                ... ]
                >>> doc = FountainDocument(elements, {"title": "Test"})
                >>> result = doc.to_dict()
                >>> result["schema_version"]
                1
                >>> result["metadata"]["title"]
                'Test'
                >>> len(result["elements"])
                2
                >>> result["elements"][0]["type"]
                'character'
                >>> result["elements"][1]["formatting"][0]["format_type"]
                'bold'
        """
        return {
            "schema_version": JSON_SCHEMA_VERSION,
            "metadata": self.metadata,
            "elements": [_element_to_dict(element) for element in self.elements],
        }

    def to_json(self) -> str:
        """Convert the document to a formatted JSON string.

        Converts the document to a JSON string representation using the same
        structure as to_dict(). The output is formatted with 2-space indentation
        for readability.

        Returns:
            Formatted JSON string representation of the document.

        Example:
            Converting document to JSON::

                >>> from fountain.elements import ElementType, FountainElement
                >>> from fountain.document import FountainDocument
                >>> elements = [FountainElement(ElementType.ACTION, "Test", [], 1)]
                >>> doc = FountainDocument(elements, {"title": "Sample"})
                >>> json_str = doc.to_json()
                >>> '"title": "Sample"' in json_str
                True
                >>> '"type": "action"' in json_str
                True
                >>> json_str.count('\\n') > 5  # Multiple lines due to formatting
                True
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Reconstruct a FountainDocument from its dictionary form.

        Inverse of :meth:`to_dict`. Rebuilds every element, including nested
        FountainElement values in metadata (such as dual-dialogue's left/right
        character and dialogue blocks), via :func:`_element_from_dict`.

        Args:
            data: Dictionary with schema_version, metadata, and elements keys,
                as produced by :meth:`to_dict`.

        Returns:
            The reconstructed FountainDocument.

        Raises:
            ValueError: If schema_version does not match JSON_SCHEMA_VERSION, or if
                any field is missing or has the wrong type.

        Example:
            Round-tripping a document through its dict form::

                >>> from fountain.elements import ElementType, FountainElement
                >>> from fountain.document import FountainDocument
                >>> doc = FountainDocument([FountainElement(ElementType.ACTION, "He runs.", [], 1)])
                >>> FountainDocument.from_dict(doc.to_dict()).to_dict() == doc.to_dict()
                True

            An unrecognized schema version is a hard error::

                >>> FountainDocument.from_dict({"schema_version": 999, "metadata": {}, "elements": []})
                Traceback (most recent call last):
                ...
                ValueError: Unsupported schema_version 999; expected 1
        """
        schema_version = data["schema_version"]
        if schema_version != JSON_SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version {schema_version!r}; expected {JSON_SCHEMA_VERSION}")

        metadata = _require_field(data, "metadata", dict)
        if not all(isinstance(key, str) and isinstance(value, str) for key, value in metadata.items()):
            raise ValueError("Malformed document data: title page metadata must map strings to strings")

        elements: list[FountainElement] = []
        for element_data in _require_field(data, "elements", list):
            if not isinstance(element_data, dict):
                raise ValueError(f"Malformed document data: element must be dict, got {type(element_data).__name__}")
            elements.append(_element_from_dict(element_data))
        return cls(elements, metadata)

    @classmethod
    def from_json(cls, text: str) -> Self:
        """Reconstruct a FountainDocument from its JSON string form.

        Args:
            text: JSON string as produced by :meth:`to_json`.

        Returns:
            The reconstructed FountainDocument.

        Raises:
            ValueError: If the text is not a JSON object, or if :meth:`from_dict`
                rejects the decoded data.

        Example:
            Round-tripping through JSON::

                >>> from fountain.elements import ElementType, FountainElement
                >>> from fountain.document import FountainDocument
                >>> doc = FountainDocument([FountainElement(ElementType.ACTION, "He runs.", [], 1)])
                >>> FountainDocument.from_json(doc.to_json()).to_dict() == doc.to_dict()
                True
        """
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Malformed document data: expected a JSON object, got {type(data).__name__}")
        return cls.from_dict(data)

    def get_characters(self) -> list[str]:
        """Extract and return all unique character names from the document.

        Scans all CHARACTER elements in the document and extracts unique character
        names. Character names are cleaned by removing dual dialogue markers (^)
        and normalizing to uppercase. The returned list is sorted alphabetically.

        Returns:
            Sorted list of unique character names found in the document.

        Note:
            Character names are automatically converted to uppercase and sorted.
            Dual dialogue markers (^) are stripped from character names.

        Example:
            Extracting characters from a document::

                >>> from fountain.elements import ElementType, FountainElement
                >>> from fountain.document import FountainDocument
                >>> elements = [
                ...     FountainElement(ElementType.CHARACTER, "alice", [], 1),
                ...     FountainElement(ElementType.DIALOGUE, "Hello!", [], 2),
                ...     FountainElement(ElementType.CHARACTER, "BOB", [], 3),
                ...     FountainElement(ElementType.DIALOGUE, "Hi there!", [], 4),
                ...     FountainElement(ElementType.CHARACTER, "alice", [], 5),  # Duplicate
                ...     FountainElement(ElementType.CHARACTER, "CHARLIE^", [], 6)  # Dual dialogue
                ... ]
                >>> doc = FountainDocument(elements)
                >>> characters = doc.get_characters()
                >>> characters
                ['ALICE', 'BOB', 'CHARLIE']
                >>> len(characters)
                3
        """
        # Normalize each cue to uppercase and drop a dual dialogue caret
        return sorted(
            {
                element.text.strip().upper().removesuffix("^").strip()
                for element in self.elements
                if element.type == ElementType.CHARACTER
            }
        )

    def get_scenes(self) -> list[str]:
        """Extract and return all scene headings from the document in order.

        Scans all SCENE_HEADING elements and returns their text content.
        Scene headings typically follow the format "INT./EXT. LOCATION - TIME"
        and are returned in the order they appear in the document.

        Returns:
            List of scene heading strings in document order.

        Example:
            Extracting scene headings::

                >>> from fountain.elements import ElementType, FountainElement
                >>> from fountain.document import FountainDocument
                >>> elements = [
                ...     FountainElement(ElementType.SCENE_HEADING, "INT. COFFEE SHOP - DAY", [], 1),
                ...     FountainElement(ElementType.ACTION, "People are chatting.", [], 2),
                ...     FountainElement(ElementType.SCENE_HEADING, "EXT. PARK - EVENING", [], 3),
                ...     FountainElement(ElementType.ACTION, "The sun is setting.", [], 4)
                ... ]
                >>> doc = FountainDocument(elements)
                >>> scenes = doc.get_scenes()
                >>> scenes
                ['INT. COFFEE SHOP - DAY', 'EXT. PARK - EVENING']
                >>> len(scenes)
                2
        """
        return [element.text.strip() for element in self.elements if element.type == ElementType.SCENE_HEADING]

    def get_statistics(self) -> dict[str, int]:
        """Generate statistics about the document content.

        Calculates various statistics about the document including total element
        count, number of unique characters, number of scenes, and counts for
        each element type. This provides a useful overview of document structure.

        Returns:
            Dictionary containing document statistics with the following keys:
            - 'total_elements': Total number of elements in document
            - 'characters': Number of unique characters
            - 'scenes': Number of scene headings
            - '{element_type}_count': Count for each ElementType (e.g., 'dialogue_count')

        Example:
            Getting document statistics::

                >>> from fountain.elements import ElementType, FountainElement
                >>> from fountain.document import FountainDocument
                >>> elements = [
                ...     FountainElement(ElementType.SCENE_HEADING, "INT. ROOM - DAY", [], 1),
                ...     FountainElement(ElementType.CHARACTER, "ALICE", [], 2),
                ...     FountainElement(ElementType.DIALOGUE, "Hello!", [], 3),
                ...     FountainElement(ElementType.CHARACTER, "BOB", [], 4),
                ...     FountainElement(ElementType.DIALOGUE, "Hi!", [], 5),
                ...     FountainElement(ElementType.ACTION, "They smile.", [], 6)
                ... ]
                >>> doc = FountainDocument(elements)
                >>> stats = doc.get_statistics()
                >>> stats['total_elements']
                6
                >>> stats['characters']
                2
                >>> stats['scenes']
                1
                >>> stats['dialogue_count']
                2
                >>> stats['action_count']
                1
        """
        type_counts = Counter(element.type for element in self.elements)

        stats: dict[str, int] = {
            "total_elements": len(self.elements),
            "characters": len(self.get_characters()),
            "scenes": len(self.get_scenes()),
        }

        for element_type in ElementType:
            stats[f"{element_type.value}_count"] = type_counts.get(element_type, 0)

        return stats

    def to_html(self) -> str:
        """Convert the document to a standalone HTML page with embedded CSS.

        Renders the entire document as properly formatted HTML suitable for
        saving as a self-contained HTML file. The output includes embedded CSS
        styling and maintains the screenplay format structure.

        Returns:
            Complete HTML string with embedded CSS, suitable for saving to a file.

        Note:
            This method creates an HTMLRenderer instance and delegates to
            ``render_page()``. For an HTML fragment without CSS (e.g., for
            embedding in another page), use ``HTMLRenderer.render()`` directly.

        Example:
            Converting to HTML::

                >>> from fountain.elements import ElementType, FountainElement
                >>> from fountain.document import FountainDocument
                >>> elements = [
                ...     FountainElement(ElementType.SCENE_HEADING, "INT. ROOM - DAY", [], 1),
                ...     FountainElement(ElementType.ACTION, "A simple room.", [], 2)
                ... ]
                >>> doc = FountainDocument(elements)
                >>> html = doc.to_html()
                >>> 'INT. ROOM - DAY' in html
                True
                >>> 'A simple room.' in html
                True
                >>> '<style>' in html
                True
        """
        from fountain.renderer import HTMLRenderer

        renderer = HTMLRenderer()
        return renderer.render_page(self)
