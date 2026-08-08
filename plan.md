# fountain-py 0.1.0 Implementation Plan

**Read `handoff.md` first.**
It states the current tree, Mason's settled rulings, and the exact next action; this plan assumes that context.

This plan turns the committed `spec.md` (commit 1056da5, dated 2026-07-03) into an executable TDD roadmap for a 0.1.0 PyPI release.
Each step below is a self-contained prompt for an implementation model: it names the failing test to add first (RED), the minimal source change (GREEN), any cleanup (REFACTOR), the exact file paths, and the acceptance criterion.
The target version is 0.1.0 throughout; there is no 0.2.0 in this release.

Scope comes straight from the spec's rulings dated 2026-07-03:

- No compliance waivers: every requirement in Groups A through E is fixed with a pinned test, regardless of severity.
- The Validation API (`FountainParser.validate` returning `ValidationIssue`) ships in 0.1.0.
- `HTMLRenderer` and `FountainRenderer` are promoted into the top-level `__all__`; `__init__.py` stays restricted to re-exports, `__all__`, and the module docstring, with no logic.
- The Python floor moves to 3.10; the ceiling tracks current CPython (3.10 through 3.14 now, 3.15 on release).
- Every published claim (the README and CHANGELOG "Full Fountain Spec Compliance" line) is made true before publish.

Out of scope for 0.1.0 (deferred by ruling): the parser pipeline and dual-dialogue-post-pass refactor and any `Counter` restructuring (Open Question 12: no refactor before the design pass).
Also out of scope: PDF, JSON-schema, and XML output modes (post-0.1.0 phases).

## How to Execute

Each step is one prompt in a `text` fence, structured RED, GREEN, then optional REFACTOR, then a verify gate.
Write the failing test first, run `uv run pytest <path>` to watch it fail, implement the minimal change, then run `just test` before moving on.
Load the `python:python` skill at the start of every code step; it is the source of truth for typing, ruff/mypy/pytest config, and the TDD loop.

The quality bar from the spec is a hard gate on every step:

- The current 241 tests keep passing, plus the new tests each step adds.
- Coverage stays at 99%+ (`just unit-test-cov`).
- `mypy --strict src/` passes.
- `just test` runs clean (it includes `just fix`, which may rewrite files; that is intentional per Open Question 11).

Test placement conventions:

- Compliance fixes: `tests/test_edge_cases.py`, `TestSpecCompliance` class.
- Renderer behavior: `tests/test_renderer.py`.
- Validation API: `tests/test_validation.py` (new file).
- Document analysis: `tests/test_document.py`.

Sequencing rationale: the Python floor and type work land first so all later code is written in 3.10 idioms; the Validation API and compliance fixes come next; documentation truth-up follows once compliance is real; the PyPI pipeline is last.

## Current Status

| Section | Focus | Steps | Status |
|---|---|---|---|
| 1 | Python floor and type system | 1.1–1.3 | Not started |
| 2 | Package API surface | 2.1–2.2 | Not started |
| 3 | Validation API | 3.1–3.3 | Not started |
| 4 | Compliance Group E (boneyard, notes, sections) | 4.1–4.10 | Not started |
| 5 | Compliance Group A (title page, whitespace) | 5.1–5.7 | Not started |
| 6 | Compliance Group B (scene headings) | 6.1–6.4 | Not started |
| 7 | Compliance Group C (characters, dialogue) | 7.1–7.7 | Not started |
| 8 | Compliance Group D (transitions, emphasis) | 8.1–8.8 | Not started |
| 9 | Documented contract ambiguities | 9.1–9.4 | Not started |
| 10 | Documentation truth-up | 10.1–10.5 | Not started |
| 11 | Tooling cleanup | 11.1 | Not started |
| 12 | Path to PyPI | 12.1–12.4 | Not started |

---

## Section 1: Python Floor and Type System

**Validator consults:**
- Skills: python:python

Move the floor to 3.10, modernize typing, and fix the `MetadataValue` annotation.
Doing this first means every compliance fix below is written clean against the 3.10 ruff target.

### Step 1.1: Move the Python floor to 3.10 in packaging and tooling

**NOTE**: Pure configuration change; the existing 241-test suite and `mypy --strict src/` are the guard, so there is no new RED test. Do this before anything else so later steps are written against the 3.10 target.

```text
Implement Step 1.1 for fountain-py.

1. RED: none. This is a configuration change guarded by the existing suite and `mypy --strict src/`.

2. GREEN: edit pyproject.toml:
   - Set `requires-python = ">=3.10"` (was `>=3.9`).
   - Replace the classifier list so it carries `Programming Language :: Python :: 3.10`, `3.11`, `3.12`, `3.13`, and `3.14`; remove the `3.9` classifier.
   - Under `[tool.ruff]`, set `target-version = "py310"` (was `py39`).
   - Under `[tool.mypy]`, set `python_version = "3.10"` (was `3.9`).

3. Verify: run `just test`; it must pass clean. Acceptance: pyproject.toml declares `>=3.10`, no `3.9` classifier remains, the ruff target is `py310`, and mypy `python_version` is `3.10`.
```

### Step 1.2: Update the CI matrix to 3.10 through 3.14

**NOTE**: CI config only. 3.15 is added to the matrix when it releases (October 2026) and is out of scope for this release.

```text
Implement Step 1.2 for fountain-py.

1. RED: none (CI config).

2. GREEN: edit .github/workflows/ci.yml:
   - Change the matrix `python-version` to `["3.10", "3.11", "3.12", "3.13", "3.14"]` (was `3.9` through `3.13`).
   - Keep the Codecov upload gated on `matrix.python-version == '3.12'`.

3. Verify: Acceptance: the ci.yml matrix lists 3.10 through 3.14 with no `3.9` entry; the file is valid YAML.
```

### Step 1.3: Modernize typing to `X | None` and apply `MetadataValue` (CR-2)

**NOTE**: `MetadataValue` is already defined and exported in elements.py; this step applies it to the annotation and sweeps `Optional`/`Union` out of `src/`. The alias stays defined and exported (ruling 2026-07-03: do not drop it).

```text
Implement Step 1.3 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_metadata_annotation_uses_metadatavalue:
   - Test that FountainElement's `metadata` field annotation resolves to `dict[str, MetadataValue] | None` (inspect via typing.get_type_hints or the raw __annotations__ string).
   Run `uv run pytest tests/test_edge_cases.py -k test_metadata_annotation_uses_metadatavalue` and confirm it FAILS.

2. GREEN:
   - src/fountain/elements.py: change FountainElement.metadata from `dict[str, Any] | None` to `dict[str, MetadataValue] | None`.
   - src/fountain/parser.py: change the metadata locals' annotations (around lines 667, 703, 759) from `dict[str, Any]` to `dict[str, MetadataValue]`.
   - Sweep all of src/fountain/ for `Optional[X]` and `Union[...]`; rewrite to `X | None` / `X | Y` per ruff UP007. Remove now-unused `Optional`/`Union` imports.

3. Verify: run `just test`. Acceptance: FountainElement.metadata is annotated `dict[str, MetadataValue] | None`; `mypy --strict src/` passes; `uv run ruff check src/` reports no UP007 findings.
```

---

## Section 2: Package API Surface

**Validator consults:**
- Skills: python:python

Promote the renderers and fix the file headers.
These are low-risk surface changes that later sections and the docs depend on.

### Step 2.1: Promote HTMLRenderer and FountainRenderer to the top-level `__all__` (Open Question 7)

**NOTE**: The library re-export pattern is the accepted exception to the empty-`__init__` rule. `__init__.py` must stay logic-free: imports, `__all__`, and the module docstring only. `DEFAULT_CSS`, `TITLE_PAGE_FIELD_ORDER`, and `FormatSpan` intentionally stay out of the top-level `__all__`.

```text
Implement Step 2.1 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_renderers_importable_from_package:
   - Test that `from fountain import HTMLRenderer, FountainRenderer` succeeds.
   - Test that both "HTMLRenderer" and "FountainRenderer" appear in fountain.__all__.
   Run `uv run pytest tests/test_edge_cases.py -k test_renderers_importable_from_package` and confirm it FAILS.

2. GREEN: src/fountain/__init__.py:
   - Add `from fountain.renderer import HTMLRenderer, FountainRenderer`.
   - Add both names to __all__.

3. Verify: run `just test`. Acceptance: `from fountain import HTMLRenderer, FountainRenderer` works; __init__.py contains nothing but imports, __all__, and the module docstring (no logic).
```

### Step 2.2: Fix ABOUTME headers to single-line form (CR-1)

**NOTE**: The rule is that only line one starts with `ABOUTME:`; the second line is a plain continuation comment. renderer.py:1-2 already has the correct form; match it.

```text
Implement Step 2.2 for fountain-py.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_aboutme_header_single_line:
   - For each source file under src/fountain/, read the first two lines and test that only line one starts with `ABOUTME:` (line two is a plain comment, not a second `ABOUTME:`).
   Run `uv run pytest tests/test_edge_cases.py -k test_aboutme_header_single_line` and confirm it FAILS for parser.py, elements.py, and document.py.

2. GREEN: rewrite the module headers so `ABOUTME:` appears on line one only, matching renderer.py:1-2:
   - src/fountain/parser.py:1-2
   - src/fountain/elements.py:1-2
   - src/fountain/document.py:1-2
   - tests/test_edge_cases.py:2-3

3. Verify: run `just test`. Acceptance: every source file's header has `ABOUTME:` on line one only; the test passes across the tree.
```

---

## Section 3: Validation API (Required for 0.1.0)

**Validator consults:**
- Skills: python:python

Add the diagnostic channel the spec requires (Open Question 8, ruled required).
`parse()` stays lenient and non-raising; `validate()` surfaces silent degradation.
The initial code set is four diagnostics: `unclosed-boneyard`, `unclosed-note`, `orphan-character-cue`, `empty-document`.

### Step 3.1: Add the ValidationIssue dataclass

**NOTE**: New public type. Frozen dataclass so issues are hashable and immutable.

```text
Implement Step 3.1 for fountain-py. Load the python:python skill first.

1. RED: create tests/test_validation.py with test_validation_issue_is_frozen_dataclass:
   - Test that ValidationIssue(line_number=1, severity="error", code="x", message="y") constructs and reads back all four fields.
   - Test that assigning to any field raises dataclasses.FrozenInstanceError.
   Run `uv run pytest tests/test_validation.py` and confirm it FAILS (import error is expected).

2. GREEN: src/fountain/elements.py: add a `@dataclass(frozen=True)` ValidationIssue with fields `line_number: int`, `severity: Literal["error", "warning"]`, `code: str`, `message: str`. Import Literal if not already present.

3. Verify: run `just test`. Acceptance: ValidationIssue constructs; field assignment raises; mypy --strict clean.
```

### Step 3.2: Implement FountainParser.validate() with the initial diagnostic set

**NOTE**: `validate()` must run the same two-pass analysis as `parse()` but collect diagnostics instead of discarding them. It must NOT change parse output. Keep the code strings as module-level constants so the growing set has a single source of truth; each shipped code string is contract.

```text
Implement Step 3.2 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_validation.py:
   - test_unclosed_boneyard_reports_error: a document with `/*` and no `*/` returns exactly one issue with code == "unclosed-boneyard", severity == "error", and line_number == the opening line's 1-based number.
   - test_unclosed_note_reports_error: `[[` with no `]]` before EOF returns one "unclosed-note" error at the opening line.
   - test_orphan_character_cue_reports_warning: an uppercase cue demoted to ACTION because no dialogue follows returns one "orphan-character-cue" warning.
   - test_empty_document_reports_warning: input that parses to zero elements returns one "empty-document" warning.
   - test_well_formed_script_returns_empty_list: a valid script returns [].
   - test_validate_does_not_change_parse_output: parse(text).to_dict() is identical whether or not validate(text) ran first.
   Run `uv run pytest tests/test_validation.py` and confirm the new tests FAIL.

2. GREEN: src/fountain/parser.py:
   - Add module-level code constants (e.g. CODE_UNCLOSED_BONEYARD = "unclosed-boneyard", etc.).
   - Add `validate(self, text: str) -> list[ValidationIssue]` that runs the same two-pass analysis as parse() and collects the four diagnostics. Do not mutate the parse contract or shared state in a way that leaks into a later parse().

3. REFACTOR: factor any shared scan helper so validate() and parse() do not duplicate the boneyard/note state tracking.

4. Verify: run `just test`. Acceptance: each diagnostic fires exactly as specced; a well-formed script returns []; parse() output is byte-identical with or without a prior validate() call; coverage stays 99%+.
```

### Step 3.3: Export ValidationIssue from the package top level

**NOTE**: Keep __init__.py logic-free (imports, __all__, docstring only), same constraint as Step 2.1.

```text
Implement Step 3.3 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_validation.py::test_validation_issue_exported:
   - Test that `from fountain import ValidationIssue` works and "ValidationIssue" is in fountain.__all__.
   Run `uv run pytest tests/test_validation.py -k test_validation_issue_exported` and confirm it FAILS.

2. GREEN: src/fountain/__init__.py: import ValidationIssue from fountain.elements and add it to __all__.

3. Verify: run `just test`. Acceptance: `from fountain import ValidationIssue` succeeds; it is listed in __all__; __init__.py still carries no logic.
```

---

## Section 4: Compliance Group E: Boneyard, Notes, Sections

**Validator consults:**
- Skills: python:python

E2 and E3 are the highest-priority fixes in the spec: they silently truncate the document.
Fix them first, then the rest of the group.

### Step 4.1: E2: boneyard close with trailing text ends the boneyard

**NOTE**: The close pattern is currently end-anchored; de-anchor it so `*/` mid-line ends boneyard state and the remainder of the line is reprocessed as body.

```text
Implement Step 4.1 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_boneyard_close_with_trailing_text:
   - Test that a `/*` block closed by `*/ And we are back.` yields an element with text `And we are back.` and every following line as its own element; nothing after the close is dropped.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around lines 140, 554-557): de-anchor the boneyard close pattern so a mid-line `*/` ends boneyard state and the trailing remainder is reprocessed through body classification.

3. Verify: run `just test`. Acceptance: content after `*/` survives as elements.
```

### Step 4.2: E3: single-line boneyard with trailing text does not swallow the document

**NOTE**: Highest-priority truncation defect. Strip the `/* ... */` span and reprocess the remainder rather than consuming the whole line.

```text
Implement Step 4.2 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_single_line_boneyard_keeps_trailing_text:
   - Test that `/* cut this */ keep this` followed by more action yields an element with text `keep this` and the following action as elements.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around lines 132, 136, 140, 568-571): strip the complete `/* ... */` span and reprocess the trailing remainder instead of consuming the line.

3. Verify: run `just test`. Acceptance: `keep this` and the following action survive as elements.
```

### Step 4.3: E4: mid-line boneyard opener does not leak interior lines

```text
Implement Step 4.3 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_midline_boneyard_opener_no_leak:
   - Test that `He waves /* begin cut`, interior lines, then `*/` yields a single ACTION element with text `He waves` and no interior text anywhere in the output.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around lines 136, 568-571): on a mid-line opener, emit the pre-`/*` text as ACTION and enter boneyard state for the rest of the line and following lines until the close.

3. Verify: run `just test`. Acceptance: interior lines never reach output; `He waves` is one ACTION element.
```

### Step 4.4: E1: mid-line `/* ... */` stripped from action and dialogue text

```text
Implement Step 4.4 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_midline_boneyard_stripped_from_text:
   - Test that `Hello /* hidden */ world.` yields an element with text `Hello world.`.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around lines 132-140, 553-571): strip complete mid-line boneyard spans from element text before classification, collapsing surrounding whitespace to a single space.

3. Verify: run `just test`. Acceptance: `Hello /* hidden */ world.` becomes `Hello world.`.
```

### Step 4.5: E11: boneyard content never ships in HTML fragments

**NOTE**: Renderer test lives in tests/test_renderer.py. Behavior must be identical for single-line and multi-line boneyards.

```text
Implement Step 4.5 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_renderer.py:
   - Test that HTMLRenderer().render(doc) output for a document containing `/* hidden scene */` contains no boneyard text, for both a single-line boneyard and a multi-line boneyard.
   Run the test and confirm it FAILS (or documents the current inconsistency).

2. GREEN: src/fountain/parser.py (around 560-566) and src/fountain/renderer.py (around 134-136, 486-487): ensure BONEYARD elements are omitted from the fragment renderer consistently.

3. Verify: run `just test`. Acceptance: fragment output contains no boneyard text; single-line and multi-line behave identically.
```

### Step 4.6: E5: sections, synopses, and notes are hidden by default (Open Question 3, mechanics)

**NOTE**: This is the mechanics half of Open Question 3; the docstring and doc-prose half is finished in Step 10.5. The ruling: notes, sections, synopses, and boneyard are writer tools omitted from formatted output by default.

```text
Implement Step 4.6 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_renderer.py:
   - Test that rendering `# Act I`, `= He meets her.`, and `[[remember to fix]]` produces formatted output where the section and synopsis are not visible by default, and any rendered note shows its content without literal `[[ ]]` brackets.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/renderer.py (around 128-132, 138-149, 250, 484-491): make DEFAULT_CSS, the fragment-mode behavior, and the element-rendering path agree that notes, sections, synopses, and boneyard are omitted from formatted output by default; strip `[[ ]]` from any note that does render.

3. Verify: run `just test`. Acceptance: sections and synopses are not visible by default; rendered notes carry no brackets.
```

### Step 4.7: E13: a `[[ ]]`-bounded line with middle text is not one NOTE

```text
Implement Step 4.7 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_bracketed_line_with_middle_text_not_single_note:
   - Test that `[[a]] middle [[b]]` parses as ACTION with text `middle` (inline notes stripped per body rule 8), not as one NOTE containing the whole line.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 597-605): require the standalone-note branch to match a single complete `[[...]]` spanning the whole line, not two notes bracketing interior text.

3. Verify: run `just test`. Acceptance: `[[a]] middle [[b]]` is ACTION with text `middle`.
```

### Step 4.8: E6 and E7: two-space vs blank line inside a note

**NOTE**: Two related requirements, one fix surface; the two RED tests must produce distinguishable outputs.

```text
Implement Step 4.8 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_edge_cases.py::TestSpecCompliance:
   - test_two_space_line_inside_note_keeps_empty_line: a note whose middle line is two spaces yields one NOTE whose text contains `\n\n` (an empty interior line).
   - test_blank_line_breaks_open_note: the same note with a truly blank middle line does NOT survive as a single NOTE; the E6 and E7 inputs produce distinguishable outputs.
   Run both and confirm they FAIL.

2. GREEN: src/fountain/parser.py (around 329-355, 574-585): treat a two-space connector line as an empty interior line inside an open note, and a genuinely blank line as a note break.

3. Verify: run `just test`. Acceptance: E6 and E7 inputs are distinguishable as specced.
```

### Step 4.9: E8: a two-space note line injects no empty DIALOGUE element

```text
Implement Step 4.9 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_two_space_note_line_no_empty_dialogue:
   - Test that a dialogue block, then a note containing a two-space line, yields CHARACTER, DIALOGUE, NOTE and no empty DIALOGUE element.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 333-351): suppress the empty-dialogue continuation emission while inside an open note.

3. Verify: run `just test`. Acceptance: no empty DIALOGUE element appears in the output.
```

### Step 4.10: E10: a lone `]` inside a note does not break recognition

```text
Implement Step 4.10 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_lone_bracket_inside_note:
   - Test that `[[check ref] ok]]` yields a NOTE with text `check ref] ok`.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 127): ensure only `]]` closes a note; a single `]` stays part of the note text.

3. Verify: run `just test`. Acceptance: `[[check ref] ok]]` is one NOTE with text `check ref] ok`.
```

---

## Section 5: Compliance Group A: Title Page and Whitespace

**Validator consults:**
- Skills: python:python

Title page structure, blank-line survival, round-trip fidelity, tabs, and the author/authors renderer divergence (Open Question 10).

### Step 5.1: A1: multi-line title page values preserve line structure

**NOTE**: This is a stored-metadata contract change. The renderer already renders multiline fields (`contact`, `notes`) with `<br>` once the value carries newlines.

```text
Implement Step 5.1 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_title_page_multiline_value_preserved:
   - Test that parsing `Contact:` followed by three indented address lines yields a `contact` value with three lines preserved.
   - Test that HTMLRenderer().render_page(doc) output contains `<br>` between the address lines.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 463-467): preserve the line structure of multi-line title page values (newline-joined string) instead of space-joining.

3. Verify: run `just test`. Acceptance: three address lines survive and render with `<br>`.
```

### Step 5.2: A2: title page continuation requires indentation; indented colons stay values

```text
Implement Step 5.2 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_title_page_continuation_requires_indent:
   - Test that `Notes:` followed by an indented `Draft 3: final revisions` yields metadata["notes"] == "Draft 3: final revisions" and no `draft 3` key.
   - Test that an unindented non-key line ends the title page instead of being absorbed into the previous value.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 448, 463): require 3+ spaces or a tab for continuation; treat indented colon-bearing lines as values of the current key, not new keys.

3. Verify: run `just test`. Acceptance: `draft 3` is not a key; an unindented non-key line ends the title page.
```

### Step 5.3: A4: blank lines survive parse and FountainRenderer round trip

**NOTE**: High severity. Shares a fix surface with A4b (Step 5.4): emitting blank-line separators from FountainRenderer.

```text
Implement Step 5.3 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_renderer.py:
   - Test that parse(FountainRenderer().render(parse(script))) preserves element types for a script with character/dialogue blocks separated by blank lines; CHARACTER does not degrade to ACTION.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 331-355) and src/fountain/renderer.py (around 727): emit blank-line separators from FountainRenderer so re-parsing keeps CHARACTER and DIALOGUE.

3. Verify: run `just test`. Acceptance: the round trip preserves element types; CHARACTER stays CHARACTER.
```

### Step 5.4: A4b: dual dialogue survives the Fountain round trip

**NOTE**: High severity. DUAL_DIALOGUE currently renders to the empty string, so the pair vanishes. Shares the A4 blank-line fix surface.

```text
Implement Step 5.4 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_renderer.py:
   - Test that rendering a document containing a DUAL_DIALOGUE element emits both character blocks with the caret on the second cue, and that re-parsing the output reproduces a DUAL_DIALOGUE element.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/renderer.py (around 865-868): render DUAL_DIALOGUE by emitting the left and right character blocks with the caret restored on the right cue.

3. Verify: run `just test`. Acceptance: dual dialogue round-trips back to a DUAL_DIALOGUE element.
```

### Step 5.5: A4c: lyrics round-trip without accreting delimiters

```text
Implement Step 5.5 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_renderer.py:
   - Test that parse(FountainRenderer().render(parse("~La la la"))) yields a LYRICS element with text `La la la` and no trailing tilde.
   Run the test and confirm it FAILS (today the text comes back as `La la la~`).

2. GREEN: reconcile src/fountain/renderer.py (around 876-877) with src/fountain/parser.py (around 160, 654-662): the renderer emits a leading `~` only, matching the parser stripping only the leading tilde.

3. Verify: run `just test`. Acceptance: `~La la la` round-trips to LYRICS text `La la la`.
```

### Step 5.6: A5 and D10: tabs and space indentation are visible in HTML

**NOTE**: A5 and D10 share this fix surface. A5 covers tab-to-four-spaces at parse time; D10 covers space indentation surviving into HTML.

```text
Implement Step 5.6 for fountain-py. Load the python:python skill first.

1. RED:
   - add tests/test_edge_cases.py::TestSpecCompliance::test_tab_action_yields_four_spaces: a tab-indented action line yields element.text starting with four spaces.
   - add to tests/test_renderer.py: rendering a ten-space-indented action line and a tab-indented action line preserves the indentation visually (assert the CSS or markup that makes leading whitespace render, e.g. `white-space: pre-wrap` on `.fountain-action`).
   Run both and confirm they FAIL.

2. GREEN:
   - src/fountain/parser.py (around 808-813): convert tabs in Action to four spaces at parse time.
   - src/fountain/renderer.py (around 96-99, 466-469): preserve indentation in HTML output.

3. Verify: run `just test`. Acceptance: tab-indented action text starts with four spaces; rendered HTML preserves both tab-origin and space indentation.
```

### Step 5.7: Open Question 10: both author and authors render, and the two renderers agree

**NOTE**: Ruling: render all authors. Drop the "skip authors if author present" shared-slot rule so HTMLRenderer matches FountainRenderer.

```text
Implement Step 5.7 for fountain-py. Load the python:python skill first.

1. RED: add to tests/test_renderer.py:
   - Test that a title page carrying both `author` and `authors` produces both values in HTMLRenderer output and in FountainRenderer output, and that the two renderers agree on the same document.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/renderer.py (around 403-404): drop the shared-slot rule so HTMLRenderer renders `author` and `authors` each as its own author paragraph.

3. Verify: run `just test`. Acceptance: both keys render in both renderers; the two agree.
```

---

## Section 6: Compliance Group B: Scene Headings

**Validator consults:**
- Skills: python:python

Space-form prefixes, the blank-line-after rule, the case-insensitive title-page guard, and scene-number character restrictions.

### Step 6.1: B1: space-form scene heading prefixes recognized

**NOTE**: High severity. Keep a prefix-boundary check so `INTERNAL AFFAIRS INVESTIGATES.` does not match on `INT`.

```text
Implement Step 6.1 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_scene_heading_space_forms:
   - Test that `INT HOUSE - DAY` and the space forms of EXT, EST, I/E, INT/EXT parse as SCENE_HEADING.
   - Test that `INTERNAL AFFAIRS INVESTIGATES.` still parses as ACTION.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 70-73): accept a space after the prefix alongside the dot forms, keeping a prefix-boundary check.

3. Verify: run `just test`. Acceptance: space forms parse as SCENE_HEADING; the prefix boundary holds.
```

### Step 6.2: B2: a natural scene heading requires a blank line after it

```text
Implement Step 6.2 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_scene_heading_requires_blank_after:
   - Test that `EXT. BRICK'S PATIO - DAY` immediately followed by a non-blank line parses as ACTION.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 702-717): require a following blank line (EOF counts) for a natural scene heading, mirroring the transition branch at line 720.

3. Verify: run `just test`. Acceptance: a scene-heading line with no blank line after is ACTION.
```

### Step 6.3: B3: case-insensitive title-page guard that accepts the space form

```text
Implement Step 6.3 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_title_page_guard_case_insensitive:
   - Test that a document whose first line is `int. house - day - 3:00 pm` parses as SCENE_HEADING, not as title-page metadata.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 448): make the scene-heading guard in the title-page detector case-insensitive and space-form aware.

3. Verify: run `just test`. Acceptance: a lowercase scene-heading first line is SCENE_HEADING.
```

### Step 6.4: B4: scene numbers restricted to alphanumerics, dashes, and periods

```text
Implement Step 6.4 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_scene_number_character_restriction:
   - Test that `INT. HOUSE - DAY #$%^&#` keeps `#$%^&#` in the heading text and sets no `scene_number` metadata.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 78): restrict the scene-number pattern to `[A-Za-z0-9.-]`.

3. Verify: run `just test`. Acceptance: an invalid scene number stays in the heading text with no `scene_number` metadata.
```

---

## Section 7: Compliance Group C: Characters and Dialogue

**Validator consults:**
- Skills: python:python

Punctuated cues, digit-first cues, lookahead corrections, forced-character behavior, and forced extensions.
The lookahead fixes (C3, C4, C6) are local corrections to `_is_dialogue_following`, not the pipeline refactor deferred in Open Question 12.

### Step 7.1: C1: punctuated uppercase cues recognized

**NOTE**: High severity.

```text
Implement Step 7.1 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_punctuated_character_cues:
   - Test that `MR. SMITH`, `O'BRIEN`, `JEAN-CLAUDE`, and `DEALER #2`, each followed by a dialogue line, parse as CHARACTER plus DIALOGUE.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 88, 93, 103): widen the cue pattern to allow `.`, `'`, `-`, and `#N` inside uppercase cues.

3. Verify: run `just test`. Acceptance: all four cue lines parse as CHARACTER plus DIALOGUE.
```

### Step 7.2: C2: digit-first cues with at least one letter

```text
Implement Step 7.2 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_digit_first_character_cue:
   - Test that `23 SKIDOO` with a dialogue line parses as CHARACTER plus DIALOGUE.
   - Test that bare `23` stays ACTION.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 88): allow a digit-leading cue that contains at least one letter.

3. Verify: run `just test`. Acceptance: `23 SKIDOO` is CHARACTER; `23` is ACTION.
```

### Step 7.3: C3: a blank line immediately after a cue disqualifies it

```text
Implement Step 7.3 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_blank_after_cue_disqualifies:
   - Test that `JOHN`, a blank line, then `He walks to the door.` parses as two ACTION elements.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 847-856): the lookahead must not skip blank lines when validating a cue.

3. Verify: run `just test`. Acceptance: `JOHN` then a blank line yields two ACTION elements.
```

### Step 7.4: C4: an all-caps line after a cue is dialogue

```text
Implement Step 7.4 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_allcaps_line_after_cue_is_dialogue:
   - Test that `JOHN` then `I SAID NO` parses as CHARACTER plus DIALOGUE.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 852): stop treating an all-caps follow line as a competing structural element inside the cue lookahead.

3. Verify: run `just test`. Acceptance: `JOHN` / `I SAID NO` is CHARACTER plus DIALOGUE.
```

### Step 7.5: C5: trailing caret on a forced character creates dual dialogue

```text
Implement Step 7.5 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_forced_character_caret_dual_dialogue:
   - Test that a `BRICK` block followed by an `@McClane ^` block yields a DUAL_DIALOGUE element whose right character text is `McClane`.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 98, 729-738): honor a trailing caret on a forced `@` cue and strip it, setting dual_dialogue.

3. Verify: run `just test`. Acceptance: the pair becomes DUAL_DIALOGUE with right character `McClane`.
```

### Step 7.6: C6: `@` forces CHARACTER unconditionally

```text
Implement Step 7.6 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_at_forces_character_unconditionally:
   - Test that `@McClane` then `I SAID NO` parses as CHARACTER (forced) plus DIALOGUE, with no literal `@` in the text.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 729-738): remove the dialogue-lookahead gate on the `@` force.

3. Verify: run `just test`. Acceptance: `@McClane` is a forced CHARACTER regardless of the following line; no `@` remains in the text.
```

### Step 7.7: C7: forced characters get extension extraction

```text
Implement Step 7.7 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_forced_character_extension:
   - Test that `@McClane (O.S.)` yields text `McClane` and metadata["extension"] == "O.S.".
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 729-738): apply the same extension extraction that natural cues get at line 103.

3. Verify: run `just test`. Acceptance: `@McClane (O.S.)` yields text `McClane` and extension `O.S.`.
```

---

## Section 8: Compliance Group D: Transitions and Emphasis

**Validator consults:**
- Skills: python:python

Transition edge cases and the emphasis rework: strip delimiters, guard delimiter-adjacent spaces, compute span offsets against stored text, and render nested spans without duplication.
The emphasis model is composable nested spans with delimiters stripped (D4/D6/D7 ruling); this changes the FormatSpan contract, so land D4, D5, D6, D7, D8 as a coherent group.

### Step 8.1: D1: trailing spaces after the colon defeat a transition

```text
Implement Step 8.1 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_trailing_space_defeats_transition:
   - Test that `CUT TO: ` (with a trailing space) parses as ACTION.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py: the transition classifier must see the untrimmed line so a trailing space defeats it. Line 331 rstrips before classification; preserve the raw line for this specific check.

3. Verify: run `just test`. Acceptance: `CUT TO: ` with a trailing space is ACTION.
```

### Step 8.2: D2: uppercase lines ending in `TO:` with punctuation are transitions

```text
Implement Step 8.2 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_punctuated_transition:
   - Test that `SMASH-CUT TO:` with surrounding blank lines parses as TRANSITION.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 108): allow punctuation before `TO:` in the transition pattern.

3. Verify: run `just test`. Acceptance: `SMASH-CUT TO:` is TRANSITION.
```

### Step 8.3: D4: emphasis delimiters stripped and spans cover only the content

**NOTE**: High severity, and the foundation of the emphasis rework. After this step, element text carries no emphasis delimiters and spans cover only the emphasized content.

```text
Implement Step 8.3 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_emphasis_delimiters_stripped:
   - Test that parsing `This is **bold** text.` yields text `This is bold text.` with a bold span over `bold`.
   - Test that HTMLRenderer output for that line is `<strong>bold</strong>` with no asterisks.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 1074-1101) and src/fountain/renderer.py (around 556-567): strip delimiters from element text; make spans cover only the emphasized content and adjust offsets accordingly.

3. Verify: run `just test`. Acceptance: text has no asterisks; the span covers `bold`; HTML shows `<strong>bold</strong>`.
```

### Step 8.4: D5: the keypad escape example renders correctly

```text
Implement Step 8.4 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_keypad_escape_example:
   - Test that `Steel enters the code on the keypad: **\*9765\***` renders with `<strong>*9765*</strong>` and no stray delimiters.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 1104-1119): resolve the escaped asterisks inside the bold span and adjust span offsets around the escapes.

3. Verify: run `just test`. Acceptance: the line renders `<strong>*9765*</strong>` with no stray delimiters.
```

### Step 8.5: D6: nested emphasis does not duplicate text

**NOTE**: High severity. Drop the partial-suppression artifact so bold, italic, and underline compose freely; the renderer segment builder must handle overlapping and nested spans.

```text
Implement Step 8.5 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_nested_emphasis_no_duplication:
   - Test that `_Steel's face FILLS the *Leupold Mark 4* scope_.` renders as an underlined phrase containing one italic span, with each word appearing exactly once.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/renderer.py (around 529-553) and src/fountain/parser.py (around 1089-1101): rework the segment builder to handle overlapping and nested spans; remove the partial-suppression logic.

3. Verify: run `just test`. Acceptance: the phrase renders once, underlined, with one nested italic span.
```

### Step 8.6: D7: bold and underline get the italic delimiter-adjacent-space guards

```text
Implement Step 8.6 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_bold_underline_space_guards:
   - Test that `_ kilos_` and `** word**` produce no formatting spans.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 191, 203): add the whitespace guards the italic pattern has at line 198 to the bold and underline patterns.

3. Verify: run `just test`. Acceptance: delimiter-adjacent-space cases produce no spans.
```

### Step 8.7: D8: span offsets computed against stored text including indentation

```text
Implement Step 8.7 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_span_offset_includes_indentation:
   - Test that ten spaces then `*Scott* --` yields an italic span over `Scott`, not over the leading whitespace.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 808-812): compute formatting offsets against the stored text, leading indentation included.

3. Verify: run `just test`. Acceptance: the italic span is positioned over `Scott`.
```

### Step 8.8: D9: forced action retains indentation after the `!`

```text
Implement Step 8.8 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_forced_action_retains_indent:
   - Test that `!    INDENTED FORCED ACTION` yields text beginning with four spaces.
   Run the test and confirm it FAILS.

2. GREEN: src/fountain/parser.py (around 622-629): strip only the `!` and keep the following indentation.

3. Verify: run `just test`. Acceptance: forced action text begins with four spaces.
```

---

## Section 9: Documented Contract Ambiguities

**Validator consults:**
- Skills: python:python

Pin the four documented ambiguities with tests and describe them in the user guide.
These are contract behaviors, not defects; changing any of them later is a breaking change.
The user-guide file `docs/source/user-guide/parsing.rst` may not exist yet; create it if needed and wire it into the guide toctree.

### Step 9.1: A3: title page detection heuristic pinned and documented

```text
Implement Step 9.1 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_title_page_detection_heuristic:
   - Test that a first line `He opens the card:` opens the title page (a colon that fails the scene-heading guard).
   - Test that a leading blank line, or forced syntax `>CUT TO:`, avoids the title page.
   Run the test and confirm it passes or FAILS depending on current behavior; adjust to pin the actual contract.

2. Document: docs/source/user-guide/parsing.rst: describe the heuristic and its documented workarounds (leading blank line; forced syntax such as `>CUT TO:`).

3. GREEN: no source change; this is contract behavior. If the test surfaces a divergence from the documented contract, stop and flag it rather than changing the parser.

4. Verify: run `just test` and `just doctest`. Acceptance: the test pins the behavior; the user guide describes it with the workarounds.
```

### Step 9.2: C8: lyrics inside a dialogue block end the block, pinned and documented

```text
Implement Step 9.2 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_lyrics_end_dialogue_block:
   - Test that `JOHN` / `~Willy Wonka!` / `Wasn't that great?` yields CHARACTER, LYRICS, ACTION.
   Run the test and confirm it pins the current behavior.

2. Document: docs/source/user-guide/parsing.rst: document that lyrics inside a dialogue block end the block, and that writers wanting the trailing line as dialogue have no supported syntax here.

3. GREEN: no source change.

4. Verify: run `just test`. Acceptance: the test pins CHARACTER, LYRICS, ACTION; the guide documents it.
```

### Step 9.3: D11: `FADE IN:` and `FADE OUT.` as natural transitions, documented as a deliberate extension

```text
Implement Step 9.3 for fountain-py. Load the python:python skill first.

1. RED: confirm the existing pins at tests/test_parser.py:57-58 and tests/test_edge_cases.py:739-740 still pass after the Group D changes. If coverage is thin, add a targeted assertion that `FADE IN:` and `FADE OUT.` parse as TRANSITION.

2. Document: docs/source/user-guide/parsing.rst: mark `FADE IN:` and `FADE OUT.` as a deliberate extension of the spec's natural-transition rule (which requires ending in `TO:`).

3. GREEN: no source change.

4. Verify: run `just test`. Acceptance: the existing tests stay green; the guide marks these as a deliberate extension.
```

### Step 9.4: E9: mid-line notes removed without a trace, documented

```text
Implement Step 9.4 for fountain-py. Load the python:python skill first.

1. RED: add tests/test_edge_cases.py::TestSpecCompliance::test_inline_note_removed_standalone_kept:
   - Test that an inline `[[note]]` is stripped and unrecoverable from the parse.
   - Test that a standalone `[[note]]` line becomes a NOTE element.
   Run the test and confirm it pins the asymmetry.

2. Document: docs/source/user-guide/parsing.rst: document the asymmetry between inline notes (removed) and standalone note lines (kept as NOTE).

3. GREEN: no source change.

4. Verify: run `just test`. Acceptance: the test pins the asymmetry; the guide documents it.
```

---

## Section 10: Documentation Truth-Up

**Validator consults:**
- Skills: python:python

Every published claim must be true before publish (Open Questions 2, 4, 5, 6, and the doc half of 3).
This section runs after the compliance work so the claims it restores are real.
Do not start it until Sections 4 through 9 are complete and green.

### Step 10.1: Open Question 2: the compliance claim stands because it is now true

```text
Implement Step 10.1 for fountain-py.

1. RED: none (documentation), guarded by the full compliance suite from Sections 4 through 9.

2. Verify the claim: confirm the compliance suite is fully green, then verify README.md:13 ("Full Fountain Spec Compliance") and CHANGELOG.md:14 are accurate now that every requirement is fixed. Keep the claim; do not soften it.

3. Verify: run `just test`. Acceptance: the compliance suite is fully green and the README and CHANGELOG claims hold without a waiver.
```

### Step 10.2: Open Question 4: FountainElement.text docstring made accurate

```text
Implement Step 10.2 for fountain-py. Load the python:python skill first.

1. RED: none (docstring); doctests still pass under `--doctest-modules`.

2. GREEN: src/fountain/elements.py (around 146, 153): rewrite the `text` docstring so it is accurate after D4 (emphasis delimiters removed) and states what BONEYARD and NOTE elements carry (their delimiters verbatim).

3. Verify: run `just test` and `just doctest`. Acceptance: the docstring matches actual behavior for emphasis, BONEYARD, and NOTE.
```

### Step 10.3: Open Question 5: round-trip docs state the real fidelity

```text
Implement Step 10.3 for fountain-py. Load the python:python skill first.

1. RED: none (documentation).

2. GREEN: rewrite the round-trip claims in README.md:81-89 and the docstring at src/fountain/renderer.py:656-672 to reflect A4, A4b, A4c (blank lines, dual dialogue, and lyrics now round-trip) and to state the remaining `_apply_formatting_removal` limitation precisely (inline emphasis markers are not re-emitted).

3. Verify: run `just test` and `just doctest`. Acceptance: the round-trip docs match actual behavior after Section 5.
```

### Step 10.4: Open Question 6: CHANGELOG tab claim reworded

```text
Implement Step 10.4 for fountain-py.

1. RED: none (documentation).

2. GREEN: reword the CHANGELOG "Tab-to-spaces conversion verified in HTML output" claim to match the A5/D10 fix: tabs convert to four spaces in element text at parse time; indentation is preserved in HTML.

3. Verify: Acceptance: the CHANGELOG tab claim matches the shipped behavior.
```

### Step 10.5: Open Question 3: hidden-by-default docs and docstrings agree

```text
Implement Step 10.5 for fountain-py. Load the python:python skill first.

1. RED: none (documentation), guarded by the E5 and E11 renderer tests from Section 4.

2. GREEN: reconcile src/fountain/renderer.py:247,250 docstrings and docs/source/user-guide/rendering.rst:167 with the E5/E11 mechanics so notes, sections, synopses, and boneyard are described as omitted from formatted output by default in both fragment and page modes.

3. Verify: run `just test` and `just doctest`. Acceptance: docstrings and docs agree with the renderer behavior from Section 4.
```

---

## Section 11: Tooling Cleanup

**Validator consults:**
- Skills: python:python

Remove the dangling pre-commit references (CR-3).
Open Question 11 is settled: `just test` keeps `just fix` inside the gate; do not change the recipe order.

### Step 11.1: CR-3: remove dangling pre-commit recipes and references

```text
Implement Step 11.1 for fountain-py.

1. RED: add a check (TestSpecCompliance::test_no_pre_commit_references, or a shell assertion in the step) that `just --list` shows no pre-commit recipes and `grep -ri pre-commit` over the tracked tree matches nothing outside git history.
   Run it and confirm it FAILS.

2. GREEN:
   - justfile (around lines 78-84): delete the `pre-commit-install` and `pre-commit-all` recipes.
   - CONTRIBUTING.md (around lines 23-24): remove the `pre-commit install` instruction.

3. Verify: run `just test`. Acceptance: no pre-commit recipes in `just --list`; `grep -ri pre-commit` over tracked files is empty. Do not touch the `just test` recipe order.
```

---

## Section 12: Path to PyPI

**Validator consults:**
- Skills: python:python

Harden the pipeline, add a TestPyPI dry run, verify the build in CI, and run a local end-to-end check.
This is the last section: it runs only after compliance is done and every published claim is true.

### Step 12.1: CI dependency install fix and build verification

**NOTE**: `docs.yml` is already tracked and builds/deploys HTML on push to `main`; it does not run doctests, which is why the Sphinx doctest build lands here in CI.

```text
Implement Step 12.1 for fountain-py.

1. RED: none (CI config); the change is self-verifying when CI runs.

2. GREEN: .github/workflows/ci.yml:
   - Replace `uv pip install -e ".[dev]"` (line 29) with `uv sync --dev` so the dev dependency group actually installs.
   - Add a `uv build` step plus a wheel-contents check that the wheel includes fountain/__init__.py, parser.py, renderer.py, and py.typed.
   - Add the Sphinx doctest build (`sphinx-build -b doctest docs/source docs/build/doctest`) so doctests run in CI.

3. Verify: Acceptance: CI installs dev tools via `uv sync --dev`, builds the wheel, verifies its contents, and runs the Sphinx doctest build; the workflow is valid YAML.
```

### Step 12.2: Harden the publish workflow

**NOTE**: Trusted publishing is preferred (no stored secret; `id-token: write` is already granted). If trusted publishing is not yet configured on PyPI for this project, that setup is Mason's to do before the first real publish.

```text
Implement Step 12.2 for fountain-py.

1. RED: none (CI config).

2. GREEN: .github/workflows/publish.yml:
   - Add a test job that runs the full suite; gate the publish job on it with `needs:`.
   - Build once, upload the wheel and sdist as artifacts, and download them in the publish job so the tested artifact is the published artifact.
   - Add an `environment:` declaration for deployment protection.
   - Switch to trusted publishing: drop `UV_PUBLISH_TOKEN` / `secrets.PYPI_API_TOKEN`; keep `id-token: write`.

3. Verify: Acceptance: publish runs only after tests pass, publishes the exact tested wheel, declares an environment, and authenticates via trusted publishing with no stored token; the workflow is valid YAML.
```

### Step 12.3: Add the TestPyPI dry-run workflow

```text
Implement Step 12.3 for fountain-py.

1. RED: none (CI config).

2. GREEN: create .github/workflows/test-publish.yml, triggered by `workflow_dispatch`, that builds and publishes to TestPyPI using trusted publishing against a TestPyPI environment, used to validate install, README rendering, and metadata before the real publish.

3. Verify: Acceptance: .github/workflows/test-publish.yml exists, is manually triggered, and targets TestPyPI; the workflow is valid YAML.
```

### Step 12.4: Local end-to-end verification

```text
Implement Step 12.4 for fountain-py.

1. RED: none (manual verification with recorded output).

2. GREEN: run the local end-to-end check and record the output:
   - `uv build`.
   - Install the wheel in a clean venv.
   - Run an import-and-parse-and-render smoke test on a sample screenplay.
   - Run full `just test`.
   - Clean up dist/.

3. Verify: Acceptance: `pip install` of the built wheel on a clean 3.10 through 3.14 interpreter parses a screenplay and renders HTML without errors; `just test` passes clean.
```

---

## Implementation Guidelines

- One step per commit; each commit includes a new `.ai-sessions/session-*.md` (the finalize dispatch creates it).
- Never commit to `main`; `init-version` is the feature branch. Mason merges to `main`.
- Never split, reorder, or skip the RED-before-GREEN discipline; the failing test must exist and fail before the fix.
- Do not restructure the parser pipeline or the `Counter` statistics pass (Open Question 12 deferral).
- Keep `__init__.py` logic-free at all times (imports, `__all__`, module docstring only).
- After every step, `just test` must pass clean: 241+ tests, 99%+ coverage, `mypy --strict src/` green, ruff lint and format clean.

## Success Metrics

- All 62 items in `todo.md` checked off.
- Every Fountain-compliance requirement (Groups A through E) fixed with a pinned, failing-first test.
- `FountainParser.validate()` ships with the four initial diagnostic codes.
- `from fountain import HTMLRenderer, FountainRenderer, ValidationIssue` works.
- Packaging and CI target 3.10 through 3.14; code uses `X | None` throughout.
- README and CHANGELOG "Full Fountain Spec Compliance" claim is true and verified last.
- Publish pipeline gated on tests, publishing the tested artifact via trusted publishing, with a TestPyPI dry run verified.
- `pip install fountain-py` on a clean 3.10 through 3.14 interpreter parses a screenplay and renders HTML without errors.

---

## Release Mechanics (Human-Gated)

After every section above is complete and green, the release is Mason's to trigger:

- Merge `init-version` to `main` (Mason merges; agents never do).
- Tag `v0.1.0`, create the GitHub Release.
- Let the gated publish workflow run.
- Verify the PyPI page renders and `pip install fountain-py` works.

Goal chain: publishing 0.1.0 to PyPI unblocks the bartleby integration and the sites built on the stack.
