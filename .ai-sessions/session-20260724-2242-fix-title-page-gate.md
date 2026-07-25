# Session Summary: Gate Title-Page Detection (Adversarial Review Fix 3)

**Date**: 2026-07-24
**Model**: Opus 4.8 (1M)

## Context

Third fix in the adversarial-review remediation pass. Addresses the HIGH finding that any
colon-bearing first line was consumed as title-page metadata, silently losing `FADE IN:`
and other transitions (and colon-bearing action) from the body.

## Key Actions

- Tightened title-page key detection (`_opens_title_page_key`). A colon is no longer
  sufficient. A key must carry a non-empty value or an indented continuation, and must
  name a recognized field (new `TITLE_PAGE_KEYS`) or be a capitalized label.
- `FADE IN:` and `CUT TO:` (empty value) now parse as body transitions; prose like
  `He opens the card: a threat.` (lowercase label) parses as body action.
- Preserved the intentional arbitrary-key feature: capitalized custom labels
  (`Custom Field:`, `Revision:`, `Network:`) and recognized fields still open the title
  page, so all "Step 4: Arbitrary Title Page Keys" tests still pass.

## Tests / Docs

- Added three tests (RED first): first-line `FADE IN:`, `CUT TO:`, and colon prose.
- Rewrote the old `test_title_page_detection_heuristic` (which pinned the removed A3
  behavior) into `test_title_page_detection_requires_a_real_key`.
- Updated spec.md A3 and the user-guide "Line-One Title Page Detection" section (with
  doctests) to the revised contract.
- Full gate green: 288 pytest, doctests, ruff/mypy/format clean.

## Observations

- A leading `>CUT TO:` on line one now correctly parses as a forced transition, which the
  old behavior could not do; the doc's former "escape routes don't work" caveat is gone.
