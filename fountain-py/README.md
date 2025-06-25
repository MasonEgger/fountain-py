# Fountain-py

A Python library for parsing Fountain markup, the industry-standard format for screenwriting and theatrical scripts.

## Features

- **Complete Fountain Support**: Parses all official Fountain elements including scene headings, dialogue, action, transitions, and metadata
- **Zero Dependencies**: Pure Python implementation with no external dependencies
- **Multiple Output Formats**: Convert to HTML, JSON, or structured data
- **Formatting Preservation**: Maintains bold, italic, and underline formatting
- **Character Analysis**: Extract character lists and dialogue statistics
- **Industry-Standard HTML**: Generates properly formatted script layouts

## Installation

```bash
# Install from PyPI (when published)
pip install fountain-py

# Or install in development mode
uv pip install -e .
```

## Quick Start

### Basic Usage

```python
from fountain import FountainParser

# Parse Fountain text
parser = FountainParser()
document = parser.parse("""
Title: My Great Script
Author: Your Name

FADE IN:

INT. COFFEE SHOP - DAY

SARAH sits at a table, typing on her laptop.

JOHN enters, looking excited.

JOHN
Sarah! I have **amazing** news!

SARAH
(looking up)
What is it?

JOHN
I just finished the Fountain parser!

SARAH
That's *incredible*! Show me.

FADE OUT.
""")

# Access metadata
print(f"Title: {document.metadata.get('title')}")
print(f"Author: {document.metadata.get('author')}")

# Get characters
characters = document.get_characters()
print(f"Characters: {', '.join(characters)}")

# Get statistics
stats = document.get_statistics()
print(f"Total elements: {stats['total_elements']}")
print(f"Dialogue lines: {stats['dialogue_count']}")
```

### Parse from File

```python
# Parse a .fountain file
document = parser.parse_file('my_script.fountain')

# Convert to HTML
html_output = document.to_html()
with open('script.html', 'w') as f:
    f.write(html_output)

# Convert to JSON
json_output = document.to_json()
with open('script.json', 'w') as f:
    f.write(json_output)
```

### Working with Elements

```python
from fountain.elements import ElementType

# Access individual elements
for element in document.elements:
    if element.type == ElementType.CHARACTER:
        print(f"Character: {element.text}")
    elif element.type == ElementType.DIALOGUE:
        print(f"  Says: {element.text}")
        
        # Check for formatting
        if element.formatting:
            print(f"  Has formatting: {[f.format_type for f in element.formatting]}")
```

## Fountain Syntax Support

Fountain-py supports the complete Fountain specification:

### Scene Headings
```
INT. COFFEE SHOP - DAY
EXT. PARK - NIGHT
.FORCED SCENE HEADING
```

### Characters and Dialogue
```
JOHN
Hello, world!

SARAH
(whispering)
Hi back.

JOHN (CONT'D)
How are you?
```

### Action
```
John enters the room and sits down at the table.

Sarah looks up from her book.
```

### Transitions
```
FADE IN:
CUT TO:
FADE OUT.

>FORCED TRANSITION
```

### Formatting
```
This is **bold** text.
This is *italic* text.
This is _underlined_ text.
```

### Title Page
```
Title: My Amazing Script
Author: Your Name
Credit: Written by
Source: Based on true events
Draft Date: June 2025
Contact: your.email@example.com
```

### Notes and Comments
```
[[This is a note that appears in the output]]

/*
This is boneyard text that is ignored
*/
```

### Sections and Synopsis
```
# Act I

## Scene 1

= This is a synopsis of the scene
```

## HTML Output

The HTML renderer creates industry-standard formatted scripts:

```python
# Generate HTML with default styling
html = document.to_html()

# The output includes:
# - Proper margins and spacing
# - Centered character names
# - Appropriate dialogue indentation
# - Scene heading formatting
# - Title page layout
```

The generated HTML includes embedded CSS that follows standard screenplay formatting conventions.

## API Reference

### FountainParser

```python
class FountainParser:
    def parse(self, text: str) -> FountainDocument
    def parse_file(self, filepath: str) -> FountainDocument
```

### FountainDocument

```python
class FountainDocument:
    def to_html(self, theme: str = "default") -> str
    def to_dict(self) -> Dict[str, Any]
    def to_json(self) -> str
    def get_characters(self) -> List[str]
    def get_scenes(self) -> List[str]
    def get_statistics(self) -> Dict[str, int]
```

### FountainElement

```python
class FountainElement:
    type: ElementType
    text: str
    formatting: List[FormatSpan]
    line_number: int
    metadata: Dict[str, Any]
```

### ElementType

All supported Fountain element types:

- `TITLE_PAGE` - Title page metadata
- `SCENE_HEADING` - Scene headings (INT./EXT.)
- `ACTION` - Action lines
- `CHARACTER` - Character names
- `DIALOGUE` - Character dialogue
- `PARENTHETICAL` - Parenthetical directions
- `TRANSITION` - Scene transitions
- `NOTE` - Visible notes
- `BONEYARD` - Hidden comments
- `SECTION` - Section headings (#)
- `SYNOPSIS` - Scene synopsis (=)

## Example Output

Given this Fountain input:
```
Title: Coffee Shop Meeting
Author: Jane Writer

FADE IN:

INT. COFFEE SHOP - DAY

SARAH types on her laptop.

JOHN
(excited)
The **parser** works perfectly!
```

The library produces:
- **Parsed Elements**: Scene heading, action, character, parenthetical, dialogue
- **Character List**: ["JOHN", "SARAH"]  
- **Formatting**: Bold formatting detected on "parser"
- **HTML Output**: Industry-standard script formatting
- **Statistics**: Element counts, character counts, etc.

## Development

```bash
# Clone and set up development environment
git clone https://github.com/MasonEgger/fountain-py
cd fountain-py
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=fountain

# Format code
uv run black src/ tests/
uv run isort src/ tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Projects

This library is designed to work with:
- **mkdocs-fountain** - MkDocs plugin for rendering Fountain scripts
- Static site generators (MkDocs, Sphinx, Hugo)
- PDF generation tools
- Other Fountain-compatible software

## Fountain Resources

- [Fountain.io](https://fountain.io/) - Official Fountain specification
- [Fountain Syntax](https://fountain.io/syntax) - Complete syntax guide
- [Fountain Apps](https://fountain.io/apps) - Other Fountain-compatible tools