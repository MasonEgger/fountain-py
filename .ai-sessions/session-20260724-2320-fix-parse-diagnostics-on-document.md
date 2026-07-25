# Session Summary: Surface Parse Diagnostics on the Document (Fix 11)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

Eleventh fix in the adversarial-review remediation pass. Addresses the MEDIUM finding that
`parse()` provided no diagnostics for unclosed constructs; only the separate `validate()`
call surfaced them, and nothing was attached to the returned document.

## Key Actions

- Added an `issues: list[ValidationIssue]` field to `FountainDocument` (defaults to empty).
- `parse()` now records every diagnostic it can detect (unclosed boneyard, unclosed note,
  orphan character cue, empty document) into `self.diagnostics` and attaches them to the
  returned document. End-of-document diagnostics are recorded before the recovery flushes
  clear the leftover state.
- The orphan-cue diagnostic is now always recorded (previously only during validation).
- Simplified `validate()` to `return list(self.parse(text).issues)` and removed the
  `_validating` flag and its recovery guards, unifying the two paths.

## Tests

- Added `test_parse_surfaces_diagnostics_on_document` (RED first): unclosed boneyard,
  unclosed note, orphan cue, clean document, and validate() parity.
- Full gate green: 296 pytest, doctests, ruff/mypy/format clean.
