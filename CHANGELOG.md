# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-09

### Added

#### Parser — Full Fountain Spec Compliance
- Two-pass parser: title page metadata extraction, then line-by-line element classification
- All 14 body element types emitted by the parser: scene headings, action, character, dialogue, parenthetical, transitions, notes, boneyard, sections, synopses, dual dialogue, page breaks, centered text, lyrics (the `ElementType` enum has 15 members; the 15th, `TITLE_PAGE`, is not emitted as an element: title page data is parsed into `FountainDocument.metadata`)
- Forced element prefixes (`.`, `!`, `@`, `>`) override natural detection rules
- Scene number extraction (`#1#`, `#2A#`)
- Character extensions (`V.O.`, `O.S.`, `CONT'D`) and automatic continuation detection
- Section level metadata (`# Act` = level 1, `## Scene` = level 2, etc.)
- Ellipsis protection on forced scene headings (`.` + alphanumeric only)
- Arbitrary title page keys (any `Key: Value` pair accepted, not just known fields)
- Blank-line-before requirement for natural scene headings, character names, and transitions
- Blank-line-after requirement for transitions
- Inline note stripping (`[[notes]]` removed from element text in non-note elements)
- Multi-line note support (`[[note\nspanning\nlines]]`)
- Dialogue continuation with whitespace-only lines (two spaces preserves blank line in dialogue)
- Backslash escaping for emphasis markers (`\*` → literal `*`, `\_` → literal `_`)
- Tabs in action elements are converted to four spaces in the element text at parse time; indentation is preserved in HTML via `white-space: pre-wrap` on `.fountain-action`
- Inline formatting: bold (`**`), italic (`*`), underline (`_`), bold-italic (`***`)

#### Renderers
- `HTMLRenderer` with three output modes:
  - `render(doc)` — pure HTML fragment for embedding (no `<style>` tags)
  - `render_page(doc)` — standalone HTML with embedded CSS
  - `get_css()` — raw CSS string for external stylesheet use
- `FountainRenderer` for round-trip conversion back to Fountain markup
- All CSS classes namespaced with `fountain-` prefix to prevent framework collisions
- Screenplay-formatted CSS: Courier font, proper margins, centered dialogue, hidden boneyard
- Dual dialogue side-by-side layout via flexbox
- Title page rendering with all standard and custom metadata fields

#### Document Analysis
- `FountainDocument` container with element access and metadata
- `get_characters()` — extract unique character names
- `get_scenes()` — list scene heading elements
- `get_statistics()` — element counts by type, character count, scene count
- `to_html()` — convenience method for standalone HTML output

#### Type System
- Full type hints throughout, strict mypy compliance
- `FormatType` literal type (`"bold"`, `"italic"`, `"underline"`, `"bold_italic"`)
- `MetadataValue` union type for element metadata documentation
- PEP 561 `py.typed` marker for downstream type checking

#### Quality
- 280 tests with 99% code coverage
- 38 module-level doctests + 446 Sphinx doctests
- Supports Python 3.10, 3.11, 3.12, 3.13, 3.14
- Zero runtime dependencies
- CI with GitHub Actions across all supported Python versions
