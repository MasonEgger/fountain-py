# PyPI Publishing Plan

## Context

Prepare fountain-py for its first public release on PyPI via automated GitHub Actions. The project already has solid foundations (pyproject.toml, CI workflow, publish workflow skeleton), but several gaps need closing before a production release.

**Package name:** `fountain-py` (confirmed available on PyPI)
**Target version:** `0.2.0` (significant work done since initial 0.1.0 — spec compliance, code review cleanup, breaking API changes)
**Build system:** hatchling (modern, correct)
**Wheel builds:** Verified locally, all files present including `py.typed`

**Key files:**
- `.github/workflows/ci.yml` — CI pipeline (tests, lint, type-check across Python 3.9–3.13)
- `.github/workflows/publish.yml` — PyPI publish trigger (on GitHub Release)
- `pyproject.toml` — Package metadata, build config, tool config
- `CHANGELOG.md` — Release notes
- `README.md` — PyPI long description

---

## Current Status

| Step | Description | Status |
|------|-------------|--------|
| 1 | Update CHANGELOG for 0.2.0 | Not Started |
| 2 | Bump version to 0.2.0 | Not Started |
| 3 | Fix README accuracy | Not Started |
| 4 | Harden publish workflow | Not Started |
| 5 | Add TestPyPI workflow | Not Started |
| 6 | Add build verification to CI | Not Started |
| 7 | Verify and test locally | Not Started |

---

## Step 1: Update CHANGELOG for 0.2.0

**NOTE**: The [Unreleased] section is empty but massive work has been done: 11 spec compliance fixes and 9 code review cleanups, including breaking API changes (`render()` → fragment, CSS class renames). This must be documented before release.

```text
Update CHANGELOG.md with all changes since 0.1.0. This is critical for PyPI — users need to understand what changed, especially the breaking changes.

1. Update `CHANGELOG.md`:
   - Move current [Unreleased] content to a new [0.2.0] section with today's date
   - Add the following sections:

   ### Breaking Changes
   - `HTMLRenderer.render()` now returns an HTML fragment without CSS (previously returned full page with `<style>` block)
   - New `HTMLRenderer.render_page()` returns the previous full-page behavior
   - New `HTMLRenderer.get_css()` returns raw CSS string for external use
   - All CSS classes renamed with `fountain-` prefix (e.g., `.action` → `.fountain-action`, `.character` → `.fountain-character`) to prevent framework collisions
   - `HTMLRenderer` no longer accepts a `theme` parameter
   - `FountainDocument.to_html()` no longer accepts a `theme` parameter

   ### Added — Spec Compliance
   - Section level metadata (`metadata["level"]` on SECTION elements)
   - Ellipsis protection on forced scene headings (`.` + alphanumeric only)
   - Arbitrary title page keys (any `Key: Value` pair accepted)
   - Blank-line-before requirement for natural scene headings
   - Blank-line-before requirement for character names
   - Blank-line-before and blank-line-after for transitions
   - Inline note stripping (`[[notes]]` removed from element text)
   - Multi-line note support (`[[note\nspanning\nlines]]`)
   - Dialogue continuation with whitespace-only lines
   - Backslash escaping for emphasis markers (`\*`, `\_`)
   - Tab-to-spaces conversion verified in HTML output

   ### Added — API
   - `HTMLRenderer.render_page()` for standalone HTML with embedded CSS
   - `HTMLRenderer.get_css()` for raw CSS string access
   - `FormatType` type alias (`Literal["bold", "italic", "underline", "bold_italic"]`)
   - `MetadataValue` type alias for element metadata values
   - `DEFAULT_CSS` module-level constant in renderer
   - `TITLE_PAGE_FIELD_ORDER` shared constant for renderer field ordering

   ### Changed
   - HTML renderer uses `html.escape()` instead of custom escape implementation
   - Title page rendering is now data-driven (shared `TITLE_PAGE_FIELD_ORDER` constant)
   - `_is_dialogue_following()` refactored to use `STRUCTURAL_PATTERNS` tuple
   - `get_statistics()` optimized from ~17 passes to single `Counter` pass
   - `FormatSpan.format_type` narrowed from `str` to `FormatType` Literal

   ### Removed
   - 90 lines of commented-out example renderer code (moved to docs)
   - `HTMLRenderer.theme` attribute and `_get_css()` private method

2. Verify the CHANGELOG reads well and covers all user-facing changes.
```

---

## Step 2: Bump version to 0.2.0

**NOTE**: Version lives in one place only — `pyproject.toml`. Sphinx reads it dynamically via `importlib.metadata`. No other files need updating.

```text
Bump the package version from 0.1.0 to 0.2.0 in pyproject.toml.

1. Update `pyproject.toml`:
   - Change `version = "0.1.0"` to `version = "0.2.0"`

2. Verify version is picked up correctly:
   - Run: `uv build` and confirm output says `fountain_py-0.2.0`
   - Run: `python -c "from importlib.metadata import version; print(version('fountain-py'))"` after reinstalling

3. No other files need version changes — Sphinx conf.py reads from metadata dynamically.
```

---

## Step 3: Fix README accuracy

**NOTE**: The README has several inaccuracies: references a `document.title` attribute that doesn't exist, mentions a CLI module that may not exist, and shows `render()` as returning full HTML (now returns fragment). The README is the PyPI landing page — it must be accurate.

```text
Fix README.md to accurately reflect the current API and features.

1. Update the Basic Usage example in `README.md`:
   - Remove `document.title` (doesn't exist — metadata is accessed via `document.metadata["title"]`)
   - Update `renderer.render(document)` context to clarify it returns a fragment
   - Add `render_page()` example for standalone HTML output
   - Fix the `get_characters()` call to use the correct method name

2. Verify the CLI section:
   - Check if `python -m fountain` actually works (look for `__main__.py`)
   - If the CLI doesn't exist, remove or mark as "coming soon"

3. Fix the Development section:
   - `just test-cov` should be `just unit-test-cov`
   - `uv sync --dev` should be `just dev` (per CLAUDE.md setup instructions)
   - Remove `pre-commit install` reference if `.pre-commit-config.yaml` doesn't exist

4. Verify all documentation links work (ReadTheDocs may not be deployed yet).
```

---

## Step 4: Harden publish workflow

**NOTE**: The current publish workflow is minimal — it builds and publishes but doesn't run tests first, doesn't use PyPI trusted publishing properly, and doesn't create a GitHub-native attestation. For a production release, the workflow should verify quality before publishing.

```text
Improve .github/workflows/publish.yml for production-quality releases.

1. Update `.github/workflows/publish.yml`:
   - Add `environment: pypi` to use GitHub Environments for deployment protection
   - Add a test job that runs before publish (same as CI but on the release tag)
   - Add build artifact upload/download pattern so the same wheel is tested and published
   - Pin Python version for the build (3.12 — stable, well-tested)
   - Add `--check` flag to `uv publish` for dry-run validation

   Target workflow structure:
   ```yaml
   name: Publish to PyPI

   on:
     release:
       types: [published]

   jobs:
     test:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]
       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v3
         - run: uv python install ${{ matrix.python-version }}
         - run: uv sync --group dev --group docs
         - run: uv run pytest --cov=fountain
         - run: uv run ruff check src/ tests/
         - run: uv run mypy src/

     build:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v3
         - run: uv build
         - uses: actions/upload-artifact@v4
           with:
             name: dist
             path: dist/

     publish:
       needs: build
       runs-on: ubuntu-latest
       environment: pypi
       permissions:
         id-token: write
       steps:
         - uses: actions/download-artifact@v4
           with:
             name: dist
             path: dist/
         - uses: astral-sh/setup-uv@v3
         - run: uv publish
           env:
             UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
   ```

2. Decision needed: **API token vs Trusted Publishing (OIDC)**
   - If using PyPI trusted publishing: remove `UV_PUBLISH_TOKEN`, add `--trusted-publishing always` to `uv publish`
   - If using API token: ensure `PYPI_API_TOKEN` secret is configured in GitHub repo settings
   - Trusted publishing is recommended (no secrets to manage) but requires PyPI configuration first

3. Verify the workflow YAML is valid.
```

---

## Step 5: Add TestPyPI workflow

**NOTE**: First-time publishes should go to TestPyPI first to validate the package installs correctly, the description renders, and metadata is right. This prevents a broken first impression on real PyPI.

```text
Add a TestPyPI workflow for pre-release validation.

1. Create `.github/workflows/test-publish.yml`:
   - Trigger: `workflow_dispatch` (manual) so you can test anytime
   - Also trigger on push to tags matching `v*-rc*` (release candidates)
   - Same build process as publish but targets TestPyPI
   - Uses `UV_PUBLISH_URL: https://test.pypi.org/legacy/` and a TestPyPI token

   ```yaml
   name: Publish to TestPyPI

   on:
     workflow_dispatch:

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v3
         - run: uv build
         - uses: actions/upload-artifact@v4
           with:
             name: dist
             path: dist/

     publish:
       needs: build
       runs-on: ubuntu-latest
       environment: testpypi
       permissions:
         id-token: write
       steps:
         - uses: actions/download-artifact@v4
           with:
             name: dist
             path: dist/
         - uses: astral-sh/setup-uv@v3
         - run: uv publish
           env:
             UV_PUBLISH_URL: https://test.pypi.org/legacy/
             UV_PUBLISH_TOKEN: ${{ secrets.TEST_PYPI_API_TOKEN }}
   ```

2. This lets you validate:
   - Package installs: `pip install -i https://test.pypi.org/simple/ fountain-py`
   - README renders correctly on the package page
   - Metadata (description, classifiers, URLs) looks right
   - No missing files in the distribution
```

---

## Step 6: Add build verification to CI

**NOTE**: The CI workflow runs tests and lint but doesn't verify the package actually builds. A broken build config would only be caught at release time. Add build verification to catch issues early.

```text
Add package build verification to CI workflow.

1. Update `.github/workflows/ci.yml`:
   - Add a build verification step after the existing test matrix:

   ```yaml
     build:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v4
       - uses: astral-sh/setup-uv@v3
       - name: Build package
         run: uv build
       - name: Verify wheel contents
         run: |
           python -c "
           import zipfile, sys
           whl = list(__import__('pathlib').Path('dist').glob('*.whl'))[0]
           names = zipfile.ZipFile(whl).namelist()
           required = ['fountain/__init__.py', 'fountain/parser.py', 'fountain/renderer.py', 'fountain/py.typed']
           missing = [f for f in required if f not in names]
           if missing:
               print(f'Missing from wheel: {missing}', file=sys.stderr)
               sys.exit(1)
           print(f'Wheel OK: {len(names)} files')
           "
   ```

   This catches:
   - Broken hatchling config
   - Missing files in the wheel
   - Packaging regressions

2. Also add `uv sync --group docs` and Sphinx doctest to CI:
   - Currently CI only runs `pytest` — it misses the 412 Sphinx doctests
   - Add: `uv run sphinx-build -b doctest docs/source docs/build/doctest`
```

---

## Step 7: Verify and test locally

**NOTE**: Before creating the first release, do a manual end-to-end verification.

```text
Final local verification before first release.

1. Build the package:
   - `uv build`
   - Confirm dist/ contains `fountain_py-0.2.0.tar.gz` and `fountain_py-0.2.0-py3-none-any.whl`

2. Test installation in a clean environment:
   - `uv venv /tmp/fountain-test && source /tmp/fountain-test/bin/activate`
   - `pip install dist/fountain_py-0.2.0-py3-none-any.whl`
   - `python -c "from fountain import FountainParser; p = FountainParser(); d = p.parse('INT. HOUSE - DAY'); print(d.elements[0].text)"`
   - `python -c "from fountain.renderer import HTMLRenderer; r = HTMLRenderer(); print(type(r.get_css()))"`
   - Verify it prints `INT. HOUSE - DAY` and `<class 'str'>`

3. Run the full test suite one more time:
   - `just test`

4. Clean up:
   - `rm -rf dist/`
   - `deactivate && rm -rf /tmp/fountain-test`

5. After all steps pass, the release process is:
   - Merge `init-version` branch to `main`
   - Tag: `git tag v0.2.0`
   - Push: `git push origin main --tags`
   - Create GitHub Release from the tag (triggers publish workflow)
   - Verify on PyPI: https://pypi.org/project/fountain-py/
```

---

## Implementation Guidelines

- **CHANGELOG accuracy is critical** — PyPI users read it. Don't skip breaking changes.
- **README is the PyPI landing page** — every code example must actually work.
- **TestPyPI first** — always validate there before real PyPI. You can't delete published versions.
- **Test the wheel, not the source tree** — install from the built wheel to catch packaging issues.
- **Pin workflow actions** — use `@v4` not `@main` for reproducibility.

## Success Metrics

After all changes:
1. `uv build` produces a clean wheel with all expected files
2. Wheel installs and imports correctly in a clean environment
3. CI runs tests + lint + type-check + build verification + doctests
4. TestPyPI publish succeeds and package page looks correct
5. Release workflow: tag → test → build → publish (automated, gated)
6. CHANGELOG documents all breaking changes and new features
7. README examples are accurate and runnable

## Release Checklist (after plan execution)

- [ ] Merge `init-version` to `main`
- [ ] Configure PyPI API token (or trusted publishing) in GitHub repo settings
- [ ] Configure TestPyPI API token in GitHub repo settings
- [ ] Run TestPyPI workflow manually — verify package page
- [ ] `git tag v0.2.0 && git push origin v0.2.0`
- [ ] Create GitHub Release from `v0.2.0` tag
- [ ] Verify publish workflow completes successfully
- [ ] Verify `pip install fountain-py` works
- [ ] Verify https://pypi.org/project/fountain-py/ looks correct
