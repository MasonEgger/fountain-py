# Session Summary: Preserve Forced-Action Marker on Round-Trip (Review 2, Fix 6)

**Date**: 2026-07-25
**Model**: Opus 4.8 (1M)

## Context

The second review's fuzzer found that a forced action whose text starts with a special
char lost its `!` on the Fountain round trip and re-parsed as a scene heading or transition.

## Key Actions

- The forced-action branch built its element without the `forced` flag, so the Fountain
  renderer (which emits `!` only when `metadata["forced"]` is set) dropped the marker. Set
  `metadata={"forced": True}` on forced action, matching the forced-scene and
  forced-transition branches.

## Tests

- Added `test_forced_action_round_trips` (RED first): `!.This looks like a scene heading`
  stays ACTION through parse -> FountainRenderer -> parse.
- Full gate green: 310 pytest, doctests, ruff/mypy/format clean.
