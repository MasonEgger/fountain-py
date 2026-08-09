# Accomplishment: fountain-py 0.1.0 (spec compliance, validation API, PyPI release)

**Archived**: 2026-08-08
**Convergence**: converged (62 of 62 todo items checked)

## Spec Slice

The plan implemented the 0.1.0 slice of `spec.md`: ship fountain-py, a zero-dependency Python library that parses Fountain screenplay markup into structured objects and renders them to HTML or back to Fountain, as a spec-compliant PyPI release. Scope per Mason's 2026-07-03 rulings: fix every Fountain-compliance gap (Groups A through E) with a pinned test and no waivers, ship the `FountainParser.validate()` diagnostic API, move the Python floor to 3.10 with `X | None` typing, promote the renderers into the top-level `__all__`, make every published claim true, and harden the publish pipeline for trusted publishing. `spec.md` stays at the repo root as the permanent record of what the project is.

## What Got Done

- **Python floor and types** (Section 1): floor to 3.10, CI matrix 3.10 through 3.14, `MetadataValue` applied and `X | None` swept through `src/`.
- **API surface** (Section 2): `HTMLRenderer` and `FountainRenderer` promoted to the top-level `__all__`; single-line ABOUTME headers.
- **Validation API** (Section 3): `ValidationIssue` frozen dataclass and `FountainParser.validate()` with the four initial diagnostic codes, exported from the package top level.
- **Full Fountain compliance** (Sections 4 through 8): every requirement in Groups A through E fixed with a failing-first test, including the boneyard truncation defects, the emphasis rework, dual-dialogue and lyrics round-trips, scene-heading and character-cue edge cases, and transitions.
- **Documented ambiguities** (Section 9): A3, C8, D11, E9 pinned by tests and described in the user guide.
- **Documentation truth-up** (Section 10): every published claim made accurate against the now-real behavior.
- **Tooling** (Section 11): dangling pre-commit references removed (CR-3).
- **Path to PyPI** (Section 12): CI install fix and build verification, hardened publish workflow (test gate, artifact upload/download, environment, trusted publishing), TestPyPI dry-run workflow, local end-to-end verification.
- **Release**: merged to `main`, tagged `v0.1.0`, cut the GitHub Release. `fountain-py 0.1.0` is live on PyPI and installs cleanly; the docs are on GitHub Pages.

Beyond the original plan, this release also carried a full documentation overhaul (Diataxis restructure, adversarial docs review in `docs-plan.md`, Vale linting) and a `contributing/releasing.rst` release guide.

## Deferred or Dropped

- Parser pipeline and dual-dialogue post-pass refactor (Open Question 12): deferred to a design pass, no refactor in 0.1.0.
- PDF, JSON-schema, and XML output modes: scoped as post-0.1.0 phases.

## Notable Decisions

- Version pinned at 0.1.0 (not 0.2.0); the "Full Fountain Spec Compliance" claim kept and made true rather than softened.
- Trusted publishing over a stored PyPI token; no secret to manage.
- The docs deliberately said "install from source" until the package was published, then flipped to `pip install fountain-py` post-release.

## Files Touched

- `src/fountain/` (parser.py, renderer.py, elements.py, document.py, __init__.py)
- `tests/` (test_edge_cases.py, test_renderer.py, test_validation.py, test_document.py, test_quickstart_examples.py)
- `docs/source/` (the full Diataxis tree: tutorials, how-to, reference, explanation, contributing)
- `.github/workflows/` (ci.yml, publish.yml, test-publish.yml, docs.yml)
- `pyproject.toml`, `README.md`, `CHANGELOG.md`, `.vale.ini`

## Lessons Cross-Reference

- See the `.ai-sessions/session-*.md` records from this release, in particular the post-compaction docs-overhaul and release sessions dated 2026-08-08 (docs P0/P1/P2, Vale rST tooling, the `-s ours` main merge, and the release cut).
