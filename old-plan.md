# Fountain Script Writing System - Implementation Plan

## Overview
Create a comprehensive system for writing theatrical scripts using Fountain markup, with integration into static site generators like MkDocs, and PDF export capabilities.

## Architecture: Two-Package System

### Package 1: `fountain-py` (Core Parser)
**Purpose**: Standalone Fountain markup parser library
**Dependencies**: Zero external dependencies for maximum compatibility
**Target**: Python 3.8+

#### Core Components

```python
# Main Parser Class
class FountainParser:
    def parse(self, text: str) -> FountainDocument
    def parse_file(self, filepath: str) -> FountainDocument
    def validate(self, text: str) -> List[ValidationError]

# Document Representation
class FountainDocument:
    def __init__(self, elements: List[FountainElement], metadata: Dict[str, str])
    def to_html(self, theme: str = "default") -> str
    def to_dict(self) -> Dict[str, Any]
    def to_json(self) -> str
    def get_characters(self) -> List[str]
    def get_scenes(self) -> List[str]
    def get_statistics(self) -> Dict[str, int]

# Element Types
class FountainElement:
    type: ElementType
    text: str
    formatting: List[FormatSpan]
    line_number: int

# Supported Element Types
class ElementType(Enum):
    TITLE_PAGE = "title_page"
    SCENE_HEADING = "scene_heading"
    ACTION = "action"
    CHARACTER = "character"
    DIALOGUE = "dialogue"
    PARENTHETICAL = "parenthetical"
    TRANSITION = "transition"
    NOTE = "note"
    BONEYARD = "boneyard"
    SECTION = "section"
    SYNOPSIS = "synopsis"
```

#### Key Features
- **Complete Fountain Spec Support**: All official Fountain elements
- **Robust Parsing**: Handle edge cases and malformed input gracefully
- **Formatting Preservation**: Bold, italic, underline within text
- **Metadata Extraction**: Title page information, notes, etc.
- **Character Analysis**: Extract speaking characters, scene participants
- **Validation**: Report parsing errors and warnings
- **Multiple Output Formats**: HTML, JSON, structured data

#### File Structure
```
fountain-py/
├── src/
│   └── fountain/
│       ├── __init__.py
│       ├── parser.py          # Main parser logic
│       ├── document.py        # Document representation
│       ├── elements.py        # Element classes
│       ├── renderer.py        # HTML rendering
│       └── utils.py           # Helper functions
├── tests/
│   ├── test_parser.py
│   ├── test_renderer.py
│   └── fixtures/              # Sample .fountain files
├── docs/
│   ├── api.md
│   └── examples.md
├── pyproject.toml
└── README.md
```

### Package 2: `mkdocs-fountain` (MkDocs Plugin)
**Purpose**: MkDocs integration with PDF export
**Dependencies**: mkdocs, fountain-py, weasyprint (for PDF)

#### Core Components

```python
# Main Plugin Class
class FountainPlugin(BasePlugin):
    config_scheme = (
        ('theme', config_options.Choice(['default', 'modern', 'classic'], default='default')),
        ('pdf_enabled', config_options.Type(bool, default=True)),
        ('pdf_css', config_options.Type(str, default=None)),
        ('character_index', config_options.Type(bool, default=False))
    )
    
    def on_page_markdown(self, markdown, page, config, files)
    def on_page_content(self, html, page, config, files)
    def on_serve(self, server, config, builder)  # PDF endpoint

# PDF Generator
class FountainPDFGenerator:
    def generate(self, document: FountainDocument, output_path: str)
    def get_css(self, theme: str = "industry_standard") -> str
```

#### Features
- **Custom Code Block**: Process `fountain` code blocks in Markdown
- **Multiple Themes**: Different visual styles for web display
- **PDF Generation**: Industry-standard script formatting
- **Character Index**: Auto-generate character lists
- **Scene Navigation**: Generate scene-based table of contents
- **Live Preview**: Hot-reload for script editing

#### File Structure
```
mkdocs-fountain/
├── src/
│   └── mkdocs_fountain/
│       ├── __init__.py
│       ├── plugin.py          # Main MkDocs plugin
│       ├── pdf_generator.py   # PDF creation logic
│       ├── templates/         # HTML templates
│       │   ├── script.html
│       │   └── character_index.html
│       └── css/               # Styling themes
│           ├── default.css
│           ├── modern.css
│           └── pdf.css
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

## Implementation Phases

### Phase 1: Core Parser Development (4-6 weeks)
1. **Week 1-2**: Basic parsing infrastructure
   - Implement lexer for Fountain syntax
   - Create element type system
   - Handle basic elements (scene headings, action, dialogue)

2. **Week 3-4**: Advanced parsing features
   - Title page parsing
   - Formatting (bold, italic, underline)
   - Notes and boneyard sections
   - Character name detection and standardization

3. **Week 5-6**: Rendering and validation
   - HTML output with proper formatting
   - Validation system for common errors
   - Comprehensive test suite
   - Documentation and examples

### Phase 2: MkDocs Integration (3-4 weeks)
1. **Week 1-2**: Plugin foundation
   - MkDocs plugin skeleton
   - Code block processor
   - Basic HTML integration

2. **Week 3-4**: Styling and features
   - CSS themes for script formatting
   - Character index generation
   - Scene navigation
   - Configuration options

### Phase 3: PDF Generation (2-3 weeks)
1. **Week 1-2**: PDF infrastructure
   - WeasyPrint integration
   - Industry-standard formatting
   - Page breaks and margins

2. **Week 3**: Polish and optimization
   - Multiple PDF themes
   - Performance optimization
   - Error handling

## Technical Specifications

### Fountain Parsing Rules
- **Scene Headings**: Lines starting with INT./EXT. or forced with '.'
- **Character Names**: ALL CAPS, centered, followed by dialogue
- **Action**: Regular text, left-aligned
- **Dialogue**: Indented under character names
- **Parentheticals**: Text in parentheses under character names
- **Transitions**: ALL CAPS, right-aligned (FADE IN:, CUT TO:, etc.)

### HTML Output Structure
```html
<div class="fountain-script">
    <div class="title-page">
        <h1 class="title">Script Title</h1>
        <p class="author">Author Name</p>
    </div>
    
    <div class="script-body">
        <div class="scene-heading">INT. HOUSE - DAY</div>
        <div class="action">John enters the room.</div>
        <div class="character">JOHN</div>
        <div class="dialogue">Hello, world!</div>
    </div>
</div>
```

### CSS Styling Principles
- **Industry Standard Spacing**: Proper margins and indentation
- **Responsive Design**: Mobile-friendly layouts
- **Print Optimization**: Clean PDF output
- **Typography**: Courier New or similar monospace fonts
- **Visual Hierarchy**: Clear distinction between element types

### MkDocs Configuration
```yaml
plugins:
  - fountain:
      theme: default
      pdf_enabled: true
      character_index: true
      pdf_css: custom.css
```

### Usage Examples

#### Basic Fountain in Markdown
```markdown
# Act I

```fountain
Title: My Amazing Play
Author: Mason Egger

FADE IN:

INT. LIVING ROOM - DAY

SARAH sits on the couch, reading a script.

SARAH
This Fountain parser makes writing 
scripts so much easier!

JOHN enters from the kitchen.

JOHN
(excited)
Did you see the PDF export feature?

SARAH
(grinning)
Theater geeks everywhere will love this!

FADE OUT.
\```
```

#### Advanced Features
```markdown
## Character Analysis

The script includes {{ characters | length }} speaking characters:
{% for character in characters %}
- {{ character }}
{% endfor %}

[Download PDF](script.pdf)
```

## Success Criteria

### fountain-py Package
- [ ] Parse all official Fountain elements correctly
- [ ] Handle malformed input gracefully
- [ ] Generate clean, semantic HTML
- [ ] Provide comprehensive API documentation
- [ ] Achieve 95%+ test coverage
- [ ] Support Python 3.8+

### mkdocs-fountain Package
- [ ] Seamless MkDocs integration
- [ ] Professional script formatting
- [ ] High-quality PDF output
- [ ] Multiple visual themes
- [ ] Fast build times (<5s for typical script)
- [ ] Mobile-responsive design

## Future Enhancements

### Phase 4: Advanced Features
- **Collaboration Tools**: Git-friendly diff viewing
- **Script Analysis**: Reading time estimation, character arc tracking
- **Export Formats**: FDX (Final Draft), WriterDuet, etc.
- **Template System**: Genre-specific formatting templates

### Phase 5: Ecosystem Integration
- **GitHub Actions**: Automated PDF generation
- **VS Code Extension**: Syntax highlighting and preview
- **Sphinx Plugin**: RestructuredText support
- **Hugo Plugin**: Hugo static site integration

## Resources and References

### Fountain Specification
- [Official Fountain Syntax](https://fountain.io/syntax)
- [Fountain Apps](https://fountain.io/apps)

### Technical References
- [MkDocs Plugin Development](https://www.mkdocs.org/dev-guide/plugins/)
- [WeasyPrint Documentation](https://weasyprint.readthedocs.io/)
- [Industry Script Formatting Standards](https://www.writersstore.com/proper-screenplay-format/)

### Similar Projects
- fountain-js (JavaScript implementation)
- afterwriting (Web-based Fountain editor)
- Beat (macOS Fountain editor)

## Getting Started

1. **Set up development environment**
2. **Create fountain-py package structure**
3. **Implement basic Fountain lexer**
4. **Add element parsing logic**
5. **Create HTML renderer**
6. **Build comprehensive test suite**
7. **Develop MkDocs plugin**
8. **Add PDF generation**
9. **Polish and document**

This plan provides a solid foundation for creating a professional-grade Fountain script writing system that integrates seamlessly with modern documentation workflows while maintaining industry formatting standards.