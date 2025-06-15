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