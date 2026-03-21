# Fountain Spec Compliance — TODO

## Step 1: Section Level Metadata
- [x] 1. RED: Write tests for section level metadata in `TestSpecCompliance`
- [x] 2. GREEN: Update parser section handling to store level in metadata
- [x] 3. REFACTOR: None needed
- [x] 4. Verify: Run `just test`

## Step 2: Ellipsis Protection on Forced Scene Headings
- [ ] 1. RED: Write tests for ellipsis protection in `TestSpecCompliance`
- [ ] 2. GREEN: Update `FORCED_SCENE_HEADING_PATTERN` regex
- [ ] 3. REFACTOR: None needed
- [ ] 4. Verify: Run `just test`

## Step 3: Tab Conversion Verification
- [ ] 1. RED: Write verification tests in `TestSpecCompliance` and `TestHTMLRenderer`
- [ ] 2. GREEN: Confirm tests pass without code changes (fix if needed)
- [ ] 3. Verify: Run `just test`

## Step 4: Arbitrary Title Page Keys
- [ ] 1. RED: Write tests for arbitrary title page keys in `TestSpecCompliance`
- [ ] 2. GREEN: Update `_parse_title_page()` to accept any key
- [ ] 3. RED: Write renderer tests for custom fields in `TestHTMLRenderer` and `TestFountainRenderer`
- [ ] 4. GREEN: Update renderers to display unknown fields
- [ ] 5. REFACTOR: None needed
- [ ] 6. Verify: Run `just test`

## Step 5: Scene Headings Require Blank Line Before
- [ ] 1. RED: Write tests for blank line requirement in `TestSpecCompliance`
- [ ] 2. GREEN: Add blank line guard to natural scene heading detection
- [ ] 3. RED: Run existing tests to check for regressions
- [ ] 4. GREEN: Fix any broken existing tests
- [ ] 5. Verify: Run `just test`

## Step 6: Character Names Require Blank Line Before
- [ ] 1. RED: Write tests for character blank line requirement in `TestSpecCompliance`
- [ ] 2. GREEN: Add blank line guards to character detection (dual, extension, regular)
- [ ] 3. RED: Run existing tests to find regressions
- [ ] 4. GREEN: Fix any broken tests
- [ ] 5. Verify: Run `just test`

## Step 7: Transitions Require Blank Lines Before and After
- [ ] 1. RED: Write tests for transition blank line requirements in `TestSpecCompliance`
- [ ] 2. GREEN: Add `_is_blank_line_after()` method and blank line guards
- [ ] 3. RED: Run existing tests for regressions
- [ ] 4. GREEN: Fix any broken tests
- [ ] 5. Verify: Run `just test`

## Step 8: Inline Notes Stripped from Elements
- [ ] 1. RED: Write tests for inline note stripping in `TestSpecCompliance`
- [ ] 2. GREEN: Add `NOTE_PATTERN.sub()` stripping after standalone note check
- [ ] 3. REFACTOR: Decide on metadata storage for stripped notes
- [ ] 4. Verify: Run `just test`

## Step 9: Multi-line Notes
- [ ] 1. RED: Write tests for multi-line notes in `TestSpecCompliance`
- [ ] 2. GREEN: Add `in_note` / `note_buffer` state tracking to parser
- [ ] 3. REFACTOR: Ensure ordering with inline note stripping from Step 8
- [ ] 4. Verify: Run `just test`

## Step 10: Dialogue Continuation with Whitespace-Only Lines
- [ ] 1. RED: Write tests for whitespace continuation in `TestSpecCompliance`
- [ ] 2. GREEN: Update parse loop to detect whitespace-only lines in dialogue context
- [ ] 3. REFACTOR: None needed
- [ ] 4. Verify: Run `just test`

## Step 11: Backslash Escaping for Emphasis
- [ ] 1. RED: Write tests for backslash escaping in `TestSpecCompliance`
- [ ] 2. GREEN: Implement `_process_escapes()` method and integrate with `_parse_line()`
- [ ] 3. REFACTOR: Handle `\\` for literal backslash
- [ ] 4. Verify: Run `just test`
