# Fountain-Py Test Coverage Gap Analysis and Fix Plan (Updated)

## Executive Summary
Current test coverage stands at 94% with 29 uncovered lines across 4 modules. This updated plan identifies all missing test cases based on the latest codebase and provides a comprehensive strategy to achieve 100% coverage.

## Current Coverage Analysis (Updated)

### Module-by-Module Coverage
- `__init__.py`: 100% (4/4 statements)
- `elements.py`: 100% (32/32 statements) ✅ **COMPLETE**
- `parser.py`: 95% (227/239 statements)
- `renderer.py`: 91% (139/152 statements)
- `document.py`: 89% (32/36 statements)

### Uncovered Lines by Module

#### src/fountain/document.py (Missing: 55, 84-87)
- **Line 55**: The `name[:-1].strip()` path for characters ending with '^'
- **Lines 84-87**: The `to_html()` method entirely

#### src/fountain/elements.py ✅ **COMPLETE**
- All lines now covered

#### src/fountain/parser.py (Missing: 121-122, 130, 173, 194, 209, 252-253, 262-263, 441, 516)
- **Lines 121-122**: Empty line continuation in title page parsing
- **Line 130**: While loop continuation for finding next non-empty line
- **Line 173**: Setting metadata value when current key exists but is empty
- **Line 194**: Return None for empty lines in `_parse_line`
- **Line 209**: Single-line boneyard element creation
- **Lines 252-253**: Section element creation and formatting
- **Lines 262-263**: Synopsis element creation and formatting
- **Line 441**: Return False in `_is_dialogue_line` when no elements exist
- **Line 516**: Break condition in dual dialogue processing

#### src/fountain/renderer.py (Missing: 58, 85, 96, 101, 106, 111, 116, 170, 172, 174, 182, 234, 433)
- **Line 58**: Rendering 'authors' when no 'author' field exists
- **Line 85**: Director field rendering
- **Line 96**: Date field rendering
- **Line 101**: Revised field rendering
- **Line 106**: Version field rendering
- **Line 111**: Format field rendering
- **Line 116**: Created field rendering
- **Line 170**: Boneyard element rendering
- **Line 172**: Section element rendering
- **Line 174**: Synopsis element rendering
- **Line 182**: Fallback rendering for unknown element types
- **Line 234**: Empty dual dialogue metadata check
- **Line 433**: Fallback CSS method call

## Missing Test Cases

### 1. Parser Tests

#### Title Page Edge Cases
- **Test Case**: Multi-line values in title page that continue across empty lines
- **Test Case**: Title page with only 'authors' field (no 'author')
- **Test Case**: Title page with all extended fields (director, version, format, created, revised, date)
- **Test Case**: Title page where empty line is followed by more title page content
- **Test Case**: Title page with value that starts empty then gets content on next line

#### Element Parsing Edge Cases
- **Test Case**: Section headers (# Section Name)
- **Test Case**: Synopsis lines (= Synopsis text)
- **Test Case**: Single-line boneyard comments (/* comment */)
- **Test Case**: Empty line parsing that returns None
- **Test Case**: Parsing when there are no existing elements (empty document)
- **Test Case**: Dual dialogue processing that hits the break condition (no valid pairing)

#### Error Conditions
- **Test Case**: Invalid file path for parse_file method
- **Test Case**: File encoding issues (non-UTF-8 files)
- **Test Case**: Extremely large files (memory stress test)

### 2. Document Tests

#### Character Processing
- **Test Case**: Character names ending with '^' (dual dialogue marker)
- **Test Case**: Mixed case character names that should be normalized

#### HTML Rendering
- **Test Case**: Direct to_html() method call with default theme
- **Test Case**: to_html() with custom theme parameter

#### Edge Cases
- **Test Case**: Empty document (no elements)
- **Test Case**: Document with only metadata, no elements
- **Test Case**: Document with duplicate character names in different cases

### 3. Renderer Tests

#### Extended Title Page Fields
- **Test Case**: Title page with 'authors' instead of 'author'
- **Test Case**: Title page with production fields (director, producer)
- **Test Case**: Title page with version control fields (date, revised, version, format, created)
- **Test Case**: Empty/null values in title page fields

#### Special Elements
- **Test Case**: Boneyard element rendering
- **Test Case**: Section element rendering
- **Test Case**: Synopsis element rendering
- **Test Case**: Unknown/future element type (fallback rendering)

#### Theme System
- **Test Case**: Custom theme that falls back to default CSS
- **Test Case**: Invalid theme name handling

### 4. Elements Tests

#### Constructor Edge Cases
- **Test Case**: FountainElement with formatting=None (tests __post_init__)
- **Test Case**: FountainElement with pre-existing empty lists

### 5. Integration Tests

#### Complex Documents
- **Test Case**: Shakespeare-style plays with complex formatting
- **Test Case**: TV scripts with scene numbers and revisions
- **Test Case**: Documents with interleaved notes and boneyards
- **Test Case**: Scripts with extensive use of all formatting types

#### Performance Tests
- **Test Case**: Parsing 500+ page scripts
- **Test Case**: Documents with thousands of formatting spans
- **Test Case**: Deeply nested dual dialogue sequences

#### Round-trip Tests
- **Test Case**: Parse → to_dict → from_dict → to_json consistency
- **Test Case**: Parse → render → re-parse consistency

## Implementation Plan

### Phase 1: Line Coverage (Priority: High)

**SKIP elements.py tests** - ✅ Now at 100% coverage

1. **test_parser.py additions**:
   ```python
   def test_section_parsing(self):
       """Test section headers with # syntax (lines 252-253)."""
       text = """# ACT ONE
       
       ## Scene 1
       
       Some action happens."""
       
   def test_synopsis_parsing(self):
       """Test synopsis with = syntax (lines 262-263)."""
       text = """= This is what happens in this scene
       
       INT. HOUSE - DAY"""
       
   def test_single_line_boneyard(self):
       """Test single-line boneyard comments (line 209)."""
       text = """/* This is a comment */
       
       JOHN
       Hello there."""
       
   def test_empty_elements_list(self):
       """Test dialogue detection with no prior elements (line 441)."""
       parser = FountainParser()
       parser.elements = []  # Explicitly empty
       result = parser._is_dialogue_line()
       assert result is False
       
   def test_title_page_empty_lines(self):
       """Test title page with empty lines (lines 121-122, 130, 173)."""
       text = """Title: My Script
       Notes:
           Line 1
           
           Line 2 after empty line
       Contact: John Doe
       
       INT. HOUSE - DAY"""
       
   def test_empty_line_parsing(self):
       """Test parsing empty lines (line 194)."""
       parser = FountainParser()
       result = parser._parse_line("   ")  # whitespace-only line
       assert result is None
       
   def test_dual_dialogue_break(self):
       """Test dual dialogue processing break condition (line 516)."""
       # Test scenario where dual dialogue pairing fails
   ```

2. **test_document.py additions**:
   ```python
   def test_character_with_dual_marker(self):
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
       
   def test_to_html_method(self):
       """Test direct to_html method (lines 84-87)."""
       elements = [
           FountainElement(ElementType.ACTION, "Some action", [], 1)
       ]
       document = FountainDocument(elements)
       html = document.to_html()
       assert '<div class="action">' in html
       
   def test_to_html_with_theme(self):
       """Test to_html with custom theme (lines 84-87)."""
       document = FountainDocument([])
       html = document.to_html(theme="custom")
       assert '<style>' in html
   ```

3. **test_renderer.py additions**:
   ```python
   def test_extended_title_page_fields(self):
       """Test all extended title page fields (lines 58, 85, 96, 101, 106, 111, 116)."""
       metadata = {
           'title': 'Test Script',
           'authors': 'John & Jane Doe',  # line 58: not 'author'
           'director': 'Famous Director',  # line 85
           'date': '2024-01-01',  # line 96
           'revised': '2024-01-15',  # line 101
           'version': '1.0',  # line 106
           'format': 'Screenplay',  # line 111
           'created': '2023-12-01'  # line 116
       }
       
   def test_special_elements_rendering(self):
       """Test rendering of special element types (lines 170, 172, 174)."""
       elements = [
           FountainElement(ElementType.BONEYARD, "/* comment */", [], 1),  # line 170
           FountainElement(ElementType.SECTION, "ACT ONE", [], 2),  # line 172
           FountainElement(ElementType.SYNOPSIS, "What happens", [], 3),  # line 174
       ]
       
   def test_unknown_element_type(self):
       """Test fallback rendering for unknown types (line 182)."""
       # Create a mock unknown element type
       element = FountainElement(ElementType.ACTION, "text", [], 1)
       element.type = "unknown_type"  # Simulate future element
       
   def test_theme_fallback(self):
       """Test theme system fallback (line 433)."""
       renderer = HTMLRenderer(theme="nonexistent")
       document = FountainDocument([])
       html = renderer.render(document)
       assert '<style>' in html
       
   def test_dual_dialogue_metadata_none(self):
       """Test dual dialogue with None metadata (line 234)."""
       # Test case where dual dialogue metadata is None
   ```

### Phase 2: Edge Cases (Priority: Medium)

1. **Error Handling Tests**:
   ```python
   def test_parse_file_not_found(self):
       """Test parsing non-existent file."""
       parser = FountainParser()
       with pytest.raises(FileNotFoundError):
           parser.parse_file("/nonexistent/file.fountain")
           
   def test_parse_file_encoding_error(self):
       """Test parsing file with encoding issues."""
       # Create a file with non-UTF-8 encoding
       
   def test_empty_document_operations(self):
       """Test operations on empty documents."""
       doc = FountainDocument([])
       assert doc.get_characters() == []
       assert doc.get_scenes() == []
       stats = doc.get_statistics()
       assert stats['total_elements'] == 0
   ```

2. **Complex Parsing Scenarios**:
   ```python
   def test_nested_formatting_edge_cases(self):
       """Test overlapping and nested formatting."""
       text = "***bold italic*** then **bold** then *italic*"
       
   def test_malformed_dual_dialogue(self):
       """Test dual dialogue with missing components."""
       text = """JOHN
       Hello
       
       SARAH^
       (No previous character to pair with)"""
       
   def test_scene_heading_edge_cases(self):
       """Test unusual but valid scene headings."""
       text = """.int. house - day #A1#
       .EXT. PARK - NIGHT #100B#
       .i/e. car - moving"""
   ```

### Phase 3: Integration Tests (Priority: Low)

1. **Large Document Tests**:
   ```python
   def test_large_document_performance(self):
       """Test parsing performance on large documents."""
       # Generate a 500-page script
       lines = []
       for i in range(500):
           lines.extend([
               f"INT. LOCATION {i} - DAY",
               "",
               "Some action happens here.",
               "",
               "CHARACTER",
               f"Dialogue for scene {i}",
               ""
           ])
       
   def test_round_trip_consistency(self):
       """Test parse → serialize → parse consistency."""
       original_text = load_fixture("complex_script.fountain")
       doc1 = parser.parse(original_text)
       json_str = doc1.to_json()
       # Reconstruct and compare
   ```

2. **Stress Tests**:
   ```python
   def test_deeply_nested_elements(self):
       """Test documents with complex nesting."""
       
   def test_extreme_formatting(self):
       """Test documents with thousands of format spans."""
   ```

### Phase 4: Behavioral Tests (Priority: High)

1. **Fountain Spec Compliance**:
   ```python
   def test_fountain_spec_examples(self):
       """Test against official Fountain spec examples."""
       # Test each example from fountain.io
       
   def test_edge_case_precedence(self):
       """Test element precedence in ambiguous cases."""
       # When text could be multiple element types
   ```

2. **Real-world Scripts**:
   ```python
   def test_published_screenplay_formats(self):
       """Test against real published screenplay formats."""
       
   def test_tv_script_formats(self):
       """Test TV-specific formatting (TEASER, END OF ACT ONE, etc.)."""
   ```

## Testing Best Practices to Implement

1. **Fixture Management**:
   - Create a comprehensive fixtures directory with various script types
   - Add malformed/edge-case fixtures for error testing
   - Include real-world examples with permission

2. **Parameterized Tests**:
   - Use pytest.mark.parametrize for testing multiple similar cases
   - Create data-driven tests for format combinations

3. **Property-based Testing**:
   - Consider adding hypothesis for generating random valid Fountain text
   - Test parser robustness with generated content

4. **Performance Benchmarks**:
   - Add pytest-benchmark for performance regression testing
   - Set performance targets for large documents

5. **Mock Testing**:
   - Mock file I/O for error condition testing
   - Mock renderer for testing document methods in isolation

## Success Metrics

1. **Coverage**: Achieve 100% line coverage
2. **Branch Coverage**: Achieve >95% branch coverage
3. **Mutation Testing**: Consider adding mutmut for mutation testing
4. **Performance**: Parse 500-page script in <1 second
5. **Reliability**: Zero crashes on malformed input

## Updated Timeline (2025)

- **Immediate (Days 1-2)**: Implement Phase 1 tests to achieve 100% line coverage
- **Short-term (Week 1)**: Add Phase 2 edge cases and error handling  
- **Medium-term (Week 2-3)**: Implement Phase 3 integration tests and performance benchmarks
- **Long-term (Month 1)**: Add comprehensive Fountain spec compliance tests

## Conclusion

This comprehensive plan addresses all current coverage gaps and adds robust testing for edge cases, performance, and real-world scenarios. Following this plan will result in a thoroughly tested, production-ready Fountain parser with excellent reliability and performance characteristics.