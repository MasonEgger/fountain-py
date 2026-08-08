# Session Summary: Recognize Stacked Character Extensions (Review 2, Fix 5)

**Date**: 2026-07-25
**Model**: Opus 4.8 (1M)

## Context

The second review found that a common cue form, `JOHN (V.O.) (CONT'D)`, fell through to
ACTION and swallowed the following dialogue, because the extension patterns allowed only
one parenthesized group.

## Key Actions

- Changed the extension content capture from `([^)]+)` to `(.+)` in both
  `CHARACTER_EXTENSION_PATTERN` and `FORCED_EXTENSION_PATTERN`, so a stacked extension is
  captured as one block. The name group still excludes `(`, and the end-anchor keeps
  matching linear (no catastrophic backtracking).
- `JOHN (V.O.) (CONT'D)` now parses as CHARACTER + DIALOGUE; the HTML shows both
  extensions and the Fountain round-trip is stable (`JOHN (V.O.) (CONT'D)`).

## Tests

- Added `test_stacked_character_extensions` (RED first): natural cue, the dual-caret
  variant, and the forced `@` variant.
- Full gate green: 309 pytest, doctests, ruff/mypy/format clean.
