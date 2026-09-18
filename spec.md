# fountain-py Product Spec

Date: 2026-07-02.
Reviewed by Mason on 2026-07-03 via `/bpe:review`; his rulings are folded in below, each marked "Ruling (2026-07-03)".
Revised 2026-08-15: 0.1.0 shipped to PyPI on 2026-08-08, and this revision scopes the 0.2.0 release (see the "0.2.0: Output Modes and Interchange" section).
This document states the behavior of fountain-py as it exists in this working tree, and the requirements that separate today's behavior from a publishable 0.1.0.
Actual behavior is the contract: where this spec describes parsing or rendering, it describes what the code does today, verified by the test suite (241 tests passing) and the compliance audit in `.ai-sessions/fountain-compliance-audit.md`.
Full compliance with the Fountain syntax specification at https://fountain.io/syntax/ is a stated product requirement.
The gaps between today's behavior and that requirement are enumerated in the Spec Compliance Requirements section; each is a defect to fix, not a contract to preserve.

## Product Goal

fountain-py is a zero-dependency Python library that parses Fountain screenplay markup into structured objects and renders them as HTML or back to Fountain text.
The 0.1.0 release ships when the library is spec-compliant per the requirements below, the publish pipeline is hardened per the Path to PyPI section, and the documentation matches the code.
0.1.0 shipped to PyPI on 2026-08-08 with all of the above true.
The 0.2.0 release adds output modes and interchange (JSON as a versioned contract with deserialization, a formal renderer protocol, plain-text, FDX, and PDF renderers, and a command-line interface); it ships when the 0.2.0 section below is green under the same quality gates.

## Public API Contract

### Package Exports

`fountain/__init__.py` exports exactly six symbols via `__all__` (src/fountain/__init__.py:14-21):

- `FountainParser` (from `fountain.parser`)
- `FountainDocument` (from `fountain.document`)
- `ElementType` (from `fountain.elements`)
- `FountainElement` (from `fountain.elements`)
- `FormatType` (from `fountain.elements`)
- `MetadataValue` (from `fountain.elements`)

`HTMLRenderer`, `FountainRenderer`, `DEFAULT_CSS`, and `TITLE_PAGE_FIELD_ORDER` are public in `fountain.renderer` but are not re-exported at the package top level.
`FormatSpan` is public in `fountain.elements` but is likewise not in the top-level `__all__`.

Ruling (2026-07-03, resolving Open Question 7): promote `HTMLRenderer` and `FountainRenderer` to the top-level `__all__` before 0.1.0.
A populated `__init__.py` is the accepted library exception to the python skill's empty-`__init__` rule: published libraries (requests, httpx, attrs) re-export their public API there to give users a stable flat import path decoupled from internal module layout, and the README and quickstart already teach the renderers as primary API.
The exception is narrow: `__init__.py` stays restricted to imports and `__all__`, no logic.
Acceptance: `from fountain import HTMLRenderer, FountainRenderer` works, and `fountain/__init__.py` contains nothing but re-exports, `__all__`, and the module docstring.

### FountainParser

`FountainParser()` takes no constructor arguments.
Parser instances hold mutable parse state (`lines`, `current_line`, `elements`, boneyard and note flags) that is reset at the top of every `parse()` call.
An instance can be reused for sequential parses; code that parses from multiple threads should construct one parser per thread, which costs nothing since the constructor takes no arguments.

`parse(text: str) -> FountainDocument` runs a two-pass parse: pass 1 extracts title page metadata, pass 2 classifies body lines, then a post-pass pairs dual dialogue.
It never raises on malformed markup; unclassifiable lines fall back to ACTION elements.
The known exceptions to that promise are the boneyard truncation defects E2 and E3 below, which silently drop document content.

`parse_file(filepath: str) -> FountainDocument` reads the file as UTF-8 and delegates to `parse()`.
It propagates `FileNotFoundError`, `OSError`, and `UnicodeDecodeError` from the underlying `open()` and `read()`.

Today `parse()` reports no warnings or errors; the only diagnostics available are the element types and line numbers on the parsed output.
Ruling (2026-07-03, resolving Open Question 8): a validation API is required for 0.1.0; it is specced in the next section.

### Validation API (Required for 0.1.0)

`parse()` stays lenient and non-raising; `validate()` is the diagnostic channel that makes silent degradation visible instead of swallowed.

- `FountainParser.validate(text: str) -> list[ValidationIssue]` runs the same two-pass analysis as `parse()` but collects diagnostics instead of discarding them.
- `ValidationIssue` is a frozen dataclass with `line_number: int` (1-based), `severity: Literal["error", "warning"]`, `code: str` (a stable machine-readable identifier), and `message: str` (human-readable).
- Initial diagnostic set:
  - `unclosed-boneyard` (error): `/*` with no closing `*/` before EOF.
  - `unclosed-note` (error): `[[` with no closing `]]` before EOF.
  - `orphan-character-cue` (warning): an uppercase line that looks like a character cue but was demoted to ACTION because no dialogue follows.
  - `empty-document` (warning): no elements parsed.
- The code set is expected to grow as compliance fixes land; once shipped, each code string is contract.
- `ValidationIssue` is exported from the package top level alongside the other public types.

Acceptance: validating a document with an unclosed boneyard returns one `unclosed-boneyard` error carrying the opening line's number; a well-formed script returns `[]`; `parse()` output is byte-identical with or without a prior `validate()` call.

### Title Page Parsing Rules (Pass 1)

- Leading blank lines are skipped.
- A line containing a colon that does not start with the literal strings `INT.`, `EXT.`, `EST.`, or `I/E.` opens or continues the title page as a `key: value` pair (src/fountain/parser.py:448).
- Keys are lowercased and arbitrary; any key is accepted per the Fountain spec's open key set.
- A line without a colon following a current key is appended to that key's value, joined with a single space, unless it starts with `INT.`, `EXT.`, `EST.`, `I/E.`, or `.`, which ends the title page instead (src/fountain/parser.py:463-473; verified by probe: `Title: X` followed by `.FLASHBACK` yields a forced SCENE_HEADING, not a longer title).
- A blank line ends the title page once at least one key has been read.
- The result is a flat `dict[str, str]` stored as `FountainDocument.metadata`.

Known deviations from the Fountain spec in this pass are requirements A1, A2, and B3 below.
The line-one detection heuristic itself (what counts as a title page at all) is documented contract behavior; see Ambiguity A3.

### Body Classification Rules (Pass 2)

Lines are classified one at a time with this precedence (src/fountain/parser.py:481-813):

1. Inside a multi-line boneyard, lines are skipped until a line ends with `*/`.
2. A line that is entirely `/* ... */` becomes a BONEYARD element with its text verbatim, including the delimiters.
3. A line starting `/*` without a closing `*/` on the same line enters boneyard state and is skipped.
4. Inside a multi-line note, lines accumulate until a line contains `]]`, then a single NOTE element is emitted with the buffered text.
5. Three or more equals signs alone on a line become PAGE_BREAK.
6. A line that starts with `[[`, ends with `]]`, and contains at least one complete `[[...]]` match becomes a NOTE element with the full line verbatim, brackets included; `[[a]] middle [[b]]` is one NOTE, so the interior text never reaches formatted output (requirement E13).
7. A line containing `[[` without `]]` starts a multi-line note.
8. Inline `[[notes]]` are stripped from the line text and discarded; the note content is unrecoverable from the parse (see Ambiguity E9).
9. `!text` forces ACTION; the `!` is removed and the remainder is stripped of surrounding whitespace.
10. `#`-prefixed lines become SECTION with `metadata["level"]` equal to the number of leading hashes.
11. `=`-prefixed lines (not page breaks) become SYNOPSIS with one `=` stripped.
12. `~text` becomes LYRICS with the `~` removed.
13. `.HEADING` (a period followed by an alphanumeric, not `..`) forces SCENE_HEADING with `metadata["forced"] = True`; a trailing `#number#` is extracted to `metadata["scene_number"]`.
14. `>text<` becomes CENTERED with the angle brackets removed.
15. `>text` (no trailing `<`) forces TRANSITION.
16. A line matching the scene heading prefixes `INT.`, `EXT.`, `EST.`, `I/E.`, `INT/EXT.`, `INT./EXT.` (case-insensitive, optional space before the dot) becomes SCENE_HEADING when preceded by a blank line or before any element has been emitted (document start, or after lines that produced no element, such as a multi-line boneyard); scene numbers are extracted as in rule 13.
17. A line matching `^[A-Z\s]+TO:$`, `FADE IN:`, `FADE OUT.`, or `CUT TO:` becomes TRANSITION when followed by a blank line (EOF counts as blank) and preceded by a blank line or no emitted element; verified by probe, `FADE OUT.` on line one is a TRANSITION.
18. `@name` forces CHARACTER with `metadata["forced"] = True`, but only when the lookahead `_is_dialogue_following()` approves the next line; otherwise the line falls through toward ACTION with the `@` retained (defect C6).
19. `NAME^` (all caps) becomes CHARACTER with `metadata["dual_dialogue"] = True` when preceded by a blank line (or no emitted element, as in rule 16) and followed by dialogue.
20. `NAME (extension)` with optional trailing `^` becomes CHARACTER with `metadata["extension"]` (and `dual_dialogue` when the caret is present) under the same blank-line and lookahead conditions.
21. A line matching `^[A-Z][A-Z0-9\s_]*$` becomes CHARACTER under the same conditions; `metadata["continuation"] = True` is set when the same character spoke earlier in the scene with intervening action and no scene break.
22. A line following a CHARACTER or PARENTHETICAL, or following DIALOGUE with no intervening blank line, becomes DIALOGUE; if it is wrapped in parentheses it becomes PARENTHETICAL instead.
23. Everything else becomes ACTION, with the original line's leading whitespace preserved (trailing whitespace stripped).

A whitespace-only line while the previous element is DIALOGUE, PARENTHETICAL, or CHARACTER emits an empty DIALOGUE element, implementing the spec's two-space dialogue continuation (src/fountain/parser.py:333-352).
Backslash escapes `\*`, `\_`, and `\\` are resolved to literal characters in element text, and formatting spans are position-adjusted around them (src/fountain/parser.py:1004-1024, 1104-1119).

The character cue lookahead `_is_dialogue_following()` skips blank lines and rejects the cue when the next non-empty line matches any structural pattern in `STRUCTURAL_PATTERNS` or is a standalone `[[...]]` note line (src/fountain/parser.py:164-178, 815-856).
This lookahead is the source of defects C3, C4, and C6 below.

### Dual Dialogue Post-Processing

After line classification, `_process_dual_dialogue()` (src/fountain/parser.py:1123-1222) finds CHARACTER elements with `dual_dialogue` metadata, pairs each with the immediately preceding character block (no scene heading or action between them), and replaces both blocks with one DUAL_DIALOGUE element.
The DUAL_DIALOGUE element has empty text and carries `left_character`, `left_dialogue`, `right_character`, and `right_dialogue` in its metadata, where the dialogue values are lists of DIALOGUE and PARENTHETICAL elements.

Ruling (2026-07-03): evaluate whether this pairing should stay a hard-coded post-pass or become a stage in a formal processing pipeline.
Mason's planned expanded-markdown library composes parsers with pre- and post-processor stages, and fountain-py needs to fit that model; some transforms may belong before line classification and some after.
The design question is tracked as Open Question 12; no refactor happens before that design pass.

### Inline Formatting Extraction

`_extract_formatting()` (src/fountain/parser.py:1026-1121) returns `FormatSpan` entries for `***bold italic***`, `**bold**`, `*italic*`, and `_underline_`, with precedence in that order.
Overlap suppression is partial: bold is suppressed only inside bold-italic spans, italic inside bold-italic and bold spans, and underline is never suppressed, so `**_word_**` yields overlapping bold and underline spans (src/fountain/parser.py:1074-1101; verified by probe; this feeds defect D6).
The italic pattern has whitespace guards (no space adjacent to the delimiters); bold and underline do not (defect D7).
Span positions cover the full match including the delimiter characters, and the delimiters remain in the element text (defect D4).

Ruling (2026-07-03): suppression is not a Fountain concept at all.
The spec lets bold, italic, and underline combine freely (its own example underlines a phrase containing an italic span), so the partial-suppression behavior above is an implementation artifact, not contract.
The required end state is composable nested spans with delimiters stripped, delivered by requirements D4, D6, and D7.

### FountainDocument

`FountainDocument(elements, metadata=None)` holds `elements: list[FountainElement]` and `metadata: dict[str, str]` (empty dict when None).

- `to_dict() -> dict[str, Any]` returns `{"metadata": ..., "elements": [...]}` where each element dict carries `type` (the enum value string), `text`, `formatting` (list of `{start, end, format_type}`), `line_number`, and `metadata`.
- `to_json() -> str` is `json.dumps(self.to_dict(), indent=2)`.
- `get_characters() -> list[str]` returns unique CHARACTER names, uppercased, trailing `^` stripped, sorted alphabetically.
- `get_scenes() -> list[str]` returns SCENE_HEADING texts in document order.
- `get_statistics() -> dict[str, int]` returns `total_elements`, `characters` (unique count), `scenes`, and a `{element_type}_count` key for each of the 15 element types; the per-type counts come from a single `Counter` pass, while `characters` and `scenes` delegate to `get_characters()` and `get_scenes()` (src/fountain/document.py:299-308).
- `to_html() -> str` constructs an `HTMLRenderer` and returns `render_page(self)` (full page with embedded CSS).

### Type System

- `ElementType` (src/fountain/elements.py:34-91) is an `Enum` with exactly 15 members: TITLE_PAGE, SCENE_HEADING, ACTION, CHARACTER, DIALOGUE, PARENTHETICAL, TRANSITION, NOTE, BONEYARD, SECTION, SYNOPSIS, DUAL_DIALOGUE, PAGE_BREAK, CENTERED, LYRICS.
  TITLE_PAGE exists in the enum but the parser never emits it as an element; title page data lives in `FountainDocument.metadata`.
- `FountainElement` (src/fountain/elements.py:136-233) is a mutable dataclass with fields `type: ElementType`, `text: str`, `formatting: list[FormatSpan]`, `line_number: int` (1-based source line), and `metadata: dict[str, Any] | None` which `__post_init__` normalizes to an empty dict.
- `FormatSpan` (src/fountain/elements.py:94-133) is a NamedTuple of `start: int`, `end: int` (exclusive), `format_type: FormatType`.
- `FormatType` is `Literal["bold", "italic", "underline", "bold_italic"]`.
- `MetadataValue` is `Union[str, int, bool, list["FountainElement"], "FountainElement", None]`, the value union that element metadata actually holds.
  It is exported but not yet applied to the `FountainElement.metadata` annotation; applying it is required per CR-2 (ruling 2026-07-03: fix it).

### HTMLRenderer

Three output modes (src/fountain/renderer.py:280-373):

- `render(document) -> str` returns a pure HTML fragment: `<div class="fountain-script">` wrapping an optional `<div class="fountain-title-page">` and a `<div class="fountain-script-body">` of element divs. No `<style>` tag.
- `render_page(document) -> str` returns `<style>` + `DEFAULT_CSS` + `</style>` followed by the fragment.
- `get_css() -> str` returns the raw `DEFAULT_CSS` string with no `<style>` tags.

All CSS classes are namespaced with the `fountain-` prefix (e.g. `fountain-scene-heading`, `fountain-action`, `fountain-character`, `fountain-dual-dialogue`).
Title page fields render in the order defined by the module constant `TITLE_PAGE_FIELD_ORDER` (src/fountain/renderer.py:199-217), shared with `FountainRenderer`; unknown keys render after known ones as `<p class="fountain-custom-field {key}">Key: value</p>`.
When both `author` and `authors` keys are present, `HTMLRenderer` renders only `author` (they share a slot; src/fountain/renderer.py:403-404) while `FountainRenderer` emits both keys; verified by probe, see Open Question 10.
Element text is HTML-escaped via `html.escape(text, quote=True)`.
Scene numbers render as `<span class="fountain-scene-number">#N#</span>`, character extensions as `<span class="fountain-character-extension">(EXT)</span>`, and continuation metadata as a `(CONT'D)` span.
Dual dialogue renders as a flexbox two-column layout.
Formatting spans map to `<strong>`, `<em>`, `<u>`, and `<strong><em>` for bold_italic; the span builder assumes non-overlapping spans (defect D6).
In ACTION elements, tabs become four `&nbsp;` entities and embedded newlines become `<br>` at render time.

### FountainRenderer

`FountainRenderer().render(document) -> str` converts a document back to Fountain markup: title page fields as `Key: Value` lines, then each element rendered with its forcing markers, scene numbers, extensions, carets, and section hashes restored, joined with single newlines (src/fountain/renderer.py:690-727).
Known limitations, stated in the code and confirmed by probe:

- Blank-line separators are not emitted, so re-parsing the output degrades CHARACTER and DIALOGUE to ACTION (requirement A4).
- DUAL_DIALOGUE elements render as the empty string, so paired dual dialogue blocks vanish entirely from the output (requirement A4b; verified by probe on this tree: a scene with a dual dialogue pair round-trips to just the scene heading line).
- Inline emphasis markers are not re-emitted; `_apply_formatting_removal()` returns the text unchanged (src/fountain/renderer.py:883-916).
- LYRICS render as `~text~` but the parser strips only the leading tilde, so every round trip appends a literal `~` to the lyric text (requirement A4c; src/fountain/renderer.py:876-877 versus src/fountain/parser.py:160, 654-662; verified by probe: `~La la la` re-parses as `La la la~`).

### Error Behavior Summary

- Malformed markup never raises from `parse()`; it degrades to ACTION.
  Ruling (2026-07-03): degrading silently with no diagnostic channel is swallowing errors, and that is bad practice.
  The Validation API above is the required remedy: `parse()` stays lenient, and every degradation the parser can detect must be reportable through `validate()`.
- `parse_file` propagates file system and decoding errors unchanged.
- Boneyard edge cases E2 and E3 silently truncate the document, which violates the library's own degrade-to-action philosophy and the Fountain spec's error-handling guidance; they are the highest-priority fixes in this spec.

### Supported Python Versions

Ruling (2026-07-03, resolving Open Question 9): the floor moves to 3.10 and the ceiling tracks current CPython releases.

- Target state: `requires-python = ">=3.10"`, classifiers for 3.10 through 3.14, ruff `target-version = "py310"`, mypy `python_version = "3.10"`.
- Code modernizes to the 3.10 floor: `X | None` over `Optional[X]`/`Union` throughout, per the python skill's standards (ruff UP007 enforces it).
- CI tests every supported version: 3.10 through 3.14 now, with 3.15 added when it releases (October 2026).
- Current state, which this ruling changes: pyproject declares `>=3.9` with a `py39` ruff target and CI runs the 3.9 through 3.13 matrix (`.github/workflows/ci.yml:14`).
- The package ships zero runtime dependencies and includes `py.typed`; that does not change.

## Spec Compliance Requirements

Full compliance with https://fountain.io/syntax/ is a product requirement.
The verified audit (`.ai-sessions/fountain-compliance-audit.md`, dated 2026-07-02, all probes re-run against this tree) confirmed 34 gaps.
Each is a numbered requirement below; IDs match the audit for traceability, and the items tagged "found during spec verification" (A4b, A4c, E13) are additions from this review, not audit items.
Each acceptance criterion is written so a failing test can encode it today and pass after the fix.
Severities come from the audit and order the work, but they no longer gate differently.
Ruling (2026-07-03): everything gets fixed before we ship; high, medium, and low items are all fixed before 0.1.0, and nothing is waived.

### Group A: Title Page and Whitespace

- **A1 (medium).** Title page multi-line values must preserve their line structure instead of flattening to a space-joined string (src/fountain/parser.py:463-467).
  Acceptance: parsing `Contact:` followed by three indented address lines yields a `contact` value with three lines (or a list of three values), and `render_page()` output contains `<br>` between them.
- **A2 (medium).** Title page continuation must require indentation (3+ spaces or a tab), and indented lines containing colons must remain values of the current key (src/fountain/parser.py:448, 463).
  Acceptance: `Notes:` followed by an indented `Draft 3: final revisions` yields `metadata["notes"] == "Draft 3: final revisions"` and no `draft 3` key; an unindented non-key line ends the title page instead of being absorbed into the previous value.
- **A4 (high).** Blank lines must survive parse and `FountainRenderer` round trip; the spec treats every carriage return as intent (src/fountain/parser.py:331-355; src/fountain/renderer.py:727).
  Acceptance: `parse(FountainRenderer().render(parse(script)))` preserves element types for a script containing character/dialogue blocks separated by blank lines; CHARACTER does not degrade to ACTION.
- **A4b (high).** Dual dialogue must survive the Fountain round trip (src/fountain/renderer.py:865-868).
  Acceptance: rendering a document containing a DUAL_DIALOGUE element emits both character blocks with the caret on the second cue; re-parsing reproduces a DUAL_DIALOGUE element.
  (Found during spec verification; same fix surface as A4.)
- **A4c (low).** Lyrics must round-trip without accreting delimiters; the Fountain lyric marker is a leading `~` only (src/fountain/renderer.py:876-877).
  Acceptance: `parse(FountainRenderer().render(parse("~La la la")))` yields a LYRICS element with text `La la la` and no trailing tilde.
  (Found during spec verification: today the text comes back as `La la la~`.)
- **A5 (medium).** Tabs in Action are retained verbatim in element text (the Fountain spec keeps tabs and spaces in Action); the renderer converts each tab to four `&nbsp;` entities so the indentation is visible in HTML output (src/fountain/renderer.py:442-446).
  Acceptance: a tab-indented action line yields `element.text` keeping the raw tab; rendered HTML shows four `&nbsp;` per tab.
  Shares a fix surface with D10.

### Group B: Scene Headings

- **B1 (high).** Scene heading prefixes followed by a space must be recognized alongside the dot forms: `INT HOUSE - DAY` is a scene heading (src/fountain/parser.py:70-73).
  Acceptance: `INT`, `EXT`, `EST`, `I/E`, `INT/EXT` space forms parse as SCENE_HEADING; `INTERNAL AFFAIRS INVESTIGATES.` still parses as ACTION (prefix boundary required).
- **B2 (medium).** A natural scene heading requires a blank line after it (src/fountain/parser.py:702-717; compare the transition branch at 720).
  Acceptance: `EXT. BRICK'S PATIO - DAY` immediately followed by a non-blank line parses as ACTION.
- **B3 (medium).** The title page guard for scene headings must be case-insensitive and accept the space form (src/fountain/parser.py:448).
  Acceptance: a document whose first line is `int. house - day - 3:00 pm` parses it as SCENE_HEADING, not as title page metadata.
- **B4 (low).** Scene numbers must be restricted to alphanumerics plus dashes and periods (src/fountain/parser.py:78).
  Acceptance: `INT. HOUSE - DAY #$%^&#` keeps `#$%^&#` in the heading text and sets no `scene_number` metadata.

### Group C: Characters and Dialogue

- **C1 (high).** Uppercase cues containing punctuation must be recognized: `MR. SMITH`, `O'BRIEN`, `JEAN-CLAUDE`, `DEALER #2` (src/fountain/parser.py:88, 93, 103).
  Acceptance: each of those lines followed by a dialogue line parses as CHARACTER plus DIALOGUE.
- **C2 (low).** Digit-first cues with at least one letter must be recognized: `23 SKIDOO` (src/fountain/parser.py:88).
  Acceptance: `23 SKIDOO` with dialogue parses as CHARACTER plus DIALOGUE; bare `23` remains ACTION.
- **C3 (medium).** A blank line immediately after a cue disqualifies it; the lookahead must not skip blank lines (src/fountain/parser.py:847-856).
  Acceptance: `JOHN`, blank line, `He walks to the door.` parses as two ACTION elements.
- **C4 (low).** An all-caps line after a cue is dialogue, not a competing structural element (src/fountain/parser.py:852).
  Acceptance: `JOHN` then `I SAID NO` parses as CHARACTER plus DIALOGUE.
- **C5 (medium).** A trailing caret on a forced character creates dual dialogue with the caret stripped (src/fountain/parser.py:98, 729-738).
  Acceptance: a `BRICK` block followed by an `@McClane ^` block yields a DUAL_DIALOGUE element and the right character's text is `McClane`.
- **C6 (medium).** `@` must force CHARACTER unconditionally; the force must not be gated on the dialogue lookahead (src/fountain/parser.py:729-738).
  Acceptance: `@McClane` then `I SAID NO` parses as CHARACTER (forced) plus DIALOGUE, with no literal `@` in the text.
- **C7 (low).** Forced characters must get extension extraction like natural cues (src/fountain/parser.py:729-738 versus 103).
  Acceptance: `@McClane (O.S.)` yields text `McClane` and `metadata["extension"] == "O.S."`.

### Group D: Transitions and Emphasis

- **D1 (low).** One or more trailing spaces after the colon defeat a transition (src/fountain/parser.py:331 rstrips before classification).
  Acceptance: `CUT TO: ` (trailing space) parses as ACTION.
- **D2 (low).** Uppercase lines ending in `TO:` with punctuation are transitions: `SMASH-CUT TO:` (src/fountain/parser.py:108).
  Acceptance: `SMASH-CUT TO:` with surrounding blank lines parses as TRANSITION.
- **D4 (high).** Emphasis delimiters must be stripped from element text, and spans must cover only the emphasized content (src/fountain/parser.py:1074-1101; src/fountain/renderer.py:556-567).
  Acceptance: parsing `This is **bold** text.` yields text `This is bold text.` with a bold span over `bold`; HTML output is `<strong>bold</strong>` with no asterisks.
- **D5 (medium).** The spec's keypad escape example must render correctly (src/fountain/parser.py:1104-1119).
  Acceptance: `Steel enters the code on the keypad: **\*9765\***` renders with `<strong>*9765*</strong>` and no stray delimiters.
- **D6 (high).** Nested emphasis must not duplicate text; the renderer's segment builder must handle overlapping or nested spans (src/fountain/renderer.py:529-553; src/fountain/parser.py:1089-1101).
  Acceptance: the spec's line `_Steel's face FILLS the *Leupold Mark 4* scope_.` renders as an underlined phrase containing one italic span, with each word appearing exactly once.
- **D7 (medium).** Bold and underline need the same delimiter-adjacent-space guards italic has (src/fountain/parser.py:191, 203 versus 198).
  Acceptance: `_ kilos_` and `** word**` produce no formatting spans.
- **D8 (medium).** Formatting span offsets must be computed against the stored text, including leading indentation (src/fountain/parser.py:808-812).
  Acceptance: ten spaces then `*Scott* --` yields an italic span positioned over `Scott`, not over the leading whitespace.
- **D9 (low).** Forced action must retain indentation after the `!` (src/fountain/parser.py:622-629).
  Acceptance: `!    INDENTED FORCED ACTION` yields text beginning with four spaces.
- **D10 (medium).** Space-indented action must be visible in HTML output; the spec's ten-space card example passes its indentation through (src/fountain/renderer.py:96-99, 466-469).
  Acceptance: rendering a ten-space-indented action line produces HTML whose visual output preserves the indentation.
  Same fix surface as A5.

### Group E: Boneyard, Notes, Sections

- **E1 (medium).** Mid-line `/* ... */` must be stripped from action and dialogue text (src/fountain/parser.py:132-140, 553-571).
  Acceptance: `Hello /* hidden */ world.` yields text `Hello world.`.
- **E2 (high).** A boneyard close with trailing text on the same line must end the boneyard; the close pattern must not be end-anchored (src/fountain/parser.py:140, 554-557).
  Acceptance: a `/*` block closed by `*/ And we are back.` yields `And we are back.` and all following lines as elements; nothing after the close is dropped.
- **E3 (high).** A single-line boneyard followed by trailing text must not swallow the document (src/fountain/parser.py:132, 136, 140, 568-571).
  Acceptance: `/* cut this */ keep this` followed by more action yields `keep this` and the following action as elements.
- **E4 (medium).** A mid-line boneyard opener must not leak the interior lines (src/fountain/parser.py:136, 568-571).
  Acceptance: `He waves /* begin cut`, interior lines, `*/` yields a single action `He waves` and no interior text.
- **E5 (medium).** Sections and synopses must be ignored in formatted output, and standalone notes must not render with literal `[[ ]]` brackets (src/fountain/renderer.py:488-491, 128-132, 138-149, 250, 484-485).
  Acceptance: rendering `# Act I`, `= He meets her.`, and `[[remember to fix]]` produces formatted output where section and synopsis are not visible by default and any rendered note shows its content without brackets.
- **E6 (low).** A two-space connector line inside a note must produce a note whose text contains an empty line (src/fountain/parser.py:329-355, 574-585).
  Acceptance: a note whose middle line is two spaces yields one NOTE whose text contains `\n\n` (an empty interior line).
- **E7 (low).** A genuinely blank line must break an open note; the bracket lines fall back to text (src/fountain/parser.py:329-355, 574-585).
  Acceptance: the same note with a truly blank middle line does not survive as a single NOTE; E6 and E7 inputs produce distinguishable outputs.
- **E8 (low).** A two-space line inside a note must not inject an empty DIALOGUE element (src/fountain/parser.py:333-351).
  Acceptance: dialogue block, then a note containing a two-space line, yields CHARACTER, DIALOGUE, NOTE and no empty dialogue element.
- **E10 (low).** A lone `]` inside a note must not break recognition; only `]]` closes (src/fountain/parser.py:127).
  Acceptance: `[[check ref] ok]]` yields a NOTE with text `check ref] ok`.
- **E11 (low).** Boneyard content must not ship in HTML fragments (src/fountain/parser.py:560-566; src/fountain/renderer.py:134-136, 486-487).
  Acceptance: `HTMLRenderer.render()` output for a document containing `/* hidden scene */` contains no boneyard text; behavior is consistent between single-line and multi-line boneyards.
- **E13 (low).** A line that starts with `[[` and ends with `]]` but carries text between two notes must not be swallowed as a single NOTE (src/fountain/parser.py:597-605).
  Acceptance: `[[a]] middle [[b]]` parses as ACTION with text `middle` (inline notes stripped per body rule 8), not as a NOTE containing the whole line.
  (Found during spec verification; today the whole line becomes one NOTE and `middle` never reaches formatted output.)

Refuted candidate for the record: double-equals synopsis handling (`== two equals` yielding SYNOPSIS text `= two equals`) is a defensible literal reading of the spec and is not a defect (audit E12; src/fountain/parser.py:150).

## Documented Contract Ambiguities

The Fountain spec leaves these underdetermined; the audit classified them as ambiguity or deliberate extension.
The behaviors below are contract: they must be documented in the user guide and pinned by tests, and changing them is a breaking change.

- **A3: title page detection.** A colon-bearing first line opens a title-page key only when it looks like one (`_opens_title_page_key`): it must carry a non-empty value or an indented continuation, and it must name a recognized field or be a capitalized label. So `FADE IN:` and `CUT TO:` (empty value) parse as body transitions and prose like `He opens the card: a threat.` (lowercase label) parses as body action, rather than being consumed as phantom metadata. A recognized field (`Title:`, `Contact:`, ...) or a capitalized custom label (`Custom Field:`) still opens the title page.
  The scene-heading guard's case sensitivity (B3) and in-page indentation (A2) are tracked separately.
- **C8: lyrics inside a dialogue block do not end the block.** A lyric or standalone note within a dialogue block does not close it; the following non-forced line continues as dialogue until a blank line. `JOHN` / `~Willy Wonka!` / `Wasn't that great?` yields CHARACTER, LYRICS, DIALOGUE (`_is_dialogue_line` looks back past LYRICS/NOTE to the block anchor).
- **D11: `FADE IN:` and `FADE OUT.` as natural transitions.** The spec's natural rule requires ending in `TO:`; fountain-py special-cases both (src/fountain/parser.py:108; pinned by tests/test_parser.py:57-58 and tests/test_edge_cases.py:739-740).
  This is a deliberate extension and must be documented as such.
- **E9: mid-line notes are removed without a trace.** Inline `[[note]]` content is stripped and unrecoverable from the parse, while a standalone `[[note]]` line becomes a NOTE element (src/fountain/parser.py:614-619).
  Document the asymmetry.

## Carried-Forward Code Review Findings

The March 2026 code review (the previous content of this file, preserved in git history at commit b9c6827) listed 14 findings.
Checked against today's code: findings 2 through 8, 11, 13, and 14 are fixed (dead code removed; `html.escape` at src/fountain/renderer.py:646; theme machinery gone; single-pass `Counter` at src/fountain/document.py:299; shared `TITLE_PAGE_FIELD_ORDER` at src/fountain/renderer.py:199; `STRUCTURAL_PATTERNS` at src/fountain/parser.py:164; `FormatType` at src/fountain/elements.py:30; fragment/page/CSS split at src/fountain/renderer.py:280-373; `fountain-` CSS namespacing throughout).
Finding 9 (non-empty `__init__.py`) and finding 12 (if/elif element dispatch) were accepted as deliberate; they stand as documented deviations.
Two findings carry forward:

- **CR-1 (low, residue of finding 1).** The ABOUTME header rule says only the first line starts with `ABOUTME:`.
  src/fountain/parser.py:1-2, src/fountain/elements.py:1-2, src/fountain/document.py:1-2, and tests/test_edge_cases.py:2-3 start both lines with `ABOUTME:` inside the module docstring.
  Acceptance: every source file's header has `ABOUTME:` on line one only, as plain comments matching src/fountain/renderer.py:1-2.
- **CR-2 (medium, residue of finding 10).** `MetadataValue` is defined and exported (src/fountain/elements.py:31, src/fountain/__init__.py:20) but `FountainElement.metadata` is still annotated `dict[str, Any] | None` (src/fountain/elements.py:209), as are the metadata locals in src/fountain/parser.py:667, 703, 759.
  Ruling (2026-07-03): fix the annotation; dropping the alias is off the table.
  Acceptance: `FountainElement.metadata` is `dict[str, MetadataValue] | None`; mypy strict passes.
- **CR-3 (low, found during spec verification).** The justfile keeps `pre-commit-install` and `pre-commit-all` recipes (justfile:78-84) and CONTRIBUTING.md:23-24 still tells contributors to run `pre-commit install`, although pre-commit is neither a dependency nor configured anywhere.
  Acceptance: `just --list` shows no pre-commit recipes and `grep -ri pre-commit` over the tracked tree matches nothing outside git history.

## Quality Metrics

Current state, which the release must not regress:

- 241 tests pass (`uv run pytest`), including module doctests via `--doctest-modules` over `src/`.
- Coverage target is 99%+ per the previous review's verification bar (`just unit-test-cov`).
- `just test` runs, in order: tests with coverage, doctests, ruff lint, mypy, `just fix` (ruff auto-fix, which can modify files; see Open Question 11), and ruff format check.
  It must pass clean.
  The pyproject mypy config stops short of `strict = true`, but `mypy --strict src/` passes today (verified by probe) and must keep passing per CR-2.
- CI runs the suite plus lint and type check on every push to `main` and on every pull request against `main` (already wired in ci.yml; pinned here as contract per the 2026-07-03 ruling), across every supported Python version (3.10 through 3.14 after the floor/ceiling ruling above; 3.15 added on release).
- Every compliance requirement above lands with a failing-first test that encodes its acceptance criterion.

## Available Tooling

Python work in this repository uses the `python:python` skill (mmegger-plugins marketplace).
It is the source of truth for typing standards, ruff/mypy/pytest configuration, uv workflows, and the TDD loop; load it before writing or reviewing any Python in this repo.
Project commands are wrapped in the `justfile` (`just dev`, `just test`, `just unit-test-cov`, `just docs`); dependency management is uv with `[dependency-groups]`.
Docs prose is linted with Vale through the repo's `.vale.ini` (per-directory registers matching the Diataxis tree); `vale docs/source/` with zero errors is the docs lint gate.

## Path to PyPI

Release contract for the first publish:

- **Version: 0.1.0**, matching pyproject.toml:3 and todo.md ("staying at 0.1.0 for first publish").
  Note the contradiction with plan.md, which targets 0.2.0 throughout; see Open Questions.
- **CHANGELOG and README** are already reconciled for 0.1.0 (todo.md steps 1 through 3 checked off), except for the accuracy findings recorded in Open Questions below.
- **Publish workflow hardening** (todo.md step 4): the current `.github/workflows/publish.yml` builds from a fresh checkout and publishes with no test gate, authenticating with `UV_PUBLISH_TOKEN` from `secrets.PYPI_API_TOKEN` even though the job already grants `id-token: write`, the one permission trusted publishing needs.
  Required: a test job before publish, build artifact upload/download so the tested wheel is the published wheel, a GitHub `environment:` declaration for deployment protection, and a decision between API token and trusted publishing (trusted publishing preferred; no secret to manage, and the permission is already declared).
- **TestPyPI workflow** (todo.md step 5): a `workflow_dispatch`-triggered `.github/workflows/test-publish.yml` targeting TestPyPI, used to validate install, README rendering, and metadata before the real publish.
- **Build verification in CI** (todo.md step 6): `uv build` plus wheel-contents verification (must include `fountain/__init__.py`, `parser.py`, `renderer.py`, `py.typed`) and the Sphinx doctest build added to ci.yml.
- **CI dependency install fix** (found during spec verification): ci.yml:29 runs `uv pip install -e ".[dev]"`, but pyproject.toml defines the dev tools under `[dependency-groups]`, not a `dev` extra, so uv warns `does not have an extra named 'dev'` and installs no dev tools (verified by probe).
  The jobs pass only because the later `uv run` commands re-sync the environment with the dev dependency group.
  Replace the install step with `uv sync --dev` so it does what it says.
- **Docs workflow**: `.github/workflows/docs.yml` builds Sphinx HTML (`sphinx-build -b html`, Python 3.12, dev and docs groups) on push to `main` and deploys to GitHub Pages behind a `github-pages` environment.
  It is currently untracked and must be committed for Pages deploys to run; it does not run the Sphinx doctest build, so todo step 6 remains the only path for doctests into CI.
- **Local end-to-end verification** (todo.md step 7): build, install the wheel in a clean venv, import-and-parse smoke test, full `just test`, then clean up `dist/`.

Production ready for this library means: every compliance requirement fixed with pinned tests regardless of severity (ruling 2026-07-03: no waivers), the Validation API shipped, the rulings in Open Questions carried out so every published claim is true, the publish pipeline gated as above, a TestPyPI dry run verified, and `pip install fountain-py` on a clean 3.10 through 3.14 interpreter parsing a screenplay and rendering HTML without errors.
Release mechanics: merge to `main` (Mason merges; agents never do), tag `v0.1.0`, create the GitHub Release, let the gated workflow publish, verify the PyPI page.

## 0.2.0: Output Modes and Interchange

Scoped 2026-08-15.
The 0.2.0 theme is output modes: finish JSON as a real interchange format, formalize the renderer contract, and add plain-text, FDX, and PDF renderers plus a command-line interface.
Requirement IDs continue the 0.1.0 lettering: Group F (serialization), G (renderer protocol), H (plain text), I (CLI), J (FDX), K (PDF), L (documentation).
Every group lands with failing-first tests under the same quality gates as 0.1.0: `just test` clean, coverage 99%+, `mypy --strict src/` green, docs updated and Vale-clean.
Target version is 0.2.0; the pyproject version bump happens in the release mechanics at the end, not as an early step.
New renderers live in their own modules so `renderer.py` does not keep growing; the plan decides the exact layout (a `fountain.renderers` package is the working assumption).

### Group F: Serialization and JSON Interchange

- **F1 (high, shipped defect).** `to_dict()` passes element metadata through verbatim, so DUAL_DIALOGUE metadata carries live `FountainElement` objects and `to_json()` raises `TypeError` on any document containing dual dialogue (verified by probe, 2026-08-15; no 0.1.0 test covered JSON of a dual-dialogue scene).
  `to_dict()` must recursively serialize metadata values: a `FountainElement` value becomes its element dict, and a list of elements becomes a list of element dicts.
  Acceptance: `to_json()` on a dual-dialogue document returns valid JSON, with the nested character and dialogue elements in the same dict shape as top-level elements.
- **F2.** The JSON shape becomes a documented, versioned contract.
  `to_dict()` gains a top-level `"schema_version": 1` key, and a reference page documents every field and every metadata value shape.
  Acceptance: `to_dict()["schema_version"] == 1`; `docs/source/reference/json-schema.rst` exists, sits in the Reference toctree, and documents the element dict shape including nested dual-dialogue metadata.
- **F3.** Deserialization: `FountainDocument.from_dict(data)` and `FountainDocument.from_json(text)` reconstruct a document, including `ElementType` values, `FormatSpan` entries, and nested elements in metadata.
  Acceptance: `FountainDocument.from_json(doc.to_json()).to_dict() == doc.to_dict()` over a corpus that includes dual dialogue, formatting spans, scene numbers, extensions, and title-page metadata; an unknown `schema_version` raises `ValueError`.

### Group G: Renderer Protocol

- **G1.** The renderer contract the docs teach informally becomes a typed protocol.
  Define a `runtime_checkable` `TextRenderer` protocol (`render(document: FountainDocument) -> str`) and a `BinaryRenderer` protocol (`render_bytes(document: FountainDocument) -> bytes`) for binary formats such as PDF.
  `HTMLRenderer` and `FountainRenderer` must satisfy `TextRenderer` structurally, with no inheritance changes.
  Acceptance: `isinstance(HTMLRenderer(), TextRenderer)` holds; both protocols are exported from the package top level; the custom-renderer guidance in the docs teaches the protocol.

### Group H: Plain-Text Renderer

- **H1.** `PlainTextRenderer().render(document) -> str` produces a formatted monospace screenplay: scene headings uppercase and flush left, action wrapped flush left, character cues indented deepest, parentheticals and dialogue in the conventional narrower columns, transitions right-aligned, page breaks as a divider line, one blank line between blocks.
  Column positions are constructor parameters with screenplay-convention defaults (working defaults: total width 60, dialogue indent 10, parenthetical indent 15, cue indent 22; the plan may tune them against real scripts).
  Writer tools (NOTE, SECTION, SYNOPSIS, BONEYARD) are omitted, matching the HTML contract.
  Acceptance: relative-position assertions hold (cue indent > parenthetical indent > dialogue indent > action at 0); wrapped lines never exceed the width; transitions end at the right edge; writer tools never appear; `PlainTextRenderer` satisfies `TextRenderer`.

### Group I: Command-Line Interface

- **I1.** A console script (name per Open Question 13) built on argparse with zero new runtime dependencies.
  `<cli> validate <file>` prints each `ValidationIssue` as `line:severity:code:message` and exits 1 when any error-severity issue exists, 0 otherwise.
  `<cli> render <file> --format {html,text,fountain,json,fdx,pdf} [-o OUT]` writes to stdout or OUT; `html` means `render_page` output; `-` as the file reads stdin.
  Requesting `pdf` without the `[pdf]` extra exits with a clear error naming the install command.
  Acceptance: a `[project.scripts]` entry exists; subprocess tests cover both subcommands, both exit codes, stdin input, and the missing-extra message.

### Group J: FDX Export

- **J1.** `FDXRenderer().render(document) -> str` emits Final Draft interchange XML using only the standard library.
  Core mapping: SCENE_HEADING, ACTION, CHARACTER, PARENTHETICAL, DIALOGUE, and TRANSITION map to FDX `<Paragraph Type="...">` elements; the title page maps to the FDX title-page structure; CENTERED and LYRICS map to the nearest FDX equivalent with alignment preserved where FDX supports it.
  Dual dialogue is emitted as the two character blocks in FDX's dual-dialogue encoding; the exact attribute form is resolved against FDX fixtures during implementation and pinned by tests.
  Writer tools follow Open Question 16's ruling.
  Acceptance: output parses with `xml.etree.ElementTree`; a fixture screenplay produces a pinned FDX document; the mapping is covered per element type; `FDXRenderer` satisfies `TextRenderer`.

### Group K: PDF Export (optional extra)

- **K1.** Page geometry is a first-class parameter: presets `LETTER` (8.5 x 11 in), `A4` (210 x 297 mm), and `HALF_LETTER` (5.5 x 8.5 in, the acting-edition booklet size), plus custom dimensions and margins, with a binding-offset option for bound editions.
  Acceptance: generated PDFs report the preset's page dimensions (read back from the media box in tests); margins and binding offset shift the text block measurably.
- **K2.** Layout is a data-driven profile, not hardcoded: the default `SCREENPLAY` profile is Courier 12 with the conventional per-element indents, stored as a profile dataclass the renderer consumes.
  Geometry and profile are orthogonal, so an acting-edition layout profile later (Open Question 15) is an addition, not a rewrite.
  Acceptance: the profile object carries per-element indent, width, and font values; the renderer reads only profile data; text extracts from the PDF in element order.
- **K3.** PDF ships as the optional extra `fountain-py[pdf]`; the core stays zero-dependency (dependency choice per Open Question 14).
  Importing the PDF renderer without the extra raises a helpful error naming the install command.
  Acceptance: the base install adds no dependencies; installing the extra enables the renderer; CI gains a job that installs the extra and runs the PDF tests, and the base-install job proves the core works without it.
- **Non-goal (pinned).** Booklet imposition (reordering pages into printer signatures for folding) stays out of scope; `HALF_LETTER` output is the enabling piece, and imposition belongs to print tooling.

### Group L: Documentation and Truth-Up

- **L1.** Each new mode gets a how-to in the existing Diataxis tree: CLI usage, plain-text export, FDX export, and PDF export (geometry and profiles), plus the JSON schema reference (F2) and `from_json` folded into the export how-to.
  Acceptance: the pages exist, sit in the toctree, pass Vale with zero errors, and every code claim is verified against the implementation.
- **L2.** README, docs landing page, and CHANGELOG updated for 0.2.0, with no hand-counted metrics reintroduced.
  Acceptance: the feature lists name the new modes; `sphinx-build` and the doctest suite stay green.

### 0.2.0 Release Mechanics (Human-Gated)

Same shape as 0.1.0, documented in `docs/source/contributing/releasing.rst`: bump the pyproject version to 0.2.0, merge the feature branch to `main` (Mason merges), tag `v0.2.0`, cut the GitHub Release, and the existing workflows publish to PyPI and redeploy the docs.

## Out of Scope and Scoped Futures

The mkdocs-fountain plugin remains fully out of scope; it imposes no requirements here beyond the renderer's fragment/CSS split, which was designed for that embedding use case.

Ruling (2026-07-03): PDF, JSON-schema, and XML output modes were scoped here as post-0.1.0 phases.
Ruling (2026-08-15): all three are promoted into 0.2.0; their spec pass is the "0.2.0: Output Modes and Interchange" section above, with XML sharpened to FDX (Final Draft interchange), the XML dialect that industry tools actually consume.

Considered and rejected for 0.2.0, recorded so the reasoning survives:

- **Generic XML.** No identified audience; every known consumer of screenplay XML speaks FDX, which Group J covers.
- **AsciiDoc.** Screenwriters do not use it, and docs toolchains embedding a screenplay are already served by the HTML fragment plus `get_css()`; anyone who wants it can build it against the Group G renderer protocol.

## Open Questions

Findings where documented behavior disagreed with actual behavior, plus decisions only Mason could make.
Mason ruled on these in the 2026-07-03 review; each ruling is recorded inline, and Question 12 is new from that review.

1. **Version number: 0.1.0 or 0.2.0?** pyproject.toml:3 and todo.md step 2 say 0.1.0; plan.md says 0.2.0 everywhere (target version, changelog section, tag, wheel names).
   The dist/ folder currently holds 0.1.0 artifacts.
   Ruling (2026-07-03): stay at 0.1.0; update plan.md to match.
2. **README claims "Full Fountain Spec Compliance" (README.md:13)** while the verified audit confirms 34 gaps.
   Either the claim softens ("parses all Fountain element types") or it waits until the requirements above are closed.
   The same claim appears in CHANGELOG.md:14.
   Ruling (2026-07-03): the claim stands, because 0.1.0 does not ship until it is true; full compliance before release, no waivers.
3. **Renderer docstring says notes and synopses are "hidden by default" (src/fountain/renderer.py:247, 250)** but `DEFAULT_CSS` styles both visibly (src/fountain/renderer.py:128-132, 145-149).
   docs/source/user-guide/rendering.rst:167 makes the boneyard "hidden by default" claim, which is true only in `render_page()` mode since fragments carry no CSS (audit E11 and E5).
   Ruling (2026-07-03): the Fountain spec decides.
   The spec says notes, sections, synopses, and boneyard are tools for the writer and are omitted from formatted output, so all four are hidden by default; make `DEFAULT_CSS`, the fragment-mode docs, and the docstrings agree (E5 and E11 cover the mechanics).
4. **`FountainElement.text` is documented as "Clean text content with Fountain markup removed" (src/fountain/elements.py:146, 153)** but emphasis delimiters remain in the text (audit D4) and BONEYARD/NOTE elements keep their delimiters verbatim.
   Fixing D4 resolves the emphasis half; the docstring still needs to state what BONEYARD and NOTE carry.
   Ruling (2026-07-03): fix it; land D4, then rewrite the docstring so it is accurate about BONEYARD and NOTE contents.
5. **FountainRenderer round-trip claims** (README.md; docstring at src/fountain/renderer.py) — resolved. Blank lines survive (A4), dual dialogue survives (A4b), and inline emphasis is re-emitted from the recorded spans (`_apply_formatting_removal`), including nesting and escaped literals. The round-trip docs now state the remaining normalization (multiple blank lines collapse to one) precisely.
6. **CHANGELOG.md claims "Tab-to-spaces conversion verified in HTML output"** but tabs survive in element text and are converted to `&nbsp;` only at render time, and space indentation collapses in browsers (audit A5/D10).
   Reword after the A5 fix or before publishing the changelog.
   Ruling (2026-07-03): just update the changelog; nothing has shipped yet.
7. **`HTMLRenderer` and `FountainRenderer` are absent from the top-level `__all__`** (src/fountain/__init__.py:14-21) while README.md:32 and the quickstart treat them as primary API via `from fountain.renderer import ...`.
   Decide whether to promote them to `fountain.__all__` before 0.1.0, since adding them later is easy but users will cargo-cult whatever the first README shows.
   Ruling (2026-07-03): promote them; the library re-export pattern is the accepted exception to the empty-`__init__` rule, and the file stays logic-free (see Package Exports).
8. **Validation API.** The June 2026 audit (origin/main audit.md, commit 1b71ea2) carried a P4 item to implement `FountainParser.validate() -> list[ValidationError]` because the then-current plan.md promised it.
   That plan.md is gone and no code or doc promises validation today.
   Ruling (2026-07-03): wanted for 0.1.0; specced above as the Validation API section under the Public API Contract.
9. **Python 3.9 support.** Python 3.9 reached end of life in October 2025, yet it is the declared floor (pyproject.toml:9) and the mypy/ruff target.
   Keeping it costs `Optional`/`Union` syntax throughout; dropping to 3.10 would allow `X | None` per the python skill's standards.
   Ruling (2026-07-03): drop to 3.10 and modernize the code; support runs through 3.14 with 3.15 added on release (see Supported Python Versions).
10. **`author` versus `authors` on the title page.** With both keys present, `HTMLRenderer` renders only `author` (src/fountain/renderer.py:403-404) while `FountainRenderer` emits both, so the two renderers disagree about the same document (verified by probe).
   Ruling (2026-07-03): render all authors.
   Both renderers emit both keys; `HTMLRenderer` renders `author` and `authors` each as its own author paragraph.
   Acceptance: a title page carrying both keys produces both values in HTML and in Fountain output, and the two renderers agree on the same document.
11. **`just test` runs the mutating `just fix`.** The quality gate's recipe order is `unit-test-cov doctest lint type-check fix check`, so running the gate can rewrite source files via `ruff check --fix` before the format check.
   Keep the auto-fix inside the gate or split it out so `just test` is read-only?
   Ruling (2026-07-03): keep the auto-fix inside the gate.
12. **Parser pipeline architecture: pre- versus post-processing.** Dual dialogue pairing is a hard-coded post-pass today (see Dual Dialogue Post-Processing).
   Mason's planned expanded-markdown library composes parsers with pre- and post-processor stages, and fountain-py should fit that model.
   Open: which transforms belong before line classification and which after, and whether the parser should expose formal pipeline stages.
   Needs a design pass against that library's processor model before any refactor; raised in the 2026-07-03 review.
13. **CLI executable name (0.2.0).** `fountain` is short and memorable but generic; alternatives are `fountainpy` or `fountain-py`.
   Ruling (2026-08-15, accepted in review): `fountain`, falling back to `fountain-py` if collisions with other tooling are a concern.
14. **PDF dependency (0.2.0).** Candidates: `fpdf2` (pure Python, light, no system libraries), `reportlab` (mature, heavier), `weasyprint` (HTML-to-PDF, needs system libraries, a poor fit for an optional extra).
   Ruling (2026-08-15, accepted in review): `fpdf2` for the `[pdf]` extra; revisit only if its Courier metrics or Unicode handling fall short.
15. **Stage-play layout profile (0.2.0 or later).** `HALF_LETTER` geometry ships in 0.2.0 either way; the question is whether a `STAGE_PLAY` element-layout profile (acting-edition conventions) ships now or waits.
   Ruling (2026-08-15, accepted in review): geometry now, `STAGE_PLAY` profile deferred until the profile system proves itself on `SCREENPLAY`.
16. **FDX mapping for writer tools (0.2.0).** NOTE, SECTION, SYNOPSIS, and BONEYARD are omitted from HTML by the 2026-07-03 ruling; FDX has a ScriptNote concept that could carry notes.
   Ruling (2026-08-15, accepted in review): omit all four in 0.2.0 for consistency with the HTML contract; a note-to-ScriptNote mapping can land later without breaking anything.

### Reconciliation of origin/main audit.md (commit 1b71ea2)

For the record, the June 2026 remediation plan's items against today's code: P1 directory flattening is done (package lives at `src/fountain/` from the repo root).
P2 CI is done (`.github/workflows/ci.yml`, 3.9 through 3.13); its pre-commit sub-item is superseded (pre-commit is no longer a dev dependency and no config exists, though dangling recipes remain; see CR-3).
P3 README and docs are done (Sphinx/furo instead of the mkdocs stack the audit referenced; the dangling mkdocs references it flagged are gone).
P4 validation is superseded pending Mason's ruling (Open Question 8); P4 spec-completeness verification was executed as the compliance audit and its output is the Spec Compliance Requirements section above.
P5 roadmap items (mkdocs plugin, PDF export) are out of scope; P5 PyPI publication is this spec's Path to PyPI.
