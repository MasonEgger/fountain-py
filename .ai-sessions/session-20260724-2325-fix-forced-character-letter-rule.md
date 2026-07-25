# Session Summary: Require a Letter in Forced @ Character Names (Fix 13)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

Thirteenth fix in the adversarial-review remediation pass. Addresses the MEDIUM finding
that a forced ``@`` cue accepted a name with no alphabetical character (``@23``), against
the Fountain rule that a character name must contain at least one letter.

## Key Actions

- Guarded the forced-character branch so it only produces a CHARACTER element when the
  resolved name (after caret and extension handling) contains at least one letter. A cue
  like ``@23`` falls through to normal classification (ultimately action), while
  ``@McClane`` still forces a character.

## Tests

- Added `test_forced_character_requires_a_letter` (RED first): ``@23`` is not a character,
  ``@McClane`` still is.
- Full gate green: 298 pytest, doctests, ruff/mypy/format clean.
