# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Set up development environment (dev + docs dependencies needed for full test suite)
just dev && uv sync --group docs
```

### Testing
```bash
# Run comprehensive quality checks (tests, coverage, doctests, lint, type check, format check)
just test

# Run only unit tests
just unit-test

# Run tests with coverage
just unit-test-cov

# Run specific test file or method
uv run pytest tests/test_parser.py
uv run pytest tests/test_edge_cases.py::TestSpecCompliance::test_section_level_1
```

### Code Quality
```bash
just format       # Format code (ruff)
just lint         # Lint check (ruff)
just fix          # Auto-fix lint issues
just type-check   # Type checking (mypy strict)
just check        # Format check without fixing
```

### Documentation
```bash
just docs          # Serve docs locally with autobuild (live reload)
just docs-build    # Build docs once
just doctest       # Run doctests (pytest + Sphinx)
```

## Architecture Overview

Python library for parsing [Fountain screenplay markup](https://fountain.io/syntax/). Clean pipeline: parse → structure → render.

### Data Flow
```
Raw Fountain Text → FountainParser → FountainDocument (list of FountainElement) → Renderer → HTML/Fountain output
```

### Core Components (`src/fountain/`)

- **`parser.py`** — Two-pass parser. Pass 1: title page metadata (`_parse_title_page()`). Pass 2: line-by-line body element classification (`_parse_line()`) using regex patterns with precedence: forced elements (`!`, `@`, `>`, `.`) → special markers (boneyard, notes, page breaks) → natural patterns (scene headings, transitions) → character/dialogue detection → action fallback.
- **`elements.py`** — `ElementType` enum (15 types), `FountainElement` dataclass (type, text, formatting spans, line_number, metadata dict), `FormatSpan` named tuple for inline bold/italic/underline.
- **`document.py`** — `FountainDocument` container with analysis methods (character extraction, statistics).
- **`renderer.py`** — `HTMLRenderer` and `FountainRenderer` (round-trip back to Fountain markup).
- **`__init__.py`** — Public API exports: `FountainParser`, `FountainDocument`, `ElementType`, `FountainElement`.

### Key Parser Internals
- `had_blank_line_before` parameter passed to `_parse_line()` for context-dependent element detection
- `_is_dialogue_following()` lookahead determines if an uppercase line is a character cue
- `self.in_boneyard` flag for multi-line `/* */` comment state tracking
- `NOTE_PATTERN` regex handles `[[inline notes]]`
- Forced element prefixes (`.`, `!`, `@`, `>`) override normal classification rules

### Test Organization
- **`test_parser.py`** — Core parser tests
- **`test_edge_cases.py`** — Edge cases and spec compliance (`TestSpecCompliance` class for spec gap fixes)
- **`test_renderer.py`** — `TestHTMLRenderer` and `TestFountainRenderer`
- **`test_document.py`** — Document analysis methods
- **`test_quickstart_examples.py`** — Validates all code examples from the quickstart docs
- **`tests/fixtures/`** — Sample `.fountain` files; loaded via `conftest.py` fixtures

## Tool Configuration
- **ruff**: Linting + formatting, line length 120, target Python 3.9
- **mypy**: Strict mode with all warnings enabled
- **pytest**: Strict markers, `--doctest-modules` enabled by default
- **coverage**: Source from `src/` directory
- **CI**: GitHub Actions runs tests on Python 3.9–3.13; PRs target `main`
