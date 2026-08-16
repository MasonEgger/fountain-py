# fountain-py 0.2.0: TODO

Read `plan.md`. Target version 0.2.0. Each Feature step is TDD: failing test first, minimal fix, `just test` clean. Task steps: Scope / Tooling / Do / Verify / Document.

## Section 1: Serialization and JSON Interchange
- [x] 1.1 F1: recursively serialize nested elements in `to_dict` (fixes the `to_json` dual-dialogue crash)
- [x] 1.2 F2: `schema_version` key + `reference/json-schema.rst` in the toctree
- [x] 1.3 F3: `from_dict` / `from_json` with round-trip and unknown-version `ValueError`

## Section 2: Renderer Protocol and Package
- [x] 2.1 G1: `TextRenderer` / `BinaryRenderer` protocols in `fountain/renderers/base.py`, exported; existing renderers conform

## Section 3: Plain-Text Renderer
- [x] 3.1 H1: `PlainTextRenderer` in `fountain/renderers/plaintext.py`, writer tools omitted, satisfies `TextRenderer`

## Section 4: Command-Line Interface
- [x] 4.1 I1: `fountain` CLI (`validate`, `render --format ...`), `[project.scripts]` entry, subprocess tests

## Section 5: FDX Export
- [x] 5.1 J1: `FDXRenderer` (stdlib XML), mapping pinned by `tests/fixtures/dual_dialogue.fdx`, writer tools omitted

## Section 6: PDF Export
- [x] 6.1 K3a: `[pdf]` extra on `fpdf2`, `pdf/` subpackage, `require_fpdf()` import guard
- [x] 6.2 K1: `PageGeometry` presets `LETTER` / `A4` / `HALF_LETTER` + custom + binding offset
- [x] 6.3 K2: `SCREENPLAY` `LayoutProfile` dataclass (data only)
- [ ] 6.4 PDFRenderer.render_bytes tying geometry + profile; media box, offset, element order; satisfies `BinaryRenderer`
- [ ] 6.5 K3b: CI jobs (base-install proves zero-dependency core; `pdf` job runs the PDF suite under the extra)

## Section 7: Documentation and Truth-Up
- [ ] 7.1 L1: how-tos for CLI, plain-text, FDX, PDF; `from_json` in the JSON how-to; Vale-clean
- [ ] 7.2 L2: README, landing page, CHANGELOG 0.2.0 truth-up; no hand-counted metrics

## Section 8: Release Mechanics
- [ ] 8.1 Bump `pyproject` version to 0.2.0; full `just test` green; `uv build` produces `fountain_py-0.2.0`

## Release (Human-Gated, Mason only)
- [ ] Merge `0.2.0-dev` to `main` (Mason merges; agents never do)
- [ ] Tag `v0.2.0`, create the GitHub Release
- [ ] Let the gated publish + docs workflows run
- [ ] Verify the PyPI page and `pip install fountain-py==0.2.0`
