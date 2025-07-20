#!/usr/bin/env python3
"""Test all code examples from the quickstart documentation."""

import json
import os

import pytest

from fountain import ElementType, FountainParser


class TestQuickstartExamples:
    """Test suite for all quickstart documentation examples."""

    @pytest.fixture
    def sample_screenplay_text(self):
        """The sample screenplay used in quickstart docs."""
        return """
    Title: The Coffee Shop Connection
    Author: Jane Doe
    Draft date: 2024-01-15
    
    FADE IN:
    
    INT. COFFEE SHOP - DAY
    
    A bustling neighborhood COFFEE SHOP. The afternoon sun streams through 
    large windows. Business people and students hunker over laptops.
    
    ALICE (28), creative but frazzled, sits at a corner table, staring at 
    her laptop screen. She sighs and rubs her temples.
    
    ALICE
    (muttering to herself)
    Come on, inspiration... where are you?
    
    The door chimes. BOB (30s), confident but approachable, enters and 
    scans the crowded shop. The only empty seat is across from Alice.
    
    BOB
    Excuse me, is this seat taken?
    
    ALICE
    (barely looking up)
    No, go ahead.
    
    Bob sits. They work in silence. Then:
    
    BOB
    Writer's block?
    
    ALICE
    (surprised)
    How did you--?
    
    BOB
    The temple rubbing. Dead giveaway.
    (extends hand)
    Bob. Fellow sufferer.
    
    ALICE
    (smiling despite herself)
    Alice. What's your poison? Novel? 
    Screenplay?
    
    BOB
    Startup pitch deck.
    
    ALICE
    (laughing)
    That's even worse!
    
    CUT TO:
    
    INT. COFFEE SHOP - LATER
    
    Alice and Bob's laptops are pushed aside. Coffee cups multiply.
    They're deep in animated conversation.
    
    ALICE
    So your app matches writers with 
    coffee shops based on their 
    creative energy?
    
    BOB
    Exactly! And the algorithm considers 
    noise levels, wifi speed, coffee 
    quality...
    
    ALICE
    (excited)
    You could add a "writer's block 
    breaker" feature!
    
    [[Note: This is where their collaboration begins]]
    
    FADE OUT.
    """

    @pytest.fixture
    def parsed_document(self, sample_screenplay_text):
        """Parse the sample screenplay."""
        parser = FountainParser()
        return parser.parse(sample_screenplay_text)

    def test_basic_parsing(self, sample_screenplay_text):
        """Test the basic parsing example from quickstart."""
        # Parse the screenplay
        parser = FountainParser()
        document = parser.parse(sample_screenplay_text)

        # Verify successful parsing
        assert len(document.elements) > 0
        assert document is not None

    def test_script_metadata(self, parsed_document):
        """Test accessing script metadata."""
        # Access title page metadata
        metadata = parsed_document.metadata

        assert metadata.get("title") == "The Coffee Shop Connection"
        assert metadata.get("author") == "Jane Doe"
        assert metadata.get("draft date") == "2024-01-15"

    def test_character_extraction(self, parsed_document):
        """Test extracting characters from the script."""
        # Extract and display all characters
        characters = parsed_document.get_characters()

        assert "ALICE" in characters
        assert "BOB" in characters
        assert len(characters) == 2

    def test_scene_extraction(self, parsed_document):
        """Test extracting scenes from the script."""
        # Get all scene headings
        scenes = parsed_document.get_scenes()

        assert len(scenes) == 2
        assert "INT. COFFEE SHOP - DAY" in scenes
        assert "INT. COFFEE SHOP - LATER" in scenes

    def test_statistics(self, parsed_document):
        """Test getting script statistics."""
        # Get comprehensive statistics
        stats = parsed_document.get_statistics()

        assert stats.get("dialogue_count", 0) > 0
        assert stats.get("action_count", 0) > 0
        assert stats.get("scene_heading_count", 0) == 2
        assert stats.get("character_count", 0) > 0

    def test_element_iteration(self, parsed_document):
        """Test iterating through elements and accessing properties."""
        # Find all dialogue from ALICE
        alice_dialogue = []
        alice_speaking = False

        for element in parsed_document.elements:
            if element.type == ElementType.CHARACTER and "ALICE" in element.text:
                alice_speaking = True
            elif element.type == ElementType.DIALOGUE and alice_speaking:
                alice_dialogue.append(element.text)
            elif element.type not in [ElementType.DIALOGUE, ElementType.PARENTHETICAL]:
                alice_speaking = False

        assert len(alice_dialogue) > 0
        assert any("inspiration" in d for d in alice_dialogue)
        assert any("poison" in d for d in alice_dialogue)

    def test_character_introductions(self, parsed_document):
        """Test finding character introductions in action lines."""
        characters = parsed_document.get_characters()
        introductions = []

        for element in parsed_document.elements:
            if element.type == ElementType.ACTION:
                if "(" in element.text and any(char in element.text for char in characters):
                    introductions.append(element.text)

        assert len(introductions) > 0
        assert any("ALICE (28)" in intro for intro in introductions)
        assert any("BOB (30s)" in intro for intro in introductions)

    def test_parentheticals(self, parsed_document):
        """Test extracting parentheticals (stage directions)."""
        parentheticals = []

        for element in parsed_document.elements:
            if element.type == ElementType.PARENTHETICAL:
                parentheticals.append(element.text)

        assert len(parentheticals) > 0
        assert any("muttering to herself" in p for p in parentheticals)
        assert any("extends hand" in p for p in parentheticals)

    def test_html_rendering(self, parsed_document):
        """Test HTML rendering functionality."""
        # Generate HTML with screenplay formatting
        html_output = parsed_document.to_html()

        assert len(html_output) > 0
        assert "<div" in html_output.lower()  # HTML format contains divs but not full HTML doc
        assert "screenplay" in html_output.lower()
        assert "ALICE" in html_output
        assert "BOB" in html_output

    def test_file_parsing(self, tmp_path):
        """Test parsing from files."""
        # Create a temporary fountain file
        fountain_file = tmp_path / "test.fountain"
        fountain_file.write_text("""
Title: Test Script
Author: Test Author

FADE IN:

INT. TEST LOCATION - DAY

This is a test script.

FADE OUT.
""")

        # Parse directly from a file
        parser = FountainParser()
        document = parser.parse_file(str(fountain_file))

        assert len(document.elements) > 0
        assert document.metadata.get("title") == "Test Script"
        assert document.metadata.get("author") == "Test Author"

    def test_safe_parse_file_error_handling(self, tmp_path):
        """Test error handling in file parsing."""

        def safe_parse_file(filepath):
            """Safely parse a Fountain file with error handling."""
            parser = FountainParser()

            # Check if file exists
            if not os.path.exists(filepath):
                print(f"Error: File '{filepath}' not found")
                return None

            try:
                # Attempt to parse the file
                document = parser.parse_file(filepath)
                print(f"Successfully parsed: {filepath}")

                # Verify we got elements
                if not document.elements:
                    print("Warning: Document appears to be empty")

                return document

            except UnicodeDecodeError:
                print(f"Error: File encoding issue. Ensure '{filepath}' is UTF-8 encoded")
                return None
            except Exception as e:
                print(f"Error parsing file: {e}")
                return None

        # Test with non-existent file
        doc = safe_parse_file("non_existent.fountain")
        assert doc is None

        # Test with valid file
        valid_file = tmp_path / "valid.fountain"
        valid_file.write_text("INT. TEST - DAY\n\nTest content.")

        doc = safe_parse_file(str(valid_file))
        assert doc is not None
        assert len(doc.elements) > 0

    def test_output_formats(self, parsed_document):
        """Test different output formats."""
        # HTML for web display
        html = parsed_document.to_html()
        assert len(html) > 0

        # JSON for data interchange
        json_data = parsed_document.to_json()
        assert len(json_data) > 0

        # Verify JSON is valid
        json_parsed = json.loads(json_data)
        assert "elements" in json_parsed
        assert len(json_parsed["elements"]) > 0

        # Python dictionary for further processing
        dict_data = parsed_document.to_dict()
        assert "elements" in dict_data
        assert "metadata" in dict_data
        assert len(dict_data["elements"]) > 0

    def test_complete_analyzer(self, tmp_path):
        """Test the complete script analyzer example."""

        def analyze_screenplay(filepath):
            """Analyze a screenplay and generate a report."""
            parser = FountainParser()

            try:
                # Parse the screenplay
                document = parser.parse_file(filepath)

                # Create analysis report
                report = {
                    "title": document.metadata.get("title", "Untitled"),
                    "author": document.metadata.get("author", "Unknown"),
                    "statistics": document.get_statistics(),
                    "characters": sorted(document.get_characters()),
                    "scenes": document.get_scenes(),
                    "scene_count": len(document.get_scenes()),
                    "page_estimate": document.get_statistics().get("dialogue", 0) // 20,
                }

                # Generate HTML version
                html_path = filepath.replace(".fountain", ".html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(document.to_html())

                # Save analysis report
                report_path = filepath.replace(".fountain", "_analysis.json")
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2)

                return report

            except Exception as e:
                print(f"Error analyzing screenplay: {e}")
                return None

        # Create test screenplay
        test_script = tmp_path / "test_analysis.fountain"
        test_script.write_text("""Title: Test Analysis Script
Author: Test Analyzer

INT. OFFICE - DAY

MANAGER
We need to test this analyzer.

DEVELOPER
I'm on it!

CUT TO:

INT. OFFICE - LATER

The tests are complete.

FADE OUT.
""")

        # Use the analyzer
        report = analyze_screenplay(str(test_script))
        assert report is not None

        assert report["title"] == "Test Analysis Script"
        assert report["author"] == "Test Analyzer"
        assert report["scene_count"] == 2
        assert "MANAGER" in report["characters"]
        assert "DEVELOPER" in report["characters"]

        # Verify files were created
        assert (tmp_path / "test_analysis.html").exists()
        assert (tmp_path / "test_analysis_analysis.json").exists()
