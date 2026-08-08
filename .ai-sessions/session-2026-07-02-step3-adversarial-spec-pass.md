# Session: Adversarial Spec Review Pass (P2), 2026-07-02

Adversarial review of the reversed product spec (portfolio-audit ce01d31) against the code, with every finding verified by probe scripts run outside the repo.

## What changed in spec.md

Behavior corrections, each probe-verified with file and line:

- Title page rules: a colon-free continuation line starting with `INT.`/`EXT.`/`EST.`/`I/E.`/`.` ends the title page instead of extending the value (parser.py:463-473).
- Body rule 6: the NOTE condition is starts-with `[[` and ends-with `]]`, not "entirely a note"; `[[a]] middle [[b]]` becomes one NOTE.
- Body rules 16, 17, 19: the blank-line-before condition is actually "blank line or no element emitted yet"; `FADE OUT.` on line one is a TRANSITION.
- Lookahead: `_is_dialogue_following()` also rejects standalone note lines, not just STRUCTURAL_PATTERNS (parser.py:853).
- Inline formatting: overlap suppression is partial; underline spans are never suppressed (parser.py:1074-1101).
- `get_statistics()`: only the per-type counts are single-Counter-pass; characters and scenes delegate.
- HTMLRenderer drops `authors` when `author` exists; FountainRenderer emits both (renderer.py:403-404).
- Quality metrics: `just test` includes the mutating `just fix` step; `mypy --strict src/` passes today despite the config not being literal strict.

New requirements appended (found during verification):

- A4c (low): lyrics round trip accretes a trailing `~` (renderer emits `~text~`, parser strips only the leading tilde).
- E13 (low): `[[a]] middle [[b]]` swallows the interior text into one NOTE.
- CR-3 (low): dangling pre-commit recipes in justfile and CONTRIBUTING.md.

Path to PyPI corrections against the real workflows:

- publish.yml already grants `id-token: write` yet authenticates with `PYPI_API_TOKEN`.
- ci.yml:29 installs a nonexistent `dev` extra (uv warns, installs nothing); CI passes only because `uv run` re-syncs the dev dependency group. Fix: `uv sync --dev`.
- docs.yml (untracked) deploys Sphinx HTML to Pages but runs no doctest build; it must be committed to take effect.

Open Questions 10 (author/authors renderer disagreement) and 11 (mutating `fix` inside `just test`) added for the /bpe:brainstorm run.

## Verification

- 241 tests pass in a scratch copy with only the dev group.
- All probe scripts under the session scratchpad (step3-adversarial/probes.py); none run inside the repo.
- Refuted self-candidates left unapplied: "mypy strict" wording (probe: `mypy --strict` passes clean), E2/E3 truncation claims (probe: accurate as written), dual-dialogue A4b claim (probe: reconfirmed), title-page field ordering claims (code-verified accurate).
