# ABOUTME: Edge case tests for Fountain parser covering spec compliance and robustness
# Tests all the edge cases discovered during implementation and validation
"""Edge case tests for Fountain parser covering spec compliance and robustness."""

import subprocess
from pathlib import Path

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
            ("INTERIOR. HOUSE - DAY", False),  # INTERIOR/EXTERIOR are not spec prefixes
            ("EXTERIOR. PARK - NIGHT", False),  # INTERIOR/EXTERIOR are not spec prefixes
            ("INTERIOR decorators arrived.", False),  # prose starting with INTERIOR is action
            ("Interior design is a career.", False),  # case-insensitive guard must not fire on prose
            ("INT/EXT. HOUSE - DAY", True),  # slash variation
            ("INT./EXT. HOUSE - DAY", True),  # period slash variation
            ("INT HOUSE - DAY", True),  # space form recognized per spec (B1)
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
        # D4: emphasis delimiters are stripped from the stored text; spans cover content.
        assert lyrics[0].text == "This has bold and italic formatting"
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

INT. CAFÉ - DAY #1#

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

    # -- Step 6.1: Space-Form Scene Heading Prefixes (B1) --

    def test_scene_heading_space_forms(self):
        """Space-form scene heading prefixes parse as SCENE_HEADING (B1).

        `INT HOUSE - DAY` and the space forms of EXT, EST, I/E, and INT/EXT are
        scene headings alongside the dot forms. A prefix boundary keeps
        `INTERNAL AFFAIRS INVESTIGATES.` as ACTION so `INT` does not match the
        start of `INTERNAL`.
        """
        space_forms = [
            "INT HOUSE - DAY",
            "EXT PARK - NIGHT",
            "EST FIELD - DAY",
            "I/E CAR - DAY",
            "INT/EXT DINER - NIGHT",
        ]
        for scene_line in space_forms:
            doc = self.parser.parse(scene_line)
            assert doc.elements[0].type == ElementType.SCENE_HEADING, scene_line

        doc = self.parser.parse("INTERNAL AFFAIRS INVESTIGATES.")
        assert doc.elements[0].type == ElementType.ACTION

    def test_scene_heading_requires_blank_after(self):
        """A natural scene heading requires a blank line after it (B2).

        `EXT. BRICK'S PATIO - DAY` immediately followed by a non-blank line is
        ACTION, mirroring the transition branch's blank-line-after rule. With a
        blank line after (or at EOF) it stays SCENE_HEADING. A forced `.` heading
        is exempt: it stays SCENE_HEADING even with a non-blank line right after.
        """
        # No blank line after: the natural heading degrades to ACTION.
        doc = self.parser.parse("EXT. BRICK'S PATIO - DAY\nThey walk in.")
        assert doc.elements[0].type == ElementType.ACTION
        assert not any(element.type == ElementType.SCENE_HEADING for element in doc.elements)

        # Blank line after: still a scene heading.
        doc = self.parser.parse("EXT. BRICK'S PATIO - DAY\n\nThey walk in.")
        assert doc.elements[0].type == ElementType.SCENE_HEADING

        # EOF counts as a blank line after: last-line heading stays a heading.
        doc = self.parser.parse("EXT. BRICK'S PATIO - DAY")
        assert doc.elements[0].type == ElementType.SCENE_HEADING

        # Forced headings are exempt from the blank-line-after requirement.
        doc = self.parser.parse(".PATIO\nThey walk in.")
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert doc.elements[0].text == "PATIO"

    def test_scene_number_character_restriction(self):
        """Scene numbers are limited to alphanumerics, dashes, and periods (B4).

        A `#...#` group containing any other character is not a scene number: it
        stays verbatim in the heading text and sets no `scene_number` metadata.
        Valid groups (letters, digits, dashes, periods) still extract to metadata
        and are stripped from the text.
        """
        # Junk characters: the group is not a scene number, so it is left in the text.
        doc = self.parser.parse("INT. HOUSE - DAY #$%^&#")
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert "#$%^&#" in doc.elements[0].text
        assert "scene_number" not in doc.elements[0].metadata

        # Valid alphanumeric scene number still extracts and strips from the text.
        doc = self.parser.parse("INT. HOUSE - DAY #2A#")
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert doc.elements[0].metadata["scene_number"] == "2A"
        assert doc.elements[0].text == "INT. HOUSE - DAY"

        # Dashes and periods are valid scene-number characters.
        doc = self.parser.parse("INT. HOUSE - DAY #1-A.2#")
        assert doc.elements[0].type == ElementType.SCENE_HEADING
        assert doc.elements[0].metadata["scene_number"] == "1-A.2"
        assert doc.elements[0].text == "INT. HOUSE - DAY"

    # -- Step 3: Tab Conversion Verification --

    def test_tab_retained_in_action(self):
        """A leading tab in action text is retained verbatim (Fountain keeps tabs)."""
        doc = self.parser.parse("\tIndented action")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "\tIndented action"

    def test_double_tab_retained_in_action(self):
        """Each leading tab in action text is retained verbatim."""
        doc = self.parser.parse("\t\tDouble indented")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "\t\tDouble indented"

    def test_tab_action_renders_indentation(self):
        """A tab-indented action retains the tab in text and renders four nbsp per tab.

        The Fountain spec keeps tabs in Action. The stored element text keeps the raw
        tab (so a span offset counts it as one character), and the HTML renderer converts
        each tab to four ``&nbsp;`` entities for a consistent visible indent.
        """
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("\tIndented action line")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "\tIndented action line"

        html = HTMLRenderer().render(doc)
        assert "&nbsp;&nbsp;&nbsp;&nbsp;Indented action line" in html

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

    def test_first_line_fade_in_is_transition_not_metadata(self):
        """A leading ``FADE IN:`` is a body transition, not a title-page key.

        The value after the colon is empty and there is no indented continuation, so it
        cannot be a title-page key. Before the gate it was consumed as ``{'fade in': ''}``
        and the transition was lost from the body.
        """
        doc = self.parser.parse("FADE IN:\n\nINT. HOUSE - DAY\n\nHe runs.")
        assert doc.metadata == {}
        assert any(element.type == ElementType.TRANSITION and element.text == "FADE IN:" for element in doc.elements)

    def test_first_line_cut_to_is_transition_not_metadata(self):
        """A leading ``CUT TO:`` is a body transition, not a title-page key."""
        doc = self.parser.parse("CUT TO:\n\nINT. HOUSE - DAY")
        assert "cut to" not in doc.metadata
        assert any(element.type == ElementType.TRANSITION and element.text == "CUT TO:" for element in doc.elements)

    def test_first_line_colon_prose_is_action_not_metadata(self):
        """A prose sentence with a colon on line one is action, not a title-page key.

        ``He opens the card`` is not a recognized field and is not a capitalized label
        (it has lowercase words), so it is body prose rather than a key.
        """
        doc = self.parser.parse("He opens the card: a threat.\n\nINT. HOUSE - DAY")
        assert doc.metadata == {}
        assert any(
            element.type == ElementType.ACTION and "He opens the card: a threat." in element.text
            for element in doc.elements
        )

    def test_title_case_prose_colon_line_is_action(self):
        """A capitalized prose line with a colon and a sentence value is action, not metadata.

        The capitalized-label guard alone let ``Warning: stay back.`` open a bogus key; a
        value ending in sentence punctuation marks it as body prose instead.
        """
        for source in ("Warning: stay back.", "Meanwhile: the clock ticks.", "Jim: Hello there!"):
            doc = self.parser.parse(f"{source}\n\nINT. HOUSE - DAY")
            assert doc.metadata == {}, f"{source!r} should be body, got {doc.metadata}"
            assert any(element.type == ElementType.ACTION and source in element.text for element in doc.elements)

        # A real capitalized custom key (no sentence punctuation) still opens the title page.
        keyed = self.parser.parse("Custom Field: Custom Value\n\nINT. HOUSE - DAY")
        assert keyed.metadata.get("custom field") == "Custom Value"

    def test_forced_transition_round_trips(self):
        """A forced transition keeps its forced flag so it survives a Fountain round trip.

        ``> SMASH CUT TO BLACK`` does not end in ``TO:`` and would not re-parse as a
        transition without the leading ``>``. The parser must record ``forced`` so the
        Fountain renderer re-emits the marker and the element stays a TRANSITION.
        """
        from fountain.renderer import FountainRenderer

        doc = self.parser.parse("> SMASH CUT TO BLACK")
        transitions = [element for element in doc.elements if element.type == ElementType.TRANSITION]
        assert len(transitions) == 1
        assert transitions[0].metadata is not None
        assert transitions[0].metadata.get("forced") is True

        rendered = FountainRenderer().render(doc)
        reparsed = self.parser.parse(rendered)
        assert [element.type for element in reparsed.elements] == [ElementType.TRANSITION]

    def test_consecutive_action_lines_form_one_paragraph(self):
        """Consecutive non-blank action lines join into one ACTION element, line breaks kept.

        Fountain treats every carriage return as intentional, so a block of adjacent action
        lines is one paragraph with internal line breaks, not one margined element per line.
        """
        doc = self.parser.parse("Line one\nLine two\nLine three")
        actions = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert len(actions) == 1
        assert actions[0].text == "Line one\nLine two\nLine three"

    def test_blank_line_separates_action_paragraphs(self):
        """A blank line still starts a new action paragraph."""
        doc = self.parser.parse("Para one.\n\nPara two.")
        actions = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert len(actions) == 2
        assert actions[0].text == "Para one."
        assert actions[1].text == "Para two."

    def test_action_paragraph_renders_line_breaks_in_one_div(self):
        """Merged action lines render as one action div; pre-wrap CSS shows the line breaks."""
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("Line one\nLine two")
        html = HTMLRenderer().render(doc)
        assert html.count('class="fountain-action"') == 1
        assert "Line one<br>Line two" in html

    # -- Step 5.1: A1 Multi-line Title Page Values Preserve Line Structure --

    def test_title_page_multiline_value_preserved(self):
        """A multi-line title page value keeps each line instead of flattening to one space-joined string."""
        from fountain.renderer import HTMLRenderer

        script = "Contact:\n    Next Level\n    1588 Mission Dr.\n    Solvang, CA\n\nINT. HOUSE - DAY"
        doc = self.parser.parse(script)

        contact = doc.metadata.get("contact", "")
        assert contact == "Next Level\n1588 Mission Dr.\nSolvang, CA"
        assert contact.count("\n") == 2
        assert contact.split("\n") == ["Next Level", "1588 Mission Dr.", "Solvang, CA"]

        html = HTMLRenderer().render_page(doc)
        assert "Next Level<br>1588 Mission Dr.<br>Solvang, CA" in html

    def test_title_page_single_line_value_stays_plain(self):
        """A single-line title page value stays a plain string with no trailing newline (A1 regression guard)."""
        doc = self.parser.parse("Title: Big Fish\n\nINT. HOUSE - DAY")
        assert doc.metadata.get("title") == "Big Fish"
        assert "\n" not in doc.metadata.get("title", "")

    # -- Step 5.2: A2 Title Page Continuation Requires Indentation --

    def test_title_page_continuation_requires_indent(self):
        """An indented colon-bearing line stays a value of the current key rather than starting a new key (A2)."""
        script = "Notes:\n    Draft 3: final revisions\n\nINT. HOUSE - DAY"
        doc = self.parser.parse(script)
        assert doc.metadata.get("notes") == "Draft 3: final revisions"
        assert "draft 3" not in doc.metadata

    def test_title_page_unindented_line_ends_page(self):
        """An unindented non-key line ends the title page and becomes a body element, not a value (A2)."""
        script = "Title: X\nUnindented body line\n\nINT. HOUSE - DAY"
        doc = self.parser.parse(script)
        assert doc.metadata.get("title") == "X"
        assert "\n" not in doc.metadata.get("title", "")
        action_texts = [element.text for element in doc.elements if element.type == ElementType.ACTION]
        assert "Unindented body line" in action_texts

    def test_title_page_guard_case_insensitive(self):
        """A lowercase scene-heading first line is a SCENE_HEADING, not title-page metadata (B3).

        ``int. house - day - 3:00 pm`` contains a colon (from the time), which naively
        looks like a ``key: value`` title-page line. The guard that stops a scene heading
        from opening the title page must be case-insensitive, so the lowercase ``int.``
        form is recognized and the line falls through to body classification.
        """
        doc = self.parser.parse("int. house - day - 3:00 pm")
        assert doc.metadata == {}
        assert "int. house - day - 3" not in doc.metadata
        scene_headings = [element for element in doc.elements if element.type == ElementType.SCENE_HEADING]
        assert len(scene_headings) == 1
        assert scene_headings[0].text == "int. house - day - 3:00 pm"

    def test_title_page_guard_space_form(self):
        """The space-form scene-heading prefix also guards against opening the title page (B3).

        ``int house - day - 3:00 pm`` uses the space form (B1) and contains a colon.
        The guard must recognize the space form too so this parses as a scene heading
        rather than a ``key: value`` metadata line.
        """
        doc = self.parser.parse("int house - day - 3:00 pm")
        assert doc.metadata == {}
        scene_headings = [element for element in doc.elements if element.type == ElementType.SCENE_HEADING]
        assert len(scene_headings) == 1
        assert scene_headings[0].text == "int house - day - 3:00 pm"

    def test_title_page_real_key_still_opens_page(self):
        """A genuine non-scene-heading key: value first line still opens the title page (B3 regression)."""
        doc = self.parser.parse("Author: Alice\n\nINT. HOUSE - DAY")
        assert doc.metadata.get("author") == "Alice"

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

    def test_bracketed_line_with_middle_text_not_single_note(self):
        """A line bounded by [[ ]] but with text between two notes is not one NOTE (E13).

        ``[[a]] middle [[b]]`` starts with ``[[`` and ends with ``]]`` but carries
        real text between two separate notes. The inline notes strip per body rule 8
        and the remaining ``middle`` classifies as ACTION, rather than the whole line
        being swallowed verbatim as a single NOTE.
        """
        doc = self.parser.parse("[[a]] middle [[b]]")
        notes = [e for e in doc.elements if e.type == ElementType.NOTE]
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert notes == []
        assert len(actions) == 1
        assert actions[0].text == "middle"

    def test_lone_bracket_inside_note(self):
        """A lone ``]`` inside a note does not break recognition; only ``]]`` closes (E10).

        ``[[check ref] ok]]`` carries a single ``]`` in the middle of the note text.
        Only ``]]`` terminates a note, so the lone ``]`` stays part of the content and
        the whole line is one NOTE (text preserved verbatim, brackets included per body
        rule 6) rather than falling through to ACTION.
        """
        doc = self.parser.parse("[[check ref] ok]]")
        notes = [e for e in doc.elements if e.type == ElementType.NOTE]
        actions = [e for e in doc.elements if e.type == ElementType.ACTION]
        assert actions == []
        assert len(notes) == 1
        assert notes[0].text == "[[check ref] ok]]"
        assert "check ref] ok" in notes[0].text

    def test_indented_action_with_trailing_note_keeps_indent(self):
        """An indented action line with a trailing inline note keeps its leading indent.

        The inline note sits at the END of the line, so removing it must not disturb the
        deliberate leading indent. Only the seam a FRONT note leaves is dropped; a
        trailing note leaves the leading indent intact. The tab indent is retained
        verbatim in the stored text.
        """
        tab_doc = self.parser.parse("\tIndented action [[note]]")
        tab_actions = [e for e in tab_doc.elements if e.type == ElementType.ACTION]
        assert len(tab_actions) == 1
        assert tab_actions[0].text == "\tIndented action"
        assert "[[" not in tab_actions[0].text

        space_doc = self.parser.parse("    Spaced action [[note]]")
        space_actions = [e for e in space_doc.elements if e.type == ElementType.ACTION]
        assert len(space_actions) == 1
        assert space_actions[0].text.startswith("    ")
        assert space_actions[0].text == "    Spaced action"
        assert "[[" not in space_actions[0].text

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

    # -- Step 8.3: D4 Emphasis Delimiters Stripped, Spans Cover Content --

    def test_emphasis_delimiters_stripped(self):
        """D4: emphasis delimiters are removed from element text and spans cover only content.

        Before D4 the parser kept the delimiters in ``element.text`` (``This is **bold**
        text.``) and its FormatSpan covered the delimiters too. D4 strips the delimiters
        from the stored text and indexes the span into that clean text, over the emphasized
        content only. The HTML renderer then emits ``<strong>bold</strong>`` with no
        asterisks.
        """
        from fountain.renderer import HTMLRenderer

        # Bold: delimiters stripped, one bold span over the clean-text content.
        doc = self.parser.parse("This is **bold** text.")
        elem = doc.elements[0]
        assert elem.text == "This is bold text."
        bold_spans = [span for span in elem.formatting if span.format_type == "bold"]
        assert len(bold_spans) == 1
        bold_span = bold_spans[0]
        assert (bold_span.start, bold_span.end) == (8, 12)
        assert elem.text[bold_span.start : bold_span.end] == "bold"
        bold_html = HTMLRenderer().render(doc)
        assert "<strong>bold</strong>" in bold_html
        assert "**" not in bold_html

        # Italic: delimiters stripped, span over the content, <em> with no asterisks.
        doc = self.parser.parse("This is *italic* text.")
        elem = doc.elements[0]
        assert elem.text == "This is italic text."
        italic_spans = [span for span in elem.formatting if span.format_type == "italic"]
        assert len(italic_spans) == 1
        italic_span = italic_spans[0]
        assert elem.text[italic_span.start : italic_span.end] == "italic"
        italic_html = HTMLRenderer().render(doc)
        assert "<em>italic</em>" in italic_html
        assert "*" not in italic_html

        # Underline: delimiters stripped, span over the content, <u> with no underscores.
        doc = self.parser.parse("This is _under_ text.")
        elem = doc.elements[0]
        assert elem.text == "This is under text."
        underline_spans = [span for span in elem.formatting if span.format_type == "underline"]
        assert len(underline_spans) == 1
        underline_span = underline_spans[0]
        assert elem.text[underline_span.start : underline_span.end] == "under"
        underline_html = HTMLRenderer().render(doc)
        assert "<u>under</u>" in underline_html
        assert "_" not in underline_html

    # -- Step 8.4: D5 Keypad Escape Example Renders Correctly --

    def test_keypad_escape_example(self):
        r"""D5: the spec's keypad escape example renders with ``<strong>*9765*</strong>``.

        The line ``Steel enters the code on the keypad: **\*9765\***`` combines two
        features from D4: emphasis delimiters are stripped (the ``**`` bold markers) and
        backslash-escaped asterisks resolve to literal ``*`` characters. D5 pins the
        combined behavior end to end: the ACTION text carries literal asterisks around
        ``9765`` with no ``**`` markers, and the HTML renderer emits
        ``<strong>*9765*</strong>`` with no stray delimiters.

        D5 is subsumed by D4 (Step 8.3), which delivers both the delimiter stripping and
        the escape resolution. This test pins that the keypad example specifically renders
        correctly. The keypad line is placed in body context (after a scene heading and a
        blank line) so it classifies as ACTION rather than being swallowed by title-page
        detection, which treats a colon-bearing first line as metadata (documented
        ambiguity A3).
        """
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("INT. VAULT - NIGHT\n\nSteel enters the code on the keypad: **\\*9765\\***")
        action_elements = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert len(action_elements) == 1
        action = action_elements[0]

        # Escaped asterisks resolve to literal ``*`` and the bold delimiters are stripped.
        assert action.text == "Steel enters the code on the keypad: *9765*"
        assert "**" not in action.text

        # One bold span covers the ``*9765*`` content in the clean text.
        bold_spans = [span for span in action.formatting if span.format_type == "bold"]
        assert len(bold_spans) == 1
        bold_span = bold_spans[0]
        assert action.text[bold_span.start : bold_span.end] == "*9765*"

        # The HTML renders the bold escaped code with no stray delimiters.
        html = HTMLRenderer().render(doc)
        assert "<strong>*9765*</strong>" in html
        assert "**9765**" not in html
        assert "**" not in html

    # -- Step 8.5: D6 Nested Emphasis Does Not Duplicate Text --

    def test_nested_emphasis_no_duplication(self):
        """D6: nested emphasis composes into nested tags with each word rendered once.

        The spec underlines a phrase that itself contains an italic span, so bold,
        italic, and underline must compose freely rather than being flattened. Before
        D6 the renderer assumed non-overlapping spans and emitted the inner content
        twice: ``<u>...Leupold Mark 4 scope</u><em>Leupold Mark 4</em> scope.``. D6
        makes the segment builder handle overlapping and nested spans, producing the
        underline wrapping the whole phrase with the italic nested inside and every
        character emitted exactly once.

        The line is placed in body context (after a scene heading and a blank line) so
        it classifies as ACTION rather than being swallowed by title-page detection,
        which treats a colon-bearing first line as metadata (documented ambiguity A3).
        """
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("INT. HOUSE - DAY\n\n_Steel's face FILLS the *Leupold Mark 4* scope_.")
        action_elements = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert len(action_elements) == 1
        action = action_elements[0]

        action_html = HTMLRenderer()._apply_formatting(action.text, action.formatting)

        # The underline wraps the whole phrase with the italic nested inside it.
        assert "<u>Steel&#x27;s face FILLS the <em>Leupold Mark 4</em> scope</u>" in action_html

        # No delimiters survive and no content is duplicated: each word appears once.
        assert "_" not in action_html
        assert "*" not in action_html
        assert action_html.count("Leupold Mark 4") == 1
        for word in ("Steel", "face", "FILLS", "the", "Leupold", "Mark", "4", "scope"):
            assert action_html.count(word) == 1, f"word {word!r} should appear exactly once"

        # A bold phrase containing a nested underline composes the same way.
        doc = self.parser.parse("Action line\n\n**bold with _underline_ inside**")
        action_elements = [element for element in doc.elements if element.type == ElementType.ACTION]
        nested = action_elements[-1]
        nested_html = HTMLRenderer()._apply_formatting(nested.text, nested.formatting)
        assert nested_html == "<strong>bold with <u>underline</u> inside</strong>"
        assert nested_html.count("underline") == 1
        for word in ("bold", "with", "underline", "inside"):
            assert nested_html.count(word) == 1, f"word {word!r} should appear exactly once"

    # -- Step 8.6: D7 Bold and Underline Get the Italic Space Guards --

    def test_bold_underline_space_guards(self):
        r"""D7: a delimiter-adjacent space defeats bold and underline emphasis.

        The italic pattern already refuses to match when a whitespace character sits
        immediately inside the delimiters (``* italic *`` produces no span). Before D7 the
        bold (``**``) and underline (``_``) patterns lacked that guard, so ``** word**``
        emitted a bold span over `` word`` and ``_ kilos_`` emitted an underline span over
        `` kilos``. D7 mirrors the italic guard onto bold, underline, and bold-italic so a
        space right after the opening delimiter or right before the closing delimiter
        suppresses the emphasis, while valid delimiter-adjacent-non-space runs still match.
        """

        def spans_of(source: str, format_type: str) -> list:
            element = self.parser.parse(source).elements[0]
            return [span for span in element.formatting if span.format_type == format_type]

        # Space immediately after the opening delimiter: no span.
        assert spans_of("_ kilos_", "underline") == []
        assert spans_of("** word**", "bold") == []
        assert spans_of("*** word***", "bold_italic") == []

        # Space immediately before the closing delimiter: no span.
        assert spans_of("_kilos _", "underline") == []
        assert spans_of("**word **", "bold") == []
        assert spans_of("***word ***", "bold_italic") == []

        # Regression guard: valid delimiter-adjacent-non-space runs still produce spans.
        underline_valid = spans_of("_kilos_", "underline")
        assert len(underline_valid) == 1
        bold_valid = spans_of("**word**", "bold")
        assert len(bold_valid) == 1
        bold_italic_valid = spans_of("***word***", "bold_italic")
        assert len(bold_italic_valid) == 1
        italic_valid = spans_of("*word*", "italic")
        assert len(italic_valid) == 1

    # -- Adversarial review: emphasis nesting, intraword underscore, stray delimiters --

    def test_emphasis_does_not_cross_line_breaks(self):
        """Emphasis delimiters on different lines do not pair (spec: not carried across breaks).

        A merged action paragraph carries embedded newlines, so an opening ``*`` on one
        line must not close against a ``*`` on the next line.
        """
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("This is *italic\nnot carried* over")
        action = [element for element in doc.elements if element.type == ElementType.ACTION][-1]
        assert action.formatting == []
        html = HTMLRenderer()._apply_formatting(action.text, action.formatting)
        assert "<em>" not in html
        assert "*italic" in html and "carried*" in html

    def test_nested_same_delimiter_emphasis(self):
        """An italic phrase containing a bold word (both asterisks) composes cleanly.

        The old regex span-finder could not cross the inner ``**`` inside an outer
        ``*...*`` run, so the outer italic was dropped and its delimiters leaked into
        the text as literal asterisks. The delimiter-stack scanner nests them.
        """
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("Body line.\n\n*italic **both** italic*")
        action = [element for element in doc.elements if element.type == ElementType.ACTION][-1]
        assert action.text == "italic both italic"
        html = HTMLRenderer()._apply_formatting(action.text, action.formatting)
        assert html == "<em>italic <strong>both</strong> italic</em>"
        assert "*" not in html

    def test_adjacent_bold_italic_shared_run(self):
        """``**bold***italic*`` splits the shared ``***`` run into bold close + italic open."""
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("Body line.\n\n**bold***italic*")
        action = [element for element in doc.elements if element.type == ElementType.ACTION][-1]
        assert action.text == "bolditalic"
        html = HTMLRenderer()._apply_formatting(action.text, action.formatting)
        assert html == "<strong>bold</strong><em>italic</em>"
        assert "*" not in html

    def test_intraword_underscore_is_literal(self):
        """Underscores inside a word are literal, per Markdown's intraword rule.

        ``some_variable_name`` and ``my_cool_script.py`` must keep their underscores and
        produce no underline span, rather than deleting the underscores and underlining
        the middle token.
        """
        from fountain.renderer import HTMLRenderer

        for source in ("some_variable_name", "my_cool_script.py"):
            doc = self.parser.parse(f"Body line.\n\n{source}")
            action = [element for element in doc.elements if element.type == ElementType.ACTION][-1]
            assert action.text == source
            assert action.formatting == []
            html = HTMLRenderer()._apply_formatting(action.text, action.formatting)
            assert "<u>" not in html

    def test_quadruple_asterisks_leave_no_stray_delimiters(self):
        """A run of four asterisks on each side consumes cleanly with no literal ``*`` left."""
        from fountain.renderer import HTMLRenderer

        doc = self.parser.parse("Body line.\n\n****word****")
        action = [element for element in doc.elements if element.type == ElementType.ACTION][-1]
        assert "*" not in action.text
        html = HTMLRenderer()._apply_formatting(action.text, action.formatting)
        assert "*" not in html
        assert "word" in html

    # -- Step 8.7: D8 Span Offsets Computed Against Stored Text Including Indentation --

    def test_span_offset_includes_indentation(self):
        """D8: formatting spans index into the stored text, leading indentation included.

        The spec's card-style action lines carry deliberate leading indentation. The stored
        ACTION text keeps that indentation, so a span must be positioned over the emphasized
        content in the indented text, not shifted left as if the indentation were absent.
        Ten spaces then ``*Scott* --`` must yield an italic span over ``Scott`` at offset 10,
        with the leading whitespace outside the span.

        D8 is subsumed by D4 (Step 8.3): ``_finalize_inline`` re-derives the content spans by
        re-running the inline pass over the element's stored text, which already carries the
        leading indentation. The spans therefore land at the correct offsets with no separate
        D8 fix. This test pins that behavior, including the harder multi-span case where two
        emphasized runs on one indented line must both land on their content. The lines are
        placed in body context (after a scene heading and a blank line) so they classify as
        ACTION rather than title-page metadata (documented ambiguity A3).
        """
        # Single span: ten leading spaces, one italic run over ``Scott``.
        doc = self.parser.parse("INT. OFFICE - DAY\n\n          *Scott* --")
        action = doc.elements[1]
        assert action.type == ElementType.ACTION
        assert action.text == "          Scott --"
        italic_spans = [span for span in action.formatting if span.format_type == "italic"]
        assert len(italic_spans) == 1
        italic_span = italic_spans[0]
        assert (italic_span.start, italic_span.end) == (10, 15)
        assert action.text[italic_span.start : italic_span.end] == "Scott"

        # Multiple spans: five leading spaces, a bold run and an italic run on one line.
        # Each span must land on its own content in the indented stored text.
        doc = self.parser.parse("INT. OFFICE - DAY\n\n     **bold** and *italic*")
        action = doc.elements[1]
        assert action.type == ElementType.ACTION
        assert action.text == "     bold and italic"
        bold_spans = [span for span in action.formatting if span.format_type == "bold"]
        italic_spans = [span for span in action.formatting if span.format_type == "italic"]
        assert len(bold_spans) == 1
        assert len(italic_spans) == 1
        assert action.text[bold_spans[0].start : bold_spans[0].end] == "bold"
        assert action.text[italic_spans[0].start : italic_spans[0].end] == "italic"

    # -- Step 8.8: D9 Forced Action Retains Indentation After the ! --

    def test_forced_action_retains_indent(self):
        """D9: a forced action keeps the indentation that follows the ``!`` marker.

        Only the leading ``!`` forcing marker is removed; the whitespace after it is
        part of the action text. ``!    INDENTED FORCED ACTION`` stores four leading
        spaces rather than dropping them. A tab after the marker follows the same
        tab-to-four-spaces rule as normal action text (A5), and a marker with no
        following indent leaves no spurious leading space. Emphasis inside a forced,
        indented action still lands on its content with the leading whitespace outside
        the span (D4/D8).
        """
        # Indentation after the marker is preserved verbatim: only the ! is stripped.
        doc = self.parser.parse("!    INDENTED FORCED ACTION")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "    INDENTED FORCED ACTION"

        # No indent after the marker: only the ! is removed, no leading space added.
        doc = self.parser.parse("!plain forced action")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "plain forced action"

        # A tab after the marker is retained verbatim, consistent with normal action.
        doc = self.parser.parse("!\tINDENTED")
        assert doc.elements[0].type == ElementType.ACTION
        assert doc.elements[0].text == "\tINDENTED"

        # Emphasis inside an indented forced action keeps the indent outside the span (D4/D8).
        doc = self.parser.parse("!    *italic*")
        action = doc.elements[0]
        assert action.type == ElementType.ACTION
        assert action.text == "    italic"
        italic_spans = [span for span in action.formatting if span.format_type == "italic"]
        assert len(italic_spans) == 1
        assert italic_spans[0].start == 4
        assert action.text[italic_spans[0].start : italic_spans[0].end] == "italic"

    def test_dialogue_not_broken_by_regular_text(self):
        """Regular text following a character name should be dialogue, not action."""
        doc = self.parser.parse("JOHN\nHello.\nMore dialogue.")
        types = [el.type for el in doc.elements]
        assert types[0] == ElementType.CHARACTER
        assert types[1] == ElementType.DIALOGUE
        assert types[2] == ElementType.DIALOGUE

    def test_dialogue_broken_by_scene_heading(self):
        """A scene heading after dialogue should break the dialogue context."""
        doc = self.parser.parse("\n\nJOHN\nHello.\n\nINT. HOUSE - DAY")
        types = [el.type for el in doc.elements]
        assert ElementType.CHARACTER in types
        assert ElementType.DIALOGUE in types
        assert ElementType.SCENE_HEADING in types

    # -- CR-2: MetadataValue annotation --

    def test_metadata_annotation_uses_metadatavalue(self):
        """FountainElement.metadata is typed dict[str, MetadataValue] | None (CR-2)."""
        from fountain.elements import FountainElement, MetadataValue

        annotation = FountainElement.__annotations__["metadata"]
        assert "MetadataValue" in annotation
        assert "Any" not in annotation
        # The MetadataValue alias is exported and usable as the metadata value type.
        assert MetadataValue is not None

    # -- Step 2.1: Renderers in top-level __all__ --

    def test_renderers_importable_from_package(self):
        """HTMLRenderer and FountainRenderer are importable from the top-level package (Open Question 7)."""
        import fountain
        from fountain import FountainRenderer, HTMLRenderer

        assert HTMLRenderer is not None
        assert FountainRenderer is not None
        assert "HTMLRenderer" in fountain.__all__
        assert "FountainRenderer" in fountain.__all__

    # -- Step 2.2: ABOUTME header single-line form (CR-1) --

    def test_aboutme_header_single_line(self):
        """Each src/fountain/ module starts with ABOUTME on line one only (CR-1)."""
        import fountain

        package_dir = Path(fountain.__file__).parent
        source_files = sorted(package_dir.glob("*.py"))
        assert source_files, "expected Python source files under src/fountain/"
        for source_file in source_files:
            first_two_lines = source_file.read_text(encoding="utf-8").splitlines()[:2]
            assert len(first_two_lines) >= 2, f"{source_file.name} has fewer than two lines"
            first_line = first_two_lines[0].lstrip("# ")
            second_line = first_two_lines[1].lstrip("# ")
            assert first_line.startswith("ABOUTME:"), (
                f"{source_file.name} line 1 must start with 'ABOUTME:' (allowing a leading '# ')"
            )
            assert not second_line.startswith("ABOUTME:"), (
                f"{source_file.name} line 2 must not start with 'ABOUTME:' (single-line ABOUTME header)"
            )

    # -- Step 4.1: Boneyard Close with Trailing Text (E2) --

    def test_boneyard_close_with_trailing_text(self):
        """A `*/` with trailing text ends the boneyard; nothing after the close is dropped (E2)."""
        text = """FADE IN:

/*
This interior should be cut
and this line too
*/ And we are back.

The scene continues.

More action here."""

        doc = self.parser.parse(text)
        texts = [element.text for element in doc.elements]

        # The remainder on the close line survives as its own element.
        assert "And we are back." in texts
        # Every line after the close survives as its own element.
        assert "The scene continues." in texts
        assert "More action here." in texts
        # The boneyard interior is still dropped.
        assert "This interior should be cut" not in texts
        assert "and this line too" not in texts

    # -- Step 4.2: Single-Line Boneyard with Trailing Text (E3) --

    def test_single_line_boneyard_keeps_trailing_text(self):
        """A `/* ... */` span with trailing text keeps the remainder; the document is not swallowed (E3)."""
        text = """/* cut this */ keep this

The scene continues.

More action here."""

        doc = self.parser.parse(text)
        texts = [element.text for element in doc.elements]

        # The trailing text after the closed span survives as an element.
        assert "keep this" in texts
        # Every following action line survives; nothing is swallowed.
        assert "The scene continues." in texts
        assert "More action here." in texts
        # The boneyard interior is dropped.
        assert "cut this" not in texts
        assert not any("cut this" in element_text for element_text in texts)

    # -- Step 4.3: Mid-Line Boneyard Opener (E4) --

    def test_midline_boneyard_opener_rejoins_and_hides_interior(self):
        """A mid-line `/*` opener rejoins its pre-text with the post-close text (E4).

        The boneyard removes the interior lines and the newlines between them, so the
        pre-text and the text after the closing `*/` form one action line.
        """
        text = """He waves /* begin cut
This interior should be cut
and this line too
*/ And we are back.

The scene continues.

More action here."""

        doc = self.parser.parse(text)
        texts = [element.text for element in doc.elements]

        # Pre-text and post-close text rejoin as a single action line.
        assert "He waves And we are back." in texts
        # No interior line leaks anywhere in the output.
        assert not any("begin cut" in element_text for element_text in texts)
        assert not any("This interior should be cut" in element_text for element_text in texts)
        assert not any("and this line too" in element_text for element_text in texts)
        # The following action paragraphs survive.
        assert "The scene continues." in texts
        assert "More action here." in texts

    def test_multiline_boneyard_rejoins_surrounding_text(self):
        """A boneyard spanning a line break rejoins the surrounding text on one line."""
        doc = self.parser.parse("Before /* boned\nstill boned */ after")
        actions = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert len(actions) == 1
        assert actions[0].text == "Before after"

    def test_notes_and_boneyard_transparent_to_heading_adjacency(self):
        """A note or boneyard flush against a heading/transition does not demote it.

        Notes and boneyards are invisible in output, so they are transparent for the
        blank-line adjacency that scene headings and transitions require.
        """
        note_after = self.parser.parse("A.\n\nINT. HOUSE - DAY\n[[note]]\n\nB.")
        assert any(element.type == ElementType.SCENE_HEADING for element in note_after.elements)

        note_before = self.parser.parse("A.\n\n[[note]]\nINT. HOUSE - DAY\n\nB.")
        assert any(element.type == ElementType.SCENE_HEADING for element in note_before.elements)

        boneyard_start = self.parser.parse("/* comment */\nINT. HOUSE - DAY\n\nAction.")
        assert any(element.type == ElementType.SCENE_HEADING for element in boneyard_start.elements)

        transition_note = self.parser.parse("A.\n\nCUT TO:\n[[note]]\n\nB.")
        assert any(element.type == ElementType.TRANSITION for element in transition_note.elements)

    def test_multiline_note_preserves_surrounding_text(self):
        """Body text before ``[[`` and after ``]]`` of a multi-line note survives.

        The multi-line note buffered the whole opening and closing lines, absorbing the
        surrounding body text into the (hidden) note and losing it from the output.
        """
        doc = self.parser.parse("KEEPME [[note\ncloses]]\n\nAfter.")
        assert any(element.type == ElementType.NOTE for element in doc.elements)
        # KEEPME survives as a visible (non-note) element rather than being absorbed.
        assert any(element.type != ElementType.NOTE and "KEEPME" in element.text for element in doc.elements)

        tail_doc = self.parser.parse("[[opens\ncloses]] TAIL")
        assert any(element.type == ElementType.NOTE for element in tail_doc.elements)
        assert any(element.type != ElementType.NOTE and "TAIL" in element.text for element in tail_doc.elements)

    def test_unclosed_boneyard_recovers_pretext(self):
        """An unclosed boneyard emits the body text before the '/*' and reports the issue."""
        doc = self.parser.parse("Some real action.\ntext /* dangles")
        combined = " ".join(element.text for element in doc.elements)
        assert "Some real action." in combined
        assert "text" in combined
        assert any(issue.code == "unclosed-boneyard" for issue in doc.issues)

    def test_dialogue_continues_across_interior_lyric_or_note(self):
        """A character who sings or has a note mid-speech keeps speaking in dialogue.

        A lyric or standalone note inside a dialogue block does not end the block; the
        following non-forced line continues as dialogue until a blank line.
        """
        lyric_doc = self.parser.parse("STEEL\nHello.\n~la la la\nGoodbye.")
        assert [element.type for element in lyric_doc.elements] == [
            ElementType.CHARACTER,
            ElementType.DIALOGUE,
            ElementType.LYRICS,
            ElementType.DIALOGUE,
        ]
        assert lyric_doc.elements[-1].text == "Goodbye."

        note_doc = self.parser.parse("STEEL\nHello.\n[[a note]]\nGoodbye.")
        assert [element.type for element in note_doc.elements] == [
            ElementType.CHARACTER,
            ElementType.DIALOGUE,
            ElementType.NOTE,
            ElementType.DIALOGUE,
        ]

        boneyard_doc = self.parser.parse("STEEL\nHello.\n/* aside */\nGoodbye.")
        assert [element.type for element in boneyard_doc.elements] == [
            ElementType.CHARACTER,
            ElementType.DIALOGUE,
            ElementType.BONEYARD,
            ElementType.DIALOGUE,
        ]

    def test_double_equals_is_not_a_synopsis(self):
        """Two equals signs are neither a synopsis nor a page break; they fall to action."""
        doc = self.parser.parse("Action.\n\n==\n\nMore.")
        assert not any(element.type == ElementType.SYNOPSIS for element in doc.elements)

        # A real synopsis (single =) still works.
        syn = self.parser.parse("Action.\n\n= A synopsis\n\nMore.")
        assert any(element.type == ElementType.SYNOPSIS and element.text == "A synopsis" for element in syn.elements)

    def test_orphan_caret_does_not_leave_dual_flag(self):
        """A lone '^' cue with no preceding character is not left flagged as dual dialogue."""
        doc = self.parser.parse("STEEL ^\nAlone.")
        characters = [element for element in doc.elements if element.type == ElementType.CHARACTER]
        assert len(characters) == 1
        assert characters[0].text == "STEEL"
        assert not (characters[0].metadata and characters[0].metadata.get("dual_dialogue"))

    def test_forced_character_requires_a_letter(self):
        """A forced ``@`` cue with no alphabetical character is not a valid character.

        The Fountain spec requires a character name to contain at least one letter, even
        when forced, so ``@23`` is not a cue while ``@McClane`` is.
        """
        no_letter = self.parser.parse("@23\nHello.")
        assert not any(element.type == ElementType.CHARACTER for element in no_letter.elements)

        valid = self.parser.parse("@McClane\nHi.")
        assert valid.elements[0].type == ElementType.CHARACTER
        assert valid.elements[0].text == "McClane"

    def test_inline_note_removal_collapses_double_space(self):
        """Removing a mid-line note leaves a single space, not two."""
        doc = self.parser.parse("Action [[a note]] here")
        actions = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert len(actions) == 1
        assert actions[0].text == "Action here"

        multi = self.parser.parse("One [[n1]] two [[n2]] three")
        multi_actions = [element for element in multi.elements if element.type == ElementType.ACTION]
        assert multi_actions[0].text == "One two three"

    def test_parse_surfaces_diagnostics_on_document(self):
        """parse() attaches the diagnostics it detects to the returned document's issues."""
        boneyard_doc = self.parser.parse("INT. HOUSE - DAY\n\n/* open boneyard")
        assert any(issue.code == "unclosed-boneyard" for issue in boneyard_doc.issues)

        note_doc = self.parser.parse("INT. HOUSE - DAY\n\n[[ open note")
        assert any(issue.code == "unclosed-note" for issue in note_doc.issues)

        orphan_doc = self.parser.parse("INT. HOUSE - DAY\n\nJOHN\n\nINT. KITCHEN - NIGHT")
        assert any(issue.code == "orphan-character-cue" for issue in orphan_doc.issues)

        clean_doc = self.parser.parse("INT. HOUSE - DAY\n\nAction.")
        assert clean_doc.issues == []

        # validate() surfaces the same diagnostics parse() records.
        assert [issue.code for issue in self.parser.validate("INT. HOUSE - DAY\n\n/* open")] == ["unclosed-boneyard"]

    def test_emphasis_round_trips_through_fountain(self):
        """Emphasis survives parse -> FountainRenderer -> parse with the same spans.

        The parser strips emphasis delimiters; the Fountain renderer must re-emit them,
        including nested emphasis and backslash-escaped literal asterisks.
        """
        from fountain.renderer import FountainRenderer

        for source in (
            "He said **bold** and *italic* and _under_ words.",
            "*italic **both** italic*",
            "Steel enters **\\*9765\\***",
        ):
            doc = self.parser.parse(source)
            rendered = FountainRenderer().render(doc)
            reparsed = self.parser.parse(rendered)
            original = doc.elements[0]
            round_tripped = reparsed.elements[0]
            assert round_tripped.text == original.text
            assert [(span.start, span.end, span.format_type) for span in round_tripped.formatting] == [
                (span.start, span.end, span.format_type) for span in original.formatting
            ]

    # -- Step 4.4: Mid-Line Boneyard Stripped from Text (E1) --

    def test_midline_boneyard_stripped_from_text(self):
        """A complete mid-line `/* ... */` span is stripped and the seam collapses to one space (E1)."""
        doc = self.parser.parse("Hello /* hidden */ world.")

        action_elements = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert len(action_elements) == 1
        # The span is removed and the whitespace left behind collapses to a single space.
        assert action_elements[0].text == "Hello world."
        # The interior never leaks into any element.
        assert not any("hidden" in element.text for element in doc.elements)

    def test_midline_boneyard_stripped_from_dialogue(self):
        """A mid-line `/* ... */` span inside a dialogue line strips to the collapsed text (E1)."""
        text = """INT. HOUSE - DAY

JOHN
Hello /* hidden */ world."""

        doc = self.parser.parse(text)
        dialogue = next((element for element in doc.elements if element.type == ElementType.DIALOGUE), None)

        assert dialogue is not None
        assert dialogue.text == "Hello world."
        assert not any("hidden" in element.text for element in doc.elements)

    # -- Step 4.8: Two-Space vs Blank Line Inside a Note (E6, E7) --

    def test_two_space_line_inside_note_keeps_empty_line(self):
        """A two-space connector line inside a note preserves an empty interior line (E6).

        A multi-line note whose middle line is exactly two spaces stays open and keeps
        that line as an empty interior line, so the resulting single NOTE carries a blank
        line (a ``\\n\\n``) between its surrounding lines.
        """
        doc = self.parser.parse("[[Start of note\n  \nEnd of note]]")
        notes = [element for element in doc.elements if element.type == ElementType.NOTE]
        assert len(notes) == 1
        assert "\n\n" in notes[0].text

    def test_blank_line_breaks_open_note(self):
        """A genuinely blank line breaks an open note; the bracket lines fall back to text (E7).

        The same note structure as the two-space case, but with a truly empty middle line,
        does not survive as a single NOTE. The buffered bracket lines fall back to action
        text, so the E6 and E7 inputs produce distinguishable outputs.
        """
        two_space_doc = self.parser.parse("[[Start of note\n  \nEnd of note]]")
        blank_doc = self.parser.parse("[[Start of note\n\nEnd of note]]")

        blank_notes = [element for element in blank_doc.elements if element.type == ElementType.NOTE]
        # The blank line breaks the note: no single NOTE spans both bracket lines.
        assert not any("Start of note" in note.text and "End of note" in note.text for note in blank_notes)
        # The E6 (two-space) and E7 (blank) inputs must be distinguishable.
        two_space_types = [element.type for element in two_space_doc.elements]
        blank_types = [element.type for element in blank_doc.elements]
        assert two_space_types != blank_types

    def test_unclosed_note_at_eof_recovers_text(self):
        """An unclosed ``[[`` note at end of input recovers its lines as action.

        Without a trailing blank line to break the note, the buffered bracket lines
        reached end of input still open and were silently dropped, taking the whole rest
        of the document with them (zero elements). The recovery re-emits them as action so
        the body text survives.
        """
        doc = self.parser.parse("[[note start\nAction after.\nMore lines.")
        assert len(doc.elements) > 0
        combined = " ".join(element.text for element in doc.elements)
        assert "Action after." in combined
        assert "More lines." in combined

    def test_two_space_note_line_no_empty_dialogue(self):
        """A two-space line inside an open note injects no empty DIALOGUE element (E8).

        A dialogue block followed by a multi-line note whose middle line is exactly two
        spaces must not treat that two-space line as a dialogue continuation. The open note
        intercepts the line, so the element sequence stays CHARACTER, DIALOGUE, NOTE with no
        empty-text DIALOGUE injected.
        """
        source = "JOHN\nHello there.\n\n[[note line one\n  \nnote line two]]"
        doc = self.parser.parse(source)
        element_types = [element.type for element in doc.elements]
        assert element_types == [ElementType.CHARACTER, ElementType.DIALOGUE, ElementType.NOTE]
        empty_dialogue = [
            element for element in doc.elements if element.type == ElementType.DIALOGUE and element.text.strip() == ""
        ]
        assert empty_dialogue == []

    # -- Step 7.1: Punctuated Uppercase Character Cues (C1) --

    def test_punctuated_character_cues(self):
        """Uppercase cues containing ``.``, ``'``, ``-``, or ``#N`` parse as CHARACTER (C1).

        The Fountain spec allows character cues to carry punctuation: ``MR. SMITH``,
        ``O'BRIEN``, ``JEAN-CLAUDE``, and ``DEALER #2`` are all valid cues. Each, when
        placed at document start and followed by a dialogue line, must parse as a
        CHARACTER element followed by a DIALOGUE element.
        """
        cues = ["MR. SMITH", "O'BRIEN", "JEAN-CLAUDE", "DEALER #2"]
        for cue in cues:
            parser = FountainParser()
            doc = parser.parse(f"{cue}\nHello there.")
            element_types = [element.type for element in doc.elements]
            assert element_types == [ElementType.CHARACTER, ElementType.DIALOGUE], (
                f"{cue!r} should parse as CHARACTER + DIALOGUE, got {element_types}"
            )
            assert doc.elements[0].text == cue

    def test_cue_followed_by_punctuated_shout(self):
        """A cue followed by a punctuated all-caps line yields CHARACTER + DIALOGUE.

        Widening the character-cue pattern to accept punctuation (C1) means an
        all-caps dialogue line like ``NO. NEVER.`` now matches the cue pattern too.
        The lookahead must not let that line masquerade as a competing structural
        element: since it is not itself followed by its own dialogue, it is dialogue
        for the preceding ``JOHN`` cue, not a reason to demote ``JOHN`` to action.
        """
        doc = FountainParser().parse("JOHN\nNO. NEVER.")
        element_types = [element.type for element in doc.elements]
        assert element_types == [ElementType.CHARACTER, ElementType.DIALOGUE], (
            f"'JOHN' / 'NO. NEVER.' should parse as CHARACTER + DIALOGUE, got {element_types}"
        )
        assert doc.elements[0].text == "JOHN"
        assert doc.elements[1].text == "NO. NEVER."

    def test_cue_followed_by_allcaps_dialogue(self):
        """An all-caps line after a cue is that cue's dialogue, not a rival cue (C4).

        A shouted line such as ``I SAID NO`` is uppercase and matches the character
        cue pattern, but it is not itself followed by its own dialogue. The lookahead
        must treat it as dialogue for the preceding ``JOHN`` cue.
        """
        doc = FountainParser().parse("JOHN\nI SAID NO")
        element_types = [element.type for element in doc.elements]
        assert element_types == [ElementType.CHARACTER, ElementType.DIALOGUE], (
            f"'JOHN' / 'I SAID NO' should parse as CHARACTER + DIALOGUE, got {element_types}"
        )
        assert doc.elements[0].text == "JOHN"
        assert doc.elements[1].text == "I SAID NO"

    def test_allcaps_line_after_cue_is_dialogue(self):
        """An all-caps line after a cue is that cue's dialogue (C4, plan Step 7.4).

        This is the plan's canonically-named pin for defect C4. The behavior was
        already delivered by Step 7.1's cue-lookahead rework: a shouted, all-caps
        follow line matches the character-cue pattern but is not itself followed by
        its own dialogue, so the lookahead must attribute it to the preceding cue as
        DIALOGUE rather than treat it as a rival CHARACTER. This test pins that
        contract explicitly under the plan's name.
        """
        doc = FountainParser().parse("JOHN\nI SAID NO")
        element_types = [element.type for element in doc.elements]
        assert element_types == [ElementType.CHARACTER, ElementType.DIALOGUE], (
            f"'JOHN' / 'I SAID NO' should parse as CHARACTER + DIALOGUE, got {element_types}"
        )
        assert doc.elements[0].text == "JOHN"
        assert doc.elements[1].text == "I SAID NO"

        shout_doc = FountainParser().parse("JOHN\nGET OUT NOW")
        shout_types = [element.type for element in shout_doc.elements]
        assert shout_types == [ElementType.CHARACTER, ElementType.DIALOGUE], (
            f"'JOHN' / 'GET OUT NOW' should parse as CHARACTER + DIALOGUE, got {shout_types}"
        )
        assert shout_doc.elements[0].text == "JOHN"
        assert shout_doc.elements[1].text == "GET OUT NOW"

    def test_digit_first_character_cue(self):
        """A digit-first cue with at least one letter parses as CHARACTER (C2).

        The Fountain spec allows a cue to begin with a digit, as in ``23 SKIDOO``,
        provided the cue still contains at least one alphabetic letter. Such a line,
        followed by a dialogue line, must parse as CHARACTER plus DIALOGUE. A purely
        numeric line like ``23``, ``007``, or ``42`` has no letter and must stay
        ACTION even when a following line could otherwise be dialogue.
        """
        doc = FountainParser().parse("23 SKIDOO\nHello there.")
        element_types = [element.type for element in doc.elements]
        assert element_types == [ElementType.CHARACTER, ElementType.DIALOGUE], (
            f"'23 SKIDOO' should parse as CHARACTER + DIALOGUE, got {element_types}"
        )
        assert doc.elements[0].text == "23 SKIDOO"
        assert doc.elements[1].text == "Hello there."

        for numeric_line in ["23", "007", "42"]:
            parser = FountainParser()
            numeric_doc = parser.parse(f"{numeric_line}\nHello there.")
            numeric_types = [element.type for element in numeric_doc.elements]
            # No letter, so it is not a cue: the numeric line and the following line are one
            # merged action paragraph, never CHARACTER + DIALOGUE.
            assert numeric_types == [ElementType.ACTION], (
                f"{numeric_line!r} has no letter and should stay ACTION, got {numeric_types}"
            )
            assert numeric_doc.elements[0].text == f"{numeric_line}\nHello there."

    # -- Step 7.3: Blank Line After a Cue Disqualifies It (C3) --

    def test_blank_after_cue_disqualifies(self):
        """A blank line immediately after a cue disqualifies it (C3).

        The Fountain spec requires a character cue to be immediately followed by
        its dialogue with no intervening blank line. ``JOHN`` on its own line, a
        blank line, then ``He walks to the door.`` is therefore not a cue plus
        dialogue: both lines are ACTION. The lookahead must not skip the blank
        line to reach a later non-empty line and treat ``JOHN`` as a cue for it.

        The guard case confirms that a cue with immediate dialogue (no blank line)
        still parses as CHARACTER plus DIALOGUE, so the disqualification is scoped
        to the blank-line-after case alone.
        """
        doc = FountainParser().parse("JOHN\n\nHe walks to the door.")
        element_types = [element.type for element in doc.elements]
        assert element_types == [ElementType.ACTION, ElementType.ACTION], (
            f"'JOHN' / blank / 'He walks to the door.' should parse as two ACTION elements, got {element_types}"
        )
        assert doc.elements[0].text == "JOHN"
        assert doc.elements[1].text == "He walks to the door."

        guard = FountainParser().parse("JOHN\nHe walks to the door.")
        guard_types = [element.type for element in guard.elements]
        assert guard_types == [ElementType.CHARACTER, ElementType.DIALOGUE], (
            f"'JOHN' with immediate dialogue should still parse as CHARACTER + DIALOGUE, got {guard_types}"
        )
        assert guard.elements[0].text == "JOHN"
        assert guard.elements[1].text == "He walks to the door."

    # -- Step 7.5: Trailing Caret on a Forced Character Creates Dual Dialogue (C5) --

    def test_forced_character_caret_dual_dialogue(self):
        """A trailing caret on a forced ``@`` cue creates dual dialogue (C5).

        A natural ``NAME^`` cue already pairs into a DUAL_DIALOGUE block via the
        post-pass. A forced ``@McClane ^`` cue carries the same intent: the caret
        marks simultaneous speech with the preceding character. The forced-``@``
        branch must honor the trailing caret by stripping it (and the surrounding
        whitespace) and setting ``dual_dialogue`` so the existing pairing pass runs.

        A ``BRICK`` block followed by ``@McClane ^`` therefore yields one
        DUAL_DIALOGUE element whose right character text is ``McClane`` (no ``@``,
        no ``^``, no trailing space).

        Two guards keep the behavior scoped: a forced ``@name`` without a caret is
        a plain forced CHARACTER (never dual), and a natural ``NAME^`` cue still
        pairs as before.
        """
        doc = FountainParser().parse("BRICK\nHere we go.\n\n@McClane ^\nRight behind you.")
        dual_elements = [element for element in doc.elements if element.type == ElementType.DUAL_DIALOGUE]
        assert len(dual_elements) == 1, (
            f"'BRICK' block + '@McClane ^' should yield one DUAL_DIALOGUE element, got {[e.type for e in doc.elements]}"
        )
        dual = dual_elements[0]
        assert dual.metadata["left_character"].text == "BRICK"
        right_text = dual.metadata["right_character"].text
        assert right_text == "McClane", (
            f"right character text should be 'McClane' (caret and @ stripped), got {right_text!r}"
        )

        # Guard: a forced @name WITHOUT a caret is a plain forced CHARACTER, not dual.
        no_caret = FountainParser().parse("BRICK\nHere we go.\n\n@McClane\nRight behind you.")
        assert not any(element.type == ElementType.DUAL_DIALOGUE for element in no_caret.elements), (
            "a forced '@McClane' without a caret must not become dual dialogue"
        )
        forced_chars = [element for element in no_caret.elements if element.type == ElementType.CHARACTER]
        assert forced_chars[-1].text == "McClane"
        assert forced_chars[-1].metadata["forced"] is True

        # Guard: a natural NAME^ dual cue still pairs as before.
        natural = FountainParser().parse("BRICK\nHere we go.\n\nMCCLANE^\nRight behind you.")
        natural_dual = [element for element in natural.elements if element.type == ElementType.DUAL_DIALOGUE]
        assert len(natural_dual) == 1
        assert natural_dual[0].metadata["right_character"].text == "MCCLANE"

    def test_at_forces_character_unconditionally(self):
        """``@`` forces CHARACTER unconditionally, never gated on the dialogue lookahead (C6).

        The ``@`` prefix is an explicit author override. Per the spec it must force a
        CHARACTER cue regardless of what follows, and the literal ``@`` never survives
        in the element text. The forced branch must therefore NOT reuse the
        ``_is_dialogue_following()`` gate that scopes natural cues: a forced cue is a
        cue whether dialogue, a blank line, action, or EOF comes next.

        Natural (non-``@``) cues stay gated: a natural cue with a blank line after it
        (C3) is still disqualified, so the ``@`` unconditional force must not leak into
        natural-cue detection.
        """
        # Dialogue follows: forced CHARACTER + DIALOGUE, no literal '@' (already worked).
        with_dialogue = FountainParser().parse("@McClane\nI SAID NO")
        cues = [element for element in with_dialogue.elements if element.type == ElementType.CHARACTER]
        assert len(cues) == 1, (
            f"expected one forced CHARACTER, got {[element.type for element in with_dialogue.elements]}"
        )
        assert cues[0].text == "McClane", f"forced cue text must strip the '@', got {cues[0].text!r}"
        assert cues[0].metadata["forced"] is True
        dialogue = [element for element in with_dialogue.elements if element.type == ElementType.DIALOGUE]
        assert len(dialogue) == 1
        assert dialogue[0].text == "I SAID NO"

        # Real defect case: a blank line (then action) follows the forced cue. The cue must
        # STILL be a forced CHARACTER, not demote to ACTION('@McClane').
        blank_after = FountainParser().parse("@McClane\n\nAction line here.")
        forced_cues = [element for element in blank_after.elements if element.type == ElementType.CHARACTER]
        assert len(forced_cues) == 1, (
            f"'@McClane' before a blank line must remain a forced CHARACTER, got "
            f"{[(element.type.value, element.text) for element in blank_after.elements]}"
        )
        assert forced_cues[0].text == "McClane", f"forced cue text must strip the '@', got {forced_cues[0].text!r}"
        assert forced_cues[0].metadata["forced"] is True
        assert not any(element.text == "@McClane" for element in blank_after.elements), (
            "no element may retain a literal '@McClane'"
        )
        # The following line still classifies correctly as ACTION.
        actions = [element for element in blank_after.elements if element.type == ElementType.ACTION]
        assert any(element.text == "Action line here." for element in actions)

        # Guard: a bare '@McClane' at EOF (nothing after) is still a forced CHARACTER.
        at_eof = FountainParser().parse("@McClane")
        eof_cues = [element for element in at_eof.elements if element.type == ElementType.CHARACTER]
        assert len(eof_cues) == 1, (
            f"'@McClane' at EOF must be a forced CHARACTER, got "
            f"{[(element.type.value, element.text) for element in at_eof.elements]}"
        )
        assert eof_cues[0].text == "McClane"
        assert eof_cues[0].metadata["forced"] is True

        # Regression guard: natural cues stay GATED. A natural cue with a blank line after
        # it (C3) must NOT be treated as a cue just because '@' became unconditional.
        natural_blank_after = FountainParser().parse("Some action.\n\nMCCLANE\n\nMore action.")
        assert not any(element.type == ElementType.CHARACTER for element in natural_blank_after.elements), (
            "a natural cue with a blank line after it must not become a CHARACTER (C3 still gates naturals)"
        )

    # -- Step 7.7: Forced Characters Get Extension Extraction (C7) --

    def test_forced_character_extension(self):
        """A forced ``@`` cue extracts a trailing ``(extension)`` like a natural cue (C7).

        A natural ``MCCLANE (V.O.)`` cue lifts the extension into
        ``metadata["extension"]`` and keeps only the name in the element text. A forced
        ``@McClane (O.S.)`` cue must behave the same: text ``McClane`` (no ``@``, no
        extension), ``metadata["extension"] == "O.S."``, and ``forced`` still True. The
        forced-``@`` branch owns its own extraction because a forced name may be any case
        (``@mcclane``), so the uppercase-gated natural pattern cannot apply.

        The extension extraction composes with the C5 caret handling: a combined
        ``@McClane (O.S.) ^`` cue strips the caret (dual dialogue) AND lifts the
        extension, yielding text ``McClane`` with both ``extension`` and ``dual_dialogue``
        set.
        """
        # Plain extension: text is the bare name, extension lifted, forced preserved.
        doc = FountainParser().parse("@McClane (O.S.)\nBehind you.")
        cues = [element for element in doc.elements if element.type == ElementType.CHARACTER]
        assert len(cues) == 1, f"expected one forced CHARACTER, got {[element.type for element in doc.elements]}"
        assert cues[0].text == "McClane", f"forced cue text must be the bare name, got {cues[0].text!r}"
        assert cues[0].metadata["extension"] == "O.S.", (
            f"forced cue must lift the extension, got {cues[0].metadata.get('extension')!r}"
        )
        assert cues[0].metadata["forced"] is True

        # Combined extension + caret: both handled. The caret pairs into DUAL_DIALOGUE.
        combined = FountainParser().parse("BRICK\nHere we go.\n\n@McClane (O.S.) ^\nRight behind you.")
        dual_elements = [element for element in combined.elements if element.type == ElementType.DUAL_DIALOGUE]
        assert len(dual_elements) == 1, (
            f"'@McClane (O.S.) ^' should pair into one DUAL_DIALOGUE, got {[e.type for e in combined.elements]}"
        )
        right = dual_elements[0].metadata["right_character"]
        assert right.text == "McClane", f"combined cue text must be the bare name, got {right.text!r}"
        assert right.metadata["extension"] == "O.S.", (
            f"combined cue must lift the extension, got {right.metadata.get('extension')!r}"
        )
        assert right.metadata["dual_dialogue"] is True

        # Regression: a forced cue with NO extension gets no extension metadata.
        plain = FountainParser().parse("@McClane\nBehind you.")
        plain_cues = [element for element in plain.elements if element.type == ElementType.CHARACTER]
        assert plain_cues[0].text == "McClane"
        assert plain_cues[0].metadata["forced"] is True
        assert "extension" not in plain_cues[0].metadata, (
            "a forced cue without a trailing '(...)' must not gain extension metadata"
        )

        # Regression: a forced caret cue with NO extension still pairs as dual, no extension.
        caret_only = FountainParser().parse("BRICK\nHere we go.\n\n@McClane ^\nRight behind you.")
        caret_dual = [element for element in caret_only.elements if element.type == ElementType.DUAL_DIALOGUE]
        assert len(caret_dual) == 1
        caret_right = caret_dual[0].metadata["right_character"]
        assert caret_right.text == "McClane"
        assert caret_right.metadata["dual_dialogue"] is True
        assert "extension" not in caret_right.metadata

        # Regression: natural extension extraction is unchanged.
        natural = FountainParser().parse("MCCLANE (V.O.)\nBehind you.")
        natural_cues = [element for element in natural.elements if element.type == ElementType.CHARACTER]
        assert natural_cues[0].text == "MCCLANE"
        assert natural_cues[0].metadata["extension"] == "V.O."

    def test_blank_line_ends_parenthetical_dialogue_block(self):
        """A blank line ends a natural CHARACTER/PARENTHETICAL dialogue block.

        Pins the natural-cue path through ``_is_dialogue_line``: after ``JOHN`` and a
        ``(softly)`` parenthetical, a blank line ends the dialogue block, so the ``Hi.``
        that follows must classify as ACTION, not DIALOGUE. The parenthetical is the
        previous element and ``had_blank_line_before`` is True on that line, so this is
        the exact natural-cue + PARENTHETICAL + blank path the guard covers (not just
        the forced-``@`` case).
        """
        doc = FountainParser().parse("JOHN\n(softly)\n\nHi.")
        types = [element.type for element in doc.elements]
        assert ElementType.CHARACTER in types, f"'JOHN' should be a CHARACTER cue, got {types}"
        assert ElementType.PARENTHETICAL in types, f"'(softly)' should be a PARENTHETICAL, got {types}"

        # The block up to the blank is CHARACTER then PARENTHETICAL, in order.
        character = next(element for element in doc.elements if element.type == ElementType.CHARACTER)
        parenthetical = next(element for element in doc.elements if element.type == ElementType.PARENTHETICAL)
        assert character.text == "JOHN"
        assert parenthetical.text == "(softly)"
        assert doc.elements.index(character) < doc.elements.index(parenthetical)

        # The blank line ends the dialogue block: 'Hi.' is ACTION, not DIALOGUE.
        hi_elements = [element for element in doc.elements if element.text == "Hi."]
        assert len(hi_elements) == 1, (
            f"expected one 'Hi.' element, got {[(element.type.value, element.text) for element in doc.elements]}"
        )
        assert hi_elements[0].type == ElementType.ACTION, (
            f"a blank line ends the dialogue block, so 'Hi.' must be ACTION, got {hi_elements[0].type.value}"
        )
        assert not any(element.type == ElementType.DIALOGUE and element.text == "Hi." for element in doc.elements), (
            "'Hi.' after a blank line must not be DIALOGUE"
        )

    # -- Step 8.1: D1 Trailing Space After the Colon Defeats a Transition --

    def test_trailing_space_defeats_transition(self):
        """D1: a trailing space after the colon makes ``CUT TO:`` action, not a transition.

        The natural transition rule is end-anchored, so trailing whitespace on an
        otherwise-transition line must fall through to action.
        """
        doc = self.parser.parse("Action.\n\nCUT TO: \n\nINT. HOUSE - DAY")
        transitions = [element for element in doc.elements if element.type == ElementType.TRANSITION]
        assert len(transitions) == 0, (
            f"'CUT TO: ' with a trailing space must not parse as a transition, got {[t.text for t in transitions]}"
        )
        actions = [element for element in doc.elements if element.type == ElementType.ACTION]
        assert any("CUT TO:" in action.text for action in actions), (
            "'CUT TO: ' with a trailing space must parse as action, "
            f"got {[(element.type.value, element.text) for element in doc.elements]}"
        )

        # Guard: the clean form (no trailing space) is still a transition.
        clean_doc = self.parser.parse("Action.\n\nCUT TO:\n\nINT. HOUSE - DAY")
        clean_transitions = [element for element in clean_doc.elements if element.type == ElementType.TRANSITION]
        assert len(clean_transitions) == 1
        assert clean_transitions[0].text == "CUT TO:"

    # -- Step 8.2: D2 Punctuated Uppercase TO: Lines Are Transitions --

    def test_punctuated_transition(self):
        """D2: an uppercase line ending in ``TO:`` with internal punctuation is a transition.

        The natural transition pattern must allow punctuation (a hyphen and similar
        marks) before ``TO:`` so ``SMASH-CUT TO:`` is recognized, while staying
        uppercase-oriented and end-anchored on ``TO:``.
        """
        # Primary acceptance: a hyphenated transition parses as TRANSITION.
        doc = self.parser.parse("Action.\n\nSMASH-CUT TO:\n\nINT. HOUSE - DAY")
        transitions = [element for element in doc.elements if element.type == ElementType.TRANSITION]
        assert len(transitions) == 1, (
            "'SMASH-CUT TO:' with surrounding blank lines must parse as a transition, "
            f"got {[(element.type.value, element.text) for element in doc.elements]}"
        )
        assert transitions[0].text == "SMASH-CUT TO:"

        # A second hyphenated example must also work.
        match_doc = self.parser.parse("Action.\n\nMATCH-CUT TO:\n\nINT. HOUSE - DAY")
        match_transitions = [element for element in match_doc.elements if element.type == ElementType.TRANSITION]
        assert len(match_transitions) == 1
        assert match_transitions[0].text == "MATCH-CUT TO:"

        # Regression: an unpunctuated transition still parses as a transition.
        dissolve_doc = self.parser.parse("Action.\n\nDISSOLVE TO:\n\nINT. HOUSE - DAY")
        dissolve_transitions = [element for element in dissolve_doc.elements if element.type == ElementType.TRANSITION]
        assert len(dissolve_transitions) == 1
        assert dissolve_transitions[0].text == "DISSOLVE TO:"

        # D1 still holds: a trailing space on the punctuated form defeats the transition.
        spaced_doc = self.parser.parse("Action.\n\nSMASH-CUT TO: \n\nINT. HOUSE - DAY")
        spaced_transitions = [element for element in spaced_doc.elements if element.type == ElementType.TRANSITION]
        assert len(spaced_transitions) == 0, (
            "'SMASH-CUT TO: ' with a trailing space must not parse as a transition, "
            f"got {[element.text for element in spaced_transitions]}"
        )

        # Guard: a mixed-case punctuated line is not a transition (stays action).
        mixed_doc = self.parser.parse("Action.\n\nSmash-Cut TO:\n\nINT. HOUSE - DAY")
        mixed_transitions = [element for element in mixed_doc.elements if element.type == ElementType.TRANSITION]
        assert len(mixed_transitions) == 0

    # -- Step 9.1: A3 Title Page Detection Heuristic (documented contract) --

    def test_title_page_detection_requires_a_real_key(self):
        """A3 (revised): a colon-bearing first line is metadata only when it looks like a key.

        A title-page key must carry a non-empty value or an indented continuation, and
        name a recognized field or a capitalized label. A bare ``FADE IN:`` / ``CUT TO:``
        (empty value) and prose like ``He opens the card:`` (lowercase label) are body
        content, not metadata. This gate keeps a transition on the first line from being
        silently consumed as a phantom metadata key.
        """
        # Prose with a colon on line one is action, not a phantom metadata key.
        doc = self.parser.parse("He opens the card:")
        assert doc.metadata == {}
        assert any(element.type == ElementType.ACTION for element in doc.elements)

        with_body = self.parser.parse("He opens the card: a threat.\nSome action here.")
        assert with_body.metadata == {}
        body_actions = [element.text for element in with_body.elements if element.type == ElementType.ACTION]
        assert body_actions == ["He opens the card: a threat.\nSome action here."]

        # A leading blank line still yields body content, not a phantom key.
        leading_blank = self.parser.parse("\nHe opens the card: a threat.\nSome action here.")
        assert leading_blank.metadata == {}

        # A forced '>CUT TO:' on line one now parses as a body transition, not a key.
        forced_first = self.parser.parse(">CUT TO:\n\nINT. HOUSE - DAY")
        assert forced_first.metadata == {}
        forced_transitions = [element for element in forced_first.elements if element.type == ElementType.TRANSITION]
        assert len(forced_transitions) == 1
        assert forced_transitions[0].text == "CUT TO:"

        # A real title page still parses, and a forced '>CUT TO:' in the body still works.
        with_title = self.parser.parse("Title: My Script\n\n>CUT TO:\n\nINT. HOUSE - DAY")
        assert with_title.metadata.get("title") == "My Script"
        transitions = [element for element in with_title.elements if element.type == ElementType.TRANSITION]
        assert len(transitions) == 1
        assert transitions[0].text == "CUT TO:"

    # -- Step 9.2 (revised): C8 Lyrics Inside a Dialogue Block Do Not End It --

    def test_lyrics_inside_dialogue_do_not_end_block(self):
        """A lyric line inside a dialogue block does not end it; the next line is dialogue.

        A character who sings and then keeps speaking stays in the dialogue block, which
        ends only at a blank line. ``JOHN`` / ``~Willy Wonka!`` / ``Wasn't that great?``
        yields CHARACTER, LYRICS, DIALOGUE.
        """
        doc = self.parser.parse("JOHN\n~Willy Wonka!\nWasn't that great?")

        types = [element.type for element in doc.elements]
        assert types == [ElementType.CHARACTER, ElementType.LYRICS, ElementType.DIALOGUE]

        # The tilde is stripped from the stored lyric text.
        assert doc.elements[1].text == "Willy Wonka!"
        # The trailing line continues as dialogue.
        assert doc.elements[2].text == "Wasn't that great?"

    # -- Step 9.3: D11 FADE IN: and FADE OUT. Are Natural Transitions (deliberate extension) --

    def test_fade_in_out_are_transitions(self):
        """``FADE IN:`` and ``FADE OUT.`` parse as TRANSITION (D11 deliberate extension).

        The Fountain spec's natural-transition rule requires a line to end in ``TO:``.
        fountain-py deliberately extends that rule to also recognize ``FADE IN:`` and
        ``FADE OUT.`` as transitions, since neither ends in ``TO:`` yet both are the
        canonical opening and closing transitions of a screenplay. This pins that
        extension so the behavior is not lost to a future tightening of the rule.
        """
        doc = self.parser.parse("The screen is black.\n\nFADE IN:\n\nINT. HOUSE - DAY\n\nFADE OUT.")

        transitions = [element for element in doc.elements if element.type == ElementType.TRANSITION]
        assert [transition.text for transition in transitions] == ["FADE IN:", "FADE OUT."]

    # -- Step 9.4: E9 Inline Notes Are Removed, Standalone Note Lines Are Kept (documented contract) --

    def test_inline_note_removed_standalone_kept(self):
        """Inline ``[[note]]`` content is stripped and unrecoverable; a standalone ``[[note]]`` line is kept (E9).

        Fountain notes behave asymmetrically depending on placement. An inline
        ``[[note]]`` embedded in a line of action has its content stripped out of
        the line text and is unrecoverable from the parse: neither the note content
        nor its brackets survive, and the whitespace seam collapses to a single
        space. A standalone ``[[note]]`` line, by contrast, becomes a NOTE element
        whose text keeps the content verbatim, brackets included (per E10). This pins
        the asymmetry so it is not lost to a future change that treats the two
        placements the same way.
        """
        inline_doc = self.parser.parse("INT. HOUSE - DAY\n\nHe waves [[secret]] hello.")

        action_elements = [element for element in inline_doc.elements if element.type == ElementType.ACTION]
        assert len(action_elements) == 1
        inline_text = action_elements[0].text
        # The note content is stripped and unrecoverable: no content, no brackets.
        assert "secret" not in inline_text
        assert "[[" not in inline_text
        assert "]]" not in inline_text
        # The whitespace seam left by the note collapses to a single space.
        assert inline_text == "He waves hello."

        standalone_doc = self.parser.parse("INT. HOUSE - DAY\n\n[[remember this]]")

        note_elements = [element for element in standalone_doc.elements if element.type == ElementType.NOTE]
        assert len(note_elements) == 1
        # The standalone note is kept verbatim, brackets included.
        assert note_elements[0].text == "[[remember this]]"


class TestToolingCompliance:
    """Tests for project tooling hygiene.

    CR-3: the justfile once carried ``pre-commit-install`` and ``pre-commit-all``
    recipes and CONTRIBUTING.md told contributors to run ``pre-commit install``,
    even though pre-commit is neither a dependency nor configured anywhere (no
    ``.pre-commit-config.yaml``). These dangling references must stay gone.
    """

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def test_justfile_has_no_pre_commit_recipe(self):
        """The justfile declares no pre-commit recipe (CR-3)."""
        justfile = self._repo_root() / "justfile"
        assert "pre-commit" not in justfile.read_text(encoding="utf-8")

    def test_contributing_has_no_pre_commit_instruction(self):
        """CONTRIBUTING.md tells no one to install pre-commit hooks (CR-3)."""
        contributing = self._repo_root() / "CONTRIBUTING.md"
        assert "pre-commit" not in contributing.read_text(encoding="utf-8")

    def test_no_pre_commit_in_source_and_config(self):
        """No tracked source or config file references pre-commit (CR-3).

        Scoped to the shipped deliverables (justfile, CONTRIBUTING.md,
        pyproject.toml, source, docs, CI). Planning and session-note files
        (``plan.md``, ``todo.md``, ``spec.md``, ``.ai-sessions/``) legitimately
        mention CR-3 by name and are intentionally excluded.
        """
        root = self._repo_root()
        try:
            result = subprocess.run(
                [
                    "git",
                    "grep",
                    "-il",
                    "pre-commit",
                    "--",
                    "justfile",
                    "CONTRIBUTING.md",
                    "pyproject.toml",
                    "src",
                    "docs",
                    ".github",
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            pytest.skip("git is not available")
        # git grep exits 1 when there are no matches; that is the success case.
        assert result.returncode == 1, f"pre-commit references remain in: {result.stdout.strip()}"
