# Fountain Compliance Audit (Verified)

Date: 2026-07-02.
Scope: verification pass over the 39 listed candidate IDs from the step 1b sweep (`/home/mmegger/Code/.ai-sessions/step-01b-candidates.md`; its header says 38, the listed IDs count 39).
Every probe below was re-run fresh against this working tree with `uv run python`; probe scripts live in the session scratchpad under `verify-1c/`.
Every spec quote was checked against https://fountain.io/syntax/ (fetched 2026-07-02); curly quotes in quoted spec text are normalized to straight quotes.
Verdicts: 34 confirmed, 1 refuted, 4 classified as ambiguity or deliberate extension.

## Confirmed Gaps

### A1. Title Page Multi-Line Values Are Flattened (medium)

- Spec: "The indenting pattern allows multiple values for the same key (multiple authors, multiple address lines)."
- Probe: `Contact:` followed by three 4-space-indented address lines.
- Expected: three distinct values (or at least preserved line breaks) for `contact`.
- Observed: `'Next Level Productions 1588 Mission Dr. Solvang, CA 93463'`, joined with single spaces; no `<br>` in HTML because the renderer's multiline path (src/fountain/renderer.py:407-408) never sees a `\n`.
- Where: src/fountain/parser.py:463-467.

### A2. Title Page Indentation Is Never Inspected (medium)

- Spec: "Values can be inline with the key or they can be indented on a newline below the key ... Indenting is 3 or more spaces, or a tab."
- Probe: `Notes:` followed by indented `Draft 3: final revisions`; also an unindented plain line after `Title:`.
- Expected: indented lines are values of the current key regardless of colons; an unindented non-key line ends the title page.
- Observed: the indented colon line becomes a new key `draft 3` and `notes` stays empty; unindented lines (including `int. house - day`) are absorbed into the previous value.
- Where: src/fountain/parser.py:448 (key test ignores indentation), 463 (continuation accepts unindented lines).

### A4. Blank Lines Discarded; Fountain Round Trip Self-Corrupts (high)

- Spec: "Fountain takes every carriage return as intent" and "Any number of empty lines in the Fountain file will be passed faithfully through to the formatted output as empty Action lines."
- Probe: parse a script with single and double blank runs, render with `FountainRenderer`, re-parse.
- Expected: blank separators preserved; round trip stable.
- Observed: the parser drops all blank-line counts, the renderer joins every element with a single `\n` (zero blank lines), and re-parsing the output degrades CHARACTER plus DIALOGUE to ACTION.
- Where: src/fountain/parser.py:331-355 (blank handling), src/fountain/renderer.py:727 (`"\n".join`).

### A5. Tabs Not Converted; Action Indentation Collapses in HTML (medium)

- Spec: "Tabs and spaces are retained in Action elements, allowing writers to indent a line. Tabs are converted to four spaces."
- Probe: tab-indented and 10-space-indented action lines, rendered to HTML.
- Expected: element text carries four spaces for the tab; indentation visible in output.
- Observed: `element.text` keeps the literal `\t` (conversion happens only at HTML render time via `&nbsp;`), and space-indented lines emit raw spaces inside a `<div>` with no `white-space` CSS, so browsers collapse them.
- Where: src/fountain/parser.py:808-813; src/fountain/renderer.py:96-99 (`.fountain-action` CSS), 466-469.
- Shares a fix surface with D10.

### B1. Space-After-Prefix Scene Headings Not Recognized (high)

- Spec: "A line beginning with any of the following, followed by either a dot or a space, is considered a Scene Heading ... INT, EXT, EST, INT./EXT, INT/EXT, I/E."
- Probe: `INT HOUSE - DAY`, plus EXT, EST, I/E, and INT/EXT space forms.
- Expected: scene_heading for all.
- Observed: action for every space-after-prefix variant; only dot forms match (`INT./EXT HOUSE - DAY` works because it starts with `INT.`).
- Where: src/fountain/parser.py:70-73 (pattern requires a dot).
- Fix constraint verified: `INTERNAL AFFAIRS INVESTIGATES.` currently parses as action and must stay that way, so the fix needs a prefix boundary.

### B2. Scene Heading Accepted Without a Following Blank Line (medium)

- Spec: "A Scene Heading is any line that has a blank line following it, and either begins with INT or EXT or similar."
- Probe: `EXT. BRICK'S PATIO - DAY` immediately followed by `Some action here.`
- Expected: action (the blank-line-after criterion fails).
- Observed: scene_heading.
- Where: src/fountain/parser.py:702-717 (never calls `_is_blank_line_after`, unlike the transition branch at 720).

### B3. Title Page Guard for Scene Headings Is Case-Sensitive and Dot-Only (medium)

- Spec: scene heading prefixes are "Case insensitive" and take "either a dot or a space".
- Probe: first line `int. house - day - 3:00 pm`.
- Expected: scene_heading (the uppercase variant `INT. HOUSE - DAY - 3:00 PM` parses correctly, verified).
- Observed: consumed as title-page metadata `{'int. house - day - 3': '00 pm'}`.
- Where: src/fountain/parser.py:448 (`line.startswith(("INT.", "EXT.", "EST.", "I/E."))`).
- Linked to the A3 ambiguity below, but this half is a plain defect: the guard exists and misses spec-defined heading forms.

### B4. Scene Number Charset Wider Than Spec (low)

- Spec: "Scene numbers are any alphanumerics (plus dashes and periods), wrapped in #."
- Probe: `INT. HOUSE - DAY #$%^&#` and `#1 A#`.
- Expected: invalid charset stays in the heading text as typed.
- Observed: `$%^&` and `1 A` extracted as `scene_number` and removed from the heading text.
- Where: src/fountain/parser.py:78 (`[^#]+` accepts anything but `#`).

### C1. Punctuation in Uppercase Cues Rejected (high)

- Spec: "A Character element is any line entirely in uppercase, with one empty line before it and without an empty line after it."
- Probe: `MR. SMITH`, `O'BRIEN`, `JEAN-CLAUDE`, `DEALER #2`, each followed by a dialogue line.
- Expected: CHARACTER plus DIALOGUE (all four lines are entirely uppercase; period, apostrophe, hyphen, and hash are case-neutral).
- Observed: all four blocks parse as ACTION; plain `STEEL` control works.
- Where: src/fountain/parser.py:88 (`^[A-Z][A-Z0-9\s_]*$`); same charset propagates to :93 (dual) and :103 (extension).

### C2. Digit-First Cue Rejected (low)

- Spec: "Character names must include at least one alphabetical character. 'R2D2' works, but '23' does not."
- Probe: `23 SKIDOO` with dialogue.
- Expected: CHARACTER (it contains alphabetical characters; the spec imposes no letter-first rule).
- Observed: ACTION; `R2D2` works and bare `23` is correctly action.
- Where: src/fountain/parser.py:88 (pattern requires `[A-Z]` first).

### C3. Blank Line After Cue Does Not Disqualify It (medium)

- Spec: Character is a line "without an empty line after it."
- Probe: `JOHN` then a blank line then `He walks to the door.`
- Expected: both lines are ACTION.
- Observed: CHARACTER plus DIALOGUE; the lookahead skips blank lines. Same result with `@JOHN`.
- Where: src/fountain/parser.py:847-856 (`_is_dialogue_following` loops past blanks).

### C4. All-Caps Dialogue Line Demotes the Cue (low)

- Spec (Action section, on forcing with `!`): "This is helpful when Action is in uppercase and directly followed by another line of Action, preventing the two from being interpreted as Character and Dialogue elements."
- That sentence states the natural, unforced interpretation of an uppercase line plus follower is Character and Dialogue.
- Probe: `JOHN` then `I SAID NO`.
- Expected: CHARACTER plus DIALOGUE.
- Observed: both ACTION, because the lookahead treats the caps line as structural.
- Where: src/fountain/parser.py:852 (STRUCTURAL_PATTERNS includes CHARACTER_PATTERN).
- Note: some other implementations share this behavior; the spec text above still puts fountain-py on the wrong side of it.

### C5. Caret on a Forced Character Does Not Create Dual Dialogue (medium)

- Spec: "dual dialogue is expressed by adding a caret ^ after the second Character element ... All that matters is that the caret is the last character on the line."
- Probe: `BRICK` block then `@McClane ^` block.
- Expected: dual dialogue pair with the caret stripped.
- Observed: no dual element; the forced character's text is `'McClane ^'`. The natural `STEEL ^` control does pair correctly.
- Where: src/fountain/parser.py:98, 729-738.

### C6. @ Force Ignored When the Next Line Looks Structural (medium)

- Spec (1.1 changelog): "A Character element can by forced by preceding it by an 'at' symbol @."
- Probe: `@McClane` then `I SAID NO`.
- Expected: forced CHARACTER plus DIALOGUE.
- Observed: both ACTION, with the literal `@` left in the text.
- Where: src/fountain/parser.py:729-738 (force is gated on `_is_dialogue_following` with no fallthrough).

### C7. Forced Character Keeps Its Extension Inline (low)

- Spec: extensions are "the parenthetical notations that follow a character name on the same line"; for forced cues, "Fountain will remove the @ and interpret McCLANE as Character, preserving its mixed case."
- Probe: `@McClane (O.S.)` with dialogue.
- Expected: text `McClane` with extension metadata, matching the natural `MOM (O. S.)` control.
- Observed: text `'McClane (O.S.)'` and no extension metadata.
- Where: src/fountain/parser.py:729-738 versus 103.

### D1. Trailing Space After the Colon Fails to Defeat a Transition (low)

- Spec: "Add one or more spaces after the colon to cause the line to be interpreted as Action (since the line no longer ends with a colon)."
- Probe: `CUT TO: ` (trailing space).
- Expected: ACTION.
- Observed: TRANSITION; the line is rstripped before classification.
- Where: src/fountain/parser.py:331.

### D2. Transitions with Punctuation Not Recognized (low)

- Spec: transition requirements are "Uppercase", "Preceded by and followed by an empty line", "Ending in TO:".
- Probe: `SMASH-CUT TO:`.
- Expected: TRANSITION (the line is uppercase and ends in TO:).
- Observed: ACTION; `SMASH CUT TO:` control works.
- Where: src/fountain/parser.py:108 (`^[A-Z\s]+TO:$` allows no punctuation).

### D4. Emphasis Delimiters Ship in Formatted Output (high)

- Spec: "Fountain follows Markdown's rules for emphasis"; `**bold**` formats the word alone, and `FountainElement.text` is documented as "Clean text content with Fountain markup removed" (src/fountain/elements.py:153).
- Probe: `This is **bold** text.` rendered to HTML; same for italic and underline.
- Expected: `<strong>bold</strong>`.
- Observed: `<strong>**bold**</strong>`; the span covers the delimiters and they are never stripped from the text.
- Where: src/fountain/parser.py:1074-1101; src/fountain/renderer.py:556-567.

### D5. Spec Keypad Escape Example Mangled (medium)

- Spec: `Steel enters the code on the keypad: **\*9765\***` "turns into: Steel enters the code on the keypad: *9765*" in bold.
- Probe: the exact spec line.
- Expected: bold `*9765*`.
- Observed: `<strong>***9765*</strong>**`; the span is misaligned after escape adjustment.
- Where: src/fountain/parser.py:1104-1119, interacting with D4.

### D6. Nested Emphasis Duplicates Text (high)

- Spec: "the writer can mix and match and combine bold, italics and underlining", with the example `_Steel's face FILLS the *Leupold Mark 4* scope_.`
- Probe: the spec's Leupold line.
- Expected: an underlined phrase containing an italic span.
- Observed: `<u>_Steel's face FILLS the *Leupold Mark 4* scope_</u><em>*Leupold Mark 4*</em> scope_.`; the inner span is emitted twice and the tail is repeated.
- Where: src/fountain/renderer.py:529-553 (segment builder assumes non-overlapping spans); src/fountain/parser.py:1089-1101.

### D7. Bold and Underline Lack the Space Guards Italic Has (medium)

- Spec: "As with Markdown, the spaces around the emphasis characters are meaningful", with the `*69 ... *23` example producing no italics.
- Probe: `_ kilos_`, `** word**`, `some_variable_name`; italic control `He dialed *69 and then *23`.
- Expected: no spans for the underscore and bold cases (the opening delimiter is followed by a space); the italic control correctly produces none.
- Observed: underline and bold spans created for all three; snake_case also gets an underline span (that sub-case is Markdown-flavor dependent, but the space cases are unambiguous).
- Where: src/fountain/parser.py:191 (BOLD) and 203 (UNDERLINE) lack the guards ITALIC has at 198.

### D8. Formatting Offsets Wrong in Indented Action (medium)

- Spec: emphasis applies to the marked phrase; leading whitespace is retained in Action.
- Probe: ten spaces then `*Scott* --`.
- Expected: an italic span on `Scott`.
- Observed: span (0, 7) lands on the leading whitespace; HTML shows `<em>       </em>   *Scott* --`.
- Where: src/fountain/parser.py:808-812 (spans computed against the stripped line, text stored with indentation).

### D9. Forced Action Strips Its Indentation (low)

- Spec: "Tabs and spaces are retained in Action elements"; the `!` prefix only forces the element type.
- Probe: `!    INDENTED FORCED ACTION`.
- Expected: text keeps the four spaces after the `!` is removed.
- Observed: text is `'INDENTED FORCED ACTION'` with the whitespace stripped.
- Where: src/fountain/parser.py:622-629.

### D10. Ten-Space Card Indent Collapses in HTML (medium)

- Spec: "Here the ten spaces before the text on the card are passed through to the formatted output."
- Probe: the spec's card lines rendered to HTML.
- Expected: visible indentation in formatted output.
- Observed: raw spaces inside `<div class="fountain-action">` with no `white-space` CSS anywhere for action, so rendered browsers collapse them; only tabs are converted to `&nbsp;`.
- Where: src/fountain/renderer.py:96-99, 466-469.
- Same fix surface as A5, distinct probe.

### E1. Mid-Line Boneyard Not Stripped (medium)

- Spec: "If you want Fountain to ignore some text, wrap it with /* some text */."
- Probe: `Hello /* hidden */ world.` as dialogue and as action.
- Expected: `Hello world.` with the wrapped text ignored.
- Observed: `'Hello /* hidden */ world.'` retained verbatim in both element types.
- Where: src/fountain/parser.py:132-140 (patterns are line-anchored), 553-571.

### E2. Close With Trailing Text Swallows the Rest of the Document (high)

- Spec: "Your /* ... */ pairs can span as much of your screenplay as you like"; the pair closes at `*/`.
- Probe: `/*` block closed by `*/ And we are back.` followed by more action.
- Expected: boneyard ends at `*/`; `And we are back.` and later lines survive.
- Observed: the close is never detected (`\*/$` is end-anchored), `in_boneyard` never clears, and everything after the opener silently disappears; the parse produced one element.
- Where: src/fountain/parser.py:140, 554-557.

### E3. Single-Line Open Plus Close With Trailing Text Swallows the Document (high)

- Spec: same as E2.
- Probe: `/* cut this */ keep this` followed by more action.
- Expected: `keep this` and the following action survive.
- Observed: the single-line pattern (`^/\*.*?\*/$`) fails on the trailing text, the multiline-start branch runs, the end anchor fails again, and the rest of the document is silently dropped.
- Where: src/fountain/parser.py:132, 136, 140, 568-571.

### E4. Mid-Line Boneyard Open Leaks Interior Text (medium)

- Spec: same as E2; nothing restricts the opener to line start.
- Probe: `He waves /* begin cut` then interior lines then `*/`.
- Expected: `He waves` as action with the wrapped text ignored.
- Observed: `'He waves /* begin cut'`, `'still cut'`, and `'*/'` all emitted as ACTION elements.
- Where: src/fountain/parser.py:136, 568-571.

### E5. Sections, Synopses, and Note Brackets Visible in HTML (medium)

- Spec: Sections "are ignored completely in formatted output"; Synopses "are ignored in formatted output."
- Probe: render `# Act I`, `= He meets her.`, and `[[remember to fix]]`.
- Expected: neither section nor synopsis appears in formatted output.
- Observed: both are emitted as divs and DEFAULT_CSS styles them visibly (bold 14pt section, italic synopsis); the note renders with literal `[[ ]]` brackets; the module docstring claims synopsis and note are hidden, contradicting the CSS.
- Where: src/fountain/renderer.py:488-491, 128-132, 138-149, 250, 484-485.

### E6. Two-Space Connector Line Loses Its Empty Line (low)

- Spec: "if you wish a note to contain an empty line, you must place two spaces there to 'connect' the element into one."
- Probe: a note whose middle line is two spaces.
- Expected: one note whose text contains an empty line.
- Observed: one note with the empty line silently dropped.
- Where: src/fountain/parser.py:329-355 (blank branch runs before the `in_note` branch at 574-585).

### E7. Plain Blank Line Fails to Break the Note (low)

- Spec (Error Handling): "it won't look past a double line break for a closing syntactical element ... The exception to this rule is the /* boneyard */ wrapper."
- Probe: the same note with a genuinely blank middle line.
- Expected: the note does not survive the double line break; the bracket lines fall back to text.
- Observed: identical single-note result to E6; the connector rule is unenforceable because both inputs collapse to the same output.
- Where: src/fountain/parser.py:329-355, 574-585.

### E8. Spurious Empty Dialogue From a Two-Space Line Inside a Note (low)

- Spec: the two-space rule belongs to dialogue and note continuation, not element creation.
- Probe: dialogue block, then a note containing a two-space line.
- Expected: CHARACTER, DIALOGUE, NOTE.
- Observed: an extra empty DIALOGUE element (`text=''`) injected between the dialogue and the note.
- Where: src/fountain/parser.py:333-351.

### E10. Lone ] Inside a Note Breaks Recognition (low)

- Spec: "A Note is created by enclosing some text with double brackets."; only `]]` closes.
- Probe: `[[check ref] ok]]`.
- Expected: a note with text `check ref] ok`.
- Observed: ACTION with the brackets leaking into output.
- Where: src/fountain/parser.py:127 (`[^\]]*` cannot match an interior `]`).

### E11. Single-Line Boneyard Text Ships in HTML (low)

- Spec: boneyard content "will be ignored completely on formatted output."
- Probe: `/* hidden scene */` on its own line, rendered with `HTMLRenderer.render()`.
- Expected: nothing in the output.
- Observed: `<div class="fountain-boneyard">/* hidden scene */</div>` in the fragment; it is hidden only by `display:none` CSS that fragment mode does not emit, and multi-line boneyards are fully omitted, so behavior is inconsistent and leaks cut text.
- Where: src/fountain/parser.py:560-566; src/fountain/renderer.py:134-136, 486-487.

## Refuted Candidates

### E12. Double Equals Synopsis

- Claim: `== two equals` parsing as SYNOPSIS with text `= two equals` is a defect.
- Refutation: the spec defines a synopsis as "single lines prefixed by an equals sign =" and defines nothing for two equals signs (page breaks need three or more).
- Stripping exactly one `=` is a defensible literal reading of "prefixed by an equals sign", and the observed output follows from it.
- Verified fresh: `= He meets her.` yields clean text and `===` yields a page break, so the defined cases behave.
- Where checked: src/fountain/parser.py:150.

## Ambiguities and Deliberate Extensions

### A3. Title Page Detection at Line One (document the heuristic)

- The spec says the title page "is always the first thing in a Fountain document" and gives the `key: value` grammar, but it never defines how a parser decides whether a title page is present.
- `FADE IN:` and `CUT TO:` are syntactically valid `key:` lines, so consuming them as metadata is a defensible reading; several other implementations do the same.
- fountain-py's chosen behavior (verified): any first line containing a colon that does not start with `INT.`, `EXT.`, `EST.`, or `I/E.` opens the title page, including indented lines such as a tab-indented `CUT TO:` and prose like `He opens the card:`.
- Document the heuristic and the workarounds (a leading blank line, or forced syntax such as `>CUT TO:`).
- Two adjacent items remain real defects, tracked separately: the guard's case sensitivity (B3) and indentation handling once inside the title page (A2).
- Where: src/fountain/parser.py:448, 463.

### C8. Lyrics Inside a Dialogue Block (spec silent)

- Probe (verified): `JOHN` / `~Willy Wonka! Willy Wonka!` / `Wasn't that great?` yields CHARACTER, LYRICS, ACTION.
- The spec defines lyrics only as forced (`~`) lines and says nothing about their effect on dialogue continuation.
- fountain-py's chosen behavior: a lyric line ends the dialogue block, so the following line is action.
- Document this choice; writers who want the trailing line as dialogue have no supported syntax for it here.
- Where: src/fountain/parser.py:654-662, 906-919.

### D11. FADE IN: and FADE OUT. as Natural Transitions (deliberate extension)

- The spec's natural-transition rule requires "Ending in TO:", which `FADE IN:` and `FADE OUT.` do not satisfy.
- fountain-py special-cases both in TRANSITION_PATTERN (src/fountain/parser.py:108) and tests pin the behavior (tests/test_parser.py:57-58, tests/test_edge_cases.py:739-740).
- Verified fresh: both parse as TRANSITION mid-document.
- Classify as a deliberate extension; document it as such.

### E9. Mid-Line Notes Removed Without a Trace (document the model)

- Probe (verified): `DAN and JACK[[Or did we think of actual names?]]. They drink beer.` yields action text `'DAN and JACK. They drink beer.'` with no NOTE element and no metadata, while a standalone `[[note]]` line becomes a NOTE element.
- The spec allows notes "between lines, or in the middle of a line" and says they suit Scriptnote-style annotation import, but it defines no API-level requirement to expose them.
- Removal from formatted output is arguably the correct spec behavior; the standalone path (kept, and rendered visibly per E5) is the inconsistent one.
- Document the asymmetry: mid-line note content is unrecoverable from the parse, standalone notes are elements.
- Where: src/fountain/parser.py:614-619.

## Cross-Cutting Notes for the Spec Writer

- A5 and D10 share one fix surface: whitespace fidelity for Action in HTML (CSS `white-space` plus tab conversion at parse time).
- A3, B3, and A2 all live in `_parse_title_page`; fixing B3 and A2 without deciding the A3 heuristic will churn the same lines twice.
- E2 and E3 are the highest-risk items in Group E: both silently truncate the document, which contradicts the spec's error-handling philosophy ("Better to show the writer what they wrote ... than skip over malformed text").
