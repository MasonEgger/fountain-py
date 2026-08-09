# fountain-py 0.1.0 Handoff

This document hands the fountain-py 0.1.0 release work to a fresh implementation agent.
Read it, then `plan.md`, then `todo.md`.
You need no other context to start.

## What This Project Is

fountain-py is a zero-dependency Python library that parses Fountain screenplay markup (https://fountain.io/syntax/) into structured objects and renders them as HTML or back to Fountain text.
The public API lives in `src/fountain/`: `FountainParser` (parse and validate), `FountainDocument` (structure and analysis), the element types in `elements.py`, and `HTMLRenderer` / `FountainRenderer` in `renderer.py`.

## Current State

- Branch: `init-version`, a feature branch off `main`. Never commit to `main`; Mason merges to `main` himself.
- The code is Mason's committed working library: 241 tests pass (`uv run pytest`), coverage is 99%+, `mypy --strict src/` passes, and `just test` runs clean.
- `spec.md` is committed and final: commit 1056da5, "spec updates from fable and review", dated 2026-07-03. It is the reversed-and-reviewed product spec with Mason's rulings folded in.
- `plan.md` and `todo.md` were regenerated from that spec (this handoff's companion work). The old "PyPI Publishing Plan" that targeted 0.2.0 is gone from the working tree and survives only in git history.
- Packaging today declares `requires-python = ">=3.9"` with a `py39` ruff target and a 3.9-through-3.13 CI matrix; the spec changes this to a 3.10 floor (see Decisions).
- Workflows: `.github/workflows/ci.yml`, `docs.yml`, and `publish.yml` are all committed. `docs.yml` already builds and deploys Sphinx HTML to GitHub Pages, so the spec's "docs.yml is untracked" note is already resolved. `publish.yml` is an unhardened skeleton. There is no `test-publish.yml` yet.
- `dist/` holds 0.1.0 wheel and sdist artifacts from an earlier build.

## Decisions Mason Settled (2026-07-03 Rulings)

These came from Mason's `/bpe:review` and `/bpe:brainstorm` on the spec. They are settled scope, not open choices.

- **Version is 0.1.0.** pyproject and the release both stay at 0.1.0. The old plan's 0.2.0 was wrong and is dropped (Open Question 1).
- **No compliance waivers.** All 37 Fountain-compliance requirements (Groups A through E) are fixed before 0.1.0, each with a failing-first test that encodes its acceptance criterion. High, medium, and low severities all ship fixed; severity only orders the work (Open Question 2, Spec Compliance ruling). This is why the README and CHANGELOG "Full Fountain Spec Compliance" claim is kept: it becomes true before publish, rather than being softened.
- **The Validation API is required for 0.1.0.** `FountainParser.validate(text) -> list[ValidationIssue]` runs the same two-pass analysis as `parse()` but reports diagnostics instead of swallowing them. `parse()` stays lenient and non-raising. Initial diagnostic codes: `unclosed-boneyard`, `unclosed-note`, `orphan-character-cue`, `empty-document`. Rationale: silent degrade-to-ACTION with no diagnostic channel is swallowing errors (Open Question 8).
- **Promote the renderers.** `HTMLRenderer` and `FountainRenderer` join the top-level `__all__`. The library re-export pattern is the accepted exception to the empty-`__init__` rule, but the file stays logic-free: imports, `__all__`, and the module docstring only (Open Question 7).
- **Python floor moves to 3.10, ceiling tracks current CPython.** Support runs 3.10 through 3.14 now, with 3.15 added on its October 2026 release. Code modernizes to `X | None` throughout, and `MetadataValue` gets applied to `FountainElement.metadata` (Open Question 9, CR-2).
- **Render all authors.** With both `author` and `authors` keys present, both renderers emit both, each as its own author paragraph, so `HTMLRenderer` and `FountainRenderer` agree (Open Question 10).
- **Documented ambiguities are contract.** A3 (title page detection heuristic), C8 (lyrics end a dialogue block), D11 (FADE IN/OUT as natural transitions), and E9 (mid-line notes vanish) are pinned by tests and documented in the user guide; changing them later is a breaking change.
- **Keep `just fix` inside `just test`.** The quality gate stays as-is (Open Question 11); no split into a read-only gate.

## Out of Scope (Deferred by Ruling)

- **The parser pipeline / dual-dialogue refactor.** Dual dialogue pairing stays a hard-coded post-pass for 0.1.0. Mason wants a design pass against his planned expanded-markdown library's processor model before any refactor, and ruled no refactor before that pass (Open Question 12). Do not restructure the parser or the `Counter` statistics pass.
- **PDF, JSON-schema, and XML output modes.** Post-0.1.0 phases, each getting its own spec pass. They do not block this release.

## Known Risks

- **The compliance claim must be true before publish.** README.md:13 and CHANGELOG.md:14 both say "Full Fountain Spec Compliance". That claim is false today (the audit confirmed 37 gaps). Do not publish until every requirement in plan.md Sections 4 through 9 is fixed and green. Section 10 verifies the claim last, on purpose.
- **The author-vs-authors renderer divergence is real but ruled.** Open Question 10 is settled (render all authors), so this is a fix to implement (plan Step 5.7), not an open decision. If any downstream reader still treats it as open, point them here: the ruling stands.
- **Publish auth: trusted publishing over API token.** `publish.yml` currently authenticates with `UV_PUBLISH_TOKEN` from `secrets.PYPI_API_TOKEN` even though it already grants `id-token: write`. The spec prefers trusted publishing (no secret to manage, permission already declared). Switch during plan Step 12.2; if trusted publishing is not yet configured on PyPI for this project, that configuration is Mason's to set up before the first real publish.
- **The 3.10 floor move touches the whole codebase.** Modernizing `Optional`/`Union` to `X | None` and flipping the ruff/mypy targets is a wide but mechanical change; do it first (plan Section 1) so every later compliance fix is written clean.

## Goal Chain

Publishing fountain-py 0.1.0 to PyPI unblocks the bartleby integration (screenplay content in bartleby sites) and the sites built on the stack.
fountain-py is rank 1 in the portfolio queue for that reason.

## The Next Action

Start with plan.md Step 1.1: move the Python floor to 3.10 in `pyproject.toml` (requires-python, classifiers, ruff `target-version`, mypy `python_version`), confirm `just test` stays green, then continue in plan order.
