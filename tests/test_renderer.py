"""
Tests for the HTML renderer.
"""

from fountain.renderer import HTMLRenderer
from fountain.document import FountainDocument
from fountain.elements import FountainElement, ElementType, FormatSpan


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
        assert '<style>' in html  # CSS should be included
    
    def test_render_with_formatting(self):
        formatting = [
            FormatSpan(5, 9, 'bold'),
            FormatSpan(10, 16, 'italic'),
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
        assert '&lt;tags&gt;' in html
        assert '&amp;' in html
        assert '&quot;quotes&quot;' in html
    
    def test_metadata_rendering(self):
        metadata = {
            "title": "My Great Script",
            "author": "Famous Writer",
            "credit": "Written by",
            "source": "Based on true events",
            "draft date": "June 2025",
            "contact": "writer@example.com"
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
        expected_html = 'He stands up.<br>His coffee spills.<br>Everyone stares.'
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
        assert '<br>' not in html
    
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
        assert '<div class="action">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Indented with two tabs.</div>' in html
    
    def test_scene_number_rendering(self):
        """Test that scene numbers are rendered correctly."""
        metadata = {'scene_number': '1'}
        scene_element = FountainElement(
            ElementType.SCENE_HEADING, 
            "INT. HOUSE - DAY", 
            [], 
            1, 
            metadata=metadata
        )
        
        document = FountainDocument([scene_element], {})
        html = self.renderer.render(document)
        
        assert '<div class="scene-heading">INT. HOUSE - DAY <span class="scene-number">#1#</span></div>' in html
    
    def test_character_extension_rendering(self):
        """Test that character extensions are rendered correctly."""
        metadata = {'extension': 'V.O.'}
        char_element = FountainElement(
            ElementType.CHARACTER, 
            "JOHN", 
            [], 
            1, 
            metadata=metadata
        )
        
        document = FountainDocument([char_element], {})
        html = self.renderer.render(document)
        
        assert '<div class="character">JOHN <span class="character-extension">(V.O.)</span></div>' in html
    
    def test_bold_italic_rendering(self):
        """Test that bold italic formatting is rendered correctly."""
        formatting = [FormatSpan(8, 22, 'bold_italic')]
        dialogue_element = FountainElement(
            ElementType.DIALOGUE,
            "This is ***bold italic*** text",
            formatting,
            1
        )
        
        document = FountainDocument([dialogue_element], {})
        html = self.renderer.render(document)
        
        assert '<strong><em>' in html
        assert '</em></strong>' in html
    
    def test_page_break_rendering(self):
        """Test that page breaks are rendered correctly."""
        page_break_element = FountainElement(
            ElementType.PAGE_BREAK,
            "===",
            [],
            1
        )
        
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
                'left_character': left_char,
                'left_dialogue': left_dialogue,
                'right_character': right_char,
                'right_dialogue': right_dialogue
            }
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
        centered_element = FountainElement(
            ElementType.CENTERED,
            "This is centered",
            [],
            1
        )
        
        document = FountainDocument([centered_element], {})
        html = self.renderer.render(document)
        
        assert '<div class="centered">This is centered</div>' in html
    
    def test_enhanced_title_page_rendering(self):
        """Test that enhanced title page fields are rendered correctly."""
        metadata = {
            'title': 'My Script',
            'writers': 'John & Jane',
            'producer': 'Big Studio',
            'copyright': '© 2024',
            'notes': 'Line 1\nLine 2',
            'contact': 'John Doe\n123 Main St'
        }
        
        document = FountainDocument([], metadata)
        html = self.renderer.render(document)
        
        assert '<p class="writers">Writers: John &amp; Jane</p>' in html
        assert '<p class="producer">Producer: Big Studio</p>' in html
        assert '<p class="copyright">© 2024</p>' in html
        assert '<br>' in html  # Multi-line content should have <br> tags
    
    def test_complex_formatting_rendering(self):
        """Test that complex formatting combinations render correctly."""
        formatting = [
            FormatSpan(0, 15, 'bold_italic'),
            FormatSpan(20, 24, 'bold'),
            FormatSpan(30, 36, 'italic'),
            FormatSpan(42, 52, 'underline')
        ]
        
        dialogue_element = FountainElement(
            ElementType.DIALOGUE,
            "***bold italic*** **bold** *italic* _underlined_",
            formatting,
            1
        )
        
        document = FountainDocument([dialogue_element], {})
        html = self.renderer.render(document)
        
        assert '<strong><em>' in html  # bold italic
        assert '<strong>' in html      # bold
        assert '<em>' in html          # italic  
        assert '<u>' in html           # underline