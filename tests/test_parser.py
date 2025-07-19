"""
Tests for the Fountain parser.
"""

import pytest
from pathlib import Path
from fountain.parser import FountainParser
from fountain.elements import ElementType


class TestFountainParser:
    
    def setup_method(self):
        self.parser = FountainParser()
    
    def test_parse_simple_text(self):
        text = """Title: Test Script
Author: Test Author

FADE IN:

INT. HOUSE - DAY

JOHN sits at a table.

JOHN
Hello, world!

FADE OUT."""
        
        document = self.parser.parse(text)
        
        # Check metadata
        assert document.metadata['title'] == 'Test Script'
        assert document.metadata['author'] == 'Test Author'
        
        # Check elements
        assert len(document.elements) > 0
        
        # Find specific elements
        scene_headings = [el for el in document.elements if el.type == ElementType.SCENE_HEADING]
        characters = [el for el in document.elements if el.type == ElementType.CHARACTER]
        dialogue = [el for el in document.elements if el.type == ElementType.DIALOGUE]
        transitions = [el for el in document.elements if el.type == ElementType.TRANSITION]
        
        assert len(scene_headings) == 1
        assert scene_headings[0].text == 'INT. HOUSE - DAY'
        
        assert len(characters) == 1
        assert characters[0].text == 'JOHN'
        
        assert len(dialogue) == 1
        assert dialogue[0].text == 'Hello, world!'
        
        assert len(transitions) == 2
        assert transitions[0].text == 'FADE IN:'
        assert transitions[1].text == 'FADE OUT.'
    
    def test_parse_file(self):
        fixture_path = Path(__file__).parent / 'fixtures' / 'simple_script.fountain'
        document = self.parser.parse_file(str(fixture_path))
        
        # Check metadata
        assert document.metadata['title'] == 'A Simple Test Script'
        assert document.metadata['author'] == 'Mason Egger'
        
        # Check that we have various element types
        element_types = {el.type for el in document.elements}
        assert ElementType.SCENE_HEADING in element_types
        assert ElementType.CHARACTER in element_types
        assert ElementType.DIALOGUE in element_types
        assert ElementType.ACTION in element_types
        assert ElementType.PARENTHETICAL in element_types
        assert ElementType.TRANSITION in element_types
    
    def test_character_detection(self):
        text = """JOHN
Hello there.

SARAH
(whispering)
Hi back."""
        
        document = self.parser.parse(text)
        characters = document.get_characters()
        
        assert 'JOHN' in characters
        assert 'SARAH' in characters
        assert len(characters) == 2
    
    def test_formatting_detection(self):
        text = """JOHN
This is **bold** and *italic* and _underlined_ text."""
        
        document = self.parser.parse(text)
        dialogue_elements = [el for el in document.elements if el.type == ElementType.DIALOGUE]
        
        assert len(dialogue_elements) == 1
        dialogue = dialogue_elements[0]
        
        # Check that formatting spans were detected
        assert len(dialogue.formatting) == 3
        
        # Check formatting types
        format_types = {span.format_type for span in dialogue.formatting}
        assert 'bold' in format_types
        assert 'italic' in format_types
        assert 'underline' in format_types
    
    def test_forced_elements(self):
        text = """.FORCED SCENE HEADING

>FORCED TRANSITION"""
        
        document = self.parser.parse(text)
        
        scene_headings = [el for el in document.elements if el.type == ElementType.SCENE_HEADING]
        transitions = [el for el in document.elements if el.type == ElementType.TRANSITION]
        
        assert len(scene_headings) == 1
        assert scene_headings[0].text == 'FORCED SCENE HEADING'
        
        assert len(transitions) == 1
        assert transitions[0].text == 'FORCED TRANSITION'
    
    def test_document_statistics(self):
        text = """Title: Test

INT. HOUSE - DAY

JOHN
Hello.

SARAH
Hi.

EXT. PARK - DAY

JOHN
Goodbye."""
        
        document = self.parser.parse(text)
        stats = document.get_statistics()
        
        assert stats['characters'] == 2
        assert stats['scenes'] == 2
        assert stats['scene_heading_count'] == 2
        assert stats['character_count'] == 3  # JOHN appears twice
        assert stats['dialogue_count'] == 3
    
    def test_action_after_dialogue(self):
        """Test that action elements following dialogue are correctly classified."""
        text = """JOHN
Hello, Sarah!

SARAH
Hi there!

They hug warmly.

JOHN
How are you?

She smiles and sits down."""
        
        document = self.parser.parse(text)
        elements = document.elements
        
        # Should have: CHARACTER, DIALOGUE, CHARACTER, DIALOGUE, ACTION, CHARACTER, DIALOGUE, ACTION
        assert len(elements) == 8
        
        # Check sequence
        assert elements[0].type == ElementType.CHARACTER
        assert elements[0].text == 'JOHN'
        
        assert elements[1].type == ElementType.DIALOGUE  
        assert elements[1].text == 'Hello, Sarah!'
        
        assert elements[2].type == ElementType.CHARACTER
        assert elements[2].text == 'SARAH'
        
        assert elements[3].type == ElementType.DIALOGUE
        assert elements[3].text == 'Hi there!'
        
        # This should be ACTION, not DIALOGUE
        assert elements[4].type == ElementType.ACTION
        assert elements[4].text == 'They hug warmly.'
        
        assert elements[5].type == ElementType.CHARACTER
        assert elements[5].text == 'JOHN'
        
        assert elements[6].type == ElementType.DIALOGUE
        assert elements[6].text == 'How are you?'
        
        # This should also be ACTION, not DIALOGUE  
        assert elements[7].type == ElementType.ACTION
        assert elements[7].text == 'She smiles and sits down.'
    
    def test_multiline_action_after_dialogue(self):
        """Test that multi-line action elements are parsed correctly."""
        text = """JOHN
I have great news!

He stands up excitedly.
His coffee cup falls to the floor.
The liquid splashes everywhere."""
        
        document = self.parser.parse(text)
        elements = document.elements
        
        # Should have: CHARACTER, DIALOGUE, ACTION, ACTION, ACTION
        assert len(elements) == 5
        
        assert elements[0].type == ElementType.CHARACTER
        assert elements[1].type == ElementType.DIALOGUE
        
        # Each line should be a separate ACTION element
        assert elements[2].type == ElementType.ACTION
        assert elements[2].text == 'He stands up excitedly.'
        
        assert elements[3].type == ElementType.ACTION
        assert elements[3].text == 'His coffee cup falls to the floor.'
        
        assert elements[4].type == ElementType.ACTION
        assert elements[4].text == 'The liquid splashes everywhere.'
    
    def test_multiline_dialogue_without_breaks(self):
        """Test that multi-line dialogue without line breaks is correctly classified."""
        text = """JOHN
Hello there, Sarah. How are you
doing today? I hope everything
is going well for you."""
        
        document = self.parser.parse(text)
        elements = document.elements
        
        # Should have: CHARACTER, DIALOGUE, DIALOGUE, DIALOGUE
        # All continuation lines should be DIALOGUE, not ACTION
        assert len(elements) == 4
        
        assert elements[0].type == ElementType.CHARACTER
        assert elements[0].text == 'JOHN'
        
        # These should all be DIALOGUE elements, not ACTION
        assert elements[1].type == ElementType.DIALOGUE
        assert elements[1].text == 'Hello there, Sarah. How are you'
        
        assert elements[2].type == ElementType.DIALOGUE  
        assert elements[2].text == 'doing today? I hope everything'
        
        assert elements[3].type == ElementType.DIALOGUE
        assert elements[3].text == 'is going well for you.'
    
    def test_dialogue_with_blank_line_separation(self):
        """Test that action after dialogue with blank line separation is correctly classified."""
        text = """JOHN
Hello there!

He walks away slowly.

SARAH
Wait up!"""
        
        document = self.parser.parse(text)
        elements = document.elements
        
        # Should have: CHARACTER, DIALOGUE, ACTION, CHARACTER, DIALOGUE
        assert len(elements) == 5
        
        assert elements[0].type == ElementType.CHARACTER
        assert elements[0].text == 'JOHN'
        
        assert elements[1].type == ElementType.DIALOGUE
        assert elements[1].text == 'Hello there!'
        
        # This should be ACTION because of blank line separation
        assert elements[2].type == ElementType.ACTION
        assert elements[2].text == 'He walks away slowly.'
        
        assert elements[3].type == ElementType.CHARACTER
        assert elements[3].text == 'SARAH'
        
        assert elements[4].type == ElementType.DIALOGUE
        assert elements[4].text == 'Wait up!'
    
    def test_forced_action_syntax(self):
        """Test that forced action syntax with ! prefix works correctly."""
        text = """JOHN
Hello!

!This is definitely action.

SARAH
Hi there!

!Even after dialogue, this is forced action."""
        
        document = self.parser.parse(text)
        elements = document.elements
        
        # Should have: CHARACTER, DIALOGUE, ACTION, CHARACTER, DIALOGUE, ACTION
        assert len(elements) == 6
        
        assert elements[0].type == ElementType.CHARACTER
        assert elements[1].type == ElementType.DIALOGUE
        
        # Forced action
        assert elements[2].type == ElementType.ACTION
        assert elements[2].text == 'This is definitely action.'
        
        assert elements[3].type == ElementType.CHARACTER
        assert elements[4].type == ElementType.DIALOGUE
        
        # Another forced action
        assert elements[5].type == ElementType.ACTION
        assert elements[5].text == 'Even after dialogue, this is forced action.'
    
    def test_action_tab_preservation(self):
        """Test that leading tabs in action text are preserved."""
        text = """JOHN
Hello!

\tThis action is indented with a tab.
\t\tThis action is indented with two tabs.
Regular action without tabs."""
        
        document = self.parser.parse(text)
        elements = document.elements
        
        # Should have: CHARACTER, DIALOGUE, ACTION, ACTION, ACTION
        assert len(elements) == 5
        
        assert elements[0].type == ElementType.CHARACTER
        assert elements[1].type == ElementType.DIALOGUE
        
        # Check tab preservation
        assert elements[2].type == ElementType.ACTION
        assert elements[2].text == '\tThis action is indented with a tab.'
        
        assert elements[3].type == ElementType.ACTION  
        assert elements[3].text == '\t\tThis action is indented with two tabs.'
        
        assert elements[4].type == ElementType.ACTION
        assert elements[4].text == 'Regular action without tabs.'
    
    def test_dual_dialogue(self):
        """Test dual dialogue parsing with ^ syntax."""
        text = """JOHN
I can't believe it!

SARAH^
Neither can I!"""
        
        document = self.parser.parse(text)
        
        # Should have one dual dialogue element
        dual_elements = [el for el in document.elements if el.type == ElementType.DUAL_DIALOGUE]
        assert len(dual_elements) == 1
        
        dual_element = dual_elements[0]
        assert dual_element.metadata['left_character'].text == 'JOHN'
        assert dual_element.metadata['right_character'].text == 'SARAH'
        assert len(dual_element.metadata['left_dialogue']) == 1
        assert len(dual_element.metadata['right_dialogue']) == 1
        assert dual_element.metadata['left_dialogue'][0].text == "I can't believe it!"
        assert dual_element.metadata['right_dialogue'][0].text == "Neither can I!"
    
    def test_forced_character_names(self):
        """Test forced character names with @ syntax."""
        text = """@McCULLY
Hello there."""
        
        document = self.parser.parse(text)
        
        character_elements = [el for el in document.elements if el.type == ElementType.CHARACTER]
        assert len(character_elements) == 1
        assert character_elements[0].text == 'McCULLY'
        assert character_elements[0].metadata.get('forced') is True
    
    def test_character_extensions(self):
        """Test character extensions like (V.O.) and (O.S.)."""
        text = """JOHN (V.O.)
You can hear my voice.

SARAH (O.S.)^
I'm off screen too!"""
        
        document = self.parser.parse(text)
        
        # Should have dual dialogue since SARAH has ^
        dual_elements = [el for el in document.elements if el.type == ElementType.DUAL_DIALOGUE]
        assert len(dual_elements) == 1
        
        # Check extensions
        dual = dual_elements[0]
        left_char = dual.metadata['left_character']
        right_char = dual.metadata['right_character']
        
        assert left_char.text == 'JOHN'
        assert left_char.metadata.get('extension') == 'V.O.'
        
        assert right_char.text == 'SARAH'
        assert right_char.metadata.get('extension') == 'O.S.'
        assert right_char.metadata.get('dual_dialogue') is True
    
    def test_scene_numbers(self):
        """Test scene number parsing with #1# syntax."""
        text = """INT. HOUSE - DAY #1#

Some action happens.

EXT. GARDEN - NIGHT #2A#

More action."""
        
        document = self.parser.parse(text)
        
        scene_elements = [el for el in document.elements if el.type == ElementType.SCENE_HEADING]
        assert len(scene_elements) == 2
        
        assert scene_elements[0].text == 'INT. HOUSE - DAY'
        assert scene_elements[0].metadata.get('scene_number') == '1'
        
        assert scene_elements[1].text == 'EXT. GARDEN - NIGHT'
        assert scene_elements[1].metadata.get('scene_number') == '2A'
    
    def test_multi_line_boneyard(self):
        """Test multi-line boneyard comments."""
        text = """JOHN
Hello there.

/*
This is a multi-line comment
that should be completely ignored
*/

SARAH
Hi back."""
        
        document = self.parser.parse(text)
        
        # Should only have character and dialogue elements, no boneyard
        element_types = [el.type for el in document.elements]
        assert ElementType.BONEYARD not in element_types
        
        characters = [el for el in document.elements if el.type == ElementType.CHARACTER]
        assert len(characters) == 2
        assert characters[0].text == 'JOHN'
        assert characters[1].text == 'SARAH'
    
    def test_notes_parsing(self):
        """Test parsing of [[note]] syntax."""
        text = """[[This is a standalone note]]

JOHN
Hello there!"""
        
        document = self.parser.parse(text)
        
        note_elements = [el for el in document.elements if el.type == ElementType.NOTE]
        assert len(note_elements) == 1
        assert note_elements[0].text == '[[This is a standalone note]]'
    
    def test_bold_italic_combination(self):
        """Test ***bold italic*** formatting."""
        text = """JOHN
This is ***bold and italic*** text."""
        
        document = self.parser.parse(text)
        
        dialogue_elements = [el for el in document.elements if el.type == ElementType.DIALOGUE]
        assert len(dialogue_elements) == 1
        
        dialogue = dialogue_elements[0]
        assert len(dialogue.formatting) == 1
        assert dialogue.formatting[0].format_type == 'bold_italic'
    
    def test_page_breaks(self):
        """Test page break parsing with === syntax."""
        text = """JOHN
Hello.

===

SARAH
Hi there."""
        
        document = self.parser.parse(text)
        
        page_break_elements = [el for el in document.elements if el.type == ElementType.PAGE_BREAK]
        assert len(page_break_elements) == 1
        assert page_break_elements[0].text == '==='
    
    def test_forced_scene_heading_with_number(self):
        """Test forced scene heading with scene number."""
        text = """.my scene heading #5#"""
        
        document = self.parser.parse(text)
        
        scene_elements = [el for el in document.elements if el.type == ElementType.SCENE_HEADING]
        assert len(scene_elements) == 1
        assert scene_elements[0].text == 'my scene heading'
        assert scene_elements[0].metadata.get('scene_number') == '5'
    
    def test_centered_text(self):
        """Test centered text parsing with >text< syntax."""
        text = """>This text should be centered<

JOHN
Hello."""
        
        document = self.parser.parse(text)
        
        centered_elements = [el for el in document.elements if el.type == ElementType.CENTERED]
        assert len(centered_elements) == 1
        assert centered_elements[0].text == 'This text should be centered'
    
    def test_enhanced_title_page(self):
        """Test enhanced title page with more fields and multi-line support."""
        text = """Title: My Great Script
Author: John Doe
Writers: John Doe and Jane Smith
Producer: Big Studio Productions
Director: Famous Director
Copyright: © 2024 John Doe. All rights reserved.
Notes: This is a note that spans
    multiple lines with additional
    information about the script.
Contact: John Doe
    123 Main Street
    Hollywood, CA 90210
    (555) 123-4567

FADE IN:

INT. HOUSE - DAY

Some action."""
        
        document = self.parser.parse(text)
        
        # Check that all new fields are parsed
        assert document.metadata.get('writers') == 'John Doe and Jane Smith'
        assert document.metadata.get('producer') == 'Big Studio Productions'
        assert document.metadata.get('director') == 'Famous Director'
        assert document.metadata.get('copyright') == '© 2024 John Doe. All rights reserved.'
        
        # Check multi-line support
        assert 'multiple lines' in document.metadata.get('notes', '')
        assert 'Hollywood, CA' in document.metadata.get('contact', '')
    
    def test_element_precedence(self):
        """Test that element precedence works correctly for ambiguous cases."""
        text = """>FADE OUT<

>CUT TO:

.INT. HOUSE - DAY

@character

==="""
        
        document = self.parser.parse(text)
        
        element_types = [el.type for el in document.elements]
        
        # Should detect: CENTERED, TRANSITION, SCENE_HEADING, CHARACTER (fallback to action), PAGE_BREAK
        assert ElementType.CENTERED in element_types
        assert ElementType.TRANSITION in element_types
        assert ElementType.SCENE_HEADING in element_types
        assert ElementType.PAGE_BREAK in element_types
    
    def test_complex_formatting_combinations(self):
        """Test complex formatting combinations."""
        text = """JOHN
This has ***bold italic***, **bold**, *italic*, and _underlined_ text all together."""
        
        document = self.parser.parse(text)
        
        dialogue_elements = [el for el in document.elements if el.type == ElementType.DIALOGUE]
        assert len(dialogue_elements) == 1
        
        dialogue = dialogue_elements[0]
        format_types = [span.format_type for span in dialogue.formatting]
        
        # Should have all different types
        assert 'bold_italic' in format_types
        assert 'bold' in format_types
        assert 'italic' in format_types
        assert 'underline' in format_types
    
    def test_dialogue_continuation_edge_cases(self):
        """Test dialogue continuation with edge cases."""
        text = """JOHN
First line of dialogue
Second line without break

This should be action after blank line.

SARAH
Her dialogue
Continued dialogue

!This is forced action even after dialogue."""
        
        document = self.parser.parse(text)
        
        elements = [(el.type, el.text) for el in document.elements]
        
        # Should be: CHARACTER, DIALOGUE, DIALOGUE, ACTION, CHARACTER, DIALOGUE, DIALOGUE, ACTION
        expected_types = [
            ElementType.CHARACTER,  # JOHN
            ElementType.DIALOGUE,   # First line
            ElementType.DIALOGUE,   # Second line
            ElementType.ACTION,     # This should be action
            ElementType.CHARACTER,  # SARAH
            ElementType.DIALOGUE,   # Her dialogue
            ElementType.DIALOGUE,   # Continued dialogue
            ElementType.ACTION      # Forced action
        ]
        
        actual_types = [el.type for el in document.elements]
        assert actual_types == expected_types