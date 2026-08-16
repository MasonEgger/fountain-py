# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - Unreleased

### Added

#### JSON Interchange
- `to_dict()` recursively serializes nested elements, including dual-dialogue side elements, fixing a crash on `to_json()` for scripts with dual dialogue
- `schema_version` key in the serialized payload, backed by a versioned `reference/json-schema` reference doc
- `from_dict()` / `from_json()` reconstruct a full `FountainDocument` from serialized data, round-tripping through `to_dict()` / `to_json()`; raise `ValueError` on an unrecognized `schema_version`

#### Renderer Protocols
- `TextRenderer` and `BinaryRenderer` protocols in `fountain.renderers.base`, formalizing the renderer contract; every existing renderer conforms

#### Plain-Text Renderer
- `PlainTextRenderer` renders a parsed script to monospace plain text, with configurable width and indents; omits writer-only elements (notes, sections, synopses, boneyard)

#### Command-Line Interface
- `fountain` CLI with `validate` and `render --format` subcommands, installed via `[project.scripts]`
- Reads from a file path or stdin (`-`); `validate` reports one diagnostic per line and exits non-zero on error-severity issues

#### FDX Export
- `FDXRenderer` exports a parsed script to Final Draft's `.fdx` XML format using only the standard library, so it adds no runtime dependency
- Dual dialogue renders as a linked `<DualDialogue>` block, pinned against `tests/fixtures/dual_dialogue.fdx`

#### PDF Export
- `PDFRenderer` renders a parsed script to PDF bytes via the optional `pdf` extra (`fpdf2`), with a clear install hint when the extra is missing
- `PageGeometry` presets for Letter, A4, and Half Letter page sizes, plus custom dimensions and a binding offset
- `SCREENPLAY` layout profile controlling font and per-element indents; layouts are pluggable via `LayoutProfile`
- CI verifies the core install stays dependency-free and runs the PDF suite separately under the `pdf` extra

#### Documentation
- How-to guides for the CLI, plain-text export, FDX export, and PDF export
- The JSON how-to now covers `from_json()` / `from_dict()` round-tripping alongside `to_json()` / `to_dict()`

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
- 314 tests with 99% code coverage
- 38 module-level doctests + 447 Sphinx doctests
- Supports Python 3.10, 3.11, 3.12, 3.13, 3.14
- Zero runtime dependencies
- CI with GitHub Actions across all supported Python versions
