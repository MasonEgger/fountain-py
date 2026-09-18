# Accomplishment: fountain-py 0.2.0 - Output Modes and Interchange

**Archived**: 2026-09-18
**Convergence**: converged (all 19 todo items done: 15 automatable steps via the `/goal` loop, 4 human-gated release steps done manually; 0.2.0 shipped to PyPI)

## Spec Slice

The "0.2.0: Output Modes and Interchange" section of spec.md (ruled 2026-08-15). Finish JSON as a real interchange format, formalize the renderer contract, and add plain-text, CLI, FDX, and PDF output modes. Rulings carried in from the review: the CLI executable is `fountain`; the PDF extra uses `fpdf2`; `HALF_LETTER` ships while the `STAGE_PLAY` profile is deferred; FDX omits the writer tools.

## What Got Done

- Recursive nested-element serialization in `to_dict`, fixing the `to_json` dual-dialogue crash.
- Versioned JSON schema (`schema_version`) with a `reference/json-schema` page.
- `from_dict` / `from_json` deserialization; JSON now round-trips, unknown schema version raises `ValueError`.
- `TextRenderer` / `BinaryRenderer` runtime-checkable protocols in a new `fountain/renderers/` package.
- `PlainTextRenderer` (monospace screenplay layout, writer tools omitted).
- `fountain` CLI: `validate` and `render --format {html,text,fountain,json,fdx,pdf}`, stdin, `-o`, `[project.scripts]` entry.
- `FDXRenderer` (Final Draft `.fdx` via stdlib XML), dual-dialogue encoding pinned by `tests/fixtures/dual_dialogue.fdx`.
- PDF export: optional `fountain-py[pdf]` extra on `fpdf2`, `require_fpdf()` guard, `PageGeometry` presets (LETTER / A4 / HALF_LETTER), `SCREENPLAY` layout profile, `PDFRenderer`; CI proves the core stays dependency-free.
- How-to guides for every new mode, README / landing page / CHANGELOG truthed up to 0.2.0, Vale-clean.
- Version bumped to 0.2.0; merged to `main`; `v0.2.0` Release cut; published to PyPI over OIDC; docs deployed.

## Deferred or Dropped

- `STAGE_PLAY` layout profile: deferred per Open Question 15; only `SCREENPLAY` ships.
- CI `pdf` job installs fpdf2 via the dev group rather than the `[pdf]` extra, so the extra's install path is exercised only indirectly (validator-rated info; the plan sanctioned `uv sync --dev`).

## Notable Decisions

- New renderers live under `fountain/renderers/`; `HTMLRenderer` / `FountainRenderer` stay in `renderer.py` (moving them was out of scope).
- Fixed-width renderers must wrap every output path: the `PlainTextRenderer` TRANSITION branch overflowed until wrapped (validator-caught).
- `# pragma: no cover` reserved for genuinely unreachable branches; a reachable-today not-yet-wired branch is tested instead (validator-caught on the CLI fdx path).
- A "missing dependency" test simulates absence via `monkeypatch.setitem(sys.modules, "fpdf", None)` rather than relying on fpdf2 being uninstalled, since the dev group installs it.
- A CI job proving a dependency is absent needs `--no-dev` on both `uv sync` and every `uv run`, because `uv run` re-syncs default groups.

## Files Touched

- `src/fountain/document.py`, `src/fountain/cli.py`, `src/fountain/__init__.py`
- `src/fountain/renderers/{__init__,base,fdx,plaintext}.py`
- `src/fountain/renderers/pdf/{__init__,_deps,geometry,profile,renderer}.py`
- `tests/test_{document,cli,fdx_renderer,plaintext_renderer,renderer_protocol,pdf_deps,pdf_geometry,pdf_profile,pdf_renderer}.py`, `tests/fixtures/dual_dialogue.fdx`
- `docs/source/how-to/{use-the-cli,export-plain-text,export-fdx,export-pdf,export-to-json}.rst`, `docs/source/reference/json-schema.rst`, `docs/source/index.rst`, `docs/source/changelog.rst`, `docs/source/conf.py`
- `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`, `README.md`, `CHANGELOG.md`

## Lessons Cross-Reference

See `.ai-sessions/lessons.md` (Recent + BPE Workflow / Testing / Rendering / Tooling categories), dated 2026-08-16 and 2026-08-30, including: fixed-width wrap contract, pragma-on-reachable-branch, git-grep blind spot for untracked files, `uv run` dev-group re-sync, and the `full`-mode `/goal` deadlock on human-gated release items.
