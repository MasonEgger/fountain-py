# Session Summary: Collapse Inline-Note Double Space (Fix 12)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

Twelfth fix in the adversarial-review remediation pass. Addresses the LOW finding that
removing a mid-line ``[[note]]`` left a doubled space (``Action  here``).

## Key Actions

- Added `NOTE_SEAM_PATTERN` (the note body plus flanking spaces/tabs) and a
  `_collapse_note_seam` replacement that returns a single space when the note was flanked
  by whitespace on both sides, and "" when it was flush against a word or the line edge.
- Both the classification pass and the stored-text pass now strip inline notes with the
  seam collapse, so a note between words leaves one space and a trailing/leading note
  leaves none, while a deliberate leading indent is untouched.

## Tests / Docs

- Added `test_inline_note_removal_collapses_double_space` (RED first), single and multiple
  notes.
- Updated `test_inline_note_removed_standalone_kept` (E9) and the user-guide notes section
  (prose + doctest) from the doubled-space contract to the single-space collapse.
- Full gate green: 297 pytest, doctests, ruff/mypy/format clean.
