# Fountain-Py

[![CI](https://github.com/MasonEgger/fountain-py/workflows/CI/badge.svg)](https://github.com/MasonEgger/fountain-py/actions?query=workflow%3ACI)
[![Python versions](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Python library for parsing [Fountain markup](https://fountain.io/), the screenwriting format. Fountain-Py converts Fountain scripts into structured Python objects and can render them as HTML.

## Features

- **Full Fountain Spec Compliance**: Parses all Fountain elements including scenes, dialogue, action, transitions, notes, dual dialogue, lyrics, and more
- **Type-Safe**: Built with full type hints and strict mypy compliance
- **Multiple Render Modes**: HTML fragments for embedding, full pages with CSS, or raw CSS for custom styling
- **Zero Dependencies**: Pure Python with no runtime dependencies
- **Well-Tested**: 314 tests, 99% coverage, doctests across all modules
- **Modern Python**: Supports Python 3.10 through 3.14

## Quick Start

### Installation

Fountain-Py is not on PyPI yet (the 0.1.0 release is pending), so install it from source:

```bash
pip install git+https://github.com/MasonEgger/fountain-py.git
```

Once it is published, `pip install fountain-py` will work.

### Basic Usage

```python
from fountain import FountainParser
from fountain.renderer import HTMLRenderer

# Parse a Fountain script
parser = FountainParser()
document = parser.parse("""Title: My Screenplay
Author: Jane Writer

INT. COFFEE SHOP - DAY

SARAH enters, looking tired.

SARAH
One large cappuccino, please!
""")

# Access parsed data
print(document.metadata["title"])       # "My Screenplay"
print(document.get_characters())        # ["SARAH"]
print(len(document.elements))           # 3

# Render as HTML fragment (for embedding in web pages)
renderer = HTMLRenderer()
html_fragment = renderer.render(document)

# Render as standalone HTML file with embedded CSS
html_page = renderer.render_page(document)

# Get raw CSS for external stylesheets
css = renderer.get_css()
```

### Rendering Modes

```python
renderer = HTMLRenderer()

# Fragment — no <style> tags, just the screenplay markup
# Use this for embedding in web pages, docs, or CMS systems
fragment = renderer.render(document)

# Full page — self-contained HTML with embedded CSS
# Use this for saving as .html files or previewing
page = renderer.render_page(document)

# Raw CSS — for custom stylesheet integration
# Use this with mkdocs, static site generators, or your own build pipeline
css = renderer.get_css()
```

### Round-Trip Conversion

```python
from fountain.renderer import FountainRenderer

# Convert back to Fountain markup
fountain_renderer = FountainRenderer()
fountain_text = fountain_renderer.render(document)
```

The round trip preserves element structure and inline emphasis.
Scene headings, action, character cues, parentheticals, dialogue, transitions, dual dialogue, lyrics, sections, synopses, and notes all keep their element types through `parse(render(parse(text)))`, and the blank lines that separate structural blocks survive so blocks are not merged on re-parse.

Inline emphasis is re-emitted too.
The parser records the bold (`**`), italic (`*`), and underline (`_`) delimiters as formatting spans, and `FountainRenderer` restores them, so a `**bold**` word round-trips as `**bold**`, including nested emphasis and backslash-escaped literals.

## Documentation

Full documentation is available at [masonegger.github.io/fountain-py](https://masonegger.github.io/fountain-py/).

- [Installation Guide](https://masonegger.github.io/fountain-py/installation.html)
- [Quick Start Tutorial](https://masonegger.github.io/fountain-py/quickstart.html)
- [API Reference](https://masonegger.github.io/fountain-py/api/index.html)

## Development

### Setup

```bash
git clone https://github.com/MasonEgger/fountain-py.git
cd fountain-py

# Install with development and docs dependencies
just dev && uv sync --group docs
```

### Running Tests

```bash
# Run comprehensive quality checks (tests, coverage, doctests, lint, type check)
just test

# Run only unit tests
just unit-test

# Run tests with coverage
just unit-test-cov

# Run specific tests
uv run pytest tests/test_parser.py
```

### Code Quality

```bash
just lint         # Lint check (ruff)
just format       # Format code (ruff)
just type-check   # Type checking (mypy strict)
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Fountain Format

Fountain is a simple markup syntax for writing, editing and sharing screenplays in plain text. Learn more at [fountain.io](https://fountain.io/).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The [Fountain](https://fountain.io/) format creators
- The screenwriting community for feedback and testing
