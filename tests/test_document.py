"""
Tests for the FountainDocument class.
"""

import json

from fountain.document import FountainDocument
from fountain.elements import ElementType, FountainElement


class TestFountainDocument:
    def test_document_creation(self):
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 2),
            FountainElement(ElementType.DIALOGUE, "Hello, world!", [], 3),
        ]
        metadata = {"title": "Test Script", "author": "Test Author"}

        document = FountainDocument(elements, metadata)

        assert len(document.elements) == 3
        assert document.metadata["title"] == "Test Script"
        assert document.metadata["author"] == "Test Author"

    def test_to_dict(self):
        elements = [
            FountainElement(ElementType.CHARACTER, "JOHN", [], 1),
            FountainElement(ElementType.DIALOGUE, "Hello!", [], 2),
        ]
        metadata = {"title": "Test"}

        document = FountainDocument(elements, metadata)
        doc_dict = document.to_dict()

        assert "metadata" in doc_dict
        assert "elements" in doc_dict
        assert doc_dict["metadata"]["title"] == "Test"
        assert len(doc_dict["elements"]) == 2
        assert doc_dict["elements"][0]["type"] == "character"
        assert doc_dict["elements"][0]["text"] == "JOHN"

    def test_to_json(self):
        elements = [
            FountainElement(ElementType.CHARACTER, "JOHN", [], 1),
        ]
        document = FountainDocument(elements)

        json_str = document.to_json()
        parsed = json.loads(json_str)

        assert "metadata" in parsed
        assert "elements" in parsed
        assert len(parsed["elements"]) == 1

    def test_get_characters(self):
        elements = [
            FountainElement(ElementType.CHARACTER, "JOHN", [], 1),
            FountainElement(ElementType.DIALOGUE, "Hello!", [], 2),
            FountainElement(ElementType.CHARACTER, "SARAH", [], 3),
            FountainElement(ElementType.DIALOGUE, "Hi back!", [], 4),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 5),  # Duplicate
            FountainElement(ElementType.DIALOGUE, "How are you?", [], 6),
        ]

        document = FountainDocument(elements)
        characters = document.get_characters()

        assert len(characters) == 2
        assert "JOHN" in characters
        assert "SARAH" in characters
        assert characters == sorted(characters)  # Should be sorted

    def test_get_scenes(self):
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.ACTION, "John sits down.", [], 2),
            FountainElement(ElementType.SCENE_HEADING, "EXT. PARK - NIGHT", [], 3),
            FountainElement(ElementType.ACTION, "Sarah walks by.", [], 4),
        ]

        document = FountainDocument(elements)
        scenes = document.get_scenes()

        assert len(scenes) == 2
        assert "INT. HOUSE - DAY" in scenes
        assert "EXT. PARK - NIGHT" in scenes

    def test_get_statistics(self):
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 2),
            FountainElement(ElementType.DIALOGUE, "Hello!", [], 3),
            FountainElement(ElementType.CHARACTER, "SARAH", [], 4),
            FountainElement(ElementType.DIALOGUE, "Hi!", [], 5),
            FountainElement(ElementType.ACTION, "They hug.", [], 6),
        ]

        document = FountainDocument(elements)
        stats = document.get_statistics()

        assert stats["total_elements"] == 6
        assert stats["characters"] == 2
        assert stats["scenes"] == 1
        assert stats["scene_heading_count"] == 1
        assert stats["character_count"] == 2
        assert stats["dialogue_count"] == 2
        assert stats["action_count"] == 1

    def test_character_with_dual_marker(self):
        """Test character names ending with ^ (line 55)."""
        elements = [
            FountainElement(ElementType.CHARACTER, "JOHN^", [], 1),
            FountainElement(ElementType.CHARACTER, "SARAH^", [], 2),
        ]
        document = FountainDocument(elements)
        characters = document.get_characters()
        assert "JOHN" in characters
        assert "SARAH" in characters
        assert "JOHN^" not in characters

    def test_to_html_method(self):
        """Test direct to_html method (lines 84-87)."""
        elements = [FountainElement(ElementType.ACTION, "Some action", [], 1)]
        document = FountainDocument(elements)
        html = document.to_html()
        assert '<div class="action">' in html

    def test_to_html_with_theme(self):
        """Test to_html with custom theme (lines 84-87)."""
        document = FountainDocument([])
        html = document.to_html(theme="custom")
        assert "<style>" in html

    def test_lyrics_in_statistics(self):
        """Test that lyrics are included in document statistics."""
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. THEATER - NIGHT", [], 1),
            FountainElement(ElementType.CHARACTER, "SARAH", [], 2),
            FountainElement(ElementType.PARENTHETICAL, "(singing)", [], 3),
            FountainElement(ElementType.LYRICS, "Oh what a beautiful morning", [], 4),
            FountainElement(ElementType.LYRICS, "Oh what a beautiful day", [], 5),
            FountainElement(ElementType.ACTION, "The audience applauds.", [], 6),
        ]

        document = FountainDocument(elements)
        stats = document.get_statistics()

        assert stats["total_elements"] == 6
        assert stats["characters"] == 1
        assert stats["scenes"] == 1
        assert stats["lyrics_count"] == 2
        assert stats["scene_heading_count"] == 1
        assert stats["character_count"] == 1
        assert stats["parenthetical_count"] == 1
        assert stats["action_count"] == 1

    def test_lyrics_document_to_dict(self):
        """Test that lyrics serialize correctly in to_dict."""
        elements = [
            FountainElement(ElementType.LYRICS, "First line", [], 1),
            FountainElement(ElementType.LYRICS, "Second line", [], 2),
        ]

        document = FountainDocument(elements)
        doc_dict = document.to_dict()

        assert len(doc_dict["elements"]) == 2
        assert doc_dict["elements"][0]["type"] == "lyrics"
        assert doc_dict["elements"][0]["text"] == "First line"
        assert doc_dict["elements"][1]["type"] == "lyrics"
        assert doc_dict["elements"][1]["text"] == "Second line"
