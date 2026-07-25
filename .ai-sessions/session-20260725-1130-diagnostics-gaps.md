# Session Summary: Diagnostics Gaps (Review 2, Fix 7)

**Date**: 2026-07-25
**Model**: Opus 4.8 (1M)

## Context

The second review found two diagnostic issues: (a) an unclosed note broken by a blank line
did not report `unclosed-note` (only the EOF path did), and (b) a title-page-only document
was falsely flagged `empty-document`.

## Key Actions

- Moved the unclosed-note diagnostic into `_flush_open_note_as_text`, which both the
  blank-line-break and end-of-input recovery paths call, so both now report it. Removed the
  duplicate recording at end of parse.
- The empty-document guard now also checks `metadata`, so a document with title-page
  metadata but no body elements is not flagged as empty.

## Tests

- Added `test_unclosed_note_broken_by_blank_reports_diagnostic` and
  `test_title_page_only_document_is_not_empty` (RED first).
- Full gate green: 312 pytest, doctests, ruff/mypy/format clean; validate() parity intact.
