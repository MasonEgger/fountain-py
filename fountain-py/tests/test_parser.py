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