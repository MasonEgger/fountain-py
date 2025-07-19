# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Set up development environment
just dev
# OR manually: uv sync --dev

# Install in development mode  
just install
# OR manually: uv pip install -e .
```

### Testing
```bash
# Run all tests
just unit-test

# Run tests with coverage (recommended)
just unit-test-cov

# Run comprehensive quality checks (tests, linting, type checking, formatting)
just test

# Run specific test file
uv run pytest tests/test_parser.py

# Run specific test method
uv run pytest tests/test_parser.py::TestFountainParser::test_parse_simple_text
```

### Code Quality
```bash
# Format code
just format

# Lint code
just lint

# Fix linting issues automatically
just fix

# Type checking (mypy in strict mode)
just type-check

# Check formatting without fixing
just check

# Clean temporary files
just clean
```

### Documentation
```bash
# Serve documentation locally
just docs
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
   - 14 distinct element types via ElementType enum including dual dialogue support

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

## Testing Architecture

### Test Organization
- **pytest** as test framework with strict configuration
- **Test fixtures** in `tests/conftest.py` provide reusable sample data
- **Fixture files** in `tests/fixtures/` contain sample Fountain scripts
- **Coverage reporting** configured for HTML and terminal output
- **Parameterized tests** for different Fountain element types

### Key Fixtures
- `simple_fountain_script`: Loads test script from fixtures directory
- `sample_fountain_text`: Inline sample Fountain text for quick tests
- `fixtures_dir`: Path helper for accessing test data files

## Tool Configuration

### Code Quality Tools
- **ruff**: Handles both linting and formatting (line length: 120)
- **mypy**: Type checking in strict mode with comprehensive warnings
- **pytest**: Test discovery with strict markers and error handling
- **coverage**: Source tracking from `src/` directory

### Contributor Workflow

- Use the commands in the Justfile for all development tasks
- Run `just test` for comprehensive quality checks before committing
- Test files follow naming pattern: `test_*.py` in `tests/` directory