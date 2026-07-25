# Session Summary: Fix Custom Title-Page Key XSS (Review 2, Fix 1)

**Date**: 2026-07-25
**Model**: Opus 4.8 (1M)

## Context

A second full adversarial review (five reviewers) after the first remediation round found a
CRITICAL parser-reachable stored XSS the earlier extension fix had missed: the custom
title-page key was interpolated into the HTML unescaped.

## Key Actions

- `HTMLRenderer._render_title_page` now escapes the custom-field key in both the class
  attribute (`css_class`) and the label text (`field_label`), matching how the value is
  already escaped. A key like `X><img/src=x/onerror=alert(1)>` no longer breaks out of the
  attribute or injects a live tag, in both `render()` and `render_page()`.
- Audited every dynamic f-string interpolation in the HTML render path (lines 373-575):
  all now route through `_escape_html` or `_apply_formatting` (which escapes) or are static.
  The custom-field key was the last hole.

## Tests

- Added `test_custom_title_page_key_is_html_escaped` (RED first): parser-reachable tag
  payload and a hand-built script-injecting key, checked in fragment and standalone page.
- Full gate green: 305 pytest, doctests, ruff/mypy/format clean.
