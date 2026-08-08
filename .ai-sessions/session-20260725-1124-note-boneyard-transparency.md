# Session Summary: Notes/Boneyard Transparent to Adjacency (Review 2, Fix 4)

**Date**: 2026-07-25
**Model**: Opus 4.8 (1M)

## Context

Two reviewers found that a note or whole-line boneyard flush against a scene heading or
transition (no blank line between) demoted it to ACTION, because blank-line adjacency ran
on raw source lines and treated the invisible annotation as content.

## Key Actions

- Added `_is_transparent_line` (whole-line note or boneyard) and `_has_visible_content`
  (any non-note/boneyard element emitted).
- `_is_blank_line_after` now skips transparent lines, so a heading followed by a note then
  a blank still has a blank line after it.
- The parse loop leaves the blank-before state unchanged across a note/boneyard line, so a
  heading after a note keeps the blank line that preceded the note.
- The "document start" checks in scene-heading/transition/character classification now use
  `_has_visible_content()` instead of `not self.elements`, so a leading boneyard/note does
  not stop the first real heading from being recognized.

## Tests

- Added `test_notes_and_boneyard_transparent_to_heading_adjacency` (RED first): note after
  heading, note before heading, leading boneyard, and transition-with-note.
- Full gate green: 308 pytest, doctests, ruff/mypy/format clean.
