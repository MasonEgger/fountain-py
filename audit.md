# fountain-py — Project Audit & Remediation Plan

_Audit date: 2026-06-19_

## Summary

`fountain-py` is an early-stage (v0.1.0, alpha) Python library for parsing
Fountain screenplay markup. The core parser is functional and well-tested
(48 tests passing, 94% coverage), but the project has structural, tooling,
and documentation gaps. This document lists the work needed, in priority
order, so it can be picked up by another agent.

## Current State

- **Branch/history:** 2 commits on `main` (`init commit` + squashed "Init
  version" PR #1, merged 2025-06-25).
- **Open PRs:** none. **Open issues:** none.
- **Tests:** all 48 pass; 94% coverage (parser 95%, renderer 92%,
  document 89%). Runs under `uv run pytest` on Python 3.10.
- **Dependencies:** zero runtime deps (intentional). Python 3.8+ target.
- **Implemented:** `FountainParser` (parse, `parse_file`, two-pass
  title-page parsing, inline formatting, dual-dialogue), `FountainDocument`
  (`to_dict`, `to_json`, `to_html`, `get_characters`, `get_scenes`,
  `get_statistics`), `FountainElement` / `ElementType` (14 element types),
  and `HTMLRenderer` with theming + CSS.

## Issues & Tasks

### Priority 1 — Structural / blocking

- [ ] **Flatten the nested directory layout.** The repo root is
  `fountain-py/` and the package lives in `fountain-py/fountain-py/`. Move
  the inner package contents (`src/`, `tests/`, `pyproject.toml`,
  `uv.lock`, `.python-version`, inner `README.md`) up to the repo root and
  remove the redundant nesting. Update `CLAUDE.md` command paths if needed
  (they currently assume you are inside the inner directory).
  - Verify after moving: `uv sync --dev && uv run pytest` still passes.

### Priority 2 — Tooling / CI

- [ ] **Add GitHub Actions CI.** Create `.github/workflows/ci.yml` that runs
  on push/PR: `uv sync --dev`, `uv run pytest --cov=fountain`, and lint
  (`black --check`, `isort --check`, `mypy src/`). Test across Python
  3.8–3.12 to match the declared classifiers.
- [ ] **Add pre-commit config.** `pre-commit` is already a dev dependency
  but there is no `.pre-commit-config.yaml`. Add hooks for black, isort,
  and mypy.

### Priority 3 — Documentation

- [ ] **Write a real README.** Both `README.md` files are effectively empty
  (`# fountain-py`). Add: project description, install instructions, a
  quickstart usage example (parse → document → HTML/JSON), supported
  Fountain elements, and a development/contributing section.
- [ ] **Add docs site scaffolding.** `pyproject.toml` references a Read the
  Docs URL and a `docs` dependency group (mkdocs + mkdocs-material +
  mkdocstrings), but there is no `docs/` directory, `mkdocs.yml`,
  `api.md`, or `examples.md`. Either build out minimal docs or remove the
  dangling references until ready.

### Priority 4 — Feature gaps (close Phase 1 of `plan.md`)

- [ ] **Implement validation.** `plan.md` promises
  `FountainParser.validate(text) -> List[ValidationError]` and lists a
  "validation system" as a success criterion, but it is not implemented.
  Add a `ValidationError` type and the `validate()` method, with tests.
- [ ] **Verify Fountain spec completeness.** Cross-check the 14 implemented
  `ElementType` values against the official Fountain spec
  (https://fountain.io/syntax) and add tests/fixtures for any edge cases
  not yet covered (e.g. forced elements, lyrics, emphasis combinations).

### Priority 5 — Roadmap (future phases, not yet started)

- [ ] **`mkdocs-fountain` plugin** (plan Phase 2): MkDocs integration with
  a `fountain` code-block processor and themes.
- [ ] **PDF export** (plan Phase 3): industry-standard formatting via
  WeasyPrint.
- [ ] **Packaging/release:** publish `0.1.0` (or first stable) to PyPI once
  README, CI, and validation are in place.

## Suggested Order of Execution

1. Flatten directory structure (P1) — unblocks everything else.
2. Add CI + pre-commit (P2) — guards subsequent changes.
3. Write README + docs scaffolding (P3).
4. Implement `validate()` and close spec gaps (P4).
5. Begin roadmap phases (P5).
