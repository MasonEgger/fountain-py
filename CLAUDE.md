# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Set up development environment
uv sync --dev

# Install in development mode  
uv pip install -e .
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=fountain

# Run specific test file
uv run pytest tests/test_parser.py

# Run specific test method
uv run pytest tests/test_parser.py::TestFountainParser::test_parse_simple_text
```

### Code Quality
```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Type checking (if configured)
uv run mypy src/
```

## Architecture Overview

This is a Python library for parsing Fountain markup (screenplay format). The architecture follows a clean parsing pipeline:

### Core Components

1. **FountainParser** (`src/fountain/parser.py`)
   - Converts raw Fountain text to structured elements using regex patterns
   - Two-pass parsing: title page metadata first, then body elements
   - Handles both structural elements and inline formatting

2. **FountainDocument** (`src/fountain/document.py`)
   - Container for complete parsed documents
   - Provides analysis methods (character extraction, statistics)
   - Bridge between parsing and rendering

3. **FountainElement** (`src/fountain/elements.py`)
   - Represents individual screenplay elements (scenes, dialogue, action, etc.)
   - Uses dataclass pattern with type, text, formatting, and metadata
   - 11 distinct element types via ElementType enum

4. **HTMLRenderer** (`src/fountain/renderer.py`)
   - Converts structured documents to HTML with proper screenplay formatting
   - Strategy pattern design for extensible output formats

### Data Flow
Raw Fountain Text → Parser (regex classification) → FountainDocument (structured elements) → Renderer → HTML/JSON output

### Key Patterns
- Separation of concerns between parsing, representation, and rendering
- Enum-driven element classification for consistency
- Immutable elements created once during parsing
- Extensible design for new renderers and element types

### Project Structure
- `src/fountain/` - Main library code
- `tests/` - Pytest test suite with fixtures
- `tests/fixtures/` - Sample Fountain files for testing
- Root level contains sample conversion scripts and Fountain files