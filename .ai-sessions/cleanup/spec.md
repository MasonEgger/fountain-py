# Fountain Spec Compliance Plan

## Context

The fountain-py library parses Fountain screenplay markup but has 11 gaps vs the [official spec](https://fountain.io/syntax/). This plan brings it to full compliance using strict TDD — write failing tests first, then minimal code to pass, then run `just test` for quality checks.

After analysis, Gap 11 (tab conversion) is likely already handled by the renderer — Step 3 confirms this. The remaining 10 gaps need real fixes.

**Key files:**
- `src/fountain/parser.py` — Two-pass parser with regex patterns, `_parse_line()`, `_extract_formatting()`
- `src/fountain/renderer.py` — HTMLRenderer and FountainRenderer
- `src/fountain/elements.py` — ElementType enum, FountainElement dataclass, FormatSpan
- `src/fountain/document.py` — FountainDocument container
- `tests/test_edge_cases.py` — Spec compliance tests (add new class `TestSpecCompliance`)
- `tests/test_parser.py` — Core parser tests (may need updates for blank-line changes)

**Existing patterns to reuse:**
- Boneyard multi-line state tracking (`self.in_boneyard` flag in parser.py) — reuse for multi-line notes
- `had_blank_line_before` parameter already passed to `_parse_line()` — reuse for context checks
- `_is_dialogue_following()` lookahead pattern — reuse for transition blank-line-after check
- `NOTE_PATTERN` regex — reuse for inline note stripping

---

## Step 1: Section Level Metadata

**NOTE**: The FountainRenderer already reads `metadata.get("level", 1)` for sections. The parser just doesn't populate it. Simplest change with zero risk.

```text
Implement section level metadata storage in the Fountain parser. The spec defines # as level 1, ## as level 2, ### as level 3, etc. The parser currently strips # characters but doesn't record the nesting level.

1. RED: Write tests for section level metadata:
   - Add class `TestSpecCompliance` to `tests/test_edge_cases.py`:
     - Test that `# Act One` produces a SECTION element with `metadata["level"] == 1`
     - Test that `## Scene One` produces a SECTION element with `metadata["level"] == 2`
     - Test that `### Beat One` produces a SECTION element with `metadata["level"] == 3`
     - Test that `###### Deep Nesting` produces `metadata["level"] == 6`
     - Test that section text content is correct (no # symbols in text)

2. GREEN: Update the parser to store section levels:
   - Modify `src/fountain/parser.py` in the section handling block (around line 600):
     - Count the number of leading `#` characters before stripping
     - Add `metadata={"level": level}` to the FountainElement constructor

3. REFACTOR: None needed — this is a minimal change.

4. Verify: Run `just test` to confirm all tests pass including existing section tests in `test_parser.py::test_section_parsing`.
```

---

## Step 2: Ellipsis Protection on Forced Scene Headings

**NOTE**: Current regex `r"^\."` matches ANY leading period. The spec says only a period followed by an alphanumeric character forces a scene heading — `...text` must NOT trigger it. The existing test `(".CUSTOM SCENE HEADING", True)` must continue to pass since `.C` is period + alpha.

```text
Fix the forced scene heading regex to prevent ellipses from triggering false scene headings. Per the Fountain spec, only a single period followed by an alphanumeric character forces a scene heading.

1. RED: Write tests for ellipsis protection:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `...HELLO` is parsed as ACTION, not SCENE_HEADING
     - Test that `..text` is parsed as ACTION, not SCENE_HEADING
     - Test that `...where the carnival is parked` is ACTION (spec example)
     - Test that `.SNIPER SCOPE POV` IS a forced SCENE_HEADING (spec example)
     - Test that `.A forced heading` IS a forced SCENE_HEADING
     - Test that `.2nd Floor` IS a forced SCENE_HEADING (period + digit)

2. GREEN: Update the forced scene heading regex:
   - Modify `src/fountain/parser.py` line 83:
     - Change `FORCED_SCENE_HEADING_PATTERN = re.compile(r"^\.")` to
       `FORCED_SCENE_HEADING_PATTERN = re.compile(r"^\.(?!\.)(?=[A-Za-z0-9])")`
     - This uses negative lookahead `(?!\.)` to reject `..` and positive lookahead `(?=[A-Za-z0-9])` to require alphanumeric after the period

3. REFACTOR: None needed.

4. Verify: Run `just test`. Confirm existing test `(".CUSTOM SCENE HEADING", True)` in `test_scene_heading_variations` still passes.
```

---

## Step 3: Tab Conversion Verification

**NOTE**: The parser preserves tabs in action text (`original_line.rstrip()` at line 776). The HTMLRenderer converts tabs to `&nbsp;` sequences. This step confirms compliance without code changes.

```text
Verify that tab-to-four-spaces conversion is already handled correctly by the existing parser and renderer. The spec says tabs in Action elements convert to four spaces in formatted output.

1. RED: Write verification tests:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that parsing `\tIndented action` preserves the tab character in element text
     - Test that parsing `\t\tDouble indented` preserves both tabs
     - Test that tabs in action are preserved while tabs in other elements (character names, transitions) are stripped by `.strip()`
   - Add to `TestHTMLRenderer` in `tests/test_renderer.py`:
     - Test that rendering action with `\t` produces four `&nbsp;` characters in HTML output
     - Test that rendering action with `\t\t` produces eight `&nbsp;` characters

2. GREEN: These tests should pass WITHOUT any code changes. If any fail, investigate and fix.

3. Verify: Run `just test`.
```

---

## Step 4: Arbitrary Title Page Keys

**NOTE**: The parser uses a `supported_fields` whitelist (line 392-410) and rejects unknown keys as end-of-title-page. The spec says ANY key ending with a colon is valid. The renderers have hardcoded field lists for display — need fallback for unknown fields.

```text
Update the title page parser to accept arbitrary key-value pairs, not just a fixed whitelist. The Fountain spec allows any key ending with a colon on the title page. Also update renderers to display unknown fields.

1. RED: Write tests for arbitrary title page keys:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `Custom Field: Custom Value` in title page is stored in metadata as `metadata["custom field"] == "Custom Value"`
     - Test that `Revision: Draft 3` is accepted as a title page key
     - Test that multiple arbitrary keys are all preserved
     - Test that arbitrary keys with multi-line values work (continuation lines)
     - Test that title page still ends correctly at blank line + body element
     - Test that standard keys (Title, Author) still work alongside custom keys

2. GREEN: Update the parser title page logic:
   - Modify `src/fountain/parser.py` in `_parse_title_page()`:
     - Remove the `if key in supported_fields:` / `else: break` branching (lines 446-457)
     - Accept any key-value pair where the key portion doesn't look like a body element
     - Keep the `supported_fields` set as a comment for documentation, or remove entirely
     - Maintain existing end-of-title-page heuristics (blank line followed by scene heading, etc.)

3. RED: Write renderer tests for custom field display:
   - Add to `TestHTMLRenderer` in `tests/test_renderer.py`:
     - Test that custom metadata fields appear in HTML output
   - Add to `TestFountainRenderer` in `tests/test_renderer.py`:
     - Test that custom metadata fields appear in Fountain round-trip output

4. GREEN: Update renderers:
   - Modify `src/fountain/renderer.py`:
     - In `HTMLRenderer._render_title_page()`: After known field rendering, loop through remaining metadata keys and render them with a generic `<p class="custom-field">` wrapper
     - In `FountainRenderer._render_title_page()`: After known fields, append remaining custom fields in `Key: Value` format

5. REFACTOR: None needed.

6. Verify: Run `just test`. Confirm existing title page tests in `test_parser.py::test_enhanced_title_page` still pass.
```

---

## Step 5: Scene Headings Require Blank Line Before

**NOTE**: `had_blank_line_before` is already passed to `_parse_line()` but not checked for scene headings. Forced scene headings (`.PREFIX`) should be exempt — forced elements override context requirements. The `not self.elements` check handles the first-element-in-document case. Existing tests parse single-line inputs (first element), so they won't break.

```text
Add blank-line-before requirement for natural scene heading detection. The Fountain spec requires a blank line before scene headings. Forced scene headings (period prefix) are exempt.

1. RED: Write tests for blank line requirement:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `"Some action.\n\nINT. HOUSE - DAY"` correctly identifies SCENE_HEADING (blank line present)
     - Test that `"Some action.\nINT. HOUSE - DAY"` does NOT produce a SCENE_HEADING (no blank line) — should be ACTION instead
     - Test that `"INT. HOUSE - DAY"` as first/only element is still SCENE_HEADING (first element exception)
     - Test that `"Some action.\n.FORCED HEADING"` still produces SCENE_HEADING even without blank line (forced elements exempt)
     - Test that `"Title: Test\n\nINT. HOUSE - DAY"` works after title page (first body element)

2. GREEN: Add blank line guard to scene heading detection:
   - Modify `src/fountain/parser.py` in `_parse_line()` around line 669:
     - Wrap the natural scene heading block with `if had_blank_line_before or not self.elements:`
     - Do NOT add this guard to the forced scene heading block (line 632) — forced elements are exempt
     - If the guard fails, the line falls through to ACTION (default)

3. RED: Run existing tests to check for regressions:
   - Run `uv run pytest tests/test_edge_cases.py::TestSceneHeadingEdgeCases -v`
   - Run `uv run pytest tests/test_parser.py -v`
   - If any existing tests break because they lack blank lines, fix those tests to include proper blank lines (this aligns them with the spec)

4. GREEN: Fix any broken existing tests by adding blank lines where needed.

5. Verify: Run `just test`.
```

---

## Step 6: Character Names Require Blank Line Before

**NOTE**: Same pattern as Step 5. Forced characters (`@PREFIX`) are exempt. The guard applies to: dual character (`^`), character with extension, and regular character checks. NOT to forced character.

```text
Add blank-line-before requirement for character name detection. The Fountain spec requires one empty line before a character cue. Forced characters (@prefix) are exempt.

1. RED: Write tests for character blank line requirement:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `"Some action.\n\nJOHN\nHello."` correctly identifies CHARACTER (blank line present)
     - Test that `"Some action.\nJOHN\nHello."` does NOT produce a CHARACTER (no blank line) — JOHN becomes ACTION
     - Test that `"JOHN\nHello."` as first element still produces CHARACTER
     - Test that `"Some action.\n@JOHN\nHello."` still produces CHARACTER even without blank line (forced character exempt)
     - Test that `"Some action.\n\nJOHN (V.O.)\nHello."` works with extensions and blank line
     - Test that `"Some action.\nJOHN (V.O.)\nHello."` without blank line does NOT produce CHARACTER

2. GREEN: Add blank line guards to character detection:
   - Modify `src/fountain/parser.py` in `_parse_line()`:
     - At the dual character check (line 707): wrap with `if had_blank_line_before or not self.elements:`
     - At the character with extension check (line 719): wrap with same guard
     - At the regular character check (line 737): wrap with same guard
     - Do NOT add to forced character check (line 695) — forced elements are exempt
     - When the guard fails, the line falls through to dialogue check or ACTION default

3. RED: Run existing tests to find regressions:
   - Run `uv run pytest tests/ -v`
   - If existing tests break, fix them to include blank lines where the spec requires them

4. GREEN: Fix any broken tests.

5. Verify: Run `just test`.
```

---

## Step 7: Transitions Require Blank Lines Before and After

**NOTE**: Transitions need both a blank line before AND after. This requires a new `_is_blank_line_after()` helper method, following the same pattern as `_is_dialogue_following()`. Forced transitions (`>PREFIX`) are exempt.

```text
Add blank-line-before and blank-line-after requirements for transition detection. The Fountain spec requires blank lines on both sides of transitions. Forced transitions (> prefix) are exempt.

1. RED: Write tests for transition blank line requirements:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `"Action.\n\nCUT TO:\n\nINT. HOUSE"` correctly identifies TRANSITION (both blank lines present)
     - Test that `"Action.\nCUT TO:\n\nINT. HOUSE"` does NOT produce a TRANSITION (no blank before)
     - Test that `"Action.\n\nCUT TO:\nINT. HOUSE"` does NOT produce a TRANSITION (no blank after)
     - Test that `"Action.\nCUT TO:\nINT. HOUSE"` does NOT produce a TRANSITION (no blanks at all)
     - Test that `"Action.\n>Burn to White.\nMore action."` still produces TRANSITION (forced, exempt)
     - Test that `"CUT TO:"` at end of document is TRANSITION (EOF counts as blank after)
     - Test that `"FADE IN:"` and `"FADE OUT."` follow the same rules

2. GREEN: Add blank line guards and lookahead:
   - Add new method `_is_blank_line_after()` to `FountainParser` in `src/fountain/parser.py`:
     - Check if `self.current_line + 1` is beyond document length (EOF = True)
     - Check if the next line is empty after strip (blank = True)
     - Return bool
   - Modify `_parse_line()` at the transition check (line 686):
     - Wrap with `if (had_blank_line_before or not self.elements) and self._is_blank_line_after():`
     - Do NOT add to forced transition check (line 658) — forced elements are exempt

3. RED: Run existing tests for regressions.

4. GREEN: Fix any broken tests by adding blank lines around transitions.

5. Verify: Run `just test`.
```

---

## Step 8: Inline Notes Stripped from Elements

**NOTE**: Standalone notes (`[[full note]]` as entire line) must remain as NOTE elements. Inline notes within other text must be stripped. The existing `NOTE_PATTERN = re.compile(r"\[\[[^\]]*\]\]")` can be reused for stripping.

```text
Strip inline notes from element text while preserving standalone note elements. The Fountain spec says notes [[text]] within other content are removed from formatted output, but the surrounding text remains.

1. RED: Write tests for inline note stripping:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `"John walks [[needs work]] to the door."` produces ACTION with text containing "John walks  to the door." (note removed)
     - Test that inline note in dialogue is stripped: parse `"JOHN\nI love you [[or do I?]] forever."` and verify dialogue text has no note content but retains surrounding text
     - Test that `"[[This is entirely a note]]"` still produces a NOTE element (standalone note unchanged)
     - Test that multiple inline notes on one line are all stripped
     - Test that text is otherwise unchanged after note stripping

2. GREEN: Add inline note stripping to the parser:
   - Modify `src/fountain/parser.py` in `_parse_line()`, after the standalone note check (line 588):
     - Use `NOTE_PATTERN.sub("", line)` to strip inline notes from the line text
     - Re-strip whitespace after removal
     - If the line becomes empty after stripping, return None
     - Continue parsing with the stripped line for element type detection

3. REFACTOR: Consider whether stripped note content should be stored in element metadata for reference. Decide based on spec — the spec says notes "won't appear in formatted screenplay" so stripping is sufficient.

4. Verify: Run `just test`.
```

---

## Step 9: Multi-line Notes

**NOTE**: Reuse the same state-tracking pattern as boneyard (`self.in_boneyard` flag). Add `self.in_note` and `self.note_buffer` to accumulate lines between `[[` and `]]`. Must handle the case where `[[` starts mid-line (prefix text becomes action, note content accumulates).

```text
Add support for multi-line notes that span across line breaks. The Fountain spec says notes [[...]] can contain carriage returns. Implement using the same state-tracking pattern as boneyard comments.

1. RED: Write tests for multi-line notes:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `"[[This is a note\nthat spans\nmultiple lines]]"` produces a single NOTE element containing all three lines
     - Test multi-line note between elements: `"INT. HOUSE - DAY\n\n[[This note\nspans lines]]\n\nJOHN\nHello."` — verify NOTE exists AND surrounding elements are correct
     - Test that the NOTE element text contains the full multi-line content
     - Test note with two-space blank line inside: `"[[Note\n  \nmore note]]"` produces single NOTE (spec says two spaces connect the element)

2. GREEN: Add multi-line note state tracking:
   - Modify `src/fountain/parser.py`:
     - Add `self.in_note: bool = False` and `self.note_buffer: list[str] = []` to `__init__()`
     - Reset both in `parse()` alongside `self.in_boneyard`
     - In `_parse_line()`, after boneyard handling but before other checks:
       - If `self.in_note`: append line to buffer; if `]]` found in line, close note, join buffer, return NOTE element; otherwise return None
       - After standalone note check: if line contains `[[` but not `]]`, set `self.in_note = True`, start buffer with line, return None
     - Store the note start line number for the element

3. REFACTOR: Ensure multi-line note handling doesn't interfere with inline note stripping from Step 8. Multi-line note detection should come first (it's a state machine check), then inline stripping applies to non-note lines.

4. Verify: Run `just test`.
```

---

## Step 10: Dialogue Continuation with Whitespace-Only Lines

**NOTE**: The spec says a line with just spaces (e.g., two spaces) preserves a blank line within dialogue without breaking to action. The distinction: truly empty line `""` breaks dialogue; whitespace-only line `"  "` continues it. The raw line must be checked before `rstrip()`. After `text.split("\n")`, a whitespace-only line is `"  "` (non-empty string that is all spaces), while a truly empty line is `""`.

```text
Support dialogue continuation across whitespace-only lines. The Fountain spec says a line containing only spaces within dialogue preserves a blank line without breaking to action. A truly empty line still breaks dialogue.

1. RED: Write tests for dialogue whitespace continuation:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `"JOHN\nFirst line.\n  \nSecond line."` produces CHARACTER + three DIALOGUE elements (no ACTION) — the two-space line continues dialogue
     - Test that `"JOHN\nFirst line.\n\nSecond line."` DOES break dialogue — produces CHARACTER + DIALOGUE + ACTION (truly empty line breaks)
     - Test that whitespace continuation works after parenthetical: `"JOHN\n(beat)\n  \nMore dialogue."` — all dialogue/parenthetical, no action
     - Test with spec example: dealer dialogue with two-space blank line between lines

2. GREEN: Update the main parse loop:
   - Modify `src/fountain/parser.py` in `parse()`, around lines 304-311:
     - Before `line = self.lines[self.current_line].rstrip()`, save the raw line
     - After rstrip, when `not line` (empty after strip):
       - Check if the raw line was whitespace-only (non-empty but all spaces): `raw_line and raw_line != raw_line.lstrip()`
       - AND previous element is dialogue context: `self.elements and self.elements[-1].type in (ElementType.DIALOGUE, ElementType.PARENTHETICAL, ElementType.CHARACTER)`
       - If both true: append an empty DIALOGUE element and continue WITHOUT setting `previous_line_was_blank = True`
       - Otherwise: proceed with existing blank line logic

3. REFACTOR: None needed.

4. Verify: Run `just test`. Pay special attention to existing dialogue continuation tests in `test_parser.py`.
```

---

## Step 11: Backslash Escaping for Emphasis

**NOTE**: Most complex change. The spec says `\*` produces a literal asterisk and `\_` a literal underscore. The parser must handle escapes before applying formatting regex. Strategy: replace escaped chars with placeholders before formatting extraction, then restore in display text.

```text
Implement backslash escaping for emphasis markers. The Fountain spec says backslash escapes emphasis characters: \* produces literal *, \_ produces literal _. Must work both standalone and within formatted text (e.g., **\*9765\*** renders literal asterisks inside bold).

1. RED: Write tests for backslash escaping:
   - Add to `TestSpecCompliance` in `tests/test_edge_cases.py`:
     - Test that `"He dialed \*69"` has no formatting spans and text contains literal `*69`
     - Test that `"Steel enters: **\*9765\***"` has bold formatting AND text contains literal asterisks `*9765*` within the bold span
     - Test that `"\_not underlined\_"` has no underline formatting and text contains literal `_`
     - Test that `"This is *italic* and \*not italic\*"` has exactly one italic span (the first) and literal asterisks for the escaped pair
     - Test that text without backslashes is unchanged (no regression)
     - Test that `\\` (escaped backslash) doesn't interfere with emphasis

2. GREEN: Implement escape processing:
   - Add new method `_process_escapes(self, text: str) -> tuple[str, str]` to `FountainParser` in `src/fountain/parser.py`:
     - `display_text`: Replace `\*` with `*` and `\_` with `_` (for element text storage)
     - `formatting_text`: Replace `\*` and `\_` with placeholder characters (e.g., `\x00`, `\x01`) that won't trigger formatting regex
     - Return `(display_text, formatting_text)`
   - Modify `_parse_line()`:
     - Before calling `_extract_formatting(text)`, call `_process_escapes(text)`
     - Pass `formatting_text` to `_extract_formatting()` for span detection
     - Use `display_text` as the element's text content
     - Adjust FormatSpan positions: each `\*` removal shifts positions by -1. Build an offset map from escape positions to correctly map formatting_text spans back to display_text positions.

3. REFACTOR: Consider whether `_process_escapes` should also handle `\\` (literal backslash). The spec mentions backslash as escape character but only shows `\*` examples. Handle `\\` → `\` for completeness.

4. Verify: Run `just test`. Confirm all formatting tests in `test_edge_cases.py::TestFormattingEdgeCases` still pass.
```

---

## Implementation Guidelines

- **TDD strictly**: Write failing tests first, then minimal code. No speculative code.
- **One step at a time**: Complete each step before moving to the next. Run `just test` after each.
- **Don't break existing tests**: If a step causes regressions, fix the tests to align with the spec (the spec is authoritative).
- **Forced elements are exempt**: Forced prefixes (`.`, `!`, `@`, `>`) override context requirements like blank-line-before. Never add context guards to forced element detection.
- **Match existing style**: Dataclasses, type hints, docstrings, 120-char lines, ruff formatting.
- **All new tests go in `TestSpecCompliance`** class in `tests/test_edge_cases.py` unless they are renderer-specific (those go in existing renderer test classes).

## Success Metrics

- All 11 gaps have passing tests confirming spec compliance
- Zero regressions in existing test suite
- `just test` passes (pytest + ruff lint + ruff format + mypy strict)
- `just unit-test-cov` shows maintained or improved coverage
- Parser correctly handles all spec examples from https://fountain.io/syntax/
