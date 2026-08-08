# Fountain Spec Compliance — TODO

## Step 1: Section Level Metadata
- [x] 1. RED: Write tests for section level metadata in `TestSpecCompliance`
- [x] 2. GREEN: Update parser section handling to store level in metadata
- [x] 3. REFACTOR: None needed
- [x] 4. Verify: Run `just test`

## Step 2: Ellipsis Protection on Forced Scene Headings
- [x] 1. RED: Write tests for ellipsis protection in `TestSpecCompliance`
- [x] 2. GREEN: Update `FORCED_SCENE_HEADING_PATTERN` regex
- [x] 3. REFACTOR: None needed
- [x] 4. Verify: Run `just test`

## Step 3: Tab Conversion Verification
- [x] 1. RED: Write verification tests in `TestSpecCompliance` and `TestHTMLRenderer`
- [x] 2. GREEN: Confirm tests pass without code changes (fix if needed)
- [x] 3. Verify: Run `just test`

## Step 4: Arbitrary Title Page Keys
- [x] 1. RED: Write tests for arbitrary title page keys in `TestSpecCompliance`
- [x] 2. GREEN: Update `_parse_title_page()` to accept any key
- [x] 3. RED: Write renderer tests for custom fields in `TestHTMLRenderer` and `TestFountainRenderer`
- [x] 4. GREEN: Update renderers to display unknown fields
- [x] 5. REFACTOR: None needed
- [x] 6. Verify: Run `just test`

## Step 5: Scene Headings Require Blank Line Before
- [x] 1. RED: Write tests for blank line requirement in `TestSpecCompliance`
- [x] 2. GREEN: Add blank line guard to natural scene heading detection
- [x] 3. RED: Run existing tests to check for regressions (0 regressions)
- [x] 4. GREEN: Fix any broken existing tests (none needed)
- [x] 5. Verify: Run `just test`

## Step 6: Character Names Require Blank Line Before
- [x] 1. RED: Write tests for character blank line requirement in `TestSpecCompliance`
- [x] 2. GREEN: Add blank line guards to character detection (dual, extension, regular)
- [x] 3. RED: Run existing tests to find regressions (0 regressions)
- [x] 4. GREEN: Fix any broken tests (none needed)
- [x] 5. Verify: Run `just test`

## Step 7: Transitions Require Blank Lines Before and After
- [x] 1. RED: Write tests for transition blank line requirements in `TestSpecCompliance`
- [x] 2. GREEN: Add `_is_blank_line_after()` method and blank line guards
- [x] 3. RED: Run existing tests for regressions (0 regressions in unit tests; 1 doctest fixed)
- [x] 4. GREEN: Fix any broken tests (rendering.rst round-trip doctest simplified)
- [x] 5. Verify: Run `just test`

## Step 8: Inline Notes Stripped from Elements
- [x] 1. RED: Write tests for inline note stripping in `TestSpecCompliance`
- [x] 2. GREEN: Add `NOTE_PATTERN.sub()` stripping after standalone note check
- [x] 3. REFACTOR: Not storing stripped notes in metadata (spec says they don't appear in output)
- [x] 4. Verify: Run `just test`

## Step 9: Multi-line Notes
- [x] 1. RED: Write tests for multi-line notes in `TestSpecCompliance`
- [x] 2. GREEN: Add `in_note` / `note_buffer` state tracking to parser
- [x] 3. REFACTOR: Ordering verified — multi-line detection before inline stripping
- [x] 4. Verify: Run `just test`

## Step 10: Dialogue Continuation with Whitespace-Only Lines
- [x] 1. RED: Write tests for whitespace continuation in `TestSpecCompliance`
- [x] 2. GREEN: Update parse loop to detect whitespace-only lines in dialogue context
- [x] 3. REFACTOR: Fixed test_quickstart_examples.py fixture with textwrap.dedent
- [x] 4. Verify: Run `just test`

## Step 11: Backslash Escaping for Emphasis
- [x] 1. RED: Write tests for backslash escaping in `TestSpecCompliance`
- [x] 2. GREEN: Implement `_process_escapes()`, `_strip_escapes()`, integrate with `_extract_formatting()`
- [x] 3. REFACTOR: `\\` → `\` handled in `_process_escapes` and `_strip_escapes`
- [x] 4. Verify: Run `just test`
