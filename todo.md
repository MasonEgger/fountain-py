# PyPI Publishing — TODO

## Step 1: Update CHANGELOG for 0.1.0
- [x] 1. Rewrote as first release (not update) — comprehensive 0.1.0 changelog
- [x] 2. Documented full parser capabilities (spec compliance, all element types)
- [x] 3. Documented renderer API (render, render_page, get_css, CSS namespacing)
- [x] 4. Documented document analysis, type system, and quality metrics

## Step 2: Bump version
- [x] N/A — staying at 0.1.0 for first publish

## Step 3: Fix README accuracy
- [x] 1. Fixed Basic Usage (removed document.title, use metadata dict, show render vs render_page)
- [x] 2. Removed CLI section (__main__.py doesn't exist)
- [x] 3. Fixed Development section (just dev, correct just commands, removed pre-commit reference)
- [x] 4. Added Rendering Modes and Round-Trip sections

## Step 4: Harden publish workflow
- [ ] 1. Add test job before publish
- [ ] 2. Add build artifact upload/download pattern
- [ ] 3. Add environment declaration for deployment protection
- [ ] 4. Decide API token vs trusted publishing

## Step 5: Add TestPyPI workflow
- [ ] 1. Create .github/workflows/test-publish.yml
- [ ] 2. Configure for manual trigger + TestPyPI URL

## Step 6: Add build verification to CI
- [ ] 1. Add package build step to ci.yml
- [ ] 2. Add wheel contents verification
- [ ] 3. Add Sphinx doctest to CI

## Step 7: Verify and test locally
- [ ] 1. Build package
- [ ] 2. Test install in clean environment
- [ ] 3. Run full test suite
- [ ] 4. Clean up
