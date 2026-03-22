"""
Tests for the HTML renderer.
"""

from fountain.document import FountainDocument
from fountain.elements import ElementType, FormatSpan, FountainElement
from fountain.renderer import FountainRenderer, HTMLRenderer


class TestHTMLRenderer:
    def setup_method(self):
        self.renderer = HTMLRenderer()

    def test_render_simple_document(self):
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 2),
            FountainElement(ElementType.DIALOGUE, "Hello, world!", [], 3),
        ]
        metadata = {"title": "Test Script", "author": "Test Author"}

        document = FountainDocument(elements, metadata)
        html = self.renderer.render(document)

        # Check that HTML contains expected elements
        assert '<div class="fountain-script">' in html
        assert '<div class="title-page">' in html
        assert '<h1 class="title">Test Script</h1>' in html
        assert '<p class="author">by Test Author</p>' in html
        assert '<div class="scene-heading">INT. HOUSE - DAY</div>' in html
        assert '<div class="character">JOHN</div>' in html
        assert '<div class="dialogue">Hello, world!</div>' in html
        assert "<style>" in html  # CSS should be included

    def test_render_with_formatting(self):
        formatting = [
            FormatSpan(5, 9, "bold"),
            FormatSpan(10, 16, "italic"),
        ]
        elements = [
            FountainElement(ElementType.DIALOGUE, "This **bold** *italic* text", formatting, 1),
        ]

        document = FountainDocument(elements)
        html = self.renderer.render(document)

        # Note: The renderer escapes HTML, so we need to check for escaped content
        assert '<div class="dialogue">' in html

    def test_render_all_element_types(self):
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.ACTION, "John enters the room.", [], 2),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 3),
            FountainElement(ElementType.DIALOGUE, "Hello there!", [], 4),
            FountainElement(ElementType.PARENTHETICAL, "(excited)", [], 5),
            FountainElement(ElementType.TRANSITION, "CUT TO:", [], 6),
            FountainElement(ElementType.NOTE, "[[This is a note]]", [], 7),
        ]

        document = FountainDocument(elements)
        html = self.renderer.render(document)

        # Check that all element types are rendered with appropriate CSS classes
        assert '<div class="scene-heading">' in html
        assert '<div class="action">' in html
        assert '<div class="character">' in html
        assert '<div class="dialogue">' in html
        assert '<div class="parenthetical">' in html
        assert '<div class="transition">' in html
        assert '<div class="note">' in html

    def test_html_escaping(self):
        elements = [
            FountainElement(ElementType.DIALOGUE, 'Text with <tags> & "quotes"', [], 1),
        ]

        document = FountainDocument(elements)
        html = self.renderer.render(document)

        # Check that HTML characters are properly escaped
        assert "&lt;tags&gt;" in html
        assert "&amp;" in html
        assert "&quot;quotes&quot;" in html

    def test_metadata_rendering(self):
        metadata = {
            "title": "My Great Script",
            "author": "Famous Writer",
            "credit": "Written by",
            "source": "Based on true events",
            "draft date": "June 2025",
            "contact": "writer@example.com",
        }

        document = FountainDocument([], metadata)
        html = self.renderer.render(document)

        assert '<h1 class="title">My Great Script</h1>' in html
        assert '<p class="author">by Famous Writer</p>' in html
        assert '<p class="credit">Written by</p>' in html
        assert '<p class="source">Based on true events</p>' in html
        assert '<p class="draft-date">June 2025</p>' in html
        assert '<p class="contact">writer@example.com</p>' in html

    def test_action_line_breaks_rendering(self):
        """Test that line breaks in action elements are converted to <br> tags."""
        # Create an action element with embedded newlines
        action_text = "He stands up.\nHis coffee spills.\nEveryone stares."
        elements = [
            FountainElement(ElementType.ACTION, action_text, [], 1),
        ]

        document = FountainDocument(elements, {})
        html = self.renderer.render(document)

        # Check that newlines are converted to <br> tags
        expected_html = "He stands up.<br>His coffee spills.<br>Everyone stares."
        assert expected_html in html
        assert '<div class="action">He stands up.<br>His coffee spills.<br>Everyone stares.</div>' in html

    def test_action_single_line_rendering(self):
        """Test that single-line action elements render normally."""
        elements = [
            FountainElement(ElementType.ACTION, "She sits down.", [], 1),
        ]

        document = FountainDocument(elements, {})
        html = self.renderer.render(document)

        # Should not have any <br> tags
        assert '<div class="action">She sits down.</div>' in html
        assert "<br>" not in html

    def test_action_tab_rendering(self):
        """Test that tabs in action elements are converted to HTML spaces."""
        # Create action elements with tabs
        action_text_single_tab = "\tIndented with one tab."
        action_text_double_tab = "\t\tIndented with two tabs."

        elements = [
            FountainElement(ElementType.ACTION, action_text_single_tab, [], 1),
            FountainElement(ElementType.ACTION, action_text_double_tab, [], 2),
        ]

        document = FountainDocument(elements, {})
        html = self.renderer.render(document)

        # Check that tabs are converted to &nbsp; sequences
        assert '<div class="action">&nbsp;&nbsp;&nbsp;&nbsp;Indented with one tab.</div>' in html
        assert (
            '<div class="action">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Indented with two tabs.</div>' in html
        )

    def test_scene_number_rendering(self):
        """Test that scene numbers are rendered correctly."""
        metadata = {"scene_number": "1"}
        scene_element = FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1, metadata=metadata)

        document = FountainDocument([scene_element], {})
        html = self.renderer.render(document)

        assert '<div class="scene-heading">INT. HOUSE - DAY <span class="scene-number">#1#</span></div>' in html

    def test_character_extension_rendering(self):
        """Test that character extensions are rendered correctly."""
        metadata = {"extension": "V.O."}
        char_element = FountainElement(ElementType.CHARACTER, "JOHN", [], 1, metadata=metadata)

        document = FountainDocument([char_element], {})
        html = self.renderer.render(document)

        assert '<div class="character">JOHN <span class="character-extension">(V.O.)</span></div>' in html

    def test_bold_italic_rendering(self):
        """Test that bold italic formatting is rendered correctly."""
        formatting = [FormatSpan(8, 22, "bold_italic")]
        dialogue_element = FountainElement(ElementType.DIALOGUE, "This is ***bold italic*** text", formatting, 1)

        document = FountainDocument([dialogue_element], {})
        html = self.renderer.render(document)

        assert "<strong><em>" in html
        assert "</em></strong>" in html

    def test_page_break_rendering(self):
        """Test that page breaks are rendered correctly."""
        page_break_element = FountainElement(ElementType.PAGE_BREAK, "===", [], 1)

        document = FountainDocument([page_break_element], {})
        html = self.renderer.render(document)

        assert '<div class="page-break"></div>' in html

    def test_dual_dialogue_rendering(self):
        """Test that dual dialogue is rendered correctly."""
        left_char = FountainElement(ElementType.CHARACTER, "JOHN", [], 1)
        left_dialogue = [FountainElement(ElementType.DIALOGUE, "Hello!", [], 2)]
        right_char = FountainElement(ElementType.CHARACTER, "SARAH", [], 3)
        right_dialogue = [FountainElement(ElementType.DIALOGUE, "Hi there!", [], 4)]

        dual_element = FountainElement(
            ElementType.DUAL_DIALOGUE,
            "",
            [],
            1,
            metadata={
                "left_character": left_char,
                "left_dialogue": left_dialogue,
                "right_character": right_char,
                "right_dialogue": right_dialogue,
            },
        )

        document = FountainDocument([dual_element], {})
        html = self.renderer.render(document)

        assert '<div class="dual-dialogue">' in html
        assert '<div class="dual-dialogue-left">' in html
        assert '<div class="dual-dialogue-right">' in html
        assert '<div class="character">JOHN</div>' in html
        assert '<div class="character">SARAH</div>' in html
        assert '<div class="dialogue">Hello!</div>' in html
        assert '<div class="dialogue">Hi there!</div>' in html

    def test_centered_text_rendering(self):
        """Test that centered text is rendered correctly."""
        centered_element = FountainElement(ElementType.CENTERED, "This is centered", [], 1)

        document = FountainDocument([centered_element], {})
        html = self.renderer.render(document)

        assert '<div class="centered">This is centered</div>' in html

    def test_enhanced_title_page_rendering(self):
        """Test that enhanced title page fields are rendered correctly."""
        metadata = {
            "title": "My Script",
            "writers": "John & Jane",
            "producer": "Big Studio",
            "copyright": "© 2024",
            "notes": "Line 1\nLine 2",
            "contact": "John Doe\n123 Main St",
        }

        document = FountainDocument([], metadata)
        html = self.renderer.render(document)

        assert '<p class="writers">Writers: John &amp; Jane</p>' in html
        assert '<p class="producer">Producer: Big Studio</p>' in html
        assert '<p class="copyright">© 2024</p>' in html
        assert "<br>" in html  # Multi-line content should have <br> tags

    def test_complex_formatting_rendering(self):
        """Test that complex formatting combinations render correctly."""
        formatting = [
            FormatSpan(0, 15, "bold_italic"),
            FormatSpan(20, 24, "bold"),
            FormatSpan(30, 36, "italic"),
            FormatSpan(42, 52, "underline"),
        ]

        dialogue_element = FountainElement(
            ElementType.DIALOGUE, "***bold italic*** **bold** *italic* _underlined_", formatting, 1
        )

        document = FountainDocument([dialogue_element], {})
        html = self.renderer.render(document)

        assert "<strong><em>" in html  # bold italic
        assert "<strong>" in html  # bold
        assert "<em>" in html  # italic
        assert "<u>" in html  # underline

    def test_extended_title_page_fields(self):
        """Test all extended title page fields (lines 58, 85, 96, 101, 106, 111, 116)."""
        metadata = {
            "title": "Test Script",
            "authors": "John & Jane Doe",  # line 58: not 'author'
            "director": "Famous Director",  # line 85
            "date": "2024-01-01",  # line 96
            "revised": "2024-01-15",  # line 101
            "version": "1.0",  # line 106
            "format": "Screenplay",  # line 111
            "created": "2023-12-01",  # line 116
        }

        document = FountainDocument([], metadata)
        html = self.renderer.render(document)

        assert '<p class="author">by John &amp; Jane Doe</p>' in html
        assert '<p class="director">Director: Famous Director</p>' in html
        assert '<p class="date">2024-01-01</p>' in html
        assert '<p class="revised">Revised: 2024-01-15</p>' in html
        assert '<p class="version">Version: 1.0</p>' in html
        assert '<p class="format">Format: Screenplay</p>' in html
        assert '<p class="created">Created: 2023-12-01</p>' in html

    def test_special_elements_rendering(self):
        """Test rendering of special element types (lines 170, 172, 174)."""
        elements = [
            FountainElement(ElementType.BONEYARD, "/* comment */", [], 1),  # line 170
            FountainElement(ElementType.SECTION, "ACT ONE", [], 2),  # line 172
            FountainElement(ElementType.SYNOPSIS, "What happens", [], 3),  # line 174
        ]

        document = FountainDocument(elements)
        html = self.renderer.render(document)

        assert '<div class="boneyard">/* comment */</div>' in html
        assert '<div class="section">ACT ONE</div>' in html
        assert '<div class="synopsis">What happens</div>' in html

    def test_unknown_element_type(self):
        """Test fallback rendering for unknown types (line 182)."""
        # Create an element with an unknown type by modifying after creation
        element = FountainElement(ElementType.ACTION, "unknown text", [], 1)

        # Simulate an unknown element type by creating a mock enum value
        class MockElementType:
            value = "unknown_type"

        element.type = MockElementType()

        document = FountainDocument([element])
        html = self.renderer.render(document)

        # Should use fallback rendering with the element type as CSS class
        assert '<div class="unknown-type">unknown text</div>' in html

    def test_theme_fallback(self):
        """Test theme system fallback (line 433)."""
        renderer = HTMLRenderer(theme="nonexistent")
        document = FountainDocument([])
        html = renderer.render(document)
        assert "<style>" in html

    def test_dual_dialogue_metadata_none(self):
        """Test dual dialogue with None metadata (line 234)."""
        # Create a dual dialogue element with no metadata
        dual_element = FountainElement(ElementType.DUAL_DIALOGUE, "", [], 1, metadata=None)

        document = FountainDocument([dual_element])
        html = self.renderer.render(document)

        # Should handle None metadata gracefully and return empty string for dual dialogue content
        # The dual dialogue div should not appear since metadata is None
        assert '<div class="dual-dialogue">' not in html

    def test_lyrics_rendering(self):
        """Test that lyrics are rendered correctly with proper styling."""
        lyrics_element = FountainElement(ElementType.LYRICS, "Oh what a beautiful morning", [], 1)

        document = FountainDocument([lyrics_element], {})
        html = self.renderer.render(document)

        assert '<div class="lyrics">Oh what a beautiful morning</div>' in html
        # Check that lyrics CSS is included
        assert ".lyrics {" in html
        assert "text-align: center;" in html
        assert "font-style: italic;" in html

    def test_lyrics_with_formatting_rendering(self):
        """Test that lyrics with formatting render correctly."""
        formatting = [FormatSpan(8, 12, "bold"), FormatSpan(17, 23, "italic")]
        lyrics_element = FountainElement(ElementType.LYRICS, "This is **bold** *italic* lyrics", formatting, 1)

        document = FountainDocument([lyrics_element], {})
        html = self.renderer.render(document)

        assert '<div class="lyrics">' in html
        assert "<strong>" in html
        assert "<em>" in html

    def test_lyrics_empty_rendering(self):
        """Test that lyrics with minimal content render correctly."""
        lyrics_element = FountainElement(ElementType.LYRICS, "a", [], 1)

        document = FountainDocument([lyrics_element], {})
        html = self.renderer.render(document)

        assert '<div class="lyrics">a</div>' in html

    def test_lyrics_multiple_rendering(self):
        """Test rendering multiple lyrics elements."""
        lyrics1 = FountainElement(ElementType.LYRICS, "First line of song", [], 1)
        lyrics2 = FountainElement(ElementType.LYRICS, "Second line of song", [], 2)

        document = FountainDocument([lyrics1, lyrics2], {})
        html = self.renderer.render(document)

        assert '<div class="lyrics">First line of song</div>' in html
        assert '<div class="lyrics">Second line of song</div>' in html

    def test_lyrics_in_complete_scene_rendering(self):
        """Test lyrics rendering in a complete scene context."""
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. THEATER - NIGHT", [], 1),
            FountainElement(ElementType.CHARACTER, "SARAH", [], 2),
            FountainElement(ElementType.PARENTHETICAL, "(singing)", [], 3),
            FountainElement(ElementType.LYRICS, "Oh what a beautiful morning", [], 4),
            FountainElement(ElementType.LYRICS, "Oh what a beautiful day", [], 5),
            FountainElement(ElementType.ACTION, "The audience applauds.", [], 6),
        ]

        document = FountainDocument(elements, {"title": "Musical Test"})
        html = self.renderer.render(document)

        # Check all elements are present
        assert '<div class="scene-heading">INT. THEATER - NIGHT</div>' in html
        assert '<div class="character">SARAH</div>' in html
        assert '<div class="parenthetical">(singing)</div>' in html
        assert '<div class="lyrics">Oh what a beautiful morning</div>' in html
        assert '<div class="lyrics">Oh what a beautiful day</div>' in html
        assert '<div class="action">The audience applauds.</div>' in html

    def test_character_continuation_html_rendering(self):
        """Test that character continuation is rendered correctly in HTML."""
        char_element = FountainElement(ElementType.CHARACTER, "JOHN", [], 1, metadata={"continuation": True})

        document = FountainDocument([char_element], {})
        html = self.renderer.render(document)

        assert '<div class="character">JOHN <span class="character-continuation">(CONT\'D)</span></div>' in html

    def test_character_continuation_vs_extension_html(self):
        """Test that explicit extensions take precedence over auto-continuation."""
        char_with_extension = FountainElement(
            ElementType.CHARACTER, "JOHN", [], 1, metadata={"extension": "V.O.", "continuation": True}
        )

        document = FountainDocument([char_with_extension], {})
        html = self.renderer.render(document)

        # Extension should take precedence
        assert '<span class="character-extension">(V.O.)</span>' in html
        assert '<span class="character-continuation">' not in html

    def test_custom_metadata_fields_in_html(self):
        """Custom metadata fields should appear in HTML output."""
        metadata = {
            "title": "My Script",
            "network": "HBO",
            "revision": "Draft 3",
        }
        document = FountainDocument([], metadata)
        html = self.renderer.render(document)

        assert '<h1 class="title">My Script</h1>' in html
        assert "HBO" in html
        assert "Draft 3" in html


class TestFountainRenderer:
    def setup_method(self):
        self.renderer = FountainRenderer()

    def test_render_simple_document(self):
        """Test basic Fountain rendering."""
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 2),
            FountainElement(ElementType.DIALOGUE, "Hello, world!", [], 3),
        ]
        metadata = {"title": "Test Script", "author": "Test Author"}

        document = FountainDocument(elements, metadata)
        fountain = self.renderer.render(document)

        lines = fountain.split("\n")
        assert "Title: Test Script" in lines
        assert "Author: Test Author" in lines
        assert "INT. HOUSE - DAY" in lines
        assert "JOHN" in lines
        assert "Hello, world!" in lines

    def test_render_title_page(self):
        """Test title page rendering."""
        metadata = {
            "title": "My Great Script",
            "author": "Famous Writer",
            "credit": "Written by",
            "source": "Based on true events",
            "draft date": "June 2025",
            "contact": "writer@example.com",
        }

        document = FountainDocument([], metadata)
        fountain = self.renderer.render(document)

        assert "Title: My Great Script" in fountain
        assert "Author: Famous Writer" in fountain
        assert "Credit: Written by" in fountain
        assert "Source: Based on true events" in fountain
        assert "Draft Date: June 2025" in fountain
        assert "Contact: writer@example.com" in fountain

    def test_render_forced_elements(self):
        """Test forced elements render with proper syntax."""
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "FORCED SCENE", [], 1, metadata={"forced": True}),
            FountainElement(ElementType.ACTION, "forced action", [], 2, metadata={"forced": True}),
            FountainElement(ElementType.CHARACTER, "McCULLY", [], 3, metadata={"forced": True}),
            FountainElement(ElementType.TRANSITION, "FORCED TRANSITION", [], 4, metadata={"forced": True}),
        ]

        document = FountainDocument(elements)
        fountain = self.renderer.render(document)

        assert ".FORCED SCENE" in fountain
        assert "!forced action" in fountain
        assert "@McCULLY" in fountain
        assert ">FORCED TRANSITION" in fountain

    def test_render_character_extensions(self):
        """Test character extensions render correctly."""
        char_element = FountainElement(ElementType.CHARACTER, "JOHN", [], 1, metadata={"extension": "V.O."})

        document = FountainDocument([char_element])
        fountain = self.renderer.render(document)

        assert "JOHN (V.O.)" in fountain

    def test_render_dual_dialogue_character(self):
        """Test dual dialogue character marker."""
        char_element = FountainElement(ElementType.CHARACTER, "SARAH", [], 1, metadata={"dual_dialogue": True})

        document = FountainDocument([char_element])
        fountain = self.renderer.render(document)

        assert "SARAH^" in fountain

    def test_render_scene_numbers(self):
        """Test scene numbers render correctly."""
        scene_element = FountainElement(
            ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1, metadata={"scene_number": "1"}
        )

        document = FountainDocument([scene_element])
        fountain = self.renderer.render(document)

        assert "INT. HOUSE - DAY #1#" in fountain

    def test_render_all_element_types(self):
        """Test all element types render correctly."""
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.ACTION, "John enters the room.", [], 2),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 3),
            FountainElement(ElementType.DIALOGUE, "Hello there!", [], 4),
            FountainElement(ElementType.PARENTHETICAL, "(excited)", [], 5),
            FountainElement(ElementType.TRANSITION, "CUT TO:", [], 6),
            FountainElement(ElementType.NOTE, "[[This is a note]]", [], 7),
            FountainElement(ElementType.BONEYARD, "/* comment */", [], 8),
            FountainElement(ElementType.SECTION, "ACT ONE", [], 9),
            FountainElement(ElementType.SYNOPSIS, "What happens here", [], 10),
            FountainElement(ElementType.PAGE_BREAK, "===", [], 11),
            FountainElement(ElementType.CENTERED, "Centered text", [], 12),
            FountainElement(ElementType.LYRICS, "Oh what a beautiful morning", [], 13),
        ]

        document = FountainDocument(elements)
        fountain = self.renderer.render(document)

        lines = fountain.split("\n")
        assert "INT. HOUSE - DAY" in lines
        assert "John enters the room." in lines
        assert "JOHN" in lines
        assert "Hello there!" in lines
        assert "(excited)" in lines
        assert "CUT TO:" in lines
        assert "[[This is a note]]" in lines
        assert "/* comment */" in lines
        assert "# ACT ONE" in lines
        assert "= What happens here" in lines
        assert "===" in lines
        assert ">Centered text<" in lines
        assert "~Oh what a beautiful morning~" in lines

    def test_render_formatting(self):
        """Test that text with formatting is preserved."""
        formatting = [
            FormatSpan(5, 9, "bold"),
            FormatSpan(14, 20, "italic"),
            FormatSpan(25, 35, "underline"),
            FormatSpan(40, 51, "bold_italic"),
        ]
        dialogue_element = FountainElement(
            ElementType.DIALOGUE, "This **bold** *italic* _underline_ ***bold italic***", formatting, 1
        )

        document = FountainDocument([dialogue_element])
        fountain = self.renderer.render(document)

        # The text should be preserved even if formatting marks aren't perfectly reconstructed
        assert "This **bold** *italic* _underline_ ***bold italic***" in fountain

    def test_render_dual_dialogue_element(self):
        """Test dual dialogue elements are skipped in rendering."""
        dual_element = FountainElement(ElementType.DUAL_DIALOGUE, "", [], 1)

        document = FountainDocument([dual_element])
        fountain = self.renderer.render(document)

        # Dual dialogue elements should not produce output
        lines = [line for line in fountain.split("\n") if line.strip()]
        assert len(lines) == 0

    def test_render_unknown_element_type(self):
        """Test unknown element types fall back to text rendering."""
        # Create an element with an unknown type by modifying after creation
        element = FountainElement(ElementType.ACTION, "unknown text", [], 1)

        # Simulate an unknown element type by creating a mock enum value
        class MockElementType:
            value = "unknown_type"

        element.type = MockElementType()

        document = FountainDocument([element])
        fountain = self.renderer.render(document)

        assert "unknown text" in fountain

    def test_render_complex_character(self):
        """Test character with both extension and dual dialogue."""
        char_element = FountainElement(
            ElementType.CHARACTER,
            "SARAH",
            [],
            1,
            metadata={"extension": "O.S.", "dual_dialogue": True},
        )

        document = FountainDocument([char_element])
        fountain = self.renderer.render(document)

        assert "SARAH (O.S.)^" in fountain

    def test_render_forced_character_with_extension(self):
        """Test forced character with extension."""
        char_element = FountainElement(
            ElementType.CHARACTER,
            "McCULLY",
            [],
            1,
            metadata={"forced": True, "extension": "V.O."},
        )

        document = FountainDocument([char_element])
        fountain = self.renderer.render(document)

        assert "@McCULLY (V.O.)" in fountain

    def test_section_with_level(self):
        """Test section rendering with level metadata."""
        section_element = FountainElement(ElementType.SECTION, "Scene 1", [], 1, metadata={"level": 2})

        document = FountainDocument([section_element])
        fountain = self.renderer.render(document)

        assert "## Scene 1" in fountain

    def test_round_trip_simple(self):
        """Test that simple round-trip parsing preserves content."""
        from fountain.parser import FountainParser

        original_text = """Title: Test Script
Author: Test Author

FADE IN:

INT. HOUSE - DAY

JOHN sits at a table.

JOHN
Hello, world!

FADE OUT."""

        parser = FountainParser()
        document = parser.parse(original_text)
        rendered = self.renderer.render(document)

        # Check key elements are preserved
        assert "Title: Test Script" in rendered
        assert "Author: Test Author" in rendered
        assert "FADE IN:" in rendered
        assert "INT. HOUSE - DAY" in rendered
        assert "JOHN sits at a table." in rendered
        assert "JOHN" in rendered
        assert "Hello, world!" in rendered
        assert "FADE OUT." in rendered

    def test_round_trip_with_lyrics(self):
        """Test that lyrics round-trip correctly."""
        from fountain.parser import FountainParser

        original_text = """SARAH
(singing)
~Oh what a beautiful morning~
~Oh what a beautiful day~

That was lovely!"""

        parser = FountainParser()
        document = parser.parse(original_text)
        rendered = self.renderer.render(document)

        assert "SARAH" in rendered
        assert "(singing)" in rendered
        assert "~Oh what a beautiful morning~" in rendered
        assert "~Oh what a beautiful day~" in rendered
        assert "That was lovely!" in rendered

    def test_empty_document(self):
        """Test rendering an empty document."""
        document = FountainDocument([])
        fountain = self.renderer.render(document)

        # Should be empty or just newlines
        assert fountain.strip() == ""

    def test_metadata_only_document(self):
        """Test rendering a document with only metadata."""
        metadata = {"title": "Just a Title"}
        document = FountainDocument([], metadata)
        fountain = self.renderer.render(document)

        assert "Title: Just a Title" in fountain

    def test_no_formatting(self):
        """Test element with no formatting."""
        element = FountainElement(ElementType.DIALOGUE, "Simple text", [], 1)
        document = FountainDocument([element])
        fountain = self.renderer.render(document)

        assert "Simple text" in fountain

    def test_render_character_continuation(self):
        """Test character continuation rendering."""
        char_element = FountainElement(ElementType.CHARACTER, "JOHN", [], 1, metadata={"continuation": True})

        document = FountainDocument([char_element])
        fountain = self.renderer.render(document)

        assert "JOHN (CONT'D)" in fountain

    def test_custom_metadata_fields_in_fountain(self):
        """Custom metadata fields should appear in Fountain round-trip output."""
        metadata = {
            "title": "My Script",
            "network": "HBO",
            "revision": "Draft 3",
        }
        document = FountainDocument([], metadata)
        fountain = self.renderer.render(document)

        assert "Title: My Script" in fountain
        assert "Network: HBO" in fountain
        assert "Revision: Draft 3" in fountain
