"""
ABOUTME: Edge case tests for Fountain parser covering spec compliance and robustness
ABOUTME: Tests all the edge cases discovered during implementation and validation
"""

import pytest

from fountain.elements import ElementType
from fountain.parser import FountainParser


class TestSceneHeadingEdgeCases:
    """Test scene heading edge cases and variations."""

    def setup_method(self):
        self.parser = FountainParser()

    def test_scene_heading_variations(self):
        """Test various scene heading formats."""
        test_cases = [
            ("INT. HOUSE - DAY", True),
            ("EXT. PARK - NIGHT", True),
            ("int. house - day", True),  # lowercase
            ("ext. park - night", True),  # lowercase
            ("EST. DOWNTOWN - DAWN", True),
            ("I/E. CAR - MOVING", True),
            ("INT.HOUSE-DAY", True),  # no spaces
            ("EXT .PARK - NIGHT", True),  # space before period
            ("INTERIOR. HOUSE - DAY", True),  # full word
            ("EXTERIOR. PARK - NIGHT", True),  # full word
            ("INT/EXT. HOUSE - DAY", True),  # slash variation
            ("INT./EXT. HOUSE - DAY", True),  # period slash variation
            ("INT HOUSE - DAY", False),  # missing period - should fail per spec
            (".CUSTOM SCENE HEADING", True),  # forced
            ("INT. CAFÉ - DAY", True),  # unicode
            ("EXT. 中文 LOCATION - DAY", True),  # unicode
        ]

        for test_input, should_be_scene in test_cases:
            doc = self.parser.parse(test_input)
            if should_be_scene:
                assert len(doc.elements) > 0
                assert doc.elements[0].type == ElementType.SCENE_HEADING
                assert doc.elements[0].text.strip()
            else:
                # Should not be scene heading
                if doc.elements:
                    assert doc.elements[0].type != ElementType.SCENE_HEADING

    def test_scene_numbers(self):
        """Test scene headings with scene numbers."""
        text = "INT. HOUSE - DAY #1#"
        doc = self.parser.parse(text)

        assert len(doc.elements) == 1
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert doc.elements[0].metadata["scene_number"] == "1"
        assert "#1#" not in doc.elements[0].text  # Scene number should be stripped


class TestCharacterExtensionEdgeCases:
    """Test character name and extension edge cases."""

    def setup_method(self):
        self.parser = FountainParser()

    def test_character_with_underscores(self):
        """Test character names with underscores."""
        test_cases = [
            "FORCED_CHARACTER (V.O.)\nHello.",
            "UNDERSCORE_NAME (O.S.)\nTesting.",
            "MULTIPLE_UNDER_SCORES (CONT'D)\nContinuing.",
        ]

        for text in test_cases:
            doc = self.parser.parse(text)
            assert len(doc.elements) >= 2
            assert doc.elements[0].type == ElementType.CHARACTER
            assert "_" in doc.elements[0].text
            assert doc.elements[0].metadata is not None
            assert "extension" in doc.elements[0].metadata

    def test_character_extensions_combinations(self):
        """Test various character extension combinations."""
        text = """ALICE (V.O.)
Alice in voice over.

BOB (O.S.)
Bob off screen.

CHARLIE (CONT'D)
Charlie continues.

DIANA (WHISPERING)
Diana whispers.

EMMA (SHOUTING)
Emma shouts."""

        doc = self.parser.parse(text)

        characters = [el for el in doc.elements if el.type == ElementType.CHARACTER]
        assert len(characters) == 5

        extensions = [char.metadata.get("extension") for char in characters]
        expected_extensions = ["V.O.", "O.S.", "CONT'D", "WHISPERING", "SHOUTING"]
        assert extensions == expected_extensions


class TestDualDialogueEdgeCases:
    """Test dual dialogue edge cases and complex scenarios."""

    def setup_method(self):
        self.parser = FountainParser()

    def test_dual_dialogue_with_extensions(self):
        """Test dual dialogue with character extensions."""
        text = """ALICE (V.O.)
Alice in voice over.

BOB (O.S.)^
Bob off screen, dual dialogue."""

        doc = self.parser.parse(text)

        dual_elements = [el for el in doc.elements if el.type == ElementType.DUAL_DIALOGUE]
        assert len(dual_elements) == 1

        dual = dual_elements[0]
        left_char = dual.metadata["left_character"]
        right_char = dual.metadata["right_character"]

        assert left_char.text == "ALICE"
        assert left_char.metadata["extension"] == "V.O."
        assert right_char.text == "BOB"
        assert right_char.metadata["extension"] == "O.S."

    def test_dual_dialogue_separation(self):
        """Test that dual dialogue doesn't incorrectly pair across dialogue blocks."""
        text = """JOHN (V.O.)
This is John speaking.

SARAH (O.S.)^
This is Sarah in dual dialogue.

NARRATOR (V.O.)
This is a narrator between blocks.

MARY (WHISPERING)
Mary whispers.

DAVID (SHOUTING)^
David shouts in dual dialogue."""

        doc = self.parser.parse(text)

        dual_elements = [el for el in doc.elements if el.type == ElementType.DUAL_DIALOGUE]
        assert len(dual_elements) == 2

        # First dual dialogue: JOHN <-> SARAH
        first_dual = dual_elements[0]
        assert first_dual.metadata["left_character"].text == "JOHN"
        assert first_dual.metadata["right_character"].text == "SARAH"

        # Second dual dialogue: MARY <-> DAVID
        second_dual = dual_elements[1]
        assert second_dual.metadata["left_character"].text == "MARY"
        assert second_dual.metadata["right_character"].text == "DAVID"

        # NARRATOR should be standalone
        narrator_elements = [el for el in doc.elements if el.type == ElementType.CHARACTER and el.text == "NARRATOR"]
        assert len(narrator_elements) == 1


class TestFormattingEdgeCases:
    """Test text formatting edge cases and robustness."""

    def setup_method(self):
        self.parser = FountainParser()

    def test_single_character_formatting(self):
        """Test single character formatting."""
        test_cases = [
            ("*a*", "italic"),
            ("**a**", "bold"),
            ("***a***", "bold_italic"),
            ("_a_", "underline"),
        ]

        for text, expected_format in test_cases:
            doc = self.parser.parse(f"JOHN\n{text}")
            dialogue = next((e for e in doc.elements if e.type == ElementType.DIALOGUE), None)
            assert dialogue is not None
            assert len(dialogue.formatting) == 1
            assert dialogue.formatting[0].format_type == expected_format

    def test_multiple_formatting_spans(self):
        """Test multiple formatting spans in one line."""
        text = "JOHN\n*a*b*c*"
        doc = self.parser.parse(text)

        dialogue = next((e for e in doc.elements if e.type == ElementType.DIALOGUE), None)
        assert dialogue is not None
        assert len(dialogue.formatting) == 2
        assert dialogue.formatting[0].format_type == "italic"
        assert dialogue.formatting[1].format_type == "italic"

    def test_unclosed_formatting(self):
        """Test unclosed formatting marks are handled gracefully."""
        test_cases = [
            "*incomplete",
            "**incomplete",
            "***incomplete",
            "_incomplete",
        ]

        for text in test_cases:
            doc = self.parser.parse(f"JOHN\n{text}")
            dialogue = next((e for e in doc.elements if e.type == ElementType.DIALOGUE), None)
            assert dialogue is not None
            # Should not crash and should not have formatting
            assert len(dialogue.formatting) == 0

    def test_complex_formatting_combinations(self):
        """Test complex formatting combinations."""
        text = "JOHN\n***bold italic*** mixed with *italic* and **bold**"
        doc = self.parser.parse(text)

        dialogue = next((e for e in doc.elements if e.type == ElementType.DIALOGUE), None)
        assert dialogue is not None
        assert len(dialogue.formatting) == 3

        format_types = [span.format_type for span in dialogue.formatting]
        assert "bold_italic" in format_types
        assert "italic" in format_types
        assert "bold" in format_types


class TestLyricsSpecCompliance:
    """Test lyrics parsing according to Fountain specification."""

    def setup_method(self):
        self.parser = FountainParser()

    def test_lyrics_start_with_tilde(self):
        """Test that lyrics start with ~ according to spec."""
        text = """~This is a lyric line
~Another lyric line
~Third lyric line"""

        doc = self.parser.parse(text)

        lyrics = [el for el in doc.elements if el.type == ElementType.LYRICS]
        assert len(lyrics) == 3
        assert lyrics[0].text == "This is a lyric line"
        assert lyrics[1].text == "Another lyric line"
        assert lyrics[2].text == "Third lyric line"

    def test_lyrics_with_formatting(self):
        """Test lyrics with text formatting."""
        text = "~This has **bold** and *italic* formatting"
        doc = self.parser.parse(text)

        lyrics = [el for el in doc.elements if el.type == ElementType.LYRICS]
        assert len(lyrics) == 1
        assert lyrics[0].text == "This has **bold** and *italic* formatting"
        assert len(lyrics[0].formatting) == 2

    def test_empty_tilde_not_lyrics(self):
        """Test that empty tilde is not parsed as lyrics."""
        text = "~"
        doc = self.parser.parse(text)

        lyrics = [el for el in doc.elements if el.type == ElementType.LYRICS]
        assert len(lyrics) == 0

        # Should be parsed as action instead
        action = [el for el in doc.elements if el.type == ElementType.ACTION]
        assert len(action) == 1
        assert action[0].text == "~"


class TestParentheticalParsing:
    """Test parenthetical parsing in various contexts."""

    def setup_method(self):
        self.parser = FountainParser()

    def test_parenthetical_after_character(self):
        """Test parenthetical immediately after character."""
        text = """JANE
(excited)
This is dialogue with a parenthetical!"""

        doc = self.parser.parse(text)

        parentheticals = [el for el in doc.elements if el.type == ElementType.PARENTHETICAL]
        assert len(parentheticals) == 1
        assert parentheticals[0].text == "(excited)"

    def test_multiple_parentheticals(self):
        """Test multiple separate parentheticals."""
        text = """JOHN
(whispering)
This is quiet.

JANE
(shouting)
This is loud!"""

        doc = self.parser.parse(text)

        parentheticals = [el for el in doc.elements if el.type == ElementType.PARENTHETICAL]
        assert len(parentheticals) == 2
        assert parentheticals[0].text == "(whispering)"
        assert parentheticals[1].text == "(shouting)"

    def test_parenthetical_in_dual_dialogue(self):
        """Test parentheticals within dual dialogue are preserved."""
        text = """ALICE
(excited)
Alice speaks!

BOB^
(confused)
Bob responds."""

        doc = self.parser.parse(text)

        dual_elements = [el for el in doc.elements if el.type == ElementType.DUAL_DIALOGUE]
        assert len(dual_elements) == 1

        dual = dual_elements[0]
        left_dialogue = dual.metadata["left_dialogue"]
        right_dialogue = dual.metadata["right_dialogue"]

        # Check that parentheticals are preserved in dual dialogue
        assert any(el.type == ElementType.PARENTHETICAL for el in left_dialogue)
        assert any(el.type == ElementType.PARENTHETICAL for el in right_dialogue)


class TestComprehensiveValidation:
    """Comprehensive validation tests covering all element types."""

    def setup_method(self):
        self.parser = FountainParser()

    def test_all_fountain_elements(self):
        """Test that all 14 Fountain element types can be parsed correctly."""
        comprehensive_test = """Title: Comprehensive Test
Author: Test Suite

FADE IN:

# Act I

= Setup and introduction

INTERIOR. CAFÉ - DAY #1#

This is action text with **bold**, *italic*, _underline_, and ***bold italic*** formatting.

!This is forced action text.

>This is centered text<

SARAH_JONES (V.O.)
~This is a lyric with voice over

MARY (WHISPERING)
(excited)
This has a parenthetical!

JOHN (O.S.)^
This is dual dialogue off screen.

EXT. PARK - NIGHT #2#

~Another lyric line
~With multiple lines of lyrics

NARRATOR
[[This is an inline note]]

/* This is a comment */

===

.FORCED SCENE HEADING

>FINAL TRANSITION TO:

THE END"""

        doc = self.parser.parse(comprehensive_test)

        # Count all element types including those in dual dialogue
        element_types = {}
        for element in doc.elements:
            element_types[element.type.value] = element_types.get(element.type.value, 0) + 1

        # Also count nested elements in dual dialogue
        for element in doc.elements:
            if element.type.value == "dual_dialogue" and element.metadata:
                for side in ["left_dialogue", "right_dialogue"]:
                    if side in element.metadata:
                        for nested in element.metadata[side]:
                            element_types[nested.type.value] = element_types.get(nested.type.value, 0) + 1

        # All 14 Fountain element types should be present
        all_fountain_types = [
            "scene_heading",
            "action",
            "character",
            "dialogue",
            "parenthetical",
            "transition",
            "centered",
            "lyrics",
            "note",
            "boneyard",
            "section",
            "synopsis",
            "dual_dialogue",
            "page_break",
        ]

        for element_type in all_fountain_types:
            assert element_type in element_types, f"Missing element type: {element_type}"
            assert element_types[element_type] > 0, f"No instances of {element_type} found"

    def test_unicode_support(self):
        """Test unicode character support throughout the parser."""
        text = """Title: Unicode Test
Author: 作者

INT. CAFÉ - DAY

Special characters: àáâãäåæçèéêë ñ öø ü 中文 العربية

JOHN
Dialogue with "quotes" and 'apostrophes' and em—dashes.

MARY (CONT'D)
More dialogue with unicode content: 中文 test."""

        doc = self.parser.parse(text)

        # Should parse without errors
        assert len(doc.elements) > 0
        assert "作者" in doc.metadata.get("author", "")

        # Check that unicode in action and dialogue is preserved
        action_elements = [el for el in doc.elements if el.type == ElementType.ACTION]
        dialogue_elements = [el for el in doc.elements if el.type == ElementType.DIALOGUE]

        assert any("中文" in el.text for el in action_elements)
        assert any("—" in el.text for el in dialogue_elements)
        assert any("中文" in el.text for el in dialogue_elements)

    def test_error_handling_robustness(self):
        """Test parser robustness with various edge cases."""
        edge_cases = [
            ("", "Empty document"),
            ("Just some text", "Plain text only"),
            ("JOHN\n\nNot dialogue", "Character without dialogue"),
            ("[[unclosed note", "Malformed note"),
            ("/* unclosed comment", "Unclosed boneyard"),
            (">unclosed centered", "Unclosed centered text"),
            ("VERY LONG CHARACTER NAME THAT MIGHT BREAK THINGS", "Very long character name"),
            ("===\n===\n===", "Multiple page breaks"),
        ]

        for test_case, description in edge_cases:
            # Should not crash on any input
            try:
                doc = self.parser.parse(test_case)
                # Basic validation - should always produce a document
                assert isinstance(doc.elements, list)
            except Exception as e:
                pytest.fail(f"Parser crashed on {description}: {e}")
