# Session Summary: Dialogue Continuation Across Interior Lyric/Note (Fix 9)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

Ninth fix in the adversarial-review remediation pass. Addresses the MEDIUM finding that a
dialogue line following an interior LYRICS or standalone NOTE inside a dialogue block was
demoted to ACTION. This reverses the earlier C8 "lyrics end the block" contract, which
diverged from Fountain (a dialogue block ends only at a blank line).

## Key Actions

- `_is_dialogue_line` now treats a LYRICS or standalone NOTE as a non-terminating element
  inside a dialogue block: it looks back past LYRICS/NOTE elements to the block anchor
  (CHARACTER/PARENTHETICAL/DIALOGUE) and continues dialogue when found. A blank line still
  ends the block (via `had_blank_line_before`), and a lyric/note outside a dialogue block
  (after action) still yields action.

## Tests / Docs

- Added `test_dialogue_continues_across_interior_lyric_or_note` (RED first) covering both
  the lyric and note cases.
- Rewrote the old C8 test into `test_lyrics_inside_dialogue_do_not_end_block`.
- Updated spec.md C8 and the user-guide "Lyrics Inside a Dialogue Block" section to the
  revised behavior.
- Full gate green: 294 pytest, doctests, ruff/mypy/format clean.
