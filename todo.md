# fountain-py 0.1.0: TODO

Read `handoff.md`, then `plan.md`. Target version 0.1.0. No 0.2.0.
Each step is TDD: failing test first, then the minimal fix, then `just test` clean.

## Section 1: Python Floor and Type System
- [x] 1.1 Move the Python floor to 3.10 in pyproject (requires-python, classifiers, ruff py310, mypy 3.10)
- [x] 1.2 Update the CI matrix to 3.10 through 3.14
- [x] 1.3 Modernize typing to `X | None` and apply `MetadataValue` to `FountainElement.metadata` (CR-2)

## Section 2: Package API Surface
- [x] 2.1 Promote `HTMLRenderer` and `FountainRenderer` to the top-level `__all__` (Open Question 7)
- [x] 2.2 Fix ABOUTME headers to single-line form (CR-1)

## Section 3: Validation API (Required for 0.1.0)
- [x] 3.1 Add the `ValidationIssue` frozen dataclass
- [x] 3.2 Implement `FountainParser.validate()` with the four initial diagnostics
- [x] 3.3 Export `ValidationIssue` from the package top level

## Section 4: Compliance Group E: Boneyard, Notes, Sections
- [x] 4.1 E2: boneyard close with trailing text ends the boneyard
- [x] 4.2 E3: single-line boneyard with trailing text does not swallow the document
- [x] 4.3 E4: mid-line boneyard opener does not leak interior lines
- [x] 4.4 E1: mid-line `/* ... */` stripped from action and dialogue text
- [x] 4.5 E11: boneyard content never ships in HTML fragments
- [x] 4.6 E5: sections, synopses, and notes hidden by default (Open Question 3, mechanics)
- [x] 4.7 E13: a `[[ ]]`-bounded line with middle text is not one NOTE
- [x] 4.8 E6 and E7: two-space vs blank line inside a note
- [x] 4.9 E8: a two-space note line injects no empty DIALOGUE element
- [ ] 4.10 E10: a lone `]` inside a note does not break recognition

## Section 5: Compliance Group A: Title Page and Whitespace
- [ ] 5.1 A1: multi-line title page values preserve line structure
- [ ] 5.2 A2: title page continuation requires indentation; indented colons stay values
- [ ] 5.3 A4: blank lines survive parse and FountainRenderer round trip
- [ ] 5.4 A4b: dual dialogue survives the Fountain round trip
- [ ] 5.5 A4c: lyrics round-trip without accreting delimiters
- [ ] 5.6 A5 and D10: tabs and space indentation visible in HTML
- [ ] 5.7 Open Question 10: both author and authors render; the two renderers agree

## Section 6: Compliance Group B: Scene Headings
- [ ] 6.1 B1: space-form scene heading prefixes recognized
- [ ] 6.2 B2: a natural scene heading requires a blank line after it
- [ ] 6.3 B3: case-insensitive title-page guard that accepts the space form
- [ ] 6.4 B4: scene numbers restricted to alphanumerics, dashes, and periods

## Section 7: Compliance Group C: Characters and Dialogue
- [ ] 7.1 C1: punctuated uppercase cues recognized
- [ ] 7.2 C2: digit-first cues with at least one letter
- [ ] 7.3 C3: a blank line immediately after a cue disqualifies it
- [ ] 7.4 C4: an all-caps line after a cue is dialogue
- [ ] 7.5 C5: trailing caret on a forced character creates dual dialogue
- [ ] 7.6 C6: `@` forces CHARACTER unconditionally
- [ ] 7.7 C7: forced characters get extension extraction

## Section 8: Compliance Group D: Transitions and Emphasis
- [ ] 8.1 D1: trailing spaces after the colon defeat a transition
- [ ] 8.2 D2: uppercase lines ending in `TO:` with punctuation are transitions
- [ ] 8.3 D4: emphasis delimiters stripped and spans cover only the content
- [ ] 8.4 D5: the keypad escape example renders correctly
- [ ] 8.5 D6: nested emphasis does not duplicate text
- [ ] 8.6 D7: bold and underline get the italic delimiter-adjacent-space guards
- [ ] 8.7 D8: span offsets computed against stored text including indentation
- [ ] 8.8 D9: forced action retains indentation after the `!`

## Section 9: Documented Contract Ambiguities
- [ ] 9.1 A3: title page detection heuristic pinned and documented
- [ ] 9.2 C8: lyrics inside a dialogue block end the block, pinned and documented
- [ ] 9.3 D11: FADE IN/FADE OUT natural transitions documented as a deliberate extension
- [ ] 9.4 E9: mid-line notes removed without a trace, documented

## Section 10: Documentation Truth-Up
- [ ] 10.1 Open Question 2: the compliance claim stands because it is now true
- [ ] 10.2 Open Question 4: `FountainElement.text` docstring made accurate
- [ ] 10.3 Open Question 5: round-trip docs state the real fidelity
- [ ] 10.4 Open Question 6: CHANGELOG tab claim reworded
- [ ] 10.5 Open Question 3: hidden-by-default docs and docstrings agree

## Section 11: Tooling Cleanup
- [ ] 11.1 CR-3: remove dangling pre-commit recipes and references

## Section 12: Path to PyPI
- [ ] 12.1 CI dependency install fix (`uv sync --dev`) and build verification (wheel contents, Sphinx doctest)
- [ ] 12.2 Harden the publish workflow (test gate, artifact upload/download, environment, trusted publishing)
- [ ] 12.3 Add the TestPyPI dry-run workflow (`test-publish.yml`, workflow_dispatch)
- [ ] 12.4 Local end-to-end verification (build, clean-venv install, smoke test, `just test`, cleanup)

## Release Mechanics (Human-Gated, Mason only)
- [ ] Merge `init-version` to `main` (Mason merges; agents never do)
- [ ] Tag `v0.1.0`, create the GitHub Release
- [ ] Let the gated publish workflow run
- [ ] Verify the PyPI page and `pip install fountain-py`
