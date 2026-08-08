# Session Summary: Remove INTERIOR/EXTERIOR Scene-Heading Prefixes (Fix 4)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

Fourth fix in the adversarial-review remediation pass. Addresses the HIGH finding that
`INTERIOR`/`EXTERIOR` spelled out were accepted as scene-heading prefixes, which the
official spec does not include, so prose like "Interior design is a career." became a
false scene heading under case-insensitive matching.

## Key Actions

- Removed `INTERIOR|EXTERIOR` from `SCENE_HEADING_PATTERN`, leaving the spec set
  INT/EXT/EST/I/E/INT/EXT/INT./EXT.
- Updated the pattern comment to explain the exclusion.

## Tests / Docs

- Changed the two `INTERIOR./EXTERIOR.` cases in `test_scene_heading_variations` to expect
  non-scene-heading, and added prose false-positive cases ("INTERIOR decorators arrived.",
  "Interior design is a career.").
- Fixed the 14-element-types fixture to use `INT. CAFÉ - DAY #1#`.
- Updated spec.md scene-heading rule 16 to drop the two prefixes.
- Full gate green: 288 pytest, doctests, ruff/mypy/format clean.
