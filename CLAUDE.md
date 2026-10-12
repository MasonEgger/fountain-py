# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Sync dev + docs dependency groups (mypy checks docs/source/conf.py, which imports sphinx)
just dev
```

### The Gate
```bash
just check   # ruff check, ruff format --check, mypy . (strict), pytest; CI runs the same steps
just fmt     # ruff format + ruff check --fix
```

### Testing
```bash
just test       # pytest (module doctests included via --doctest-modules)
just test-cov   # with coverage report (informational, never a gate)
just test-all   # every supported Python version, 3.11 through 3.15
just doctest    # Sphinx doctests in the .rst pages

# Specific file or test
uv run pytest tests/test_parser.py
uv run pytest tests/test_edge_cases.py::TestSpecCompliance::test_section_level_1
```

### Documentation
```bash
just docs        # serve with live reload
just docs-build  # build once
```

## Architecture Overview

Python library for parsing [Fountain screenplay markup](https://fountain.io/syntax/), with a `fountain` CLI.
Zero runtime dependencies; PDF output needs the optional `[pdf]` extra (fpdf2).

### Data Flow
```
Raw Fountain Text -> FountainParser -> FountainDocument (list of FountainElement) -> Renderer -> HTML / Fountain / text / FDX / PDF / JSON
```

### Core Components (`src/fountain/`)

- **`parser.py`**: Two-pass parser. Pass 1: title page metadata (`_parse_title_page()`). Pass 2: line-by-line body classification (`_parse_line()`) with precedence: forced elements (`!`, `@`, `>`, `.`) -> boneyard/notes/page breaks -> natural patterns (scene headings, transitions) -> character cues (dialogue lookahead) -> dialogue -> action fallback. `_parse_line()` returns raw text with empty formatting; `_finalize_inline()` is the single place emphasis is resolved (delimiters stripped, content-only spans via the CommonMark-style delimiter-run scanner in `_extract_inline()`). Parsing never raises; structural problems become `ValidationIssue` diagnostics on `document.issues` (and `validate()`). `_process_dual_dialogue()` post-processes `NAME^` cues into one DUAL_DIALOGUE element.
- **`elements.py`**: `ElementType` (15 types), `FountainElement` dataclass (`metadata` is always a dict), `FormatSpan`, `ValidationIssue`, and the `FormatType` / `MetadataValue` aliases. `FountainElement.dual_dialogue_columns()` is the typed accessor for a DUAL_DIALOGUE element's left/right `[cue, *dialogue]` columns; every renderer uses it instead of reading the metadata keys.
- **`document.py`**: `FountainDocument` container with analysis methods plus `to_dict`/`to_json` and `from_dict`/`from_json` (versioned by `JSON_SCHEMA_VERSION`; input is validated and bad fields raise `ValueError`).
- **`renderer.py`**: `HTMLRenderer` (`render()` fragment, `render_page()` with CSS, `get_css()`; all classes `fountain-` prefixed; title page driven by `TITLE_PAGE_FIELD_ORDER`) and `FountainRenderer` (round trip, re-emits emphasis markers). Both use the shared `_wrap_spans()` sweep for nested/overlapping spans.
- **`renderers/`**: `base.py` (`TextRenderer`/`BinaryRenderer` protocols), `plaintext.py`, `fdx.py` (stdlib ElementTree), `pdf/` (`PageGeometry`, `LayoutProfile`, `PDFRenderer`; `_deps.require_fpdf()` guards the optional extra).
- **`cli.py`**: argparse `validate` and `render --format {html,text,fountain,json,fdx,pdf}` subcommands; `-` reads stdin.
- Writer tools (notes, boneyard, sections, synopses) are omitted by every formatted renderer but kept by `FountainRenderer`.

### Test Organization
- `test_parser.py`, `test_edge_cases.py` (spec compliance in `TestSpecCompliance`, plus `TestToolingCompliance`, which git-greps tracked files and forbids the word "pre-commit" in the justfile, docs, src, and CI), `test_renderer.py`, `test_document.py`, `test_cli.py`, the per-renderer `test_*_renderer.py` files, and `test_quickstart_examples.py` (validates the quickstart doc examples).
- `test_properties.py`: hypothesis property tests (parse totality, span bounds, JSON round trip).
- `tests/fixtures/`: sample `.fountain` / `.fdx` files, loaded via `conftest.py`.

## Tool Configuration
- **ruff** and **mypy** use the python skill's canonical blocks verbatim (`select = ["E","W","F","I","N","UP","B","SIM","C4","TC"]`, `strict = true`); fix code rather than adding ignores. Ruff's target comes from `requires-python`.
- **pytest**: strict markers, `--doctest-modules`, warnings are errors (except User/Deprecation warnings).
- **CI** (`ci.yml`): matrix 3.11 through 3.15 with `UV_PYTHON` pinned per entry, pip-audit, monthly schedule; separate jobs prove the base install has no fpdf, run the PDF suite, build the wheel, and run Sphinx doctests. `docs.yml` deploys Sphinx to GitHub Pages on pushes to `main` and on releases. `publish.yml` publishes to PyPI on a GitHub Release; `test-publish.yml` is a manual TestPyPI dry run.

## Release Status
- 0.2.0 is published on PyPI. Changes since then live under `## [Unreleased]` in `CHANGELOG.md` and `docs/source/changelog.rst` (keep both in sync).
- Python floor is 3.11 (3.10 dropped at its October 2026 EOL).
