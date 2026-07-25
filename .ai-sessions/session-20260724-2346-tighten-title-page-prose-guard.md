# Session Summary: Tighten Title-Page Prose Guard (Verification Residual 3)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

The re-verification pass found the title-page gate still let a capitalized prose line with
a colon at document start be eaten as metadata (e.g. `Warning: stay back.`), silently
dropping that action line. The lowercase-prose case was already fixed; this Title-Case
sub-case slipped through the capitalized-label heuristic.

## Key Actions

- `_opens_title_page_key` now rejects a custom (non-recognized) capitalized-label key whose
  value ends in sentence punctuation (`.`, `!`, `?`), treating it as body prose. Recognized
  fields (which can legitimately end in a period, like Copyright) still open a key via the
  known-key branch, and custom keys with label-like values (`Custom Field: Custom Value`)
  still work.

## Tests

- Added `test_title_case_prose_colon_line_is_action`: `Warning:`/`Meanwhile:`/`Jim:`
  sentence lines are action; `Custom Field: Custom Value` still opens the title page.
- Full gate green: 304 pytest, doctests, ruff/mypy/format clean.

## Residual note

- A capitalized `Label: Title-Case value` with no ending punctuation (`New York: The City`)
  is still read as metadata. That is inherently ambiguous with the intentional
  arbitrary-custom-key feature and is left as the documented tradeoff.
