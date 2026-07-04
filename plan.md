# fountain-py 0.1.0 Implementation Plan

**Read `handoff.md` first.**
It states the current tree, Mason's settled rulings, and the exact next action; this plan assumes that context.

This plan turns the committed `spec.md` (commit 1056da5, dated 2026-07-03) into an executable TDD roadmap for a 0.1.0 PyPI release.
Every step is written for an implementation model: it names the test to add first (RED), the source change (GREEN), the file paths, and the acceptance criterion.
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

Each step follows RED, GREEN, then an optional REFACTOR note.
Write the failing test first, run `uv run pytest` to see it fail, implement the minimal change, then run `just test` before moving on.
The quality bar from the spec is a hard gate: the current 241 tests keep passing (plus the new tests each step adds), coverage stays at 99%+, `mypy --strict src/` passes, and `just test` runs clean.
Every compliance step lands with a failing-first test that encodes its acceptance criterion.

Test placement conventions:

- Compliance fixes: `tests/test_edge_cases.py`, `TestSpecCompliance` class.
- Renderer behavior: `tests/test_renderer.py`.
- Validation API: `tests/test_validation.py` (new file).
- Document analysis: `tests/test_document.py`.

Sequencing rationale: the Python floor and type work land first so all later code is written in 3.10 idioms; the Validation API and compliance fixes come next; documentation truth-up follows once compliance is real; the PyPI pipeline is last.

---

## Section 1: Python Floor and Type System

**Validator consults:** python:python

Move the floor to 3.10, modernize typing, and fix the `MetadataValue` annotation.
Doing this first means every compliance fix below is written clean against the 3.10 ruff target.

Fable checkpoint (optional): confirm the 3.10-through-3.14 support window still matches Mason's intent before starting.

### Step 1.1: Move the Python floor to 3.10 in packaging and tooling

- RED: none (configuration change; guarded by the existing suite and by `mypy --strict`).
- GREEN:
  - `pyproject.toml`: set `requires-python = ">=3.10"` (was `>=3.9`).
  - `pyproject.toml`: replace the classifier list so it carries `Programming Language :: Python :: 3.10` through `3.14` and drops `3.9`.
  - `pyproject.toml`: set `[tool.ruff] target-version = "py310"` (was `py39`).
  - `pyproject.toml`: set `[tool.mypy] python_version = "3.10"` (was `3.9`).
- Acceptance: `pyproject.toml` declares `>=3.10`, no 3.9 classifier remains, ruff target is `py310`, mypy python_version is `3.10`; `just test` passes clean.

### Step 1.2: Update the CI matrix to 3.10 through 3.14

- RED: none (CI config).
- GREEN: `.github/workflows/ci.yml`: change the matrix `python-version` to `["3.10", "3.11", "3.12", "3.13", "3.14"]` (was `3.9` through `3.13`); keep the Codecov upload gated on `matrix.python-version == '3.12'`.
- Acceptance: `.github/workflows/ci.yml` matrix lists 3.10 through 3.14 and no 3.9 entry.
- Note: 3.15 is added to the matrix when it releases (October 2026); out of scope for this release.

### Step 1.3: Modernize typing to `X | None` and apply `MetadataValue` (CR-2)

- RED: add `tests/test_edge_cases.py::TestSpecCompliance::test_metadata_annotation_uses_metadatavalue` asserting `FountainElement`'s `metadata` annotation resolves to `dict[str, MetadataValue] | None` (via `typing.get_type_hints` or the raw annotation string).
- GREEN:
  - `src/fountain/elements.py:209`: change `FountainElement.metadata` from `dict[str, Any] | None` to `dict[str, MetadataValue] | None`.
  - `src/fountain/parser.py:667,703,759`: change the metadata locals' annotations from `dict[str, Any]` to `dict[str, MetadataValue]`.
  - Sweep all of `src/fountain/` for `Optional[X]` and `Union[...]` and rewrite to `X | None` / `X | Y` per ruff UP007; remove now-unused `Optional`/`Union` imports.
- Acceptance: `FountainElement.metadata` is annotated `dict[str, MetadataValue] | None`; `mypy --strict src/` passes; `uv run ruff check src/` reports no UP007 findings.
- REFACTOR: `MetadataValue` stays defined and exported; the alias is not dropped (ruling 2026-07-03).

---

## Section 2: Package API Surface

**Validator consults:** python:python

Promote the renderers and fix the file headers.
These are low-risk surface changes that later sections and the docs depend on.

Fable checkpoint (optional): none needed; proceed.

### Step 2.1: Promote HTMLRenderer and FountainRenderer to the top-level `__all__` (Open Question 7)

- RED: add `tests/test_edge_cases.py::TestSpecCompliance::test_renderers_importable_from_package` asserting `from fountain import HTMLRenderer, FountainRenderer` succeeds and both names appear in `fountain.__all__`.
- GREEN: `src/fountain/__init__.py`: add `from fountain.renderer import HTMLRenderer, FountainRenderer` and add both to `__all__`.
- Acceptance: `from fountain import HTMLRenderer, FountainRenderer` works; `src/fountain/__init__.py` contains nothing but imports, `__all__`, and the module docstring (no logic).
- Note: `DEFAULT_CSS`, `TITLE_PAGE_FIELD_ORDER`, and `FormatSpan` stay module-public but are intentionally left out of the top-level `__all__` per the spec's Package Exports section.

### Step 2.2: Fix ABOUTME headers to single-line form (CR-1)

- RED: add `tests/test_edge_cases.py::TestSpecCompliance::test_aboutme_header_single_line` that reads each source file under `src/fountain/` and asserts only line one starts with `ABOUTME:`, matching the plain form at `src/fountain/renderer.py:1-2`.
- GREEN: rewrite the module headers in `src/fountain/parser.py:1-2`, `src/fountain/elements.py:1-2`, `src/fountain/document.py:1-2`, and `tests/test_edge_cases.py:2-3` so `ABOUTME:` appears on line one only and the second line is a plain continuation comment.
- Acceptance: every source file's header has `ABOUTME:` on line one only; the test passes across the tree.

---

## Section 3: Validation API (Required for 0.1.0)

**Validator consults:** python:python

Add the diagnostic channel the spec requires (Open Question 8, ruled required).
`parse()` stays lenient and non-raising; `validate()` surfaces silent degradation.

Fable checkpoint (optional): confirm the initial diagnostic code set (four codes below) is still the intended 0.1.0 surface before building on it.

### Step 3.1: Add the ValidationIssue dataclass

- RED: add `tests/test_validation.py::test_validation_issue_is_frozen_dataclass` asserting `ValidationIssue` is a frozen dataclass with fields `line_number: int`, `severity: Literal["error", "warning"]`, `code: str`, `message: str`, and that mutation raises `FrozenInstanceError`.
- GREEN: `src/fountain/elements.py`: add a frozen `@dataclass(frozen=True)` `ValidationIssue` with those four fields and the `Literal["error", "warning"]` severity annotation.
- Acceptance: `ValidationIssue(line_number=1, severity="error", code="x", message="y")` constructs; assignment to any field raises.

### Step 3.2: Implement FountainParser.validate() with the initial diagnostic set

- RED: add to `tests/test_validation.py`:
  - `test_unclosed_boneyard_reports_error`: a document with `/*` and no `*/` returns exactly one issue with `code == "unclosed-boneyard"`, `severity == "error"`, and `line_number` equal to the opening line's 1-based number.
  - `test_unclosed_note_reports_error`: `[[` with no `]]` before EOF returns one `unclosed-note` error at the opening line.
  - `test_orphan_character_cue_reports_warning`: an uppercase cue demoted to ACTION because no dialogue follows returns one `orphan-character-cue` warning.
  - `test_empty_document_reports_warning`: input that parses to zero elements returns one `empty-document` warning.
  - `test_well_formed_script_returns_empty_list`: a valid script returns `[]`.
  - `test_validate_does_not_change_parse_output`: `parse(text)` output (via `to_dict()`) is byte-identical whether or not `validate(text)` ran first.
- GREEN: `src/fountain/parser.py`: add `validate(self, text: str) -> list[ValidationIssue]` that runs the same two-pass analysis as `parse()` but collects diagnostics for the four codes instead of discarding them; do not mutate the parse contract.
- Acceptance: each diagnostic fires exactly as specced; a well-formed script returns `[]`; `parse()` output is unchanged by a prior `validate()` call.
- REFACTOR: keep the code strings as module-level constants so the growing code set stays a single source of truth; each shipped code string is contract.

### Step 3.3: Export ValidationIssue from the package top level

- RED: add `tests/test_validation.py::test_validation_issue_exported` asserting `from fountain import ValidationIssue` works and `"ValidationIssue" in fountain.__all__`.
- GREEN: `src/fountain/__init__.py`: import `ValidationIssue` from `fountain.elements` and add it to `__all__`.
- Acceptance: `from fountain import ValidationIssue` succeeds; it is listed in `__all__`; `__init__.py` still carries no logic.

---

## Section 4: Compliance Group E: Boneyard, Notes, Sections

**Validator consults:** python:python

E2 and E3 are the highest-priority fixes in the spec: they silently truncate the document.
Fix them first, then the rest of the group.

Fable checkpoint (optional): confirm the boneyard close-pattern change (de-anchoring `*/`) does not need a design discussion before touching the parse loop.

### Step 4.1: E2: boneyard close with trailing text ends the boneyard

- RED: `TestSpecCompliance::test_boneyard_close_with_trailing_text`: a `/*` block closed by `*/ And we are back.` yields `And we are back.` and every following line as elements; nothing after the close is dropped.
- GREEN: `src/fountain/parser.py:140,554-557`: de-anchor the boneyard close pattern so `*/` mid-line ends boneyard state and the remainder of the line is reprocessed as body.
- Acceptance: content after `*/` survives as elements.

### Step 4.2: E3: single-line boneyard with trailing text does not swallow the document

- RED: `TestSpecCompliance::test_single_line_boneyard_keeps_trailing_text`: `/* cut this */ keep this` followed by more action yields `keep this` and the following action as elements.
- GREEN: `src/fountain/parser.py:132,136,140,568-571`: strip the `/* ... */` span and reprocess the trailing remainder rather than consuming the line.
- Acceptance: `keep this` and following action survive.

### Step 4.3: E4: mid-line boneyard opener does not leak interior lines

- RED: `TestSpecCompliance::test_midline_boneyard_opener_no_leak`: `He waves /* begin cut`, interior lines, `*/` yields a single ACTION `He waves` and no interior text.
- GREEN: `src/fountain/parser.py:136,568-571`: on a mid-line opener, emit the pre-`/*` text as ACTION and enter boneyard state for the rest.
- Acceptance: interior lines never reach output; `He waves` is one ACTION.

### Step 4.4: E1: mid-line `/* ... */` stripped from action and dialogue text

- RED: `TestSpecCompliance::test_midline_boneyard_stripped_from_text`: `Hello /* hidden */ world.` yields text `Hello world.`.
- GREEN: `src/fountain/parser.py:132-140,553-571`: strip complete mid-line boneyard spans from element text before classification.
- Acceptance: `Hello /* hidden */ world.` becomes `Hello world.`.

### Step 4.5: E11: boneyard content never ships in HTML fragments

- RED: `tests/test_renderer.py`: `HTMLRenderer.render()` output for a document containing `/* hidden scene */` contains no boneyard text, for both single-line and multi-line boneyards.
- GREEN: `src/fountain/parser.py:560-566` and `src/fountain/renderer.py:134-136,486-487`: ensure BONEYARD elements are omitted from the fragment renderer consistently.
- Acceptance: fragment output contains no boneyard text; single-line and multi-line behave identically.

### Step 4.6: E5: sections, synopses, and notes are hidden by default (Open Question 3)

- RED: `tests/test_renderer.py`: rendering `# Act I`, `= He meets her.`, and `[[remember to fix]]` produces formatted output where section and synopsis are not visible by default, and any rendered note shows its content without literal `[[ ]]` brackets.
- GREEN: `src/fountain/renderer.py:128-132,138-149,250,484-491`: make `DEFAULT_CSS`, the fragment-mode behavior, and the docstrings agree that notes, sections, synopses, and boneyard are omitted from formatted output by default; strip `[[ ]]` from any note that does render.
- Acceptance: sections and synopses are not visible by default; rendered notes carry no brackets.
- Note: this is the mechanics half of Open Question 3; the docstring and doc wording are finished in Section 10.

### Step 4.7: E13: a line bounded by `[[ ]]` but carrying text between two notes is not one NOTE

- RED: `TestSpecCompliance::test_bracketed_line_with_middle_text_not_single_note`: `[[a]] middle [[b]]` parses as ACTION with text `middle` (inline notes stripped), not as one NOTE containing the whole line.
- GREEN: `src/fountain/parser.py:597-605`: require the standalone-note branch to match a single complete `[[...]]` spanning the line, not two notes bracketing text.
- Acceptance: `[[a]] middle [[b]]` is ACTION with text `middle`.

### Step 4.8: E6 and E7: two-space vs blank line inside a note

- RED:
  - `TestSpecCompliance::test_two_space_line_inside_note_keeps_empty_line`: a note whose middle line is two spaces yields one NOTE whose text contains `\n\n`.
  - `TestSpecCompliance::test_blank_line_breaks_open_note`: the same note with a truly blank middle line does not survive as a single NOTE; E6 and E7 inputs produce distinguishable outputs.
- GREEN: `src/fountain/parser.py:329-355,574-585`: treat a two-space connector line as an empty interior line inside a note, and a genuinely blank line as a note break.
- Acceptance: E6 and E7 inputs are distinguishable as specced.

### Step 4.9: E8: a two-space line inside a note injects no empty DIALOGUE element

- RED: `TestSpecCompliance::test_two_space_note_line_no_empty_dialogue`: a dialogue block, then a note containing a two-space line, yields CHARACTER, DIALOGUE, NOTE and no empty DIALOGUE element.
- GREEN: `src/fountain/parser.py:333-351`: suppress the empty-dialogue continuation emission while inside an open note.
- Acceptance: no empty DIALOGUE element appears.

### Step 4.10: E10: a lone `]` inside a note does not break recognition

- RED: `TestSpecCompliance::test_lone_bracket_inside_note`: `[[check ref] ok]]` yields a NOTE with text `check ref] ok`.
- GREEN: `src/fountain/parser.py:127`: ensure only `]]` closes a note; a single `]` stays part of the note text.
- Acceptance: `[[check ref] ok]]` is one NOTE with text `check ref] ok`.

---

## Section 5: Compliance Group A: Title Page and Whitespace

**Validator consults:** python:python

Title page structure, blank-line survival, round-trip fidelity, tabs, and the author/authors renderer divergence (Open Question 10).

Fable checkpoint (optional): confirm the multi-line title-page value shape (list vs newline-joined string) for A1 before implementing, since it is a stored-metadata contract.

### Step 5.1: A1: multi-line title page values preserve line structure

- RED: `TestSpecCompliance::test_title_page_multiline_value_preserved`: parsing `Contact:` followed by three indented address lines yields a `contact` value with three lines; `render_page()` output contains `<br>` between them.
- GREEN: `src/fountain/parser.py:463-467`: preserve the line structure of multi-line values instead of space-joining; `src/fountain/renderer.py` already renders multiline fields (`contact`, `notes`) with `<br>`.
- Acceptance: three address lines survive and render with `<br>`.

### Step 5.2: A2: title page continuation requires indentation; indented colons stay values

- RED: `TestSpecCompliance::test_title_page_continuation_requires_indent`: `Notes:` followed by an indented `Draft 3: final revisions` yields `metadata["notes"] == "Draft 3: final revisions"` and no `draft 3` key; an unindented non-key line ends the title page.
- GREEN: `src/fountain/parser.py:448,463`: require 3+ spaces or a tab for continuation; treat indented colon lines as values of the current key.
- Acceptance: `draft 3` is not a key; an unindented non-key line ends the title page.

### Step 5.3: A4: blank lines survive parse and FountainRenderer round trip

- RED: `tests/test_renderer.py`: `parse(FountainRenderer().render(parse(script)))` preserves element types for a script with character/dialogue blocks separated by blank lines; CHARACTER does not degrade to ACTION.
- GREEN: `src/fountain/parser.py:331-355` and `src/fountain/renderer.py:727`: emit blank-line separators from `FountainRenderer` so re-parsing keeps CHARACTER and DIALOGUE.
- Acceptance: the round trip preserves element types; CHARACTER stays CHARACTER.

### Step 5.4: A4b: dual dialogue survives the Fountain round trip

- RED: `tests/test_renderer.py`: rendering a document containing a DUAL_DIALOGUE element emits both character blocks with the caret on the second cue; re-parsing reproduces a DUAL_DIALOGUE element.
- GREEN: `src/fountain/renderer.py:865-868`: render DUAL_DIALOGUE by emitting the left and right character blocks with the caret restored on the right cue (shares the A4 blank-line fix surface).
- Acceptance: dual dialogue round-trips back to a DUAL_DIALOGUE element.

### Step 5.5: A4c: lyrics round-trip without accreting delimiters

- RED: `tests/test_renderer.py`: `parse(FountainRenderer().render(parse("~La la la")))` yields a LYRICS element with text `La la la` and no trailing tilde.
- GREEN: reconcile `src/fountain/renderer.py:876-877` with `src/fountain/parser.py:160,654-662`: the renderer emits a leading `~` only, matching the parser stripping only the leading tilde.
- Acceptance: `~La la la` round-trips to LYRICS text `La la la`.

### Step 5.6: A5 and D10: tabs and space indentation are visible in HTML

- RED:
  - `TestSpecCompliance::test_tab_action_yields_four_spaces`: a tab-indented action line yields `element.text` starting with four spaces.
  - `tests/test_renderer.py`: rendering a ten-space-indented action line and a tab-indented action line preserves the indentation visually.
- GREEN: `src/fountain/parser.py:808-813`: convert tabs in Action to four spaces at parse time; `src/fountain/renderer.py:96-99,466-469`: preserve indentation in HTML (for example `white-space: pre-wrap` on `.fountain-action`).
- Acceptance: tab-indented action text starts with four spaces; rendered HTML preserves both tab-origin and space indentation. (A5 and D10 share this fix surface.)

### Step 5.7: Open Question 10: both author and authors render, and the two renderers agree

- RED: `tests/test_renderer.py`: a title page carrying both `author` and `authors` produces both values in HTML and in Fountain output, and `HTMLRenderer` and `FountainRenderer` agree on the same document.
- GREEN: `src/fountain/renderer.py:403-404`: drop the "skip authors if author present" shared-slot rule so `HTMLRenderer` renders `author` and `authors` each as its own author paragraph, matching `FountainRenderer`.
- Acceptance: both keys render in both renderers; the two agree.

---

## Section 6: Compliance Group B: Scene Headings

**Validator consults:** python:python

Space-form prefixes, the blank-line-after rule, the case-insensitive title-page guard, and scene-number character restrictions.

Fable checkpoint (optional): none needed.

### Step 6.1: B1: space-form scene heading prefixes recognized

- RED: `TestSpecCompliance::test_scene_heading_space_forms`: `INT`, `EXT`, `EST`, `I/E`, `INT/EXT` space forms (e.g. `INT HOUSE - DAY`) parse as SCENE_HEADING; `INTERNAL AFFAIRS INVESTIGATES.` still parses as ACTION.
- GREEN: `src/fountain/parser.py:70-73`: accept a space after the prefix alongside the dot forms, keeping a prefix-boundary check so `INTERNAL` does not match.
- Acceptance: space forms parse as SCENE_HEADING; the prefix boundary holds.

### Step 6.2: B2: a natural scene heading requires a blank line after it

- RED: `TestSpecCompliance::test_scene_heading_requires_blank_after`: `EXT. BRICK'S PATIO - DAY` immediately followed by a non-blank line parses as ACTION.
- GREEN: `src/fountain/parser.py:702-717`: require a following blank line (EOF counts) for a natural scene heading, mirroring the transition branch at line 720.
- Acceptance: a scene-heading line with no blank line after is ACTION.

### Step 6.3: B3: case-insensitive title-page guard that accepts the space form

- RED: `TestSpecCompliance::test_title_page_guard_case_insensitive`: a document whose first line is `int. house - day - 3:00 pm` parses as SCENE_HEADING, not title-page metadata.
- GREEN: `src/fountain/parser.py:448`: make the scene-heading guard in the title-page detector case-insensitive and space-form aware.
- Acceptance: a lowercase scene-heading first line is SCENE_HEADING.

### Step 6.4: B4: scene numbers restricted to alphanumerics, dashes, and periods

- RED: `TestSpecCompliance::test_scene_number_character_restriction`: `INT. HOUSE - DAY #$%^&#` keeps `#$%^&#` in the heading text and sets no `scene_number` metadata.
- GREEN: `src/fountain/parser.py:78`: restrict the scene-number pattern to `[A-Za-z0-9.-]`.
- Acceptance: an invalid scene number stays in the heading text with no `scene_number` metadata.

---

## Section 7: Compliance Group C: Characters and Dialogue

**Validator consults:** python:python

Punctuated cues, digit-first cues, lookahead corrections, forced-character behavior, and forced extensions.

Fable checkpoint (optional): confirm the `_is_dialogue_following` lookahead corrections (C3, C4, C6) do not warrant the pipeline design pass deferred in Open Question 12; these are local fixes, not a refactor.

### Step 7.1: C1: punctuated uppercase cues recognized

- RED: `TestSpecCompliance::test_punctuated_character_cues`: `MR. SMITH`, `O'BRIEN`, `JEAN-CLAUDE`, `DEALER #2`, each followed by a dialogue line, parse as CHARACTER plus DIALOGUE.
- GREEN: `src/fountain/parser.py:88,93,103`: widen the cue pattern to allow `.`, `'`, `-`, and `#N` inside uppercase cues.
- Acceptance: all four cue lines parse as CHARACTER plus DIALOGUE.

### Step 7.2: C2: digit-first cues with at least one letter

- RED: `TestSpecCompliance::test_digit_first_character_cue`: `23 SKIDOO` with dialogue parses as CHARACTER plus DIALOGUE; bare `23` stays ACTION.
- GREEN: `src/fountain/parser.py:88`: allow a digit-leading cue that contains at least one letter.
- Acceptance: `23 SKIDOO` is CHARACTER; `23` is ACTION.

### Step 7.3: C3: a blank line immediately after a cue disqualifies it

- RED: `TestSpecCompliance::test_blank_after_cue_disqualifies`: `JOHN`, blank line, `He walks to the door.` parses as two ACTION elements.
- GREEN: `src/fountain/parser.py:847-856`: the lookahead must not skip blank lines when validating a cue.
- Acceptance: `JOHN` then a blank line yields two ACTION elements.

### Step 7.4: C4: an all-caps line after a cue is dialogue

- RED: `TestSpecCompliance::test_allcaps_line_after_cue_is_dialogue`: `JOHN` then `I SAID NO` parses as CHARACTER plus DIALOGUE.
- GREEN: `src/fountain/parser.py:852`: stop treating an all-caps follow line as a competing structural element inside the cue lookahead.
- Acceptance: `JOHN` / `I SAID NO` is CHARACTER plus DIALOGUE.

### Step 7.5: C5: trailing caret on a forced character creates dual dialogue

- RED: `TestSpecCompliance::test_forced_character_caret_dual_dialogue`: a `BRICK` block followed by an `@McClane ^` block yields a DUAL_DIALOGUE element whose right character text is `McClane`.
- GREEN: `src/fountain/parser.py:98,729-738`: honor a trailing caret on a forced `@` cue and strip it, setting `dual_dialogue`.
- Acceptance: the pair becomes DUAL_DIALOGUE with right character `McClane`.

### Step 7.6: C6: `@` forces CHARACTER unconditionally

- RED: `TestSpecCompliance::test_at_forces_character_unconditionally`: `@McClane` then `I SAID NO` parses as CHARACTER (forced) plus DIALOGUE, with no literal `@` in the text.
- GREEN: `src/fountain/parser.py:729-738`: remove the dialogue-lookahead gate on the `@` force.
- Acceptance: `@McClane` is a forced CHARACTER regardless of the following line; no `@` remains.

### Step 7.7: C7: forced characters get extension extraction

- RED: `TestSpecCompliance::test_forced_character_extension`: `@McClane (O.S.)` yields text `McClane` and `metadata["extension"] == "O.S."`.
- GREEN: `src/fountain/parser.py:729-738`: apply the same extension extraction natural cues get at line 103.
- Acceptance: `@McClane (O.S.)` yields text `McClane` and `extension` `O.S.`.

---

## Section 8: Compliance Group D: Transitions and Emphasis

**Validator consults:** python:python

Transition edge cases and the emphasis rework: strip delimiters, guard delimiter-adjacent spaces, compute span offsets against stored text, and render nested spans without duplication.

Fable checkpoint (optional): confirm the emphasis model (composable nested spans with delimiters stripped, per the D4/D6/D7 ruling) before touching `_extract_formatting`, since it changes the FormatSpan contract.

### Step 8.1: D1: trailing spaces after the colon defeat a transition

- RED: `TestSpecCompliance::test_trailing_space_defeats_transition`: `CUT TO: ` (trailing space) parses as ACTION.
- GREEN: `src/fountain/parser.py`: the transition classifier must see the untrimmed line so a trailing space defeats it (line 331 rstrips before classification; preserve the raw line for this check).
- Acceptance: `CUT TO: ` with a trailing space is ACTION.

### Step 8.2: D2: uppercase lines ending in `TO:` with punctuation are transitions

- RED: `TestSpecCompliance::test_punctuated_transition`: `SMASH-CUT TO:` with surrounding blank lines parses as TRANSITION.
- GREEN: `src/fountain/parser.py:108`: allow punctuation before `TO:` in the transition pattern.
- Acceptance: `SMASH-CUT TO:` is TRANSITION.

### Step 8.3: D4: emphasis delimiters stripped and spans cover only the content

- RED: `TestSpecCompliance::test_emphasis_delimiters_stripped`: parsing `This is **bold** text.` yields text `This is bold text.` with a bold span over `bold`; HTML output is `<strong>bold</strong>` with no asterisks.
- GREEN: `src/fountain/parser.py:1074-1101` and `src/fountain/renderer.py:556-567`: strip delimiters from element text; make spans cover only the emphasized content.
- Acceptance: text has no asterisks; the span covers `bold`; HTML shows `<strong>bold</strong>`.

### Step 8.4: D5: the keypad escape example renders correctly

- RED: `TestSpecCompliance::test_keypad_escape_example`: `Steel enters the code on the keypad: **\*9765\***` renders with `<strong>*9765*</strong>` and no stray delimiters.
- GREEN: `src/fountain/parser.py:1104-1119`: resolve the escaped asterisks inside the bold span and adjust span offsets around the escapes.
- Acceptance: the line renders `<strong>*9765*</strong>` with no stray delimiters.

### Step 8.5: D6: nested emphasis does not duplicate text

- RED: `TestSpecCompliance::test_nested_emphasis_no_duplication`: `_Steel's face FILLS the *Leupold Mark 4* scope_.` renders as an underlined phrase containing one italic span, each word appearing exactly once.
- GREEN: `src/fountain/renderer.py:529-553` and `src/fountain/parser.py:1089-1101`: rework the segment builder to handle overlapping and nested spans; drop the partial-suppression artifact so bold, italic, and underline compose freely.
- Acceptance: the phrase renders once, underlined, with one nested italic span.

### Step 8.6: D7: bold and underline get the italic delimiter-adjacent-space guards

- RED: `TestSpecCompliance::test_bold_underline_space_guards`: `_ kilos_` and `** word**` produce no formatting spans.
- GREEN: `src/fountain/parser.py:191,203`: add the whitespace guards the italic pattern has at line 198 to the bold and underline patterns.
- Acceptance: delimiter-adjacent-space cases produce no spans.

### Step 8.7: D8: span offsets computed against stored text including indentation

- RED: `TestSpecCompliance::test_span_offset_includes_indentation`: ten spaces then `*Scott* --` yields an italic span over `Scott`, not over the leading whitespace.
- GREEN: `src/fountain/parser.py:808-812`: compute formatting offsets against the stored text, leading indentation included.
- Acceptance: the italic span is positioned over `Scott`.

### Step 8.8: D9: forced action retains indentation after the `!`

- RED: `TestSpecCompliance::test_forced_action_retains_indent`: `!    INDENTED FORCED ACTION` yields text beginning with four spaces.
- GREEN: `src/fountain/parser.py:622-629`: strip only the `!` and keep the following indentation.
- Acceptance: forced action text begins with four spaces.

---

## Section 9: Documented Contract Ambiguities

**Validator consults:** python:python

Pin the four documented ambiguities with tests and describe them in the user guide.
Changing any of these later is a breaking change.

Fable checkpoint (optional): none needed.

### Step 9.1: A3: title page detection heuristic pinned and documented

- RED: `TestSpecCompliance::test_title_page_detection_heuristic`: a first line `He opens the card:` opens the title page (colon, fails the scene-heading guard); a leading blank line or `>CUT TO:` avoids it.
- GREEN: no code change (this is contract behavior); document the heuristic and its workarounds in `docs/source/user-guide/parsing.rst`.
- Acceptance: the test pins the behavior; the user guide describes it with the documented workarounds.

### Step 9.2: C8: lyrics inside a dialogue block end the block, pinned and documented

- RED: `TestSpecCompliance::test_lyrics_end_dialogue_block`: `JOHN` / `~Willy Wonka!` / `Wasn't that great?` yields CHARACTER, LYRICS, ACTION.
- GREEN: no code change; document the behavior in `docs/source/user-guide/parsing.rst`.
- Acceptance: the test pins CHARACTER, LYRICS, ACTION; the guide documents it.

### Step 9.3: D11: `FADE IN:` and `FADE OUT.` as natural transitions, documented as a deliberate extension

- RED: confirm the existing pins at `tests/test_parser.py:57-58` and `tests/test_edge_cases.py:739-740` still pass after the Group D changes; add a targeted assertion if coverage is thin.
- GREEN: no code change; document the extension in `docs/source/user-guide/parsing.rst`.
- Acceptance: the existing tests stay green; the guide marks these as a deliberate extension.

### Step 9.4: E9: mid-line notes removed without a trace, documented

- RED: `TestSpecCompliance::test_inline_note_removed_standalone_kept`: an inline `[[note]]` is stripped and unrecoverable while a standalone `[[note]]` line becomes a NOTE element.
- GREEN: no code change; document the asymmetry in `docs/source/user-guide/parsing.rst`.
- Acceptance: the test pins the asymmetry; the guide documents it.

---

## Section 10: Documentation Truth-Up

**Validator consults:** python:python

Every published claim must be true before publish (Open Questions 2, 4, 5, 6, and the doc half of 3).
This section runs after the compliance work so the claims it restores are real.

Fable checkpoint (optional): confirm compliance Sections 4 through 9 are complete and green before asserting "Full Fountain Spec Compliance" anywhere.

### Step 10.1: Open Question 2: the compliance claim stands because it is now true

- RED: none (documentation), guarded by the full compliance suite from Sections 4 through 9.
- GREEN: verify `README.md:13` ("Full Fountain Spec Compliance") and `CHANGELOG.md:14` ("Full Fountain Spec Compliance") are accurate now that every requirement is fixed; keep the claim.
- Acceptance: the compliance suite is fully green and the README and CHANGELOG claims hold without a waiver.

### Step 10.2: Open Question 4: FountainElement.text docstring made accurate

- RED: none (docstring); doctests still pass under `--doctest-modules`.
- GREEN: `src/fountain/elements.py:146,153`: rewrite the `text` docstring so it is accurate after D4 (emphasis delimiters removed) and states what BONEYARD and NOTE elements carry (their delimiters verbatim).
- Acceptance: the docstring matches actual behavior for emphasis, BONEYARD, and NOTE.

### Step 10.3: Open Question 5: round-trip docs state the real fidelity

- RED: none (documentation).
- GREEN: rewrite the round-trip claims in `README.md:81-89` and the docstring at `src/fountain/renderer.py:656-672` to reflect A4, A4b, A4c (blank lines, dual dialogue, and lyrics now round-trip) and state the remaining `_apply_formatting_removal` limitation precisely (inline emphasis markers are not re-emitted).
- Acceptance: the round-trip docs match actual behavior after Section 5.

### Step 10.4: Open Question 6: CHANGELOG tab claim reworded

- RED: none (documentation).
- GREEN: reword the CHANGELOG "Tab-to-spaces conversion verified in HTML output" claim to match the A5/D10 fix (tabs convert to four spaces in element text at parse time; indentation is preserved in HTML).
- Acceptance: the CHANGELOG tab claim matches the shipped behavior.

### Step 10.5: Open Question 3: hidden-by-default docs and docstrings agree

- RED: none (documentation), guarded by the E5 and E11 renderer tests.
- GREEN: reconcile `src/fountain/renderer.py:247,250` docstrings and `docs/source/user-guide/rendering.rst:167` with the E5/E11 mechanics so notes, sections, synopses, and boneyard are described as omitted from formatted output by default in both fragment and page modes.
- Acceptance: docstrings and docs agree with the renderer behavior from Section 4.

---

## Section 11: Tooling Cleanup

**Validator consults:** python:python

Remove the dangling pre-commit references (CR-3) and keep the quality gate intact (Open Question 11: `just fix` stays inside `just test`).

Fable checkpoint (optional): none needed.

### Step 11.1: CR-3: remove dangling pre-commit recipes and references

- RED: `TestSpecCompliance::test_no_pre_commit_references` (or a shell check in the step) asserting `just --list` shows no pre-commit recipes and `grep -ri pre-commit` over the tracked tree matches nothing outside git history.
- GREEN: `justfile:78-84`: delete the `pre-commit-install` and `pre-commit-all` recipes; `CONTRIBUTING.md:23-24`: remove the `pre-commit install` instruction.
- Acceptance: no pre-commit recipes in `just --list`; `grep -ri pre-commit` over tracked files is empty.
- Note: Open Question 11 is settled: `just test` keeps `just fix` inside the gate; no change to the recipe order.

---

## Section 12: Path to PyPI

**Validator consults:** python:python

Harden the pipeline, add a TestPyPI dry run, verify the build in CI, and run a local end-to-end check.
This is the last section: it runs only after compliance is done and every published claim is true.

Fable checkpoint (optional): confirm with Mason that 0.1.0 is the version to publish and that trusted publishing is the chosen auth path before wiring the release workflow.

### Step 12.1: CI dependency install fix and build verification

- RED: none (CI config); the change is self-verifying when CI runs.
- GREEN: `.github/workflows/ci.yml`:
  - Replace `uv pip install -e ".[dev]"` (line 29) with `uv sync --dev` so the dev dependency group actually installs.
  - Add a `uv build` step plus a wheel-contents check that the wheel includes `fountain/__init__.py`, `parser.py`, `renderer.py`, and `py.typed`.
  - Add the Sphinx doctest build (`sphinx-build -b doctest docs/source docs/build/doctest`) so doctests run in CI.
- Acceptance: CI installs dev tools via `uv sync --dev`, builds the wheel, verifies its contents, and runs the Sphinx doctest build.
- Note: `.github/workflows/docs.yml` is already tracked and builds/deploys HTML on push to `main`; it does not run doctests, which is why the doctest build lands here.

### Step 12.2: Harden the publish workflow

- RED: none (CI config).
- GREEN: `.github/workflows/publish.yml`:
  - Add a test job that runs the full suite, and gate the publish job on it with `needs:`.
  - Build once, upload the wheel and sdist as artifacts, and download them in the publish job so the tested artifact is the published artifact.
  - Add an `environment:` declaration for deployment protection.
  - Switch to trusted publishing (drop `UV_PUBLISH_TOKEN` / `secrets.PYPI_API_TOKEN`; keep `id-token: write`, the only permission trusted publishing needs).
- Acceptance: publish runs only after tests pass, publishes the exact tested wheel, declares an environment, and authenticates via trusted publishing with no stored token.

### Step 12.3: Add the TestPyPI dry-run workflow

- RED: none (CI config).
- GREEN: create `.github/workflows/test-publish.yml`, triggered by `workflow_dispatch`, that builds and publishes to TestPyPI (using trusted publishing against the TestPyPI environment), used to validate install, README rendering, and metadata before the real publish.
- Acceptance: `.github/workflows/test-publish.yml` exists, is manually triggered, and targets TestPyPI.

### Step 12.4: Local end-to-end verification

- RED: none (manual verification with recorded output).
- GREEN: run the local end-to-end check: `uv build`, install the wheel in a clean venv, run an import-and-parse-and-render smoke test on a sample screenplay, run full `just test`, then clean up `dist/`.
- Acceptance: `pip install` of the built wheel on a clean 3.10 through 3.14 interpreter parses a screenplay and renders HTML without errors; `just test` passes clean.

---

## Release Mechanics (Human-Gated)

After every section above is complete and green, the release is Mason's to trigger:

- Merge `init-version` to `main` (Mason merges; agents never do).
- Tag `v0.1.0`, create the GitHub Release.
- Let the gated publish workflow run.
- Verify the PyPI page renders and `pip install fountain-py` works.

Goal chain: publishing 0.1.0 to PyPI unblocks the bartleby integration and the sites built on the stack.
