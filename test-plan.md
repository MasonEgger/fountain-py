# fountain-py Adversarial Test Plan

> **Living document.** This is a black-box test plan derived only from the Fountain
> spec (https://fountain.io/syntax/, fetched 2026-07-25) and the project's own docs
> (`README.md`, `docs/source/**`, `CHANGELOG.md`, `spec.md`, `pyproject.toml`). No
> source under `src/` or `tests/` was read. Every row is a distinct, checkable case.
> Update the Status checkboxes as cases are written and run. When a spec ambiguity is
> resolved, move the ruling into the Expected column and clear the Ambiguity flag.

## Methodology and Coverage Model

### The Coverage Denominator

The plan is built from an explicit product of dimensions, not an ad-hoc list.

- **15 element types** (`ElementType` has 15 members; `TITLE_PAGE` is metadata-only,
  14 are emitted; `spec.md` Type System). Each element is exercised across four
  **input classes** (equivalence partitioning): `{valid, boundary, forced, malformed}`.
- **4 observation surfaces** per element where applicable: `{parse (element type + text
  + metadata), HTML fragment render(), full-page render_page(), Fountain round-trip
  FountainRenderer.render()}`, plus the `validate()` diagnostic surface.
- **Interaction matrix**: every element adjacent to / nested in / interrupting every
  other element that can legally abut it (pairwise testing). The full 15x15 adjacency
  grid is sampled at the high-risk cells enumerated in section INTER.
- **Hazard layer** (spec-silent, historically the worst bugs): security (XSS on every
  dynamic render surface), performance/DoS, robustness/fuzz invariants, whitespace/
  encoding/Unicode, round-trip fidelity, diagnostics parity, public-API contract.

Coverage claim: **element conformance is enumerated exhaustively** across the 15 types
x 4 classes x observation surfaces; **interactions and hazards are risk-prioritized**
(exhaustive enumeration of a 15x15x{adjacent,nested,interrupt} cube is ~675 raw cells,
most degenerate, so those are sampled at the disambiguation-critical cells and the
sampling rationale is stated in the Coverage Self-Assessment).

### Techniques Applied (and Where)

| Technique | Where it drives cases |
|---|---|
| Equivalence partitioning | Every element section: valid / boundary / forced / malformed classes |
| Boundary-value analysis | Delimiter-count edges: `=`/`==`/`===`, `*`/`**`/`***`, `#`.. depth, 0/1/many blank lines, empty/whitespace-only input, 1-char vs 2-char brackets |
| Pairwise / interaction | Section INTER: element A abutting/nesting/interrupting element B |
| State-transition | Section STATE: title-page mode, in-note, in-boneyard, dialogue-block, action-accumulation, and parser-instance re-entrancy |
| Error guessing / negative | `malformed` rows throughout, plus FUZZ and XSS |
| Decision tables | Section PREC: ALL-CAPS line disambiguation (character vs action vs scene vs transition) |

### How a Reviewer Should Read This

1. Priorities: **P0** = security / data-loss / crash / infinite-loop; **P1** =
   spec-conformance common case; **P2** = edge; **P3** = cosmetic.
2. The **Ambiguity** column flags rows where "Expected" is a judgment call. Those are
   the rows most likely to encode the wrong oracle; review them first. They are
   collected in section AMB.
3. Many "Expected" values are pinned by `spec.md`, which documents both intended
   behavior and **known defects** (IDs like A4b, D6, E2). Rows citing a known-defect ID
   are expected to **fail today** and pass after the fix; they are the regression net.

### Citation Key

- **[FIO §X]** = fountain.io/syntax, section X (fetched 2026-07-25).
- **[SPEC §X]** = `spec.md`, named section or requirement ID (e.g. [SPEC E2], [SPEC A3]).
- **[DOC parse|elem|render §]** = `docs/source/user-guide/{parsing,elements,rendering}.rst`.
- **[QUICK]** = `docs/source/quickstart.rst`. **[README]**, **[CHANGELOG]**, **[PYPROJ]**.
- A row with **no external citation** in Expected is a hazard-layer invariant derived
  from general parser/renderer risk (stated as such per the black-box brief).

### Observation API (how rows are exercised)

- `p = FountainParser(); doc = p.parse(text)` then inspect `doc.elements[i].type`,
  `.text`, `.metadata`, `.formatting`, `.line_number`, and `doc.metadata`.
- `doc.to_dict()`, `doc.to_json()`, `doc.get_characters()`, `doc.get_scenes()`,
  `doc.get_statistics()`, `doc.to_html()`.
- `HTMLRenderer().render(doc)` (fragment), `.render_page(doc)` (full page), `.get_css()`.
- `FountainRenderer().render(doc)` (round-trip to Fountain).
- `FountainParser().validate(text) -> list[ValidationIssue]` (per [SPEC Validation API];
  not yet shipped, so DIAG rows are spec-forward).

---

## TP — Title Page

Rule [FIO Title Page]: "Optional first element ... `key: value` format. Keys can contain
spaces but must end with colon." Values may be inline or indented (3+ spaces or tab).
Detection contract [SPEC A3 / DOC parse "Line-One Title Page Detection"].

| ID | Technique | Input | Expected (citation) | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| TP-V01 | Valid | `Title: My Script\n\nINT. HOUSE - DAY` | `metadata["title"]=="My Script"`; keys lowercased [DOC parse] | `doc.metadata` | P1 | [ ] | |
| TP-V02 | Valid | `Title: X\nAuthor: Y\nDraft Date: Z\n\n...` | keys `title,author,draft date` present, lowercased [DOC parse] | metadata keys | P1 | [ ] | |
| TP-V03 | Valid | Standard keys: Title, Credit, Author, Source, Draft date, Contact, Notes, Copyright | each accepted as a field [FIO] | metadata | P1 | [ ] | |
| TP-V04 | Valid | Arbitrary key `Custom Field: value\n\n...` | opens title page; `metadata["custom field"]` set [SPEC A3: "capitalized custom label"] | metadata | P1 | [ ] | |
| TP-V05 | Valid | Multiple values same key (`Author:` then two indented lines) | both values retained [FIO "Multiple values allowed"] | metadata | P1 | [ ] | ✔ (list vs join) |
| TP-B01 | Boundary | Empty input `""` | no title page, `metadata=={}`, no elements [DOC render empty-doc] | metadata,elements | P1 | [ ] | |
| TP-B02 | Boundary | Only metadata, no body: `Title: X\nAuthor: Y` | metadata parsed, `elements==[]` [DOC render metadata_only] | both | P1 | [ ] | |
| TP-B03 | Boundary | Leading blank lines before `Title:` | blank lines skipped, title page still detected [SPEC Pass 1] | metadata | P2 | [ ] | |
| TP-B04 | Boundary | Indented continuation exactly 3 spaces vs tab vs 2 spaces | 3-space/tab continue the value; 2-space must NOT [SPEC A2, FIO] | metadata | P2 | [ ] | |
| TP-B05 | Boundary | `Contact:` then 3 indented address lines | value preserves 3 lines; HTML shows `<br>` between [SPEC A1] | metadata,HTML | P2 | [ ] | ✔ |
| TP-B06 | Boundary | Key with empty value then blank line: `Title:\n\nX` | empty-value field; blank ends page [SPEC Pass 1] | metadata | P2 | [ ] | ✔ |
| TP-M01 | Malformed | First line `FADE IN:` (empty value, no continuation) | body TRANSITION, NOT `fade in` key [SPEC A3, DOC parse] | metadata,elements | P0 | [ ] | ✔ |
| TP-M02 | Malformed | First line `CUT TO:` | body transition, no phantom key [SPEC A3] | both | P1 | [ ] | ✔ |
| TP-M03 | Malformed | `He opens the card: a threat.` (lowercase label) | ACTION, `metadata=={}` [DOC parse doctest] | both | P1 | [ ] | |
| TP-M04 | Malformed | `>CUT TO:` first line | body transition, not `> cut to` key [DOC parse doctest] | both | P1 | [ ] | |
| TP-M05 | Malformed | `> FADE IN:` first line | captured as key `> fade in` (documented quirk) [DOC parse] | metadata | P2 | [ ] | ✔ |
| TP-M06 | Malformed | Colon inside value: `Notes:` then indented `Draft 3: final` | `notes=="Draft 3: final revisions"`, no `draft 3` key [SPEC A2] | metadata | P1 | [ ] | |
| TP-M07 | Malformed | Unindented non-key line after a key | ends title page; line becomes body [SPEC A2] | both | P2 | [ ] | |
| TP-M08 | Malformed | First line `int. house - day - 3:00 pm` (lowercase scene) | SCENE_HEADING, not title metadata (case-insensitive guard) [SPEC B3] | elements | P1 | [ ] | |
| TP-M09 | Malformed | First line `.FLASHBACK` after `Title: X` (no blank) | `.FLASHBACK` ends page, forced SCENE_HEADING [SPEC Pass 1] | both | P2 | [ ] | |
| TP-M10 | Malformed | Duplicate key `Title: A\nTitle: B` | last-wins or documented merge (flat dict) [SPEC: `dict[str,str]`] | metadata | P2 | [ ] | ✔ |
| TP-M11 | Malformed | `author` and `authors` both present | both rendered; renderers agree [SPEC OQ10 ruling] | HTML,Fountain | P1 | [ ] | ✔ |
| TP-M12 | Malformed | Title page with no blank line before body (`Title: X\nINT. HOUSE`) | scene-heading prefix ends page [SPEC Pass 1 rule] | both | P2 | [ ] | |
| TP-M13 | Malformed | Key only, colon, trailing whitespace `Title:   ` | treated as empty value [SPEC Pass 1] | metadata | P3 | [ ] | ✔ |
| TP-M14 | Malformed | Key containing multiple colons `Time: 3:00: PM` | first colon splits key/value [FIO key ends with colon] | metadata | P2 | [ ] | ✔ |
| TP-M15 | Malformed | Non-ASCII/Unicode key `Título: X` | capitalized label opens page; key lowercased with Unicode casefold | metadata | P2 | [ ] | ✔ |
| TP-M16 | Boundary | Whitespace-only first line then `Title:` | leading blanks skipped, page detected [SPEC Pass 1] | metadata | P3 | [ ] | |

---

## SCENE — Scene Heading

Rule [FIO Scene Heading]: "any line that has a blank line following it, and either begins
with `INT` or `EXT` or similar." Forced with leading `.` (not `..`). Scene numbers in `#..#`
are "alphanumerics ... plus dashes/periods." Prefix set [SPEC Pass2 rule 16]: INT/EXT/EST/
I/E/INT/EXT/INT./EXT, case-insensitive, optional space before dot.

| ID | Technique | Input | Expected (citation) | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| SCENE-V01 | Valid | `INT. HOUSE - DAY` (blank after) | SCENE_HEADING, text `INT. HOUSE - DAY` [FIO] | type,text | P1 | [ ] | |
| SCENE-V02 | Valid | `EXT. PARK - NIGHT` | SCENE_HEADING [FIO] | type | P1 | [ ] | |
| SCENE-V03 | Valid | `EST. CITY - DAWN` | SCENE_HEADING [FIO] | type | P1 | [ ] | |
| SCENE-V04 | Valid | `INT./EXT. CAR - DAY` | SCENE_HEADING [SPEC rule 16] | type | P1 | [ ] | |
| SCENE-V05 | Valid | `I/E. BOAT - DUSK` | SCENE_HEADING [SPEC rule 16] | type | P1 | [ ] | |
| SCENE-V06 | Valid | Space form `INT HOUSE - DAY` (no dot) | SCENE_HEADING [SPEC B1] | type | P1 | [ ] | |
| SCENE-V07 | Valid | Lowercase `int. house - day` | SCENE_HEADING (case-insensitive) [SPEC B3] | type | P2 | [ ] | |
| SCENE-V08 | Valid | Scene number `INT. HOUSE - DAY #1#` | text strips number; `metadata["scene_number"]=="1"` [DOC parse] | text,meta | P1 | [ ] | |
| SCENE-V09 | Valid | Alphanumeric number `#2A#` | `scene_number=="2A"` [DOC elem] | meta | P1 | [ ] | |
| SCENE-V10 | Valid | Dash number `#FB-1#` / `#I-1-A#` | `scene_number` retains dashes [FIO, DOC parse] | meta | P2 | [ ] | |
| SCENE-F01 | Forced | `.FLASHBACK SEQUENCE` | SCENE_HEADING, `text=="FLASHBACK SEQUENCE"`, `metadata["forced"]==True` [DOC parse] | type,text,meta | P1 | [ ] | |
| SCENE-F02 | Forced | Forced + number `.FLASHBACK #FB-1#` | forced, `scene_number=="FB-1"` [DOC parse] | meta | P2 | [ ] | |
| SCENE-F03 | Forced | `.` at document start (no preceding blank) | forced SCENE_HEADING (start counts as blank) [SPEC rule 13] | type | P2 | [ ] | |
| SCENE-B01 | Boundary | `..DOUBLE DOT` (ellipsis guard) | NOT scene heading; `.` + alnum required, `..` protected [CHANGELOG, SPEC rule 13] | type | P1 | [ ] | |
| SCENE-B02 | Boundary | `...ELLIPSIS LEAD` | ACTION (leading ellipsis protected) [CHANGELOG] | type | P1 | [ ] | |
| SCENE-B03 | Boundary | `.` alone on a line | ACTION or empty, not a forced heading (no alnum) [SPEC rule 13] | type | P2 | [ ] | ✔ |
| SCENE-B04 | Boundary | `INT.` alone (prefix only, nothing after) | boundary: heading vs action [FIO "similar"] | type | P2 | [ ] | ✔ |
| SCENE-M01 | Malformed | `INTERNAL AFFAIRS INVESTIGATES.` | ACTION, prefix boundary required (INT must be a token) [SPEC B1] | type | P1 | [ ] | |
| SCENE-M02 | Malformed | `INTERIOR HOUSE` | ACTION (not a recognized prefix) [FIO] | type | P2 | [ ] | |
| SCENE-M03 | Malformed | `INT. HOUSE - DAY` immediately followed by non-blank line | ACTION (natural heading needs blank after) [SPEC B2] | type | P1 | [ ] | |
| SCENE-M04 | Malformed | `!INT. HOUSE - DAY` | forced ACTION, `!` prevents heading [FIO "! preceding prevents"] | type,text | P1 | [ ] | |
| SCENE-M05 | Malformed | Bad number chars `INT. HOUSE - DAY #$%^&#` | `#$%^&#` stays in text; no `scene_number` [SPEC B4] | text,meta | P2 | [ ] | |
| SCENE-M06 | Malformed | Empty number `INT. HOUSE #  #` | no scene_number extracted (empty/space) [SPEC B4] | meta | P3 | [ ] | ✔ |
| SCENE-M07 | Malformed | Unclosed number `INT. HOUSE #1` | `#1` stays literal in text, no metadata [FIO wrap in `#`] | text,meta | P2 | [ ] | |
| SCENE-I01 | Interaction | Scene heading with inline emphasis `INT. *HOUSE* - DAY` | heading text; emphasis span recorded [FIO emphasis] | text,formatting | P2 | [ ] | ✔ |
| SCENE-I02 | State | `INT. A` `INT. B` `INT. C` consecutive with blanks | 3 SCENE_HEADING elements [FIO] | count | P2 | [ ] | |
| SCENE-H01 | HTML | Render heading with number | `<span class="fountain-scene-number">#1#</span>` present [DOC render] | HTML | P2 | [ ] | |
| SCENE-RT01 | Round-trip | Parse->Fountain->parse of `INT. HOUSE - DAY #1#` | heading + number survive [DOC render RT] | element eq | P1 | [ ] | |

---

## ACT — Action

Rule [FIO Action]: "Any paragraph that doesn't meet criteria for another element." Tabs
and spaces retained; tabs -> four spaces; "every carriage return as intent." Forced with `!`.

| ID | Technique | Input | Expected (citation) | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| ACT-V01 | Valid | `The doorbell rings.` | ACTION, verbatim text [FIO] | type,text | P1 | [ ] | |
| ACT-V02 | Valid | Three adjacent prose lines | merge into ONE action paragraph [DOC parse error-handling doctest] | count==1 | P1 | [ ] | |
| ACT-V03 | Valid | Two prose paragraphs separated by blank | two ACTION elements [FIO blank lines preserved] | count==2 | P1 | [ ] | |
| ACT-F01 | Forced | `!DEFINITELY ACTION (caps)` | ACTION, `!` stripped, text without `!` [DOC elem doctest] | type,text | P1 | [ ] | |
| ACT-F02 | Forced | `!    INDENTED FORCED` | text keeps 4 leading spaces after `!` [SPEC D9] | text | P2 | [ ] | |
| ACT-B01 | Boundary | Single space line ` ` | boundary: empty vs whitespace action [FIO indenting] | type,text | P2 | [ ] | ✔ |
| ACT-B02 | Boundary | Ten-space indented line | leading whitespace preserved in `.text` [SPEC D8/D10] | text | P2 | [ ] | |
| ACT-B03 | Boundary | Tab-indented action line | raw tab kept in `.text` [SPEC A5, CHANGELOG] | text | P2 | [ ] | ✔ |
| ACT-B04 | Boundary | Many consecutive blank lines between two actions | blanks passed through faithfully [FIO "any number of empty lines"] | structure | P2 | [ ] | ✔ |
| ACT-M01 | Malformed | ALL CAPS line not followed by dialogue: `HE WALKS.` then blank | demoted to ACTION [FIO character needs no blank after] | type | P1 | [ ] | |
| ACT-H01 | HTML | Ten-space indented action rendered | indentation visible in HTML (`white-space:pre-wrap`/`&nbsp;`) [SPEC D10, CHANGELOG] | HTML | P2 | [ ] | |
| ACT-H02 | HTML | Tab-indented action rendered | tab -> four `&nbsp;` [SPEC A5] | HTML | P2 | [ ] | |
| ACT-H03 | HTML | Action with embedded newline (multi-line paragraph) | newline -> `<br>` at render [SPEC HTMLRenderer] | HTML | P2 | [ ] | |
| ACT-M02 | Malformed | Action containing `<script>` (see XSS-01) | HTML-escaped in output | HTML | P0 | [ ] | |
| ACT-RT01 | Round-trip | Forced action `!Action line.` parse->render->parse | element type preserved [DOC render RT doctest] | type eq | P1 | [ ] | |

---

## CHAR — Character

Rule [FIO Character]: "line entirely in uppercase, with one empty line before it and without
an empty line after it." Must contain >=1 letter. Extensions in parens. Forced with `@`.
Dual with trailing `^`.

| ID | Technique | Input | Expected (citation) | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| CHAR-V01 | Valid | `JOHN\nHello there!` | CHARACTER `JOHN` + DIALOGUE [DOC elem] | types | P1 | [ ] | |
| CHAR-V02 | Valid | `MARY JANE\nHi.` | CHARACTER (spaces allowed) [DOC elem] | type | P1 | [ ] | |
| CHAR-V03 | Valid | `ROBOT_1\nBeep.` | CHARACTER (underscore/digit ok, has letter) [DOC elem] | type | P2 | [ ] | |
| CHAR-V04 | Valid | `SARAH (V.O.)\nHi.` | CHARACTER text `SARAH`, `metadata["extension"]=="V.O."` [DOC elem] | text,meta | P1 | [ ] | |
| CHAR-V05 | Valid | `JOHN (O.S.)` | extension `O.S.` [DOC elem] | meta | P1 | [ ] | |
| CHAR-V06 | Valid | Continuation `CHEF` ... action ... `CHEF (CONT'D)` | extension `CONT'D`; auto `continuation` metadata [DOC parse] | meta | P2 | [ ] | |
| CHAR-F01 | Forced | `@john\nlowercase dialogue` | CHARACTER (forced), text `john`, `metadata["forced"]==True` [DOC parse] | type,text,meta | P1 | [ ] | |
| CHAR-F02 | Forced | `@McClane` then `I SAID NO` | CHARACTER + DIALOGUE; `@` unconditional, not gated on lookahead [SPEC C6] | types,text | P1 | [ ] | |
| CHAR-F03 | Forced | `@McClane (O.S.)` | forced char gets extension `O.S.` [SPEC C7] | meta | P2 | [ ] | |
| CHAR-F04 | Forced | `@McClane ^` after a BRICK block | dual dialogue; right char text `McClane` [SPEC C5] | dual meta | P2 | [ ] | |
| CHAR-C01 | Punctuation | `MR. SMITH\nHi.` | CHARACTER + DIALOGUE [SPEC C1] | types | P1 | [ ] | |
| CHAR-C02 | Punctuation | `O'BRIEN\nHi.` | CHARACTER [SPEC C1] | type | P1 | [ ] | |
| CHAR-C03 | Punctuation | `JEAN-CLAUDE\nHi.` | CHARACTER [SPEC C1] | type | P1 | [ ] | |
| CHAR-C04 | Punctuation | `DEALER #2\nHi.` | CHARACTER [SPEC C1] | type | P1 | [ ] | |
| CHAR-C05 | Digit-first | `23 SKIDOO\nHi.` | CHARACTER (has letter) [SPEC C2] | type | P2 | [ ] | |
| CHAR-M01 | Malformed | `23\nHi.` (digits only) | ACTION, not character (needs a letter) [FIO, SPEC C2] | type | P1 | [ ] | |
| CHAR-M02 | Malformed | `R2D2\nBeep.` | CHARACTER (valid per FIO "R2D2 valid") [FIO] | type | P2 | [ ] | |
| CHAR-M03 | Malformed | `JOHN` then blank then `He walks.` | cue disqualified: CHARACTER->ACTION; two ACTION [SPEC C3] | types | P1 | [ ] | |
| CHAR-M04 | Malformed | `JOHN` (last line, EOF, no dialogue) | orphan cue demoted to ACTION; `orphan-character-cue` warning [SPEC C3, Validation] | type,validate | P1 | [ ] | |
| CHAR-M05 | Malformed | `JOHN` with no blank line before (mid-action) | ACTION unless blank-before satisfied [FIO "empty line before"] | type | P1 | [ ] | |
| CHAR-M06 | Malformed | `@` alone / `@ ` | not a valid forced char; ACTION fallback [SPEC C6 edge] | type | P3 | [ ] | ✔ |
| CHAR-B01 | Boundary | Character then immediately-next all-caps `JOHN\nI SAID NO` | CHARACTER + DIALOGUE (caps line is dialogue) [SPEC C4] | types | P2 | [ ] | |
| CHAR-B02 | Boundary | Cue with trailing whitespace `JOHN   \nHi.` | still CHARACTER (trailing ws stripped) [SPEC line strip] | type | P2 | [ ] | |
| CHAR-M07 | Malformed | Mixed-case natural `John\nHi.` | ACTION (natural cue must be uppercase) [FIO] | type | P1 | [ ] | |
| CHAR-DOC01 | API mismatch | `document.get_character_names()` (docs) vs `get_characters()` (spec) | one is wrong; verify actual method name [QUICK/DOC parse use `get_character_names`; SPEC/CHANGELOG say `get_characters`] | AttributeError? | P1 | [ ] | ✔ |
| CHAR-DOC02 | API | `get_characters()` returns uppercased, `^` stripped, sorted unique [SPEC] | list contents | P1 | [ ] | |
| CHAR-XSS01 | Security | Character name `<b>EVIL</b>` (forced `@`) | escaped in HTML; also inside `(CONT'D)`/extension spans | HTML | P0 | [ ] | |

---

## DLG — Dialogue

Rule [FIO Dialogue]: "Any text following a Character or Parenthetical element."

| ID | Technique | Input | Expected (citation) | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| DLG-V01 | Valid | `JOHN\nHello.` | DIALOGUE `Hello.` [DOC elem] | type,text | P1 | [ ] | |
| DLG-V02 | Valid | Multi-line dialogue (2 lines, no blank) | continues as dialogue; block ends at blank [DOC elem] | count | P1 | [ ] | ✔ |
| DLG-V03 | Valid | Dialogue after parenthetical `JOHN\n(beat)\nHi.` | PARENTHETICAL then DIALOGUE [DOC elem] | types | P1 | [ ] | |
| DLG-B01 | Boundary | Two-space-only line inside dialogue | empty DIALOGUE element (2-space continuation) [SPEC Pass2, FIO] | element | P2 | [ ] | ✔ |
| DLG-B02 | Boundary | Genuinely blank line in dialogue | ends the block [FIO] | structure | P1 | [ ] | |
| DLG-I01 | Interaction | `JOHN\n~Willy Wonka!\nWasn't that great?` | CHARACTER, LYRICS, DIALOGUE (lyric does not close block) [SPEC C8, DOC parse] | types | P2 | [ ] | ✔ |
| DLG-I02 | Interaction | Dialogue containing standalone `[[note]]` line mid-block | note does not close block; dialogue resumes [SPEC C8] | types | P2 | [ ] | ✔ |
| DLG-I03 | Interaction | Dialogue with inline emphasis `I *love* it` | DIALOGUE, italic span over `love` [DOC elem] | formatting | P1 | [ ] | |
| DLG-M01 | Malformed | Parenthetical-looking dialogue `(not a paren` (unclosed) | DIALOGUE not PARENTHETICAL (needs closing paren) [FIO] | type | P2 | [ ] | ✔ |
| DLG-XSS01 | Security | Dialogue text with `<img src=x onerror=alert(1)>` | HTML-escaped in fragment and page | HTML | P0 | [ ] | |
| DLG-B03 | Boundary | Dialogue with leading indentation | indentation ignored (non-action) [FIO indenting] | text | P2 | [ ] | |

---

## PAREN — Parenthetical

Rule [FIO Parenthetical]: wrapped in `()`, following Character or Dialogue; no blank lines
before/after.

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| PAREN-V01 | Valid | `JOHN\n(nervously)\nHi.` | PARENTHETICAL `(nervously)` [DOC elem] | type,text | P1 | [ ] | |
| PAREN-V02 | Valid | `(beat)` between dialogue lines | PARENTHETICAL, keeps parens in text [DOC elem] | text | P1 | [ ] | |
| PAREN-B01 | Boundary | `()` empty parens | boundary: paren vs dialogue [FIO] | type | P3 | [ ] | ✔ |
| PAREN-B02 | Boundary | Nested parens `(to (young) Mary)` | single PARENTHETICAL, text intact [FIO] | text | P2 | [ ] | ✔ |
| PAREN-M01 | Malformed | `(unclosed` in dialogue position | not parenthetical -> DIALOGUE [FIO closed parens] | type | P2 | [ ] | ✔ |
| PAREN-M02 | Malformed | `(nervously)` with NO preceding character/dialogue (standalone) | ACTION (context required) [FIO] | type | P2 | [ ] | ✔ |
| PAREN-B03 | Boundary | Indented parenthetical | indentation ignored [FIO] | text | P3 | [ ] | |
| PAREN-XSS01 | Security | `(<svg onload=alert(1)>)` | escaped in HTML | HTML | P0 | [ ] | |
| PAREN-I01 | Interaction | Parenthetical after action (no character) | ACTION not PARENTHETICAL | type | P2 | [ ] | ✔ |
| PAREN-RT01 | Round-trip | paren survives parse->Fountain->parse | type preserved [DOC render RT] | type | P2 | [ ] | |

---

## DUAL — Dual Dialogue

Rule [FIO Dual]: "adding a caret `^` after the second Character element." One blank line
precedes second character. Post-processing pairs the two blocks into one DUAL_DIALOGUE
[SPEC Dual Dialogue Post-Processing].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| DUAL-V01 | Valid | `JOHN\nDid you see that?\n\nMARY^\nI can't believe it!` | one DUAL_DIALOGUE; left=JOHN, right=MARY [DOC elem] | meta | P1 | [ ] | |
| DUAL-V02 | Valid | Access `metadata["left_dialogue"][0].text` | `"Did you see that?"` [DOC elem] | meta | P1 | [ ] | |
| DUAL-V03 | Valid | `left_dialogue`/`right_dialogue` are lists of DIALOGUE/PARENTHETICAL [SPEC] | list types | P2 | [ ] | |
| DUAL-B01 | Boundary | Caret with spaces before `MARY  ^` | caret recognized, spaces ignored [FIO] | type | P2 | [ ] | |
| DUAL-B02 | Boundary | Second char with extension + caret `MARY (V.O.)^` | dual + extension both captured [SPEC rule 20] | meta | P2 | [ ] | |
| DUAL-M01 | Malformed | `^` on FIRST character (no preceding block) | no pair; degrade gracefully (no crash) [SPEC post-pass] | no crash | P1 | [ ] | ✔ |
| DUAL-M02 | Malformed | Caret char with scene heading between the two blocks | not paired (scene break) [SPEC post-pass] | types | P2 | [ ] | ✔ |
| DUAL-M03 | Malformed | Two consecutive caret chars | pairing behavior defined / no crash [SPEC] | no crash | P2 | [ ] | ✔ |
| DUAL-H01 | HTML | Render dual | `<div class="fountain-dual-dialogue">` + left/right columns [DOC render] | HTML | P1 | [ ] | |
| DUAL-H02 | HTML | Empty-text DUAL_DIALOGUE element renders children not `.text` | both characters visible [SPEC] | HTML | P1 | [ ] | |
| DUAL-RT01 | Round-trip | dual parse->Fountain->parse | reproduces DUAL_DIALOGUE (known defect today) [SPEC A4b] | type | P0 | [ ] | |
| DUAL-RT02 | Round-trip | Fountain output emits caret on 2nd cue | caret present in text [SPEC A4b] | Fountain text | P1 | [ ] | |
| DUAL-XSS01 | Security | dual char/dialogue with `<script>` | escaped in HTML | HTML | P0 | [ ] | |
| DUAL-STAT01 | Analysis | `get_statistics()` counts dual_dialogue and characters correctly | counts | P2 | [ ] | ✔ |
| DUAL-DICT01 | Serialization | `to_dict()`/`to_json()` on a DUAL element (nested element metadata) | serializable without error [SPEC to_dict] | no crash | P1 | [ ] | ✔ |

---

## LYR — Lyrics

Rule [FIO Lyrics]: start line with `~`; "always forced"; tilde removed.

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| LYR-V01 | Valid | `~Happy birthday to you` | LYRICS, text `Happy birthday to you` (tilde stripped) [DOC elem] | type,text | P1 | [ ] | |
| LYR-V02 | Valid | 3 consecutive `~` lines | 3 LYRICS elements [DOC elem] | count | P1 | [ ] | |
| LYR-B01 | Boundary | `~` alone | LYRICS with empty text [FIO] | type,text | P3 | [ ] | ✔ |
| LYR-B02 | Boundary | `~ leading space kept?` | leading tilde stripped only; content per contract [SPEC A4c] | text | P3 | [ ] | ✔ |
| LYR-I01 | Interaction | Lyrics inside dialogue block (see DLG-I01) | does not end block [SPEC C8] | types | P2 | [ ] | |
| LYR-RT01 | Round-trip | `~La la la` parse->Fountain->parse | LYRICS text `La la la`, NO trailing `~` (known defect) [SPEC A4c] | text | P1 | [ ] | |
| LYR-M01 | Malformed | `~` mid-line (not leading) `oh ~la` | not lyrics; ACTION [FIO leading tilde] | type | P2 | [ ] | |
| LYR-H01 | HTML | Render lyrics | `.fountain-lyrics` styling, content present [DOC render] | HTML | P2 | [ ] | |
| LYR-XSS01 | Security | `~<script>alert(1)</script>` | escaped in HTML | HTML | P0 | [ ] | |
| LYR-EMPH01 | Interaction | `~*italic lyric*` | LYRICS with italic span [FIO emphasis] | formatting | P2 | [ ] | ✔ |

---

## TRANS — Transition

Rule [FIO Transition]: "Uppercase, preceded by and followed by an empty line, ending in
`TO:`." Forced with `>`. Extensions: FADE IN:/FADE OUT./CUT TO: special-cased [SPEC D11].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| TRANS-V01 | Valid | `CUT TO:` (blank before/after) | TRANSITION [FIO] | type | P1 | [ ] | |
| TRANS-V02 | Valid | `DISSOLVE TO:` | TRANSITION [FIO] | type | P1 | [ ] | |
| TRANS-V03 | Valid | `FADE IN:` (after an action line) | TRANSITION (deliberate extension) [SPEC D11, DOC parse] | type | P1 | [ ] | |
| TRANS-V04 | Valid | `FADE OUT.` | TRANSITION (extension, no colon) [SPEC D11] | type | P1 | [ ] | |
| TRANS-V05 | Punctuation | `SMASH-CUT TO:` | TRANSITION (punctuation ok) [SPEC D2] | type | P2 | [ ] | |
| TRANS-F01 | Forced | `>SMASH CUT TO:` | TRANSITION, `>` stripped, text `SMASH CUT TO:` [DOC elem] | type,text | P1 | [ ] | |
| TRANS-F02 | Forced | `> FORCED TRANSITION` (no TO:) | TRANSITION [DOC parse] | type | P1 | [ ] | |
| TRANS-B01 | Boundary | `FADE IN:` on line ONE (title-page grab) | consumed as `fade in` key, no body element [DOC parse] | metadata | P1 | [ ] | ✔ |
| TRANS-B02 | Boundary | `FADE OUT.` on line one | TRANSITION (no colon, not grabbed) [SPEC rule 17, DOC parse] | type | P2 | [ ] | |
| TRANS-M01 | Malformed | `CUT TO: ` (trailing space) | ACTION (trailing space defeats) [SPEC D1] | type | P2 | [ ] | |
| TRANS-M02 | Malformed | `cut to:` (lowercase) | not transition -> ACTION [FIO uppercase] | type | P2 | [ ] | |
| TRANS-M03 | Malformed | `CUT TO:` not followed by blank line | ACTION (needs blank after) [SPEC rule 17] | type | P2 | [ ] | ✔ |
| TRANS-M04 | Malformed | `CUT TO:` not preceded by blank | context: only at start or after blank [SPEC rule 17] | type | P2 | [ ] | ✔ |
| TRANS-D01 | Decision | `THE END TO:` vs forced `.THE END TO:` | natural TRANSITION vs forced SCENE_HEADING (disambiguation) [FIO] | type | P2 | [ ] | ✔ |
| TRANS-H01 | HTML | Render transition | `.fountain-transition` (right-aligned) [DOC render] | HTML | P3 | [ ] | |
| TRANS-RT01 | Round-trip | forced transition survives | type preserved [DOC render RT] | type | P2 | [ ] | |
| TRANS-XSS01 | Security | `>` + `<script>` forced transition | escaped in HTML | HTML | P0 | [ ] | |
| TRANS-M05 | Malformed | `TO:` alone | boundary: transition vs action [FIO] | type | P3 | [ ] | ✔ |
| TRANS-M06 | Malformed | ALL CAPS `GO TO:` followed by dialogue | transition vs character ambiguity (see PREC) [FIO] | type | P2 | [ ] | ✔ |

---

## CENT — Centered Text

Rule [FIO Centered]: "bracketed with greater/less-than: `>text<`"; leading spaces not
preserved; `> text <` allowed.

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| CENT-V01 | Valid | `>THE END<` | CENTERED, text `THE END` (brackets stripped) [DOC elem] | type,text | P1 | [ ] | |
| CENT-V02 | Valid | `> text <` (spaces inside) | CENTERED, spaces trimmed for readability [FIO] | text | P2 | [ ] | ✔ |
| CENT-V03 | Valid | `>FIVE YEARS LATER<` | CENTERED [DOC elem] | type | P1 | [ ] | |
| CENT-B01 | Boundary | `><` empty centered | boundary: centered vs transition [FIO] | type | P3 | [ ] | ✔ |
| CENT-M01 | Malformed | `>text` (no closing `<`) | TRANSITION not centered (forced transition) [SPEC rule 15] | type | P1 | [ ] | |
| CENT-M02 | Malformed | `text<` (no leading `>`) | ACTION [FIO] | type | P2 | [ ] | |
| CENT-H01 | HTML | Render | `<div class="fountain-centered">THE END</div>` [DOC render] | HTML | P2 | [ ] | |
| CENT-XSS01 | Security | `><script>alert(1)</script><` | escaped in HTML | HTML | P0 | [ ] | |
| CENT-EMPH01 | Interaction | `>*THE END*<` | CENTERED with italic span [FIO] | formatting | P2 | [ ] | ✔ |
| CENT-RT01 | Round-trip | centered survives round-trip | type preserved [DOC render RT] | type | P2 | [ ] | |

---

## SEC — Section

Rule [FIO Section]: leading `#`; more `#` = deeper; "Ignored completely in formatted output."
`metadata["level"]` = hash count [SPEC rule 10].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| SEC-V01 | Valid | `# Act I` | SECTION, text `Act I`, `level==1` [DOC elem] | text,meta | P1 | [ ] | |
| SEC-V02 | Valid | `## Scene 1` | `level==2` [DOC elem] | meta | P1 | [ ] | |
| SEC-V03 | Valid | `### Subplot` | `level==3` [DOC elem] | meta | P1 | [ ] | |
| SEC-B01 | Boundary | `#` alone (no text) | SECTION level 1, empty text [FIO] | type,text | P3 | [ ] | ✔ |
| SEC-B02 | Boundary | 6+ hashes `###### Deep` | level==6 (no ceiling) [FIO "one or more"] | meta | P3 | [ ] | ✔ |
| SEC-B03 | Boundary | `#NoSpace` (no space after hash) | SECTION text `NoSpace` or per contract [FIO] | text | P2 | [ ] | ✔ |
| SEC-M01 | Malformed | `#1#` alone (looks like scene number) | SECTION not scene-number; disambiguate [FIO] | type | P2 | [ ] | ✔ |
| SEC-H01 | HTML render | `# Act I` in render() and render_page() | NOT visible; no `.fountain-section` markup/CSS [SPEC E5, DOC render, OQ3 ruling] | HTML | P1 | [ ] | |
| SEC-P01 | Parse-retain | section still in `doc.elements` though not rendered | element present [DOC render] | elements | P2 | [ ] | |
| SEC-XSS01 | Security | `# <script>` (if ever rendered) | no injection; not rendered anyway [SPEC E5] | HTML | P1 | [ ] | |
| SEC-RT01 | Round-trip | `## Scene` -> Fountain -> parse | hashes restored, level preserved [DOC render RT] | text,meta | P2 | [ ] | |
| SEC-STAT01 | Analysis | section counted in get_statistics | `section_count` correct [SPEC get_statistics] | stats | P3 | [ ] | |

---

## SYN — Synopsis

Rule [FIO Synopsis]: single line prefixed by `=`; "Ignored in formatted output."

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| SYN-V01 | Valid | `= He meets her.` | SYNOPSIS, text `He meets her.` (one `=` stripped) [DOC elem] | type,text | P1 | [ ] | |
| SYN-B01 | Boundary | `=` alone | boundary: page-break vs synopsis [FIO] | type | P2 | [ ] | ✔ |
| SYN-B02 | Boundary | `==` (two equals) | SYNOPSIS text `= two equals` (documented, not defect) [SPEC E12 refuted] | type,text | P2 | [ ] | ✔ |
| SYN-B03 | Boundary | `===` (three) | PAGE_BREAK not synopsis [FIO] | type | P1 | [ ] | |
| SYN-H01 | HTML | render + render_page | NOT visible; no `.fountain-synopsis` [SPEC E5, OQ3] | HTML | P1 | [ ] | |
| SYN-P01 | Parse-retain | synopsis in doc.elements | present [DOC render] | elements | P2 | [ ] | |
| SYN-XSS01 | Security | `= <script>` | not rendered; no injection [SPEC E5] | HTML | P1 | [ ] | |
| SYN-RT01 | Round-trip | `= X` round-trips | `=` restored [DOC render RT] | text | P2 | [ ] | |
| SYN-I01 | Interaction | synopsis between scenes `= x\n\nINT. HOUSE - DAY` | SYNOPSIS then SCENE [DOC elem doctest] | types | P2 | [ ] | |
| SYN-B04 | Boundary | `=text` no space | one `=` stripped -> `text` [SPEC rule 11] | text | P3 | [ ] | ✔ |

---

## NOTE — Notes

Rule [FIO Notes]: enclose in `[[text]]`; between lines or mid-line; supports carriage
returns; "Not included in formatted output." Asymmetry [SPEC E9/DOC parse]: standalone
kept verbatim (brackets included), inline stripped and unrecoverable.

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| NOTE-V01 | Valid standalone | `[[Remember this]]` on its own line | NOTE, text `[[Remember this]]` verbatim [DOC parse doctest] | type,text | P1 | [ ] | |
| NOTE-V02 | Valid inline | `He waves [[secret]] hello.` | ACTION text `He waves hello.`; note stripped, seam->1 space [DOC parse] | text | P1 | [ ] | |
| NOTE-V03 | Multi-line | `[[note\nspanning\nlines]]` | single NOTE with buffered text [SPEC rule 4/7, CHANGELOG] | type,text | P1 | [ ] | |
| NOTE-B01 | Boundary | `[[a]] middle [[b]]` | ACTION text `middle` (both inline notes stripped), NOT one NOTE [SPEC E13] | type,text | P1 | [ ] | |
| NOTE-B02 | Boundary | Note with two-space connector line inside | NOTE text contains empty interior line `\n\n` [SPEC E6] | text | P2 | [ ] | ✔ |
| NOTE-B03 | Boundary | Note with truly blank middle line | breaks the note; distinguishable from E6 [SPEC E7] | structure | P2 | [ ] | ✔ |
| NOTE-B04 | Boundary | Lone `]` inside `[[check ref] ok]]` | NOTE text `check ref] ok`; only `]]` closes [SPEC E10] | text | P2 | [ ] | |
| NOTE-M01 | Unterminated | `[[ open with no close before EOF` | multi-line note swallows to EOF; `unclosed-note` error [SPEC rule 7, Validation] | validate,elements | P0 | [ ] | |
| NOTE-M02 | Malformed | Empty note `[[]]` | NOTE or empty per contract [FIO] | type | P3 | [ ] | ✔ |
| NOTE-M03 | Interaction | note-inside-dialogue two-space line does NOT inject empty DIALOGUE [SPEC E8] | elements | P2 | [ ] | ✔ |
| NOTE-H01 | HTML | render + render_page of a note | NOT visible; if rendered, no literal `[[ ]]` [SPEC E5, OQ3] | HTML | P1 | [ ] | |
| NOTE-H02 | HTML fragment | note text must not leak into fragment [SPEC E5/E11 parity] | HTML | P1 | [ ] | |
| NOTE-XSS01 | Security | `[[<script>alert(1)</script>]]` standalone | not rendered; if rendered, escaped [SPEC E5] | HTML | P0 | [ ] | |
| NOTE-P01 | Parse-retain | standalone note present in doc.elements | element present [DOC render] | elements | P2 | [ ] | |
| NOTE-RT01 | Round-trip | standalone note round-trips verbatim | brackets preserved [SPEC/DOC] | text | P2 | [ ] | ✔ |
| NOTE-M04 | Data-loss | inline note content unrecoverable (documented) [SPEC E9] | text | P2 | [ ] | ✔ |
| NOTE-B05 | Boundary | note at end of scene heading line `INT. HOUSE [[chk]]` | note stripped from heading text [SPEC rule 8] | text | P2 | [ ] | ✔ |

---

## BONE — Boneyard

Rule [FIO Boneyard]: `/* text */`; may span multiple lines/scenes; "Completely ignored in
formatted output." Highest-priority defects E2/E3/E4 [SPEC].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| BONE-V01 | Valid single-line | `/* cut this */` on its own line | BONEYARD element (text verbatim incl delimiters per SPEC rule 2) [DOC elem] | type,text | P1 | [ ] | |
| BONE-V02 | Valid multi-line | `/*` ... lines ... `*/` | interior swallowed; single boneyard [SPEC rule 1-3] | elements | P1 | [ ] | |
| BONE-V03 | Spans scenes | boneyard across a scene heading | whole span ignored (exception to line-break rule) [FIO] | elements | P2 | [ ] | ✔ |
| BONE-E2 | Data-loss | `/*` block closed by `*/ And we are back.` | `And we are back.` + following lines survive; close not end-anchored [SPEC E2] | elements | P0 | [ ] | |
| BONE-E3 | Data-loss | `/* cut this */ keep this` + more action | `keep this` + following survive; no document truncation [SPEC E3] | elements | P0 | [ ] | |
| BONE-E4 | Data-loss | `He waves /* begin cut`, interior, `*/` | single ACTION `He waves`, no interior leak [SPEC E4] | text,elements | P0 | [ ] | |
| BONE-E1 | Mid-line strip | `Hello /* hidden */ world.` | ACTION text `Hello world.` [SPEC E1] | text | P1 | [ ] | |
| BONE-M01 | Unterminated | `/* open` with no `*/` before EOF | boneyard to EOF; `unclosed-boneyard` error [SPEC rule 3, Validation] | validate,elements | P0 | [ ] | |
| BONE-B01 | Boundary | Empty boneyard `/**/` | recognized, no crash [FIO] | type | P3 | [ ] | ✔ |
| BONE-B02 | Boundary | Nested-looking `/* a /* b */ c */` | first `*/` closes; `c */` is body [FIO no nesting] | elements | P2 | [ ] | ✔ |
| BONE-H01 | HTML fragment | render() with boneyard | no boneyard text in fragment [SPEC E11] | HTML | P1 | [ ] | |
| BONE-H02 | HTML page | render_page() with boneyard | no boneyard text/CSS [SPEC E5/E11, OQ3] | HTML | P1 | [ ] | |
| BONE-H03 | Parity | single-line vs multi-line boneyard both hidden [SPEC E11] | HTML | P1 | [ ] | |
| BONE-P01 | Parse-retain | boneyard present in doc.elements | element present [DOC elem] | elements | P2 | [ ] | |
| BONE-XSS01 | Security | `/* <script>alert(1)</script> */` | not rendered; no injection | HTML | P0 | [ ] | |
| BONE-RT01 | Round-trip | boneyard dropped from Fountain output (writer tool) [DOC render RT] | Fountain text | P2 | [ ] | |
| BONE-STATE01 | State | script with 2 separate boneyards | in_boneyard flag resets between them; no leak [SPEC in_boneyard] | elements | P1 | [ ] | |
| BONE-M02 | Malformed | `*/` with no opening `/*` | literal text as ACTION [FIO] | type,text | P2 | [ ] | ✔ |

---

## PAGE — Page Break

Rule [FIO Page Breaks]: "Line containing three or more consecutive equals signs, and nothing
more."

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| PAGE-V01 | Valid | `===` | PAGE_BREAK, text `===` [DOC elem] | type,text | P1 | [ ] | |
| PAGE-V02 | Valid | `======` (six) | PAGE_BREAK [FIO "three or more"] | type | P2 | [ ] | |
| PAGE-B01 | Boundary | `==` (two) | SYNOPSIS `= two equals`, not page break [SPEC E12] | type | P1 | [ ] | |
| PAGE-B02 | Boundary | `=` (one) | SYNOPSIS (empty) not page break [FIO] | type | P2 | [ ] | |
| PAGE-M01 | Malformed | `=== text` (equals + text) | NOT page break ("and nothing more") -> synopsis/action [FIO] | type | P1 | [ ] | ✔ |
| PAGE-M02 | Malformed | `=== ` (trailing space) | boundary: page break vs action after strip [FIO] | type | P2 | [ ] | ✔ |
| PAGE-H01 | HTML | render page break | `.fountain-page-break` present [DOC render] | HTML | P3 | [ ] | |
| PAGE-RT01 | Round-trip | `===` round-trips | preserved [DOC render RT] | type | P2 | [ ] | |
| PAGE-I01 | Interaction | `End of Act.\n\n===\n\n# Act II` | ACTION, PAGE_BREAK, SECTION [DOC elem] | types | P2 | [ ] | |
| PAGE-XSS01 | Security | page break can't carry text; confirm no injection surface | HTML | P3 | [ ] | |

---

## EMPH — Inline Emphasis

Rule [FIO Emphasis]: `*italic*`, `**bold**`, `***bold italic***`, `_underline_`. Combos allowed.
"Emphasis is not carried across line breaks." Spaces around emphasis chars are meaningful.
Delimiters must be stripped from text; spans cover content only [SPEC D4].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| EMPH-V01 | Valid | `This is **bold** text.` | text `This is bold text.`; bold span over `bold`; HTML `<strong>bold</strong>` [SPEC D4, DOC render] | text,formatting,HTML | P1 | [ ] | |
| EMPH-V02 | Valid | `*italic*` | italic span; `<em>italic</em>` [DOC render] | formatting,HTML | P1 | [ ] | |
| EMPH-V03 | Valid | `***bold italic***` | `bold_italic` span; `<strong><em>` [DOC elem, SPEC] | formatting | P1 | [ ] | |
| EMPH-V04 | Valid | `_underline_` | underline span; `<u>` [DOC parse] | formatting | P1 | [ ] | |
| EMPH-V05 | Valid | Three spans one line `**b** *i* _u_` | 3 spans in order [DOC elem] | formatting | P1 | [ ] | |
| EMPH-B01 | Boundary count | `*` vs `**` vs `***` (1/2/3 asterisks) | italic / bold / bold-italic respectively [FIO] | formatting | P1 | [ ] | |
| EMPH-B02 | Boundary | `****` (four asterisks) | boundary behavior defined; no crash [FIO] | formatting | P2 | [ ] | ✔ |
| EMPH-B03 | Boundary | Unclosed `*italic` (no closing) | no span; literal `*` retained [FIO] | text,formatting | P2 | [ ] | ✔ |
| EMPH-N01 | Nesting | `_underlined *italic* phrase_` | underline over phrase, nested italic; each word once [FIO example, SPEC D6] | formatting,HTML | P1 | [ ] | |
| EMPH-N02 | Nesting | `_Steel's face FILLS the *Leupold Mark 4* scope_.` | underlined phrase with one italic span; no duplication [SPEC D6] | HTML | P0 | [ ] | |
| EMPH-N03 | Nesting | `**_word_**` | bold + underline composable, no dup [SPEC D6] | HTML | P1 | [ ] | |
| EMPH-N04 | Overlap | `*a **b* c**` (crossed delimiters) | defined behavior, no crash/no text loss [FIO] | text,HTML | P2 | [ ] | ✔ |
| EMPH-W01 | Flanking | `** word**` (space after `**`) | no bold span (space guard) [SPEC D7] | formatting | P2 | [ ] | |
| EMPH-W02 | Flanking | `_ kilos_` (space after `_`) | no underline span [SPEC D7] | formatting | P2 | [ ] | |
| EMPH-W03 | Flanking | `*italic *` (space before closing) | italic guard behavior [SPEC D7/FIO] | formatting | P2 | [ ] | ✔ |
| EMPH-W04 | Intraword | `un*believe*able` | intraword italic per FIO "asterisks need no surrounding spaces" | formatting | P2 | [ ] | ✔ |
| EMPH-LB01 | Line break | `*italic\nnot italic*` (across newline) | emphasis NOT carried across line break [FIO] | formatting | P1 | [ ] | |
| EMPH-D08 | Offset | 10 spaces then `*Scott* --` | italic span over `Scott`, offsets against stored text incl indent [SPEC D8] | formatting | P1 | [ ] | |
| EMPH-D06 | Renderer | nested spans render without text duplication [SPEC D6] | HTML | P0 | [ ] | |
| EMPH-RT01 | Round-trip | `**bold**` parse->Fountain->parse | `**bold**` restored incl nesting [README, DOC render RT] | text | P1 | [ ] | |
| EMPH-RT02 | Round-trip | nested `_a *b* c_` round-trips | delimiters restored [README] | text | P1 | [ ] | |
| EMPH-M01 | Malformed | Bold with only opening `**bold` | no span; literal retained [FIO] | text | P2 | [ ] | ✔ |
| EMPH-PERF01 | DoS | `*`*N (thousands of lone asterisks) | linear time, no catastrophic backtracking | timing | P0 | [ ] | |
| EMPH-PERF02 | DoS | Deeply nested `***...***` alternating | no exponential blowup | timing | P0 | [ ] | |
| EMPH-XSS01 | Security | `*<script>*` | escaped inside `<em>` [SPEC HTMLRenderer escape] | HTML | P0 | [ ] | |
| EMPH-B04 | Boundary | Empty emphasis `**` `**` -> `****`; `__`; `**` | no span, no crash [FIO] | formatting | P3 | [ ] | ✔ |

---

## ESC — Backslash Escapes

Rule [SPEC Pass2]: `\*`, `\_`, `\\` resolve to literals; spans position-adjusted. Keypad
example [SPEC D5].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| ESC-V01 | Valid | `\*not italic\*` | text `*not italic*`, no span [SPEC, FIO backslash] | text,formatting | P1 | [ ] | |
| ESC-V02 | Valid | `\_not underline\_` | text `_not underline_`, no span [SPEC] | text | P1 | [ ] | |
| ESC-V03 | Valid | `\\` | single backslash in text [SPEC] | text | P2 | [ ] | |
| ESC-D05 | Keypad | `Steel enters the code on the keypad: **\*9765\***` | renders `<strong>*9765*</strong>`, no stray delimiters [SPEC D5, FIO example] | HTML | P1 | [ ] | |
| ESC-B01 | Boundary | Trailing lone backslash `text\` | literal backslash or per contract; no crash [SPEC] | text | P3 | [ ] | ✔ |
| ESC-B02 | Boundary | Escaped then real emphasis `\* *real*` | first literal, second italic span; offsets correct [SPEC span adjust] | text,formatting | P2 | [ ] | |
| ESC-M01 | Malformed | `\a` (escape non-special char) | behavior defined; likely literal `\a` [SPEC only \*\_\\] | text | P2 | [ ] | ✔ |
| ESC-RT01 | Round-trip | escaped literal round-trips | escape preserved [README "escaped literals"] | text | P2 | [ ] | |
| ESC-XSS01 | Security | `\<script\>` | escaped in HTML regardless | HTML | P0 | [ ] | |
| ESC-B03 | Boundary | Double-escaped `\\*bold*` | literal backslash + bold span [SPEC] | text,formatting | P3 | [ ] | ✔ |

---

## PREC — Precedence and Disambiguation Decision Tables

Force prefixes override natural rules; precedence order [SPEC Pass2 rules 1-23]. The core
ambiguity: an ALL-CAPS line can be Scene Heading, Transition, Character, or Action.

### Decision Table: ALL-CAPS line classification

Conditions: blank-before? / blank-after? / matches scene prefix? / ends in `TO:`? / next line dialogue?

| ID | Technique | Input scenario | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| PREC-D01 | Decision | Caps, scene prefix, blank after | SCENE_HEADING [FIO] | type | P1 | [ ] | |
| PREC-D02 | Decision | Caps, ends `TO:`, blank before+after | TRANSITION [FIO] | type | P1 | [ ] | |
| PREC-D03 | Decision | Caps, blank before, next line non-blank dialogue | CHARACTER [FIO] | type | P1 | [ ] | |
| PREC-D04 | Decision | Caps, blank before, blank after (nothing follows) | ACTION (orphan cue) [SPEC C3] | type | P1 | [ ] | |
| PREC-D05 | Decision | Caps, no blank before | ACTION (default) [FIO "when in doubt, Action"] | type | P1 | [ ] | |
| PREC-D06 | Decision | Caps ends `TO:` AND scene prefix `INT. CUT TO:` | which wins? define precedence [SPEC rule 16 vs 17 order] | type | P2 | [ ] | ✔ |
| PREC-P01 | Precedence | `.` vs `!` vs `@` vs `>` all combined nonsensically | first-matching force wins per rule order [SPEC rules 9-15] | type | P2 | [ ] | ✔ |
| PREC-P02 | Precedence | Boneyard beats everything: `/* .SCENE */` | inside boneyard, not scene [SPEC rule 1-3 first] | type | P1 | [ ] | |
| PREC-P03 | Precedence | Note-line vs section `[[# note]]` | NOTE (rule 6) before section (rule 10) [SPEC order] | type | P2 | [ ] | ✔ |
| PREC-P04 | Precedence | Page break vs synopsis `===` (rule 5 before 11) | PAGE_BREAK [SPEC order] | type | P1 | [ ] | |
| PREC-P05 | Precedence | Forced action `!` beats scene prefix `!INT. HOUSE` | ACTION [FIO, SPEC rule 9] | type | P1 | [ ] | |
| PREC-P06 | Precedence | `.` forced scene beats transition `.CUT TO:` | SCENE_HEADING [FIO disambiguation] | type | P1 | [ ] | |
| PREC-P07 | Precedence | `>text<` centered beats `>text` transition | CENTERED when trailing `<` present [SPEC rule 14 before 15] | type | P1 | [ ] | |
| PREC-P08 | Precedence | Lyrics `~` vs everything | LYRICS when leading `~` [SPEC rule 12] | type | P2 | [ ] | |
| PREC-D07 | Decision | `FADE IN:` (ends colon not TO:) | TRANSITION via special-case [SPEC D11] | type | P1 | [ ] | |
| PREC-D08 | Decision | Caps line that is also emphasis-only `**WORD**` | ACTION with bold span (not character) [FIO] | type | P2 | [ ] | ✔ |
| PREC-P09 | Precedence | `@` forces character even over dialogue-lookahead failure [SPEC C6] | type | P1 | [ ] | |
| PREC-D09 | Decision | Title-page mode active vs body: colon line ambiguity [SPEC A3] | metadata vs element | P1 | [ ] | ✔ |
| PREC-D10 | Decision | Mixed-case with scene prefix `Int. house` (title guard) | SCENE_HEADING case-insensitive [SPEC B3] | type | P1 | [ ] | |

---

## BLANK — Blank Line, Adjacency, Context Rules

"Fountain takes every carriage return as intent" [FIO]. Blank-before/after gate character,
scene, transition detection [CHANGELOG, SPEC].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| BLANK-01 | Boundary | Zero blank lines between two dialogue-y caps lines | second is dialogue not character [FIO] | types | P1 | [ ] | |
| BLANK-02 | Boundary | Exactly one blank between action and character | character recognized [FIO] | type | P1 | [ ] | |
| BLANK-03 | Boundary | Two+ blanks before character | still character; extra blanks preserved as structure [FIO] | type | P2 | [ ] | ✔ |
| BLANK-04 | Boundary | Trailing blank lines at EOF | no phantom elements; EOF counts as blank for transition [SPEC rule 17] | elements | P2 | [ ] | |
| BLANK-05 | Boundary | Leading blank lines before body (post title page) | skipped, no empty elements | elements | P2 | [ ] | ✔ |
| BLANK-06 | Adjacency | Scene heading with no blank after | degrades to ACTION [SPEC B2] | type | P1 | [ ] | |
| BLANK-07 | Adjacency | Transition with no blank after | ACTION [SPEC rule 17] | type | P2 | [ ] | ✔ |
| BLANK-08 | Adjacency | Character immediately followed by blank | orphan -> ACTION [SPEC C3] | type | P1 | [ ] | |
| BLANK-09 | Whitespace | Blank line that contains only spaces (not truly empty) | behavior: dialogue continuation vs block end (context-dependent) [SPEC Pass2 333-355] | structure | P1 | [ ] | ✔ |
| BLANK-10 | Whitespace | Blank line with exactly two trailing spaces in dialogue | 2-space continuation keeps block [FIO, SPEC] | structure | P2 | [ ] | ✔ |
| BLANK-11 | Boundary | Document that is only blank lines | empty document; `empty-document` warning [SPEC Validation] | validate,elements | P2 | [ ] | |
| BLANK-12 | Adjacency | Action paragraph accumulation across a single newline vs blank | single newline continues paragraph; blank splits [DOC parse error-handling] | count | P1 | [ ] | |

---

## INTER — Interaction / Pairwise Matrix

Element A abutting / nesting in / interrupting element B. Sampled at disambiguation-critical
cells (rationale in Self-Assessment).

| ID | Technique | Input pattern | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| INTER-01 | Adjacent | Scene -> Character -> Dialogue (canonical block) | 3 correct types [DOC parse] | types | P1 | [ ] | |
| INTER-02 | Adjacent | Character -> Parenthetical -> Dialogue | 3 types [DOC elem] | types | P1 | [ ] | |
| INTER-03 | Interrupt | Dialogue interrupted by Lyrics then resumes | CHAR,LYRICS,DIALOGUE [SPEC C8] | types | P2 | [ ] | ✔ |
| INTER-04 | Interrupt | Dialogue interrupted by standalone Note then resumes | CHAR,NOTE,DIALOGUE? (block continues) [SPEC C8] | types | P2 | [ ] | ✔ |
| INTER-05 | Interrupt | Dialogue interrupted by Scene heading | block ends, new scene [FIO] | types | P1 | [ ] | |
| INTER-06 | Nested | Emphasis inside dialogue inside dual dialogue | spans preserved through nesting | formatting | P2 | [ ] | ✔ |
| INTER-07 | Nested | Inline note inside dialogue line | stripped from dialogue text [SPEC rule 8] | text | P2 | [ ] | ✔ |
| INTER-08 | Nested | Boneyard inside a character block `/* */` | boneyard hidden, block integrity [SPEC E1] | types | P2 | [ ] | ✔ |
| INTER-09 | Adjacent | Section immediately before scene heading | SECTION, SCENE [DOC elem] | types | P2 | [ ] | |
| INTER-10 | Adjacent | Synopsis before scene heading | SYNOPSIS, SCENE [DOC elem] | types | P2 | [ ] | |
| INTER-11 | Adjacent | Two dialogue blocks -> dual dialogue pairing | one DUAL element [DOC elem] | type | P1 | [ ] | |
| INTER-12 | Adjacent | Transition -> Scene heading | TRANSITION, SCENE [QUICK] | types | P1 | [ ] | |
| INTER-13 | Adjacent | Action -> Transition -> Scene (FADE IN pattern) | correct 3 types [DOC parse] | types | P1 | [ ] | |
| INTER-14 | Interrupt | Page break inside a dialogue block | block ends at page break [FIO] | types | P2 | [ ] | ✔ |
| INTER-15 | Nested | Centered text containing emphasis | CENTERED with span [FIO] | formatting | P2 | [ ] | ✔ |
| INTER-16 | Adjacent | Character with extension then dual caret next block | dual + extension metadata [SPEC rule 20] | meta | P2 | [ ] | |
| INTER-17 | Interrupt | Note (multi-line) interrupting action accumulation | action splits around note [SPEC] | types | P2 | [ ] | ✔ |
| INTER-18 | Interrupt | Boneyard (multi-line) spanning a character->dialogue boundary | whole span hidden, no partial block [SPEC E4] | elements | P1 | [ ] | ✔ |
| INTER-19 | Adjacent | Lyrics block directly after scene heading (not in dialogue) | LYRICS standalone [FIO] | type | P2 | [ ] | |
| INTER-20 | Adjacent | Parenthetical with no character before it | ACTION (no context) [FIO] | type | P2 | [ ] | ✔ |
| INTER-21 | Nested | Scene number `#..#` adjacent to inline note `INT. X [[n]] #1#` | number + note both handled | text,meta | P3 | [ ] | ✔ |
| INTER-22 | Interrupt | Two-space dialogue-continuation line between two dialogue lines | empty DIALOGUE inserted [SPEC] | elements | P2 | [ ] | ✔ |
| INTER-23 | Adjacent | Title page directly followed by section `# Act I` (no scene) | metadata then SECTION | types | P2 | [ ] | |
| INTER-24 | Adjacent | Dialogue then action (character continuation detection) | `continuation` metadata on next same-char cue [SPEC rule 21] | meta | P2 | [ ] | ✔ |
| INTER-25 | Interrupt | Forced action `!` interrupting a dialogue block | ACTION, block ends [SPEC rule 9] | types | P2 | [ ] | |

---

## STATE — State-Transition and Re-entrancy

Parser states: title-page mode, in-note, in-boneyard, dialogue-block, action-accumulation.
Instance reuse [SPEC: "reset at the top of every parse()"].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| STATE-01 | Re-entrancy | Parse doc A (unclosed boneyard) then doc B (clean) with SAME parser | doc B unaffected; in_boneyard reset [SPEC state reset] | doc B elements | P0 | [ ] | |
| STATE-02 | Re-entrancy | Parse doc A with title page, then doc B without | doc B `metadata=={}` (no leak) [SPEC reset] | doc B metadata | P0 | [ ] | |
| STATE-03 | Re-entrancy | Parse same text twice; outputs identical | deterministic; `elements` equal [SPEC reset] | equality | P1 | [ ] | |
| STATE-04 | Re-entrancy | Parse doc A (unclosed note), then doc B | in_note reset; doc B correct [SPEC] | doc B | P0 | [ ] | |
| STATE-05 | Transition | title-page mode exit on first blank after a key | body parsing begins [SPEC Pass1] | elements | P1 | [ ] | |
| STATE-06 | Transition | title-page mode exit on scene-prefix line | body begins [SPEC Pass1] | elements | P1 | [ ] | |
| STATE-07 | Transition | dialogue-block enter on character, exit on blank | correct block boundaries [FIO] | types | P1 | [ ] | |
| STATE-08 | Transition | in-boneyard enter `/*`, exit on `*/` (mid-line) | correct exit [SPEC E2] | elements | P0 | [ ] | |
| STATE-09 | Transition | in-note enter `[[`, exit on `]]` (across lines) | single NOTE [SPEC rule 4] | element | P1 | [ ] | |
| STATE-10 | Re-entrancy | Two-thread scenario: separate parser per thread (documented) | no shared state [SPEC threads] | correctness | P2 | [ ] | ✔ |
| STATE-11 | Transition | action-accumulation flushed by blank line | separate ACTION elements [DOC parse] | count | P1 | [ ] | |
| STATE-12 | Idempotence | `parse(x)` then `validate(x)`: parse output byte-identical [SPEC Validation acceptance] | equality | P1 | [ ] | |
| STATE-13 | Re-entrancy | Reuse parser 100x in a loop | no accumulation, stable memory | memory | P2 | [ ] | |
| STATE-14 | Transition | dialogue continuation across two-space line then real blank | continuation then block end [SPEC] | structure | P2 | [ ] | ✔ |
| STATE-15 | Transition | line_number correctness across state changes | 1-based line numbers accurate [SPEC line_number] | line_number | P1 | [ ] | |
| STATE-16 | Re-entrancy | line_number does not carry over between parses | resets to 1-based each parse | line_number | P2 | [ ] | |

---

## XSS — Security / HTML Escaping (every dynamic render surface)

Element text is escaped via `html.escape(text, quote=True)` [SPEC HTMLRenderer]. Every
surface where user input reaches HTML is its own row. Payloads: `<script>alert(1)</script>`,
`"><img src=x onerror=alert(1)>`, `javascript:`, `</style>`, `"><` for attribute breakout.

| ID | Surface | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| XSS-01 | Action text | `<script>alert(1)</script>` action | escaped `&lt;script&gt;` [SPEC escape] | render()/render_page() | P0 | [ ] | |
| XSS-02 | Dialogue text | payload in dialogue | escaped | HTML | P0 | [ ] | |
| XSS-03 | Scene heading text | `INT. <script> - DAY` | escaped | HTML | P0 | [ ] | |
| XSS-04 | Character name | `@<img onerror>` forced char | escaped | HTML | P0 | [ ] | |
| XSS-05 | Character extension | `SARAH (<script>)` extension span | escaped inside `.fountain-character-extension` | HTML | P0 | [ ] | |
| XSS-06 | Scene number | `INT. X #<script>#` (if it parses as number) | escaped inside `.fountain-scene-number` | HTML | P0 | [ ] | |
| XSS-07 | Title (title page) | `Title: <script>alert(1)</script>` | escaped inside `<h1 class="fountain-title">` | HTML | P0 | [ ] | |
| XSS-08 | Author | `Author: "><script>` | escaped in `<p class="fountain-author">` | HTML | P0 | [ ] | |
| XSS-09 | Draft date | payload | escaped | HTML | P0 | [ ] | |
| XSS-10 | Custom title-page KEY | `<script>: value` (if it opens a key) | KEY escaped; class name derived from key must not break out [SPEC custom-field class] | HTML | P0 | [ ] | ✔ |
| XSS-11 | Custom title-page VALUE | `Custom Field: "><img onerror=alert(1)>` | value escaped | HTML | P0 | [ ] | |
| XSS-12 | CSS class from key | key `foo" onload="x` -> `class="fountain-custom-field {key}"` | key must not break out of the class attribute [SPEC render 164] | HTML raw | P0 | [ ] | ✔ |
| XSS-13 | Parenthetical | payload | escaped | HTML | P0 | [ ] | |
| XSS-14 | Transition | payload | escaped | HTML | P0 | [ ] | |
| XSS-15 | Centered | payload | escaped | HTML | P0 | [ ] | |
| XSS-16 | Lyrics | payload | escaped | HTML | P0 | [ ] | |
| XSS-17 | Dual dialogue left/right char + dialogue | payload in each | escaped | HTML | P0 | [ ] | |
| XSS-18 | Continuation `(CONT'D)` span | derived, but confirm char name escaped around it | escaped | HTML | P0 | [ ] | |
| XSS-19 | Emphasis content | `*<script>*` | escaped inside `<em>` | HTML | P0 | [ ] | |
| XSS-20 | Note (if rendered) | payload | not rendered by default; if shown, escaped [SPEC E5] | HTML | P0 | [ ] | |
| XSS-21 | Boneyard (if leaked) | payload | must NOT leak to fragment [SPEC E11] | HTML | P0 | [ ] | |
| XSS-22 | Section (if rendered) | payload | not rendered [SPEC E5] | HTML | P0 | [ ] | |
| XSS-23 | Synopsis (if rendered) | payload | not rendered [SPEC E5] | HTML | P0 | [ ] | |
| XSS-24 | Quote breakout | `"` in any text with `quote=True` | `&quot;` (attribute-safe) [SPEC escape] | HTML | P0 | [ ] | |
| XSS-25 | Fragment vs page parity | same payload in `render()` and `render_page()` | both escape identically | both | P0 | [ ] | |
| XSS-26 | to_html() convenience | payload via `document.to_html()` | escaped (delegates to render_page) [SPEC] | HTML | P0 | [ ] | |
| XSS-27 | Ampersand handling | raw `&` and `&amp;` in text | `&` -> `&amp;`, no double-escape corruption | HTML | P1 | [ ] | ✔ |
| XSS-28 | Unicode/entity smuggling | `&#60;script&#62;` literal in source | treated as literal text, escaped, not decoded | HTML | P1 | [ ] | ✔ |
| XSS-29 | to_json escaping | payload through `to_json()` | valid JSON, properly string-escaped [SPEC to_json] | JSON parse | P1 | [ ] | |
| XSS-30 | Fountain round-trip injection | payload survives to Fountain output without becoming markup | text preserved literally | Fountain | P1 | [ ] | ✔ |

---

## PERF — Performance / Complexity / DoS

Docs claim "100+ pages in milliseconds" and "streaming, line by line" [DOC parse]. Adversarial
inputs target regex backtracking and quadratic assembly. Complexity expectation: **O(n)** in
input size for all.

| ID | Technique | Input shape | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| PERF-01 | Backtracking | Long line of alternating `*a*a*a...` (10k) | linear time; no ReDoS in emphasis regex | wall time | P0 | [ ] | |
| PERF-02 | Backtracking | Long run of `[[[[[[...` (unclosed note delimiters) | no catastrophic backtracking | time | P0 | [ ] | |
| PERF-03 | Backtracking | Long run of `/*/*/*...` | linear | time | P0 | [ ] | |
| PERF-04 | Delimiter run | 100k consecutive `*` | bounded time/memory | time,mem | P0 | [ ] | |
| PERF-05 | Nesting | `***`x1000 then `***`x1000 | no exponential | time | P0 | [ ] | |
| PERF-06 | Huge input | 10 MB screenplay | completes; memory ~O(n) | time,mem | P1 | [ ] | |
| PERF-07 | Many same-type lines | 100k consecutive action lines | linear assembly, no quadratic string concat | time | P1 | [ ] | ✔ |
| PERF-08 | Many blank lines | 1M blank lines | bounded; no per-blank element explosion | time,mem | P1 | [ ] | |
| PERF-09 | Long single line | one 5 MB line, no newline | handled without quadratic scan | time | P1 | [ ] | |
| PERF-10 | Deep sections | 100k `#`-depth on one line | bounded level computation | time | P2 | [ ] | ✔ |
| PERF-11 | Unclosed boneyard huge | `/*` + 1M lines, no close | linear skip to EOF | time | P1 | [ ] | |
| PERF-12 | Scene-number regex | `#` + 100k chars + `#` | bounded number extraction | time | P2 | [ ] | |
| PERF-13 | Title page flood | 100k title-page keys | bounded metadata dict build | time,mem | P2 | [ ] | |
| PERF-14 | Dual pairing | 10k dual-caret characters | pairing post-pass stays linear/near-linear | time | P2 | [ ] | ✔ |
| PERF-15 | Render scale | render_page() of 100k elements | linear render, single style block | time | P1 | [ ] | |
| PERF-16 | to_json scale | to_json() of large doc | completes, valid JSON | time | P2 | [ ] | |

---

## FUZZ — Robustness / Fuzzing Invariants

Property-based invariants that must hold for arbitrary input [SPEC "never raises on malformed
markup"].

| ID | Invariant | Input class | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| FUZZ-01 | No crash | Any random byte-ish string (valid UTF-8) | `parse()` never raises [SPEC] | no exception | P0 | [ ] | |
| FUZZ-02 | No crash | All control chars (`\x00`-`\x1f`) | no raise | no exception | P0 | [ ] | |
| FUZZ-03 | No infinite loop | Adversarial delimiter combos | terminates within timeout | timeout | P0 | [ ] | |
| FUZZ-04 | No data loss | Every source char rendered OR intentionally dropped (note/boneyard/section/synopsis) | account for all input chars | diff | P0 | [ ] | ✔ |
| FUZZ-05 | Idempotent render | `render(doc) == render(doc)` twice | identical output | equality | P1 | [ ] | |
| FUZZ-06 | Idempotent parse | `parse(x).elements == parse(x).elements` | deterministic | equality | P1 | [ ] | |
| FUZZ-07 | Round-trip stability | `parse(render_fountain(parse(x)))` element types stable [SPEC A4] | type list | P1 | [ ] | ✔ |
| FUZZ-08 | Render never raises | render/render_page/get_css on any parsed doc | no exception | no exception | P1 | [ ] | |
| FUZZ-09 | to_dict/to_json total | serialization never raises on any doc (incl dual nesting) | no exception, valid JSON | JSON parse | P1 | [ ] | |
| FUZZ-10 | Line numbers valid | every element `line_number >= 1` and within input | invariant | P2 | [ ] | |
| FUZZ-11 | Span bounds valid | every FormatSpan `0 <= start <= end <= len(text)` | invariant | P1 | [ ] | |
| FUZZ-12 | Span non-crossing (post-fix) | spans map cleanly to nested tags [SPEC D6] | no dup text | P1 | [ ] | ✔ |
| FUZZ-13 | Metadata JSON-safe | all metadata values in `MetadataValue` union [SPEC CR-2] | type check | P2 | [ ] | |
| FUZZ-14 | Empty-input stability | `""`, `"\n"`, `"\n\n\n"`, `" "`, `"\t"` | no crash; empty or whitespace doc | elements | P1 | [ ] | ✔ |
| FUZZ-15 | Escape safety | random backslash placements | no crash, no index error in span adjust | no exception | P1 | [ ] | |
| FUZZ-16 | Reparse convergence | `render_fountain` output re-parses to same types (2nd gen == 3rd gen) | fixpoint after 1 iteration | equality | P2 | [ ] | ✔ |

---

## RT — Round-Trip Fidelity

`FountainRenderer.render()` back to Fountain. Preserved: types, metadata, scene numbers,
extensions, forced markers, order, emphasis (incl nesting/escapes). Normalized: multiple
blanks -> one; capitalization kept; boneyard dropped [DOC render RT, README].

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| RT-01 | Preserve | Full script (scene+char+dialogue+paren) | all types survive parse->Fountain->parse [DOC render RT] | type list | P1 | [ ] | |
| RT-02 | Preserve | Title page metadata | keys/values survive [DOC render] | metadata | P1 | [ ] | |
| RT-03 | Preserve | Scene number `#1#` | survives [DOC render] | meta | P1 | [ ] | |
| RT-04 | Preserve | Character extension `(V.O.)` | survives [DOC render] | meta | P1 | [ ] | |
| RT-05 | Preserve | Forced scene/action/transition markers | restored [DOC render] | text | P1 | [ ] | |
| RT-06 | Preserve | Blank lines separate blocks; CHARACTER not degraded to ACTION [SPEC A4] | types | P0 | [ ] | |
| RT-07 | Preserve | Dual dialogue reproduces DUAL element [SPEC A4b] | type | P0 | [ ] | |
| RT-08 | Preserve | Lyrics no trailing tilde accretion [SPEC A4c] | text | P1 | [ ] | |
| RT-09 | Preserve | Inline emphasis `**bold**` re-emitted [README] | text | P1 | [ ] | |
| RT-10 | Preserve | Nested emphasis re-emitted [README] | text | P1 | [ ] | |
| RT-11 | Preserve | Escaped literal `\*` re-emitted [README] | text | P2 | [ ] | |
| RT-12 | Normalize | Multiple consecutive blanks collapse to one [DOC render RT] | structure | P2 | [ ] | |
| RT-13 | Drop | Boneyard dropped from Fountain output [DOC render RT] | absent | P2 | [ ] | |
| RT-14 | Preserve | Section hashes and level restored [SPEC FountainRenderer] | text | P2 | [ ] | |
| RT-15 | Preserve | Synopsis `=` restored | text | P2 | [ ] | |
| RT-16 | Preserve | Standalone note restored | text | P2 | [ ] | ✔ |
| RT-17 | Idempotent | 2nd round-trip == 1st (fixpoint) | equality | P2 | [ ] | ✔ |
| RT-18 | Parity | HTMLRenderer and FountainRenderer agree on author/authors [SPEC OQ10] | both | P1 | [ ] | |
| RT-19 | Element-count | `len(doc1.elements)==len(doc2.elements)` for forced-action script [DOC render RT doctest] | count | P1 | [ ] | |
| RT-20 | Preserve | Page break `===` restored | text | P2 | [ ] | |

---

## WS — Whitespace, Line Endings, Encoding, Unicode

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| WS-01 | Line endings | CRLF (`\r\n`) line separators | parsed same as LF; no stray `\r` in text | text | P1 | [ ] | ✔ |
| WS-02 | Line endings | CR-only (`\r`) (classic Mac) | handled or documented; no data loss | elements | P2 | [ ] | ✔ |
| WS-03 | Line endings | Mixed CRLF/LF in one file | consistent parse | elements | P2 | [ ] | ✔ |
| WS-04 | BOM | UTF-8 BOM (`﻿`) at start | BOM stripped; first line still detected as title/scene | metadata | P1 | [ ] | ✔ |
| WS-05 | Trailing ws | Trailing spaces on element lines | stripped from text (except action leading) [SPEC rule 23] | text | P2 | [ ] | |
| WS-06 | Leading ws | Tabs vs spaces indent in non-action | ignored [FIO indenting] | text | P2 | [ ] | |
| WS-07 | Tabs in action | tab -> 4 spaces at parse; raw kept per A5 contract | tension: CHANGELOG says parse-time convert, SPEC A5 says raw kept [conflict] | text | P1 | [ ] | ✔ |
| WS-08 | Encoding | parse_file on non-UTF-8 file | raises `UnicodeDecodeError` [SPEC parse_file] | exception | P1 | [ ] | |
| WS-09 | Encoding | parse_file on valid UTF-8 | reads correctly [SPEC] | metadata | P1 | [ ] | |
| WS-10 | Unicode text | Accented chars `Café`, `naïve` in dialogue | preserved; correct span offsets around them | text,spans | P1 | [ ] | |
| WS-11 | Multi-byte | CJK `内景` in action | preserved; length by code points not bytes | text | P1 | [ ] | ✔ |
| WS-12 | Emoji | Emoji in dialogue `Hi 👋` | preserved; span offsets correct (astral chars) | text,spans | P1 | [ ] | ✔ |
| WS-13 | Combining marks | `e` + combining acute vs precomposed `é` | offsets consistent; no split inside grapheme mishap | spans | P2 | [ ] | ✔ |
| WS-14 | Zero-width | ZWSP/ZWJ inside a caps line | does it break character detection? define | type | P2 | [ ] | ✔ |
| WS-15 | RTL | Hebrew/Arabic dialogue | preserved; escaping still correct | text,HTML | P2 | [ ] | ✔ |
| WS-16 | Homoglyphs | Cyrillic `А` in `INT.`-like line | not confused with ASCII scene prefix | type | P3 | [ ] | ✔ |
| WS-17 | Unicode uppercase | Non-ASCII all-caps `ÜBER` as character | recognized? define (spec is ASCII-centric) | type | P2 | [ ] | ✔ |
| WS-18 | Emphasis offsets | `*café*` italic span over accented word | span covers `café` exactly | spans | P1 | [ ] | |
| WS-19 | Escape + unicode | `\*café\*` | literal with unicode; offsets ok | text | P2 | [ ] | |
| WS-20 | NBSP | non-breaking space `\xa0` as "blank" line | treated as content not blank line | structure | P2 | [ ] | ✔ |
| WS-21 | Form feed / vertical tab | `\x0c`, `\x0b` in text | no crash; defined handling | no crash | P3 | [ ] | ✔ |
| WS-22 | Null byte | `\x00` in text | no crash; preserved or escaped | no crash | P1 | [ ] | ✔ |
| WS-23 | Surrogate/invalid | lone surrogate in string input | no crash on parse or JSON dump | no exception | P2 | [ ] | ✔ |
| WS-24 | Trailing newline | file with/without final newline | same element set | elements | P2 | [ ] | |
| WS-25 | Whitespace-only doc | `"   \n\t\n  "` | empty document; no phantom action | elements | P1 | [ ] | ✔ |
| WS-26 | Unicode in title-page key | `Título:` opens page; key casefolded | metadata key | P2 | [ ] | ✔ |
| WS-27 | Wide chars in HTML | emoji in `render_page()` | UTF-8 output valid, escaped where needed | HTML | P2 | [ ] | |
| WS-28 | Line-number with multibyte | line_number correct when earlier lines have multibyte chars | line_number | P2 | [ ] | |

---

## DIAG — Diagnostics / Validation API

`FountainParser.validate(text) -> list[ValidationIssue]`; `ValidationIssue(line_number,
severity, code, message)` [SPEC Validation API]. Note: not yet shipped, so these are
spec-forward. Parity: `parse()` output byte-identical with/without prior `validate()`.

| ID | Technique | Input | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| DIAG-01 | Diagnostic | Unclosed `/*` before EOF | one `unclosed-boneyard` error at opening line number [SPEC] | validate() | P1 | [ ] | |
| DIAG-02 | Diagnostic | Unclosed `[[` before EOF | one `unclosed-note` error at opening line [SPEC] | validate() | P1 | [ ] | |
| DIAG-03 | Diagnostic | Orphan cue (caps then blank) | `orphan-character-cue` warning at cue line [SPEC] | validate() | P1 | [ ] | |
| DIAG-04 | Diagnostic | Empty document | `empty-document` warning [SPEC] | validate() | P2 | [ ] | |
| DIAG-05 | Clean | Well-formed script | `validate()==[]` [SPEC acceptance] | validate() | P1 | [ ] | |
| DIAG-06 | Line accuracy | Multi-line preamble then unclosed boneyard at line 20 | `line_number==20` (1-based) [SPEC] | line_number | P1 | [ ] | |
| DIAG-07 | Severity | error vs warning literal values | `Literal["error","warning"]` [SPEC] | field | P2 | [ ] | |
| DIAG-08 | Parity | `parse(x)` bytes identical with/without prior `validate(x)` [SPEC acceptance] | equality | P1 | [ ] | |
| DIAG-09 | Frozen | `ValidationIssue` is a frozen dataclass (immutable) [SPEC] | mutation raises | P2 | [ ] | |
| DIAG-10 | Export | `ValidationIssue` importable from `fountain` top-level [SPEC] | import | P2 | [ ] | |
| DIAG-11 | Code stability | `code` strings are stable identifiers [SPEC contract] | value | P2 | [ ] | |
| DIAG-12 | Multiple issues | doc with unclosed note AND orphan cue | both issues returned, correct lines | list | P2 | [ ] | |
| DIAG-13 | No false positive | closed boneyard/note | no unclosed-* issue | list | P1 | [ ] | |
| DIAG-14 | Ordering | issues ordered (by line?) | defined order [SPEC unspecified] | order | P3 | [ ] | ✔ |
| DIAG-15 | Return type | `validate` returns `list[ValidationIssue]` | type | P2 | [ ] | |
| DIAG-16 | Empty vs whitespace | `validate("")` vs `validate("  ")` | both empty-document warning? define | list | P2 | [ ] | ✔ |
| DIAG-17 | Line-number for inline defects | unclosed note starting mid-line | line of the `[[` [SPEC] | line_number | P2 | [ ] | ✔ |
| DIAG-18 | Growth contract | new codes may be added; existing not removed [SPEC "each code string is contract"] | n/a (doc) | P3 | [ ] | ✔ |

---

## API — Public API Contract

Exports [SPEC Package Exports]: `FountainParser, FountainDocument, ElementType,
FountainElement, FormatType, MetadataValue`, plus promoted `HTMLRenderer, FountainRenderer`,
plus `ValidationIssue`. Python 3.10-3.14 [PYPROJ].

| ID | Technique | Target | Expected | Observe | Prio | Status | Amb |
|---|---|---|---|---|---|---|---|
| API-01 | Contract | `from fountain import FountainParser, FountainDocument, ElementType, FountainElement, FormatType, MetadataValue` | all importable [SPEC] | import | P1 | [ ] | |
| API-02 | Contract | `from fountain import HTMLRenderer, FountainRenderer` (promoted) | importable [SPEC OQ7 ruling] | import | P1 | [ ] | ✔ |
| API-03 | Contract | `__all__` exact membership | matches spec list [SPEC] | `fountain.__all__` | P2 | [ ] | ✔ |
| API-04 | Contract | `FountainParser()` no-arg constructor | works [SPEC] | construct | P1 | [ ] | |
| API-05 | Contract | `parse(text: str) -> FountainDocument` | return type [SPEC] | type | P1 | [ ] | |
| API-06 | Contract | `parse_file(filepath) -> FountainDocument`, UTF-8 | reads + delegates [SPEC] | type | P1 | [ ] | |
| API-07 | Error | `parse_file` on missing file | `FileNotFoundError` propagates [SPEC] | exception | P1 | [ ] | |
| API-08 | Error | `parse_file` on bad encoding | `UnicodeDecodeError` [SPEC] | exception | P1 | [ ] | |
| API-09 | Contract | `ElementType` has exactly 15 members | count==15 [SPEC] | enum | P1 | [ ] | |
| API-10 | Contract | `TITLE_PAGE` never emitted as element | absent from any parse [SPEC] | elements | P2 | [ ] | |
| API-11 | Contract | `FountainElement` fields: type, text, formatting, line_number, metadata | dataclass fields [SPEC] | fields | P1 | [ ] | |
| API-12 | Contract | `metadata=None` normalized to `{}` in `__post_init__` [SPEC] | value | P2 | [ ] | |
| API-13 | Contract | `FormatSpan(start, end, format_type)` NamedTuple | shape [SPEC] | namedtuple | P2 | [ ] | |
| API-14 | Contract | `FormatType == Literal["bold","italic","underline","bold_italic"]` | values [SPEC] | literal | P2 | [ ] | |
| API-15 | Contract | `FountainDocument(elements, metadata=None)` | constructs; metadata `{}` if None [SPEC] | construct | P2 | [ ] | |
| API-16 | Method | `to_dict()` shape `{metadata, elements[]}` with element keys type/text/formatting/line_number/metadata [SPEC] | dict | P1 | [ ] | |
| API-17 | Method | `to_json()` == `json.dumps(to_dict(), indent=2)` [SPEC] | str/parse | P1 | [ ] | |
| API-18 | Method | `get_characters()` uppercased, `^` stripped, sorted, unique [SPEC] | list | P1 | [ ] | |
| API-19 | Method | `get_scenes()` scene texts in order [SPEC] | list | P1 | [ ] | |
| API-20 | Method | `get_statistics()` has total_elements, characters, scenes, + `{type}_count` for 15 types [SPEC] | dict keys | P1 | [ ] | |
| API-21 | Method | `to_html()` == `HTMLRenderer().render_page(self)` [SPEC] | equality | P1 | [ ] | |
| API-22 | DOC bug | docs use `get_character_names()` but API is `get_characters()` [QUICK/DOC parse vs SPEC/CHANGELOG] | one raises AttributeError | P1 | [ ] | ✔ |
| API-23 | Empty | `parse("")` -> doc with `elements==[]`, `metadata=={}` | values | P1 | [ ] | |
| API-24 | None | `parse(None)` | TypeError (str expected) or defined | exception | P2 | [ ] | ✔ |
| API-25 | Reuse | parser instance reused across parses (no state leak) [SPEC] | correctness | P1 | [ ] | |
| API-26 | Version | import + parse on Python 3.10 and 3.14 | works both [PYPROJ] | smoke | P1 | [ ] | |
| API-27 | py.typed | package ships `py.typed`; downstream mypy sees types [PYPROJ, CHANGELOG] | file present | P2 | [ ] | |
| API-28 | Zero deps | no runtime dependencies [PYPROJ dependencies==[]] | metadata | P2 | [ ] | |
| API-29 | CSS API | `get_css()` returns raw CSS, no `<style>` tags [DOC render doctest] | str | P2 | [ ] | |
| API-30 | Render modes | `render()` has no `<style>`; `render_page()` embeds it [SPEC/DOC] | HTML | P2 | [ ] | |
| API-31 | MetadataValue | `FountainElement.metadata` annotated `dict[str, MetadataValue] | None` [SPEC CR-2] | mypy | P2 | [ ] | ✔ |
| API-32 | Element mutability | `FountainElement` is mutable dataclass (docs say "immutable"; SPEC says mutable) [DOC parse perf vs SPEC] | attr set | P2 | [ ] | ✔ |

---

## AMB — Documented Ambiguities and Divergences (review-focus list)

Places where "Expected" is a judgment call. These are the rows a reviewer should scrutinize
first; each cites where the divergence is documented.

| ID | Area | Ambiguity / divergence | Documented at | Prio | Status |
|---|---|---|---|---|---|
| AMB-01 | Title page detection | Colon line opens a key only if recognized field or capitalized label with value/continuation; `FADE IN:`/lowercase labels excluded | [SPEC A3, DOC parse] | P1 | [ ] |
| AMB-02 | FADE IN/OUT | Special-cased as transitions though they don't end in `TO:` | [SPEC D11, DOC parse] | P1 | [ ] |
| AMB-03 | Lyrics/notes in dialogue | Do not close the dialogue block | [SPEC C8, DOC parse] | P2 | [ ] |
| AMB-04 | Inline note asymmetry | Inline note content stripped and unrecoverable; standalone kept verbatim | [SPEC E9, DOC parse] | P2 | [ ] |
| AMB-05 | `==` synopsis | `== two` yields SYNOPSIS `= two`, deemed valid not a defect | [SPEC E12 refuted] | P2 | [ ] |
| AMB-06 | First-line `FADE IN:` | Consumed as title-page key; documented workaround (precede with action) | [DOC parse] | P2 | [ ] |
| AMB-07 | `> FADE IN:` first line | Captured as key `> fade in` | [DOC parse] | P2 | [ ] |
| AMB-08 | Multi-line title value shape | List vs `<br>`-joined string; A1 in flight | [SPEC A1] | P2 | [ ] |
| AMB-09 | author vs authors | Both must render; renderers must agree | [SPEC OQ10] | P1 | [ ] |
| AMB-10 | Tabs in action | CHANGELOG says converted at parse; SPEC A5 says raw kept, converted at render. Contradiction | [CHANGELOG vs SPEC A5] | P1 | [ ] |
| AMB-11 | `get_character_names` vs `get_characters` | Docs and API name disagree | [QUICK/DOC parse vs SPEC] | P1 | [ ] |
| AMB-12 | Element mutability claim | DOC parse says "immutable"; SPEC says mutable dataclass | [DOC parse vs SPEC] | P2 | [ ] |
| AMB-13 | Whitespace-only "blank" line | Space-only line: dialogue continuation vs block end vs action | [SPEC Pass2 333-355] | P1 | [ ] |
| AMB-14 | Custom title-page key -> CSS class | Key interpolated into `class="fountain-custom-field {key}"`; injection/validity unclear | [SPEC render 164] | P0 | [ ] |
| AMB-15 | Unicode uppercase / prefixes | Spec is ASCII-centric; non-ASCII caps and homoglyph prefixes undefined | (none; derived) | P2 | [ ] |
| AMB-16 | CRLF/CR/BOM | Line-ending and BOM normalization not documented | (none; derived) | P1 | [ ] |
| AMB-17 | Empty delimiters | `[[]]`, `/**/`, `()`, `><`, `**`, `~` alone: behavior underspecified | [FIO silent] | P2 | [ ] |
| AMB-18 | Boneyard round-trip drop | Boneyard silently dropped from Fountain output (writer tool) | [DOC render RT] | P2 | [ ] |

---

## Coverage Self-Assessment

### Claimed Exhaustive

- **Element conformance.** All 15 `ElementType` members are covered across the four input
  classes (valid / boundary / forced / malformed) and, where each applies, across parse /
  HTML fragment / HTML page / Fountain round-trip / diagnostics surfaces. Every element has
  a dedicated section.
- **XSS surface enumeration.** Every dynamic-render surface named in `spec.md` (element text
  for each type, character name, extension, scene number, title-page key and value, custom
  key, derived CSS class, fragment vs page, `to_html`, `to_json`) is an individual row
  (XSS-01..30). This is the single highest-value section and is meant to be complete, not
  sampled.
- **Boundary counts.** The off-by-one delimiter families (`=`/`==`/`===`, `*`/`**`/`***`,
  `_`, `#` depth, `[`/`[[`, `/*`/`*/`) each have explicit boundary rows.
- **Known-defect regression net.** Every `spec.md` requirement ID (A1..E13) and carried
  ambiguity (A3, C8, D11, E9) has at least one row that encodes its acceptance criterion.

### Sampled, Not Exhaustive (with rationale)

- **Interaction matrix (INTER).** The full cube is 15 elements x 15 elements x
  {adjacent, nested, interrupting} ~= 675 raw cells, and most are degenerate or
  structurally impossible (e.g. a page break "nested in" a scene number). INTER samples the
  ~25 cells where classification actually flips based on neighbors (dialogue-block
  interruption, dual pairing, force-prefix vs context, boneyard/note spanning a block
  boundary). Rationale: bugs cluster at state-transition edges, not at inert adjacencies.
- **Fuzzing (FUZZ).** Invariants are enumerated exhaustively, but the input corpus behind
  each is generative and sampled at runtime (random UTF-8, control chars, delimiter storms).
  The property is the oracle, not any single input.
- **Performance (PERF).** Input shapes are chosen to hit the specific complexity risks
  (regex backtracking, quadratic string assembly, per-line element explosion). Exact
  thresholds (what wall-clock counts as a failure) are left for the reviewer to set against
  the "milliseconds for 100+ pages" claim in `docs/source/user-guide/parsing.rst`.
- **Unicode (WS).** Representative characters per category (accented, CJK, emoji, combining,
  RTL, zero-width, homoglyph, null). Not every Unicode block; the risk is offset/escaping
  logic, which a handful of representatives exercises.

### Inherently Uncertain (spec ambiguities)

Collected in section AMB. The oracle for each is a judgment call and should be confirmed with
the maintainer before the corresponding test is treated as authoritative. AMB-10
(tabs-in-action: CHANGELOG contradicts SPEC A5) and AMB-11 (`get_character_names` vs
`get_characters`) and AMB-14 (custom key to CSS class injection) are outright doc/spec
contradictions and are the most likely to have a wrong test oracle or a real bug behind them.

### Known Gaps a Reviewer Must Fill

1. **Exact method signatures the docs do not pin down.** `validate()` is spec'd but not yet
   shipped; the real `ValidationIssue` field order, the concrete `code` string set beyond the
   initial four, and issue ordering are unverified from docs alone (DIAG-11, DIAG-14, DIAG-18).
2. **`get_character_names` vs `get_characters`.** The docs (`quickstart.rst`,
   `user-guide/parsing.rst`) call a method the API contract does not list. One of them is
   wrong; a reviewer with source access must resolve which (API-22, AMB-11). Until then the
   test oracle is "exactly one of these names exists."
3. **Element-count oracles in doctests.** Several docs assert precise counts (e.g. the
   `FADE IN:` sample yields 6 elements; the coffee-shop quickstart). These are usable oracles
   but were written against the current implementation; a black-box reviewer cannot confirm
   they match the spec's intent without running them.
4. **Tabs-in-action final behavior.** AMB-10: whether the tab is stored raw (SPEC A5) or
   converted at parse (CHANGELOG). Both a parse-surface and a render-surface assertion are
   staged; the reviewer must pick the authoritative one.
5. **Whitespace-only line semantics.** AMB-13: the space-only line is overloaded (dialogue
   two-space continuation vs block terminator vs action). The exact trigger (is it precisely
   two spaces, or any non-empty whitespace?) is not derivable from the public docs with
   confidence.
6. **Custom title-page key to CSS class name.** AMB-14 / XSS-12: whether an arbitrary key can
   break out of the `class="fountain-custom-field {key}"` attribute is a genuine security
   question the docs do not answer; requires either a source read or a live probe.
7. **Line-ending and BOM normalization.** AMB-16: no doc states CRLF/CR/BOM handling; the
   plan assumes LF-equivalence and BOM-stripping as the desired behavior, which needs
   confirmation.
8. **Performance thresholds.** No numeric SLA is documented beyond "milliseconds"; PERF rows
   assert asymptotic behavior (linear, no ReDoS) rather than absolute times, which the
   reviewer should quantify for a real gate.
