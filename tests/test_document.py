# ABOUTME: Tests for FountainDocument analysis and container methods.
# Covers character extraction, scene listing, statistics, and document-level operations.
"""
Tests for the FountainDocument class.
"""

import json

import pytest

from fountain.document import JSON_SCHEMA_VERSION, FountainDocument
from fountain.elements import ElementType, FormatSpan, FountainElement
from fountain.parser import FountainParser


class TestFountainDocument:
    def test_document_creation(self) -> None:
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

    def test_to_dict(self) -> None:
        elements = [
            FountainElement(ElementType.CHARACTER, "JOHN", [], 1),
            FountainElement(ElementType.DIALOGUE, "Hello!", [], 2),
        ]
        metadata = {"title": "Test"}

        document = FountainDocument(elements, metadata)
        doc_dict = document.to_dict()

        assert "metadata" in doc_dict
        assert "elements" in doc_dict
        metadata_data = doc_dict["metadata"]
        elements_data = doc_dict["elements"]
        assert isinstance(metadata_data, dict)
        assert isinstance(elements_data, list)
        assert metadata_data["title"] == "Test"
        assert len(elements_data) == 2
        assert elements_data[0]["type"] == "character"
        assert elements_data[0]["text"] == "JOHN"

    def test_to_json(self) -> None:
        elements = [
            FountainElement(ElementType.CHARACTER, "JOHN", [], 1),
        ]
        document = FountainDocument(elements)

        json_str = document.to_json()
        parsed = json.loads(json_str)

        assert "metadata" in parsed
        assert "elements" in parsed
        assert len(parsed["elements"]) == 1

    def test_get_characters(self) -> None:
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

    def test_get_scenes(self) -> None:
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

    def test_get_statistics(self) -> None:
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

    def test_character_with_dual_marker(self) -> None:
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

    def test_to_html_method(self) -> None:
        """Test direct to_html method (lines 84-87)."""
        elements = [FountainElement(ElementType.ACTION, "Some action", [], 1)]
        document = FountainDocument(elements)
        html = document.to_html()
        assert '<div class="fountain-action">' in html

    def test_to_html_returns_standalone_page(self) -> None:
        """Test that to_html returns a full page with embedded CSS."""
        document = FountainDocument([])
        html = document.to_html()
        assert "<style>" in html
        assert ".fountain-script" in html

    def test_lyrics_in_statistics(self) -> None:
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

    def test_lyrics_document_to_dict(self) -> None:
        """Test that lyrics serialize correctly in to_dict."""
        elements = [
            FountainElement(ElementType.LYRICS, "First line", [], 1),
            FountainElement(ElementType.LYRICS, "Second line", [], 2),
        ]

        document = FountainDocument(elements)
        doc_dict = document.to_dict()

        elements_data = doc_dict["elements"]
        assert isinstance(elements_data, list)
        assert len(elements_data) == 2
        assert elements_data[0]["type"] == "lyrics"
        assert elements_data[0]["text"] == "First line"
        assert elements_data[1]["type"] == "lyrics"
        assert elements_data[1]["text"] == "Second line"


class TestJsonSerialization:
    def test_to_json_handles_dual_dialogue(self) -> None:
        document = FountainParser().parse("BRICK\nHi.\n\nSTEEL^\nHello.")

        parsed = json.loads(document.to_json())

        dual_dialogue_elements = [element for element in parsed["elements"] if element["type"] == "dual_dialogue"]
        assert len(dual_dialogue_elements) == 1
        metadata = dual_dialogue_elements[0]["metadata"]
        assert metadata["left_character"]["type"] == "character"
        assert metadata["left_character"]["text"] == "BRICK"
        assert isinstance(metadata["left_dialogue"], list)
        assert all(isinstance(item, dict) for item in metadata["left_dialogue"])

    def test_to_dict_nested_elements_match_top_level_shape(self) -> None:
        document = FountainParser().parse("BRICK\nHi.\n\nSTEEL^\nHello.")

        doc_dict = document.to_dict()

        elements_data = doc_dict["elements"]
        assert isinstance(elements_data, list)
        dual_dialogue_elements = [element for element in elements_data if element["type"] == "dual_dialogue"]
        top_level_keys = set(dual_dialogue_elements[0].keys())
        nested_keys = set(dual_dialogue_elements[0]["metadata"]["left_character"].keys())

        assert nested_keys == {"type", "text", "formatting", "line_number", "metadata"}
        assert nested_keys == top_level_keys

    def test_to_dict_carries_schema_version(self) -> None:
        assert FountainDocument([]).to_dict()["schema_version"] == 1

    def test_schema_version_is_module_constant(self) -> None:
        assert FountainDocument([]).to_dict()["schema_version"] == JSON_SCHEMA_VERSION

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("BRICK\nHi.\n\nSTEEL^\nHello.", id="dual_dialogue"),
            pytest.param("This line has **bold** and *italic* and _underline_ text.", id="inline_formatting"),
            pytest.param("INT. GARDEN - NIGHT #2A#\n\nRoses everywhere.", id="scene_number"),
            pytest.param("SARAH (V.O.)\nI can see you.", id="character_extension"),
            pytest.param(
                "Title: Test Script\nAuthor: Test Author\nDraft date: 2024-01-15\n\nFADE IN:",
                id="full_title_page",
            ),
        ],
    )
    def test_from_json_round_trips(self, source: str) -> None:
        document = FountainParser().parse(source)

        reconstructed = FountainDocument.from_json(document.to_json())

        assert reconstructed.to_dict() == document.to_dict()

    def test_from_dict_reconstructs_types(self) -> None:
        document = FountainParser().parse("SARAH (V.O.)\nI can see you.")

        reconstructed = FountainDocument.from_dict(document.to_dict())

        character = next(element for element in reconstructed.elements if element.type == ElementType.CHARACTER)
        assert isinstance(character.type, ElementType)
        dialogue = next(element for element in reconstructed.elements if element.type == ElementType.DIALOGUE)
        formatted = FountainParser().parse("**bold** text")
        formatted_reconstructed = FountainDocument.from_dict(formatted.to_dict())
        formatted_element = formatted_reconstructed.elements[0]
        assert all(isinstance(span, FormatSpan) for span in formatted_element.formatting)
        assert isinstance(dialogue.type, ElementType)

    def test_from_dict_unknown_schema_version_raises(self) -> None:
        with pytest.raises(ValueError, match="schema_version"):
            FountainDocument.from_dict({"schema_version": 999, "metadata": {}, "elements": []})

    @pytest.mark.parametrize(
        ("element_data", "message"),
        [
            pytest.param(
                {"type": "action", "formatting": [], "line_number": 1, "metadata": {}},
                "'text' must be str, got NoneType",
                id="missing_text",
            ),
            pytest.param(
                {"type": "action", "text": "Hi.", "formatting": [], "line_number": "1", "metadata": {}},
                "'line_number' must be int, got str",
                id="string_line_number",
            ),
            pytest.param(
                {
                    "type": "action",
                    "text": "Hi.",
                    "formatting": [{"start": 0, "end": 2, "format_type": "strikethrough"}],
                    "line_number": 1,
                    "metadata": {},
                },
                "unknown format_type 'strikethrough'",
                id="unknown_format_type",
            ),
            pytest.param(
                {"type": "action", "text": "Hi.", "formatting": [], "line_number": 1, "metadata": {"level": 1.5}},
                "metadata 'level' has unsupported type float",
                id="float_metadata",
            ),
            pytest.param(
                {"type": "dual_dialogue", "text": "", "formatting": [], "line_number": 1, "metadata": {"left": ["x"]}},
                "metadata list 'left' must hold serialized elements",
                id="list_of_strings_metadata",
            ),
        ],
    )
    def test_from_dict_malformed_element_raises(self, element_data: dict[str, object], message: str) -> None:
        data: dict[str, object] = {"schema_version": JSON_SCHEMA_VERSION, "metadata": {}, "elements": [element_data]}

        with pytest.raises(ValueError, match=message):
            FountainDocument.from_dict(data)

    def test_from_dict_non_string_title_page_raises(self) -> None:
        data: dict[str, object] = {"schema_version": JSON_SCHEMA_VERSION, "metadata": {"title": 3}, "elements": []}

        with pytest.raises(ValueError, match="title page metadata"):
            FountainDocument.from_dict(data)

    def test_from_json_non_object_raises(self) -> None:
        with pytest.raises(ValueError, match="expected a JSON object, got list"):
            FountainDocument.from_json("[]")
