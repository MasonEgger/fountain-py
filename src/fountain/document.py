"""ABOUTME: Complete Fountain document representation and analysis functionality.
ABOUTME: Provides FountainDocument class for managing parsed screenplay documents with metadata.

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

import json
from typing import Any, Optional

from fountain.elements import ElementType, FountainElement


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

    def __init__(self, elements: list[FountainElement], metadata: Optional[dict[str, str]] = None):
        """Initialize a FountainDocument with elements and optional metadata.

        Args:
            elements: Ordered list of FountainElement objects
            metadata: Optional dictionary of document metadata

        Example:
            Basic initialization::

                >>> from fountain.elements import ElementType, FountainElement
                >>> element = FountainElement(ElementType.ACTION, "Test action", [], 1)
                >>> doc = FountainDocument([element])
                >>> len(doc.elements)
                1
                >>> doc.metadata
                {}
        """
        self.elements = elements
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert the entire document to a dictionary representation.

        Creates a comprehensive dictionary representation of the document,
        including all metadata and element details. This format is useful
        for serialization, debugging, and integration with other tools.

        Returns:
            Dictionary containing 'metadata' and 'elements' keys, where elements
            is a list of dictionaries representing each FountainElement with all
            its properties including type, text, formatting, line_number, and metadata.

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
            "metadata": self.metadata,
            "elements": [
                {
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
                    "metadata": element.metadata,
                }
                for element in self.elements
            ],
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
        characters = set()
        for element in self.elements:
            if element.type == ElementType.CHARACTER:
                # Clean up character name (remove parentheticals, etc.)
                name = element.text.strip().upper()
                if name.endswith("^"):
                    name = name[:-1].strip()
                characters.add(name)
        return sorted(characters)

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
        scenes = []
        for element in self.elements:
            if element.type == ElementType.SCENE_HEADING:
                scenes.append(element.text.strip())
        return scenes

    def get_statistics(self) -> dict[str, int]:
        """Generate comprehensive statistics about the document content.

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
        stats = {
            "total_elements": len(self.elements),
            "characters": len(self.get_characters()),
            "scenes": len(self.get_scenes()),
        }

        # Count by element type
        for element_type in ElementType:
            count = sum(1 for el in self.elements if el.type == element_type)
            stats[f"{element_type.value}_count"] = count

        return stats

    def to_html(self, theme: str = "default") -> str:
        """Convert the document to HTML format using the specified theme.

        Renders the entire document as properly formatted HTML suitable for
        display in web browsers or HTML viewers. The output includes appropriate
        CSS classes for styling and maintains the screenplay format structure.

        Args:
            theme: Theme name for styling the HTML output (default: "default")

        Returns:
            Complete HTML string representation of the document.

        Note:
            This method creates an HTMLRenderer instance and delegates rendering
            to it. Different themes may produce different visual presentations
            while maintaining the same semantic structure.

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
                >>> '<div class=' in html or '<p class=' in html  # Has CSS classes
                True
        """
        from fountain.renderer import HTMLRenderer

        renderer = HTMLRenderer(theme)
        return renderer.render(self)
