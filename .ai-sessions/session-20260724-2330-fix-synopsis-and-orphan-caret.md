# Session Summary: Edge Cases - == Synopsis and Orphan Caret (Fix 14a)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

First of the final cleanup batch from the adversarial review (two LOW behavior edge cases).

## Key Actions

- `SYNOPSIS_PATTERN` now requires the leading `=` not be followed by another `=`
  (`^=(?!=)\s*`), so `==` is no longer read as a synopsis of `=`. Two equals are neither a
  synopsis nor a page break (which needs 3+) and fall through to action.
- `_process_dual_dialogue` clears the `dual_dialogue` metadata flag on any caret cue that
  never pairs (a lone `^`, or no dialogue on both sides), and on the left character of a
  both-caret pair, so a non-dual character is not left latently flagged.

## Tests

- Added `test_double_equals_is_not_a_synopsis` and `test_orphan_caret_does_not_leave_dual_flag`.
- Full gate green: 300 pytest, doctests, ruff/mypy/format clean.

## Note

- The Author+Authors double "by" the review flagged is a deliberate, tested Q10 product
  decision (render both keys), not a defect, so it is kept as-is.
