# Session Summary: Fix O(n^2) Merged-Action Assembly (Review 2 re-verify)

**Date**: 2026-07-25
**Model**: Opus 4.8 (1M)

## Context

The review-2 re-verification emphasis fuzzer surfaced a pre-existing O(n^2) parse cost:
each action continuation line re-extracted the whole growing paragraph buffer, so a large
no-blank action block was quadratic (2000 lines ~13.9s), a DoS-ish concern for untrusted
input. Introduced by the review-1 action-merge, not the line-break refactor.

## Key Actions

- Since emphasis is now line-bounded, a continuation line is extracted independently and
  its clean text and offset spans appended to the paragraph, instead of re-joining and
  re-extracting the entire buffer each line. Paragraph assembly is now O(n).
- Removed the now-dead `_action_raw` buffer (init, reset, and the merge path).
- Result: 2000 lines dropped from ~13,861ms to ~53ms; 5000 lines ~162ms (linear).

## Tests

- Added `test_merged_action_emphasis_per_line_and_linear`: per-line emphasis in a merged
  paragraph is preserved, and a 3000-line no-blank block parses in under 2s.
- Full gate green: 314 pytest, doctests, ruff/mypy/format clean.
