# fountain-py 0.2.0 Implementation Plan

This plan turns the 0.2.0 scope in `spec.md` (the "0.2.0: Output Modes and Interchange" section, ruled 2026-08-15) into an executable roadmap.
0.1.0 shipped to PyPI on 2026-08-08; the 0.1.0 body of the spec is contract, not work.
The theme is output modes: finish JSON as interchange, formalize the renderer contract, and add plain-text, CLI, FDX, and PDF outputs.

Rulings baked in from the review (Open Questions 13-16): the CLI executable is `fountain`; the PDF extra uses `fpdf2`; `HALF_LETTER` geometry ships now while the `STAGE_PLAY` layout profile is deferred; FDX omits the writer tools (NOTE, SECTION, SYNOPSIS, BONEYARD), matching the HTML contract.

## How to Execute

Each Feature step is one prompt: write the failing test first (RED), run `uv run pytest <path>` to watch it fail, implement the minimal change (GREEN), refactor if needed, then run `just test` before moving on.
Task steps follow Scope / Tooling / Do / Verify / Document.
Load the `python:python` skill at the start of every code step; it is the source of truth for typing, ruff/mypy/pytest config, and the TDD loop.

Hard gate on every step (unchanged from 0.1.0):

- The existing suite keeps passing, plus the new tests each step adds.
- Coverage stays 99%+ (`just unit-test-cov`).
- `mypy --strict src/` passes; no `Any`, `X | None` typing throughout.
- `just test` runs clean.

Module layout decision (resolving the spec's open layout question): new renderers live under a new `fountain/renderers/` package, one module per format, so `renderer.py` does not keep growing.
`HTMLRenderer` and `FountainRenderer` stay in `src/fountain/renderer.py` (moving them is an out-of-scope refactor); the package holds the shared renderer protocols and every new renderer.

Sequencing rationale: the JSON fix and interchange land first (they touch the document core every later format reuses); the renderer protocol and package scaffold come next so every new renderer targets one interface; plain text, CLI, and FDX build on that; PDF is last among features because of its optional-dependency machinery; documentation and the version bump close the release.

## Current Status

| Section | Focus | Steps | Status |
|---|---|---|---|
| 1 | Serialization and JSON interchange (Group F) | 1.1-1.3 | Not started |
| 2 | Renderer protocol and package (Group G) | 2.1 | Not started |
| 3 | Plain-text renderer (Group H) | 3.1 | Not started |
| 4 | Command-line interface (Group I) | 4.1 | Not started |
| 5 | FDX export (Group J) | 5.1 | Not started |
| 6 | PDF export (Group K) | 6.1-6.5 | Not started |
| 7 | Documentation and truth-up (Group L) | 7.1-7.2 | Not started |
| 8 | Release mechanics | 8.1 | Not started |

---

## Section 1: Serialization and JSON Interchange

**Tools:**
- Skills: python:python
- MCPs: none
- Linters: uv run ruff check src/ tests/

Fix the shipped `to_json` crash, version the schema, and add deserialization so JSON becomes interchange rather than a one-way export.
Every later format reuses `to_dict`, so this lands first.

### Step 1.1: F1 - recursively serialize nested elements in to_dict

**NOTE**: `to_dict()` (src/fountain/document.py:107-165) passes `element.metadata` through verbatim. DUAL_DIALOGUE metadata holds live `FountainElement` objects (`left_character`, `right_character`) and lists of them (`left_dialogue`, `right_dialogue`), so `json.dumps` raises `TypeError`. No existing test serializes a dual-dialogue document.

```text
Implement Step 1.1 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_document.py a class TestJsonSerialization:
   - test_to_json_handles_dual_dialogue: parse "BRICK\nHi.\n\nSTEEL^\nHello." (a dual-dialogue scene), call doc.to_json(), and assert json.loads(...) round-trips to a dict; assert the dual_dialogue element's metadata["left_character"] is a dict with "type" == "character" and "text" == "BRICK", and metadata["left_dialogue"] is a list of element dicts.
   - test_to_dict_nested_elements_match_top_level_shape: assert a nested element dict has exactly the keys {"type","text","formatting","line_number","metadata"}, the same shape as a top-level element dict.
   Run `uv run pytest tests/test_document.py -k TestJsonSerialization` and confirm it FAILS with TypeError from json.dumps.

2. GREEN: src/fountain/document.py:
   - Extract the element-to-dict conversion into a module-level helper `_element_to_dict(element: FountainElement) -> dict[str, object]`.
   - In that helper, serialize the metadata dict recursively: a FountainElement value becomes `_element_to_dict(value)`; a list value maps each FountainElement item through `_element_to_dict` (leaving non-element list items as-is); all other values pass through.
   - Rewrite `to_dict()` to build elements via `_element_to_dict`.

3. REFACTOR: ensure `_element_to_dict` is the single place element serialization happens; remove the inline dict comprehension duplication.

4. Verify: run `just test`. Acceptance: to_json() on a dual-dialogue document returns valid JSON; nested character/dialogue elements carry the same dict shape as top-level elements; coverage stays 99%+.
```

### Step 1.2: F2 - versioned JSON schema and reference page

**NOTE**: The JSON shape becomes a documented, versioned contract. `schema_version` is a top-level key alongside `metadata` and `elements`.

```text
Implement Step 1.2 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_document.py::TestJsonSerialization:
   - test_to_dict_carries_schema_version: assert FountainDocument([]).to_dict()["schema_version"] == 1.
   - test_schema_version_is_module_constant: assert the value equals a module-level constant `JSON_SCHEMA_VERSION` imported from fountain.document.
   Run the tests and confirm they FAIL.

2. GREEN: src/fountain/document.py:
   - Add module-level `JSON_SCHEMA_VERSION = 1`.
   - Add `"schema_version": JSON_SCHEMA_VERSION` as a top-level key in the dict `to_dict()` returns (alongside "metadata" and "elements").

3. Document: create docs/source/reference/json-schema.rst:
   - Document the top-level shape ({schema_version, metadata, elements}), the element dict shape ({type, text, formatting, line_number, metadata}), the formatting-span shape ({start, end, format_type}), and the nested dual-dialogue metadata (left_character/right_character as element dicts, left_dialogue/right_dialogue as lists of element dicts).
   - Add `reference/json-schema` to the Reference toctree in docs/source/index.rst.

4. Verify: run `just test` and `uv run sphinx-build -b html docs/source docs/build/html`. Acceptance: to_dict()["schema_version"] == 1; json-schema.rst exists and resolves in the toctree; the docs build has no new warnings.
```

### Step 1.3: F3 - from_dict and from_json deserialization

**NOTE**: Deserialization reconstructs a document, including nested elements in metadata, so JSON becomes a real interchange format. An unknown schema version is a hard error.

```text
Implement Step 1.3 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_document.py::TestJsonSerialization:
   - test_from_json_round_trips: for each of a corpus of scripts (a dual-dialogue scene; a line with **bold** and *italic* and _underline_ formatting; a scene heading with #2A# scene number; a "SARAH (V.O.)" extension; a full title page with author and draft date), assert FountainDocument.from_json(doc.to_json()).to_dict() == doc.to_dict().
   - test_from_dict_reconstructs_types: assert a reconstructed element's `type` is an ElementType member (not a str) and its `formatting` entries are FormatSpan instances.
   - test_from_dict_unknown_schema_version_raises: assert FountainDocument.from_dict({"schema_version": 999, "metadata": {}, "elements": []}) raises ValueError.
   Run the tests and confirm they FAIL.

2. GREEN: src/fountain/document.py:
   - Add classmethods `from_dict(cls, data: dict[str, object]) -> FountainDocument` and `from_json(cls, text: str) -> FountainDocument`.
   - from_dict: reject a schema_version other than JSON_SCHEMA_VERSION with ValueError; rebuild each element with a module-level `_element_from_dict` that maps `type` back to ElementType(value), `formatting` back to FormatSpan(**span), and recursively rebuilds FountainElement values and lists in metadata (the inverse of _element_to_dict).
   - from_json: json.loads then from_dict.

3. REFACTOR: keep _element_from_dict as the single inverse of _element_to_dict; assert with a comment that the two stay symmetric.

4. Verify: run `just test`. Acceptance: from_json(to_json(doc)) round-trips to_dict()-equal over the corpus including dual dialogue; reconstructed types are ElementType/FormatSpan; an unknown schema_version raises ValueError; coverage stays 99%+.
```

---

## Section 2: Renderer Protocol and Package

**Tools:**
- Skills: python:python
- MCPs: none
- Linters: uv run ruff check src/ tests/

Formalize the renderer contract the docs teach informally, and create the package every new renderer lives in.

### Step 2.1: G1 - renderer protocols and the renderers package

**NOTE**: `HTMLRenderer`/`FountainRenderer` stay in renderer.py; the protocols and new renderers live in a new `fountain/renderers/` package. `__init__.py` for the package stays empty per the python skill's package rule.

```text
Implement Step 2.1 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_renderer_protocol.py:
   - test_text_renderer_is_runtime_checkable: import TextRenderer from fountain; assert isinstance(HTMLRenderer(), TextRenderer) and isinstance(FountainRenderer(), TextRenderer).
   - test_binary_renderer_protocol_shape: assert BinaryRenderer is runtime_checkable and a trivial object with a render_bytes(document)->bytes method satisfies it, while HTMLRenderer (no render_bytes) does not.
   - test_protocols_exported: assert "TextRenderer" and "BinaryRenderer" are in fountain.__all__.
   Run `uv run pytest tests/test_renderer_protocol.py` and confirm it FAILS (import error expected).

2. GREEN:
   - Create the package: src/fountain/renderers/__init__.py (empty).
   - Create src/fountain/renderers/base.py defining two `@runtime_checkable` `Protocol`s: `TextRenderer` with `render(self, document: FountainDocument) -> str`, and `BinaryRenderer` with `render_bytes(self, document: FountainDocument) -> bytes`. Use absolute imports; full type hints.
   - src/fountain/__init__.py: import TextRenderer and BinaryRenderer from fountain.renderers.base and add both to __all__ (keep __init__ logic-free: imports, __all__, docstring only).

3. Verify: run `just test`. Acceptance: isinstance(HTMLRenderer(), TextRenderer) holds structurally with no inheritance change; both protocols import from fountain top level and appear in __all__; mypy --strict clean.
```

---

## Section 3: Plain-Text Renderer

**Tools:**
- Skills: python:python
- MCPs: none
- Linters: uv run ruff check src/ tests/

### Step 3.1: H1 - PlainTextRenderer

**NOTE**: Monospace screenplay layout with column positions as constructor parameters. Writer tools omitted, matching the HTML contract. Reuse the existing dual-dialogue metadata shape for the two columns.

```text
Implement Step 3.1 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_plaintext_renderer.py:
   - test_relative_indents: render a script with a scene heading, an action line, a character cue, a parenthetical, and a dialogue line; assert the scene heading and action start at column 0, and that cue-indent > parenthetical-indent > dialogue-indent > 0 (measure leading spaces of each rendered line).
   - test_wrap_never_exceeds_width: render an action paragraph longer than the width with a small PlainTextRenderer(width=40); assert no output line exceeds 40 characters.
   - test_transition_right_aligned: render "CUT TO:" as a transition; assert its line ends at the right edge (width).
   - test_writer_tools_omitted: render a doc containing NOTE, SECTION, SYNOPSIS, and BONEYARD; assert none of their text appears in the output.
   - test_satisfies_text_renderer: assert isinstance(PlainTextRenderer(), TextRenderer).
   Run the tests and confirm they FAIL (import error expected).

2. GREEN: create src/fountain/renderers/plaintext.py:
   - PlainTextRenderer with constructor params width=60, dialogue_indent=10, parenthetical_indent=15, cue_indent=22 (tune only if a RED test on a real fixture forces it).
   - render(document) walks elements: SCENE_HEADING upper flush left; ACTION wrapped flush left via textwrap at width; CHARACTER at cue_indent; PARENTHETICAL at parenthetical_indent; DIALOGUE wrapped at dialogue_indent within the narrower column; TRANSITION right-aligned to width; PAGE_BREAK as a divider line of "=" to width; one blank line between blocks; DUAL_DIALOGUE renders left then right block (single-column stacking is acceptable for text). Omit NOTE, SECTION, SYNOPSIS, BONEYARD.

3. Integrate: export PlainTextRenderer from fountain top level (add to fountain.renderers import surface and to fountain.__all__), keeping __init__ logic-free.

4. REFACTOR: factor the "indent + wrap a block to a column" logic into one private helper the element cases share.

5. Verify: run `just test`. Acceptance: all relative-position and wrap assertions hold; writer tools never appear; PlainTextRenderer satisfies TextRenderer; coverage stays 99%+.
```

---

## Section 4: Command-Line Interface

**Tools:**
- Skills: python:python
- MCPs: none
- Linters: uv run ruff check src/ tests/

### Step 4.1: I1 - the fountain CLI

**NOTE**: Console script name is `fountain` (Open Question 13). argparse only, zero new runtime dependencies. Reuse `validate()` and the renderers. `pdf` format routes to the PDF renderer, which is added in Section 6; until then the `pdf` branch raises the missing-extra error, and Section 6 wires the real renderer behind the same guard.

```text
Implement Step 4.1 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_cli.py using subprocess to invoke `python -m fountain.cli` (the console-script entry calls the same main):
   - test_validate_clean_exits_zero: `validate` on a well-formed script file (written to tmp_path) prints nothing to stderr and exits 0.
   - test_validate_errors_exit_one: `validate` on a file containing an unclosed `/*` prints a line matching `\d+:error:unclosed-boneyard:` and exits 1.
   - test_render_html_to_stdout: `render <file> --format html` writes output containing `<div class="fountain-script">` to stdout and exits 0.
   - test_render_json_matches_to_json: `render <file> --format json` output equals FountainParser().parse_file(file).to_json().
   - test_render_stdin: piping a script to `render - --format text` renders from stdin.
   - test_render_to_output_file: `render <file> --format fountain -o OUT` writes to OUT and stdout is empty.
   - test_pdf_without_extra_errors: `render <file> --format pdf` (with fpdf2 not installed) exits non-zero with a message naming `pip install "fountain-py[pdf]"`.
   Run `uv run pytest tests/test_cli.py` and confirm it FAILS.

2. GREEN: create src/fountain/cli.py:
   - argparse with subcommands `validate` (positional file) and `render` (positional file, `--format` choices html/text/fountain/json/fdx/pdf, `-o/--output`).
   - `-` as file reads stdin; otherwise parse_file.
   - validate: print each ValidationIssue as `line_number:severity:code:message`; exit 1 if any issue has severity == "error", else 0.
   - render: map format to renderer (html -> HTMLRenderer().render_page; text -> PlainTextRenderer; fountain -> FountainRenderer; json -> to_json; fdx -> FDXRenderer once Section 5 lands; pdf -> PDF renderer once Section 6 lands). For pdf, attempt the import and on ImportError exit with the message `Install the PDF extra: pip install "fountain-py[pdf]"`.
   - `main(argv: list[str] | None = None) -> int` returns the exit code; a `__main__` guard calls sys.exit(main()).

3. Integrate: add `[project.scripts]` to pyproject.toml: `fountain = "fountain.cli:main"`.

4. REFACTOR: keep the format-to-renderer mapping in one dict/function so Sections 5 and 6 only add an entry.

5. Verify: run `just test`. Acceptance: `[project.scripts]` has the `fountain` entry; subprocess tests cover both subcommands, both exit codes, stdin, output-file, and the missing-extra message; coverage stays 99%+.
```

---

## Section 5: FDX Export

**Tools:**
- Skills: python:python
- MCPs: none
- Linters: uv run ruff check src/ tests/

### Step 5.1: J1 - FDXRenderer

**NOTE**: Final Draft interchange XML using only `xml.etree.ElementTree`. Writer tools (NOTE, SECTION, SYNOPSIS, BONEYARD) are omitted per Open Question 16. The dual-dialogue attribute form is the one detail to pin against a real FDX sample; encode the pinned form in a fixture.

```text
Implement Step 5.1 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_fdx_renderer.py:
   - test_output_is_wellformed_xml: FDXRenderer().render(doc) parses with xml.etree.ElementTree.fromstring without error, and the root tag is "FinalDraft".
   - test_paragraph_type_mapping: render a doc with a scene heading, action, character, parenthetical, dialogue, and transition; assert one <Paragraph Type="Scene Heading">, "Action", "Character", "Parenthetical", "Dialogue", and "Transition" each, with the element text inside a <Text> child.
   - test_title_page_maps: render a doc with title and author metadata; assert the FDX title-page structure carries both.
   - test_dual_dialogue_emits_both_blocks: render a dual-dialogue doc; assert both character names appear as Character paragraphs in the pinned dual-dialogue encoding (compare against tests/fixtures/dual_dialogue.fdx).
   - test_writer_tools_omitted: render a doc with NOTE/SECTION/SYNOPSIS/BONEYARD; assert none of their text appears in the XML.
   - test_satisfies_text_renderer: assert isinstance(FDXRenderer(), TextRenderer).
   Run the tests and confirm they FAIL.

2. GREEN:
   - Create tests/fixtures/dual_dialogue.fdx: a minimal hand-authored FDX document with one dual-dialogue pair, used to pin the encoding.
   - Create src/fountain/renderers/fdx.py: FDXRenderer building the tree with ElementTree. Map SCENE_HEADING/ACTION/CHARACTER/PARENTHETICAL/DIALOGUE/TRANSITION to <Paragraph Type="..."> with a <Text> child; map the title page to the FDX TitlePage structure; map CENTERED and LYRICS to the nearest Paragraph type with alignment where FDX supports it; emit dual dialogue as the two Character blocks matching the fixture's encoding; skip the four writer-tool types. Return ElementTree.tostring(..., encoding="unicode").

3. Integrate: export FDXRenderer from fountain top level; add the `fdx` entry to the CLI format-to-renderer mapping from Step 4.1.

4. REFACTOR: keep the element-type-to-FDX-paragraph-type map as a module-level dict.

5. Verify: run `just test`. Acceptance: output parses with ElementTree; the per-type mapping and dual-dialogue encoding match the fixture; writer tools omitted; FDXRenderer satisfies TextRenderer; coverage stays 99%+.
```

---

## Section 6: PDF Export

**Tools:**
- Skills: python:python
- MCPs: none
- Linters: uv run ruff check src/ tests/

PDF ships as the optional extra `fountain-py[pdf]` on `fpdf2` (Open Question 14). Geometry and layout are orthogonal data; `HALF_LETTER` ships, the `STAGE_PLAY` profile is deferred (Open Question 15). Build the extra and the import guard first, then the geometry and profile data, then the renderer, then CI.

### Step 6.1: K3 (part 1) - the [pdf] optional extra and import guard (task)

**NOTE**: Landing the extra and the guard first lets every later PDF step assume fpdf2 is importable under the extra, and gives the CLI's pdf branch (Step 4.1) its real target.

```text
1. Scope:
   - Artifact(s): pyproject.toml, src/fountain/renderers/pdf/__init__.py (new subpackage).
   - Desired end state: `pip install "fountain-py[pdf]"` installs fpdf2; importing the PDF renderer without it raises a clear, install-command-naming error.

2. Tooling:
   - Skills: python:python
   - MCPs: none
   - External: uv

3. Do the work:
   - pyproject.toml: add `[project.optional-dependencies]` with `pdf = ["fpdf2>=2.7"]`; add fpdf2 to the dev dependency group so the suite can exercise PDF locally.
   - Create the subpackage src/fountain/renderers/pdf/__init__.py (empty).
   - Create src/fountain/renderers/pdf/_deps.py with a helper `require_fpdf()` that imports fpdf and, on ImportError, raises ImportError('Install the PDF extra: pip install "fountain-py[pdf]"').

4. Verify:
   - `uv sync --dev` succeeds and `python -c "import fpdf"` works; `uv run ruff check src/` is clean.

5. Document: none (Section 7 documents PDF).
```

### Step 6.2: K1 - page geometry presets

**NOTE**: Geometry is pure data: page size, margins, binding offset. Presets plus custom. Unit-testable without producing a PDF.

```text
Implement Step 6.2 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_pdf_geometry.py:
   - test_presets_dimensions: assert LETTER is (8.5, 11.0) inches, A4 is (8.27, 11.69) inches (210x297mm within 0.02in), HALF_LETTER is (5.5, 8.5) inches, reading a PageGeometry's width_in/height_in.
   - test_custom_geometry: PageGeometry(width_in=6, height_in=9, margin_in=1, binding_offset_in=0.25) exposes those values.
   - test_text_block_shrinks_with_binding_offset: a geometry with a binding offset has a smaller usable text width than the same geometry without one (assert a `text_width_in` property reflects margins + binding offset).
   Run the tests and confirm they FAIL.

2. GREEN: create src/fountain/renderers/pdf/geometry.py:
   - A frozen `PageGeometry` dataclass with width_in, height_in, top/bottom/left/right margins (or a single margin_in), binding_offset_in, and a computed `text_width_in`.
   - Module constants LETTER, A4, HALF_LETTER as PageGeometry instances.

3. Verify: run `just test`. Acceptance: preset dimensions match; custom geometry carries its values; binding offset measurably reduces text_width_in; mypy --strict clean.
```

### Step 6.3: K2 - the SCREENPLAY layout profile

**NOTE**: Layout is a data-driven profile (per-element indent, width, font), separate from geometry. Only SCREENPLAY ships; STAGE_PLAY is deferred.

```text
Implement Step 6.3 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_pdf_profile.py:
   - test_screenplay_profile_fields: assert SCREENPLAY.font_name == "Courier", font_size_pt == 12, and that it exposes a per-element-type indent map covering SCENE_HEADING, ACTION, CHARACTER, PARENTHETICAL, DIALOGUE, TRANSITION with cue indent > parenthetical indent > dialogue indent > action indent.
   - test_profile_is_data_only: assert the profile object has no methods beyond the dataclass-generated ones (it is pure data the renderer consumes).
   Run the tests and confirm they FAIL.

2. GREEN: create src/fountain/renderers/pdf/profile.py:
   - A frozen `LayoutProfile` dataclass: font_name, font_size_pt, and a mapping of ElementType to per-element layout (left indent and column width in inches).
   - Module constant SCREENPLAY with the conventional Courier-12 screenplay indents.

3. Verify: run `just test`. Acceptance: SCREENPLAY carries the documented font and indent map with the correct relative ordering; the profile is data only; mypy --strict clean.
```

### Step 6.4: PDFRenderer tying geometry and profile

**NOTE**: The renderer consumes a PageGeometry and a LayoutProfile and emits bytes via fpdf2. It satisfies the BinaryRenderer protocol. Tests read the PDF back to assert geometry and element order.

```text
Implement Step 6.4 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_pdf_renderer.py (these tests require the [pdf] extra, installed in dev):
   - test_media_box_matches_geometry: render_bytes with geometry=HALF_LETTER; parse the produced PDF (with fpdf2's own reader or pypdf if already available, else assert the page-size bytes fpdf writes) and assert the page is 5.5x8.5in.
   - test_binding_offset_shifts_text_block: two renders, one with binding_offset_in=0 and one with 0.5; assert the left start of body text differs.
   - test_text_extracts_in_element_order: render a scene heading then action then a character/dialogue block; extract the text and assert the strings appear in document order.
   - test_satisfies_binary_renderer: assert isinstance(PDFRenderer(), BinaryRenderer).
   Run the tests and confirm they FAIL.

2. GREEN: create src/fountain/renderers/pdf/renderer.py:
   - PDFRenderer(geometry: PageGeometry = SCREENPLAY-compatible default LETTER, profile: LayoutProfile = SCREENPLAY). Call require_fpdf() in __init__.
   - render_bytes(document) builds an fpdf document at the geometry's page size and margins (plus binding offset on the left), sets the profile font, and writes each element at its profile indent/width, wrapping as needed; omit the four writer-tool types; return the PDF bytes.

3. Integrate: export PDFRenderer, PageGeometry, LayoutProfile, and the presets (LETTER, A4, HALF_LETTER, SCREENPLAY) from fountain top level; wire the `pdf` entry in the CLI format-to-renderer mapping so `render --format pdf` calls PDFRenderer behind require_fpdf().

4. REFACTOR: keep geometry-to-fpdf setup and profile-to-write logic in small private helpers.

5. Verify: run `just test`. Acceptance: the media box matches the geometry; binding offset shifts the text block; text extracts in element order; PDFRenderer satisfies BinaryRenderer; coverage stays 99%+.
```

### Step 6.5: K3 (part 2) - CI jobs for the extra (task)

**NOTE**: One CI job proves the core works with no extra installed; another installs `[pdf]` and runs the PDF tests.

```text
1. Scope:
   - Artifact(s): .github/workflows/ci.yml.
   - Desired end state: CI proves the base install is dependency-free and functional, and separately runs the PDF suite under the [pdf] extra.

2. Tooling:
   - Skills: python:python
   - MCPs: none
   - External: none

3. Do the work:
   - Add a `base-install` job: install without the extra (`uv sync` without the pdf group), then `python -c "import fountain; from fountain import FountainParser; FountainParser().parse('INT. X - DAY')"` and assert `python -c "import fpdf"` FAILS (prove zero-dependency core).
   - Add a `pdf` job: install the extra (`uv sync --dev` includes fpdf2, or `uv pip install "fountain-py[pdf]"`), then `uv run pytest tests/test_pdf_renderer.py tests/test_pdf_geometry.py tests/test_pdf_profile.py`.
   - Keep the existing matrix test job unchanged.

4. Verify:
   - The workflow is valid YAML (`python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`).

5. Document: none.
```

---

## Section 7: Documentation and Truth-Up

**Tools:**
- Skills: python:python
- MCPs: none
- Linters: vale docs/source/

Docs land with the features, under the existing Diataxis tree, and pass the Vale gate. Do not start until Sections 1-6 are green.

### Step 7.1: L1 - how-to guides for the new modes (task)

**NOTE**: One how-to per new mode plus the JSON deserialization guidance, all Vale-clean, every code claim verified against the implementation.

```text
1. Scope:
   - Artifact(s): docs/source/how-to/use-the-cli.rst, docs/source/how-to/export-plain-text.rst, docs/source/how-to/export-fdx.rst, docs/source/how-to/export-pdf.rst; docs/source/how-to/export-to-json.rst (extend with from_json); docs/source/index.rst toctree.
   - Desired end state: each new mode has a task-focused how-to in the How-to Guides toctree; the JSON how-to covers to_json and from_json; the json-schema reference (from Step 1.2) is linked.

3. Do the work:
   - Write each how-to using verified code (run the snippets or mirror the tested behavior): the CLI (validate and render, exit codes, stdin, the pdf extra), plain-text export, FDX export, PDF export (geometry presets including HALF_LETTER, and layout profiles).
   - Extend export-to-json.rst with from_json / from_dict round-tripping and a link to reference/json-schema.
   - Add all new how-to pages to the How-to Guides toctree in index.rst.

4. Verify:
   - `uv run sphinx-build -b html docs/source docs/build/html` has no new warnings; `vale docs/source/` reports zero errors.

5. Document: this step is the documentation.
```

### Step 7.2: L2 - README, landing page, and CHANGELOG truth-up (task)

**NOTE**: Name the new modes in the feature lists; no hand-counted metrics reintroduced.

```text
1. Scope:
   - Artifact(s): README.md, docs/source/index.rst (Features), CHANGELOG.md.
   - Desired end state: the feature lists name JSON interchange, the CLI, and the plain-text/FDX/PDF renderers; the CHANGELOG has a 0.2.0 entry; no hand-counted test/coverage numbers appear.

3. Do the work:
   - README.md and index.rst Features: add the new output modes and the CLI.
   - CHANGELOG.md: add a 0.2.0 section listing the F-through-L capabilities (capability-level entries, not per-commit).

4. Verify:
   - `uv run sphinx-build -b html docs/source docs/build/html` and the doctest build stay green; `vale docs/source/` reports zero errors; `grep -rE '[0-9]+ tests' README.md docs/source` finds no hand-counted metric.

5. Document: this step is the documentation.
```

---

## Section 8: Release Mechanics

**Tools:** none

### Step 8.1: bump the version to 0.2.0 and run the full gate (task)

**NOTE**: The merge, tag, and Release are human-gated (Mason merges to main), documented in docs/source/contributing/releasing.rst. This step only prepares the branch.

```text
1. Scope:
   - Artifact(s): pyproject.toml.
   - Desired end state: the package version reads 0.2.0 and the full quality gate is green on the branch, ready for Mason to merge and release.

3. Do the work:
   - pyproject.toml: set `version = "0.2.0"`.

4. Verify:
   - `just test` passes clean (full suite, doctests, ruff, mypy, format); `uv build` produces `fountain_py-0.2.0` wheel and sdist.

5. Document: none; the release steps (merge to main, tag v0.2.0, cut the Release) are the human-gated flow in contributing/releasing.rst.
```

---

## Implementation Guidelines

- One step per commit; each commit includes a new `.ai-sessions/session-*.md` (the finalize dispatch creates it).
- Never commit to `main`; `0.2.0-dev` is the feature branch. Mason merges to `main`.
- Never split, reorder, or skip RED-before-GREEN; the failing test must exist and fail before the fix.
- Keep `src/fountain/__init__.py` logic-free (imports, `__all__`, module docstring only); package `__init__.py` files stay empty.
- The core stays zero-dependency; `fpdf2` lives only in the `[pdf]` extra and the dev group.
- After every step, `just test` must pass clean at 99%+ coverage with `mypy --strict src/` green.

## Success Metrics

- All items in `todo.md` checked off.
- `to_json()` works on dual dialogue; `from_json(to_json(doc))` round-trips; the JSON schema is versioned and documented.
- `TextRenderer` / `BinaryRenderer` protocols ship; `HTMLRenderer`, `FountainRenderer`, `PlainTextRenderer`, `FDXRenderer` satisfy `TextRenderer`; `PDFRenderer` satisfies `BinaryRenderer`.
- `fountain validate` and `fountain render --format {html,text,fountain,json,fdx,pdf}` work; `pdf` without the extra prints the install command.
- FDX output parses as XML and matches the pinned fixture; writer tools omitted.
- `fountain-py[pdf]` produces PDFs at LETTER/A4/HALF_LETTER geometry with the SCREENPLAY profile; the base install stays dependency-free (CI proves both).
- Docs cover every new mode, pass Vale with zero errors, and reintroduce no hand-counted metrics.
- `pyproject` version is 0.2.0 and `just test` is green, ready for the human-gated release.
