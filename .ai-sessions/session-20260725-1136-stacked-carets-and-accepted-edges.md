# Session Summary: Stacked Carets + Accepted Low-Severity Edges (Review 2, Fix 9)

**Date**: 2026-07-25
**Model**: Opus 4.8 (1M)

## Context

Final batch of the second review's low-severity findings.

## Key Actions (fixed)

- Stacked carets: `MARY^^^` fell through to action and swallowed the dialogue. Made the
  dual-cue caret anchor accept one-or-more carets (`\^+`) in `DUAL_CHARACTER_PATTERN` and
  `CHARACTER_EXTENSION_PATTERN`, and made the forced `@name^^^` strip all trailing carets.
  A stacked-caret cue now pairs as dual dialogue (or degrades to a plain character with no
  preceding cue), never swallowing the following line.

## Tests

- Added `test_stacked_carets_parse_as_dual_cue`.
- Full gate green: 313 pytest, doctests, ruff/mypy/format clean.

## Accepted as-is (documented, not defects)

- **Redundant nested emphasis tags** on pathological unbalanced input (`****x****` ->
  `<strong><em><em>x</em></em></strong>`): the HTML is well-formed and renders identically
  to the clean form; the redundancy only appears on malformed delimiter runs. Any dedup
  splits tags in the fuzzed-clean (~25k cases) render path, so it is left as-is.
- **Multi-line parenthetical** (`(beat and\nlong pause)`): kept as two dialogue lines. The
  text is preserved (no data loss), single-line parentheticals are the norm, and the
  reviewer rated it low impact.
- **Trailing tilde** (`~I sing~` -> lyric text `I sing~`): only the leading `~` is
  spec-significant; the trailing one is literal.
- **Delimiter-soup round-trip instability**: pathological mixed `* _ \` inputs may take a
  couple of parse/render iterations to converge (they always do, and never diverge);
  realistic prose is 100% stable on the first round trip. Inherent to escaping literal
  delimiters and re-parsing.
