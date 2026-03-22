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


class TestSpecCompliance:
    """Tests for Fountain spec compliance gaps."""

    def setup_method(self):
        self.parser = FountainParser()

    # -- Step 1: Section Level Metadata --

    def test_section_level_1(self):
        """# produces a SECTION with metadata level 1."""
        doc = self.parser.parse("# Act One")
        assert doc.elements[0].type == ElementType.SECTION
        assert doc.elements[0].metadata["level"] == 1
        assert doc.elements[0].text == "Act One"

    def test_section_level_2(self):
        """## produces a SECTION with metadata level 2."""
        doc = self.parser.parse("## Scene One")
        assert doc.elements[0].type == ElementType.SECTION
        assert doc.elements[0].metadata["level"] == 2
        assert doc.elements[0].text == "Scene One"

    def test_section_level_3(self):
        """### produces a SECTION with metadata level 3."""
        doc = self.parser.parse("### Beat One")
        assert doc.elements[0].type == ElementType.SECTION
        assert doc.elements[0].metadata["level"] == 3
        assert doc.elements[0].text == "Beat One"

    def test_section_level_6(self):
        """###### produces a SECTION with metadata level 6."""
        doc = self.parser.parse("###### Deep Nesting")
        assert doc.elements[0].type == ElementType.SECTION
        assert doc.elements[0].metadata["level"] == 6
        assert doc.elements[0].text == "Deep Nesting"

    def test_section_text_no_hash_symbols(self):
        """Section text should not contain # symbols."""
        doc = self.parser.parse("## My Section")
        assert "#" not in doc.elements[0].text

    # -- Step 2: Ellipsis Protection on Forced Scene Headings --

    def test_ellipsis_not_scene_heading(self):
        """...HELLO should be ACTION, not SCENE_HEADING."""
        doc = self.parser.parse("...HELLO")
        assert doc.elements[0].type == ElementType.ACTION

    def test_double_period_not_scene_heading(self):
        """..text should be ACTION, not SCENE_HEADING."""
        doc = self.parser.parse("..text")
        assert doc.elements[0].type == ElementType.ACTION

    def test_ellipsis_spec_example(self):
        """...where the carnival is parked (spec example) should be ACTION."""
        doc = self.parser.parse("...where the carnival is parked")
        assert doc.elements[0].type == ElementType.ACTION

    def test_forced_scene_heading_with_period(self):
        """.SNIPER SCOPE POV should be a forced SCENE_HEADING (spec example)."""
        doc = self.parser.parse(".SNIPER SCOPE POV")
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert doc.elements[0].text == "SNIPER SCOPE POV"

    def test_forced_scene_heading_alpha(self):
        """.A forced heading should be a forced SCENE_HEADING."""
        doc = self.parser.parse(".A forced heading")
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert doc.elements[0].text == "A forced heading"

    def test_forced_scene_heading_digit(self):
        """.2nd Floor should be a forced SCENE_HEADING (period + digit)."""
        doc = self.parser.parse(".2nd Floor")
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert doc.elements[0].text == "2nd Floor"

    # -- Step 3: Tab Conversion Verification --

    def test_tab_preserved_in_action(self):
        """Parser preserves tab character in action element text."""
        doc = self.parser.parse("\tIndented action")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "\tIndented action"

    def test_double_tab_preserved_in_action(self):
        """Parser preserves multiple tabs in action element text."""
        doc = self.parser.parse("\t\tDouble indented")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "\t\tDouble indented"

    def test_tab_stripped_from_character_name(self):
        """Tabs in character names are stripped by .strip()."""
        doc = self.parser.parse("\tJOHN\nHello.")
        # The tab-prefixed line should not be parsed as a character
        # (strip() removes leading whitespace before pattern matching)
        # but the underlying behavior depends on whether JOHN is detected as character
        # Either way, the element text should not have leading tabs
        for elem in doc.elements:
            if elem.type == ElementType.CHARACTER:
                assert not elem.text.startswith("\t")

    # -- Step 4: Arbitrary Title Page Keys --

    def test_custom_title_page_key(self):
        """Custom Field: Custom Value should be stored in metadata."""
        doc = self.parser.parse("Custom Field: Custom Value\n\nINT. HOUSE - DAY")
        assert doc.metadata.get("custom field") == "Custom Value"

    def test_revision_title_page_key(self):
        """Revision: Draft 3 should be accepted as a title page key."""
        doc = self.parser.parse("Revision: Draft 3\n\nINT. HOUSE - DAY")
        assert doc.metadata.get("revision") == "Draft 3"

    def test_multiple_arbitrary_keys(self):
        """Multiple arbitrary keys should all be preserved."""
        script = "Title: Test\nRevision: Draft 3\nSeries: My Show\n\nINT. HOUSE - DAY"
        doc = self.parser.parse(script)
        assert doc.metadata.get("title") == "Test"
        assert doc.metadata.get("revision") == "Draft 3"
        assert doc.metadata.get("series") == "My Show"

    def test_arbitrary_key_multiline_value(self):
        """Arbitrary keys with multi-line continuation values should work."""
        script = "Custom Field: Line 1\n   Line 2\n\nINT. HOUSE - DAY"
        doc = self.parser.parse(script)
        assert "Line 1" in doc.metadata.get("custom field", "")
        assert "Line 2" in doc.metadata.get("custom field", "")

    def test_title_page_ends_at_blank_line_plus_body(self):
        """Title page still ends correctly at blank line + body element."""
        script = "Title: Test\nCustom: Value\n\nINT. HOUSE - DAY"
        doc = self.parser.parse(script)
        assert doc.metadata.get("title") == "Test"
        assert doc.metadata.get("custom") == "Value"
        assert any(e.type == ElementType.SCENE_HEADING for e in doc.elements)

    def test_standard_and_custom_keys_together(self):
        """Standard keys (Title, Author) should work alongside custom keys."""
        script = "Title: My Script\nAuthor: Jane\nNetwork: HBO\n\nINT. OFFICE - DAY"
        doc = self.parser.parse(script)
        assert doc.metadata.get("title") == "My Script"
        assert doc.metadata.get("author") == "Jane"
        assert doc.metadata.get("network") == "HBO"

    # -- Step 5: Scene Headings Require Blank Line Before --

    def test_scene_heading_with_blank_line_before(self):
        """Scene heading with blank line before should be detected."""
        doc = self.parser.parse("Some action.\n\nINT. HOUSE - DAY")
        scene_headings = [e for e in doc.elements if e.type == ElementType.SCENE_HEADING]
        assert len(scene_headings) == 1
        assert scene_headings[0].text == "INT. HOUSE - DAY"

    def test_scene_heading_without_blank_line_before(self):
        """Scene heading without blank line before should NOT be detected."""
        doc = self.parser.parse("Some action.\nINT. HOUSE - DAY")
        scene_headings = [e for e in doc.elements if e.type == ElementType.SCENE_HEADING]
        assert len(scene_headings) == 0

    def test_scene_heading_as_first_element(self):
        """Scene heading as first/only element should still be detected."""
        doc = self.parser.parse("INT. HOUSE - DAY")
        assert doc.elements[0].type == ElementType.SCENE_HEADING

    def test_forced_scene_heading_without_blank_line(self):
        """Forced scene heading without blank line should still be detected (exempt)."""
        doc = self.parser.parse("Some action.\n.FORCED HEADING")
        scene_headings = [e for e in doc.elements if e.type == ElementType.SCENE_HEADING]
        assert len(scene_headings) == 1
        assert scene_headings[0].text == "FORCED HEADING"

    def test_scene_heading_after_title_page(self):
        """Scene heading after title page (first body element) should be detected."""
        doc = self.parser.parse("Title: Test\n\nINT. HOUSE - DAY")
        scene_headings = [e for e in doc.elements if e.type == ElementType.SCENE_HEADING]
        assert len(scene_headings) == 1

    # -- Step 6: Character Names Require Blank Line Before --

    def test_character_with_blank_line_before(self):
        """Character with blank line before should be detected."""
        doc = self.parser.parse("Some action.\n\nJOHN\nHello.")
        characters = [e for e in doc.elements if e.type == ElementType.CHARACTER]
        assert len(characters) == 1
        assert characters[0].text == "JOHN"

    def test_character_without_blank_line_before(self):
        """Character without blank line before should NOT be detected."""
        doc = self.parser.parse("Some action.\nJOHN\nHello.")
        characters = [e for e in doc.elements if e.type == ElementType.CHARACTER]
        assert len(characters) == 0

    def test_character_as_first_element(self):
        """Character as first element should still be detected."""
        doc = self.parser.parse("JOHN\nHello.")
        assert doc.elements[0].type == ElementType.CHARACTER

    def test_forced_character_without_blank_line(self):
        """Forced character without blank line should still be detected (exempt)."""
        doc = self.parser.parse("Some action.\n@JOHN\nHello.")
        characters = [e for e in doc.elements if e.type == ElementType.CHARACTER]
        assert len(characters) == 1

    def test_character_extension_with_blank_line(self):
        """Character with extension and blank line before should be detected."""
        doc = self.parser.parse("Some action.\n\nJOHN (V.O.)\nHello.")
        characters = [e for e in doc.elements if e.type == ElementType.CHARACTER]
        assert len(characters) == 1

    def test_character_extension_without_blank_line(self):
        """Character with extension without blank line should NOT be detected."""
        doc = self.parser.parse("Some action.\nJOHN (V.O.)\nHello.")
        characters = [e for e in doc.elements if e.type == ElementType.CHARACTER]
        assert len(characters) == 0

    # -- Step 7: Transitions Require Blank Lines Before and After --

    def test_transition_with_both_blank_lines(self):
        """Transition with blank lines before and after should be detected."""
        doc = self.parser.parse("Action.\n\nCUT TO:\n\nINT. HOUSE - DAY")
        transitions = [e for e in doc.elements if e.type == ElementType.TRANSITION]
        assert len(transitions) == 1
        assert transitions[0].text == "CUT TO:"

    def test_transition_without_blank_before(self):
        """Transition without blank line before should NOT be detected."""
        doc = self.parser.parse("Action.\nCUT TO:\n\nINT. HOUSE - DAY")
        transitions = [e for e in doc.elements if e.type == ElementType.TRANSITION]
        assert len(transitions) == 0

    def test_transition_without_blank_after(self):
        """Transition without blank line after should NOT be detected."""
        doc = self.parser.parse("Action.\n\nCUT TO:\nINT. HOUSE - DAY")
        transitions = [e for e in doc.elements if e.type == ElementType.TRANSITION]
        assert len(transitions) == 0

    def test_transition_without_any_blanks(self):
        """Transition without any blank lines should NOT be detected."""
        doc = self.parser.parse("Action.\nCUT TO:\nINT. HOUSE - DAY")
        transitions = [e for e in doc.elements if e.type == ElementType.TRANSITION]
        assert len(transitions) == 0

    def test_forced_transition_without_blanks(self):
        """Forced transition without blank lines should still be detected (exempt)."""
        doc = self.parser.parse("Action.\n>Burn to White.\nMore action.")
        transitions = [e for e in doc.elements if e.type == ElementType.TRANSITION]
        assert len(transitions) == 1

    def test_transition_at_end_of_document(self):
        """Transition at end of document should be detected (EOF counts as blank after)."""
        doc = self.parser.parse("Action.\n\nCUT TO:")
        transitions = [e for e in doc.elements if e.type == ElementType.TRANSITION]
        assert len(transitions) == 1

    def test_fade_in_and_fade_out_transitions(self):
        """FADE IN: and FADE OUT. should follow the same blank line rules."""
        doc = self.parser.parse("Title: Test\n\nFADE IN:\n\nINT. HOUSE - DAY\n\nAction.\n\nFADE OUT.")
        transitions = [e for e in doc.elements if e.type == ElementType.TRANSITION]
        assert len(transitions) == 2

    # -- Step 8: Inline Notes Stripped from Elements --

    def test_inline_note_stripped_from_action(self):
        """Inline note in action text should be stripped."""
        doc = self.parser.parse("John walks [[needs work]] to the door.")
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert len(actions) == 1
        assert "[[" not in actions[0].text
        assert "needs work" not in actions[0].text
        assert "John walks" in actions[0].text
        assert "to the door." in actions[0].text

    def test_inline_note_stripped_from_dialogue(self):
        """Inline note in dialogue should be stripped."""
        doc = self.parser.parse("JOHN\nI love you [[or do I?]] forever.")
        dialogues = [e for e in doc.elements if e.type == ElementType.DIALOGUE]
        assert len(dialogues) == 1
        assert "[[" not in dialogues[0].text
        assert "or do I?" not in dialogues[0].text
        assert "I love you" in dialogues[0].text
        assert "forever." in dialogues[0].text

    def test_standalone_note_unchanged(self):
        """Standalone note [[text]] should still produce a NOTE element."""
        doc = self.parser.parse("[[This is entirely a note]]")
        notes = [e for e in doc.elements if e.type == ElementType.NOTE]
        assert len(notes) == 1

    def test_multiple_inline_notes_stripped(self):
        """Multiple inline notes on one line should all be stripped."""
        doc = self.parser.parse("He [[first note]] walked [[second note]] away.")
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert len(actions) == 1
        assert "[[" not in actions[0].text
        assert "first note" not in actions[0].text
        assert "second note" not in actions[0].text

    def test_text_preserved_after_note_stripping(self):
        """Text should be otherwise unchanged after note stripping."""
        doc = self.parser.parse("The door opened [[slowly]] and he entered.")
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert len(actions) == 1
        assert "The door opened" in actions[0].text
        assert "and he entered." in actions[0].text

    # -- Step 9: Multi-line Notes --

    def test_multiline_note_basic(self):
        """Multi-line note spanning multiple lines should produce a single NOTE element."""
        doc = self.parser.parse("[[This is a note\nthat spans\nmultiple lines]]")
        notes = [e for e in doc.elements if e.type == ElementType.NOTE]
        assert len(notes) == 1
        assert "This is a note" in notes[0].text
        assert "that spans" in notes[0].text
        assert "multiple lines" in notes[0].text

    def test_multiline_note_between_elements(self):
        """Multi-line note between elements should preserve surrounding elements."""
        script = "INT. HOUSE - DAY\n\n[[This note\nspans lines]]\n\nJOHN\nHello."
        doc = self.parser.parse(script)
        notes = [e for e in doc.elements if e.type == ElementType.NOTE]
        assert len(notes) == 1
        scenes = [e for e in doc.elements if e.type == ElementType.SCENE_HEADING]
        assert len(scenes) == 1
        characters = [e for e in doc.elements if e.type == ElementType.CHARACTER]
        assert len(characters) == 1

    def test_multiline_note_full_content(self):
        """Multi-line note should contain all lines in its text."""
        doc = self.parser.parse("[[Line one\nLine two\nLine three]]")
        notes = [e for e in doc.elements if e.type == ElementType.NOTE]
        assert len(notes) == 1
        assert "Line one" in notes[0].text
        assert "Line two" in notes[0].text
        assert "Line three" in notes[0].text

    # -- Step 10: Dialogue Continuation with Whitespace-Only Lines --

    def test_whitespace_line_continues_dialogue(self):
        """Two-space line within dialogue should continue dialogue, not break to action."""
        doc = self.parser.parse("JOHN\nFirst line.\n  \nSecond line.")
        characters = [e for e in doc.elements if e.type == ElementType.CHARACTER]
        dialogues = [e for e in doc.elements if e.type == ElementType.DIALOGUE]
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert len(characters) == 1
        assert len(dialogues) >= 2  # At least first and second dialogue lines
        assert len(actions) == 0

    def test_empty_line_breaks_dialogue(self):
        """Truly empty line should break dialogue into action."""
        doc = self.parser.parse("JOHN\nFirst line.\n\nSecond line.")
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert len(actions) >= 1  # "Second line." should be action

    def test_whitespace_continuation_after_parenthetical(self):
        """Whitespace continuation should work after parenthetical."""
        doc = self.parser.parse("JOHN\n(beat)\n  \nMore dialogue.")
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert len(actions) == 0
        dialogues = [e for e in doc.elements if e.type == ElementType.DIALOGUE]
        assert len(dialogues) >= 1

    # -- Step 11: Backslash Escaping for Emphasis --

    def test_escaped_asterisk_no_formatting(self):
        r"""He dialed \*69 should have no formatting spans and text contains literal *69."""
        doc = self.parser.parse("He dialed \\*69")
        assert doc.elements[0].type == ElementType.ACTION
        assert "*69" in doc.elements[0].text
        assert doc.elements[0].formatting == []

    def test_escaped_asterisks_within_bold(self):
        r"""Text with **\*9765\*** should have bold AND literal asterisks in text."""
        doc = self.parser.parse("Steel enters **\\*9765\\***")
        elem = doc.elements[0]
        assert "*9765*" in elem.text
        bold_spans = [s for s in elem.formatting if s.format_type == "bold"]
        assert len(bold_spans) >= 1

    def test_escaped_underscores_no_formatting(self):
        r"""\_not underlined\_ should have no underline formatting."""
        doc = self.parser.parse("\\_not underlined\\_")
        elem = doc.elements[0]
        assert "_not underlined_" in elem.text
        underline_spans = [s for s in elem.formatting if s.format_type == "underline"]
        assert len(underline_spans) == 0

    def test_mixed_escaped_and_real_formatting(self):
        r"""*italic* and \*not italic\* should have exactly one italic span."""
        doc = self.parser.parse("This is *italic* and \\*not italic\\*")
        elem = doc.elements[0]
        italic_spans = [s for s in elem.formatting if s.format_type == "italic"]
        assert len(italic_spans) == 1
        assert "*not italic*" in elem.text

    def test_no_backslashes_unchanged(self):
        """Text without backslashes should be unchanged (no regression)."""
        doc = self.parser.parse("Normal **bold** text")
        elem = doc.elements[0]
        bold_spans = [s for s in elem.formatting if s.format_type == "bold"]
        assert len(bold_spans) == 1
        assert "Normal" in elem.text
