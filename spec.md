# Code Review: fountain-py

## Context

Full code review of the fountain-py library against: global CLAUDE.md rules, /python skill standards, and general Python best practices. Optimizing for simplicity, speed, and good architecture.

**Overall assessment: This is a high-quality, well-structured codebase.** The issues below are refinements, not fundamental problems. The architecture (two-pass parser, immutable elements, clean pipeline) is solid.

---

## Findings

### 1. Missing ABOUTME Comments (Rule Violation)

**Files missing the required 2-line ABOUTME header:**
- `src/fountain/renderer.py` — has a docstring but no ABOUTME
- `src/fountain/__init__.py` — has a docstring but no ABOUTME
- `tests/conftest.py`
- `tests/test_parser.py`
- `tests/test_renderer.py`
- `tests/test_document.py`
- `tests/test_quickstart_examples.py`

**Rule:** "All code files should start with a brief 2-line comment explaining what the file does. Only the first line starts with 'ABOUTME: '"

### 2. Dead Commented-Out Code in `renderer.py:984-1074`

~90 lines of commented-out example renderer code (MarkdownRenderer, StatsRenderer). Per Clean Code rules: "Remove any leftover debug or commented-out code."

This belongs in documentation (e.g., `docs/source/user-guide/rendering.rst`), not as dead code in the source file.

**Action:** Remove the commented-out code block.

### 3. `_escape_html` Reinvents `html.escape` (Simplicity)

`renderer.py:460-488` — Custom HTML escaping that duplicates `html.escape()` from stdlib. The stdlib version handles the same entities and is battle-tested.

**Action:** Replace with `import html` and `html.escape(text, quote=True)`. Note: stdlib uses `&#x27;` for `'` which matches the current behavior.

### 4. `_get_css` Theme Fallback Mutates State (Bad Pattern)

`renderer.py:683-689` — The "else" branch temporarily mutates `self.theme`, calls itself recursively, then restores. This is fragile and not thread-safe.

```python
# Current (bad):
old_theme = self.theme
self.theme = "default"
css = self._get_css()
self.theme = old_theme
return css

# Better (simple):
return self._get_default_css()
```

**Action:** Extract the CSS string into a module-level constant or a `_get_default_css()` method, and have `_get_css` just return it (since only one theme exists).

### 5. `get_statistics` Iterates Elements ~17x (Performance + Simplicity)

`document.py:298-309` — Calls `get_characters()` (1 pass), `get_scenes()` (1 pass), then loops through all 15 `ElementType` values (15 passes). That's 17 full iterations over elements.

**Action:** Single-pass implementation using a `Counter`:

```python
from collections import Counter
type_counts = Counter(el.type for el in self.elements)
```

### 6. Title Page Rendering Is Highly Repetitive (DRY)

`renderer.py:149-259` — 15+ nearly identical `if "field" in metadata:` blocks. Each follows the pattern: check key, format HTML, append.

**Action:** Use a data-driven approach with an ordered list of `(key, css_class, prefix)` tuples. Keeps the rendering logic DRY and makes adding new fields trivial.

### 7. `title_order` List Duplicated Between Renderers (DRY)

Both `HTMLRenderer._render_title_page` and `FountainRenderer._render_title_page` maintain separate but overlapping lists of known/ordered title page fields.

**Action:** Extract to a module-level constant `TITLE_PAGE_FIELD_ORDER` shared by both renderers.

### 8. `_is_dialogue_following` Pattern Chain (Simplicity)

`parser.py:834-849` — A 14-line `or` chain checking every structural pattern. Hard to read and easy to miss a pattern.

**Action:** Collect structural patterns into a tuple and use `any()`:

```python
STRUCTURAL_PATTERNS = (
    self.SCENE_HEADING_PATTERN, self.FORCED_SCENE_HEADING_PATTERN,
    self.TRANSITION_PATTERN, ...
)
return not any(p.match(next_line) for p in STRUCTURAL_PATTERNS)
```

Plus the special `[[...]]` check as a separate condition.

### 9. `__init__.py` Has Exports (Python Skill Conflict)

The /python skill says "Empty `__init__.py` — never add anything to `__init__.py`". However, this is a published library where `from fountain import FountainParser` is the primary API. **Keeping the exports is the right call here** — the skill rule is better suited to application code. No action needed, but noting the deliberate deviation.

### 10. `Any` Type Usage (Python Skill Conflict)

The /python skill says "No `Any`". Used in `elements.py` (`dict[str, Any]`), `document.py`, and `parser.py` for metadata. The metadata dict genuinely holds heterogeneous types (str, int, bool, nested FountainElement). A precise union type would be complex and fragile.

**Action:** Define a `MetadataValue` type alias to at least narrow the type surface:

```python
MetadataValue = Union[str, int, bool, list["FountainElement"], "FountainElement", None]
```

This is more informative than `Any` while remaining practical.

### 11. `format_type: str` Could Be a StrEnum (Type Safety)

`elements.py:128` — `FormatSpan.format_type` is an untyped string. Values are one of `"bold"`, `"italic"`, `"underline"`, `"bold_italic"`. A `StrEnum` would prevent typos and improve IDE support.

**Caveat:** `StrEnum` requires Python 3.11+. Since the project targets 3.9+, use a regular string `Literal` type instead:

```python
FormatType = Literal["bold", "italic", "underline", "bold_italic"]
```

### 12. `_render_element` Long If/Elif Chain (Minor)

`renderer.py:261-337` — 15-branch if/elif for element types. A dispatch dict would be cleaner, but the per-type special handling (scene numbers, character extensions, dual dialogue) makes a pure dispatch impractical. **No action needed** — the current approach is readable and each branch is small.

### 13. `render()` Should Return Fragments, Not Full Pages (Architecture)

The current `HTMLRenderer.render()` emits a `<style>` block + `<div>` wrapper — a near-complete HTML page. This makes the renderer unsuitable for embedding (mkdocs plugins, fence handlers, web frameworks) where CSS is managed externally and only an HTML fragment is needed.

**Action:** Restructure `HTMLRenderer` so that:

- **`render(doc)` returns a pure HTML fragment** — just the `<div class="fountain-script">...</div>` with element markup inside. No `<style>` tag. This is the universal default suitable for embedding anywhere.
- **`render_page(doc)` returns a full standalone page** — the fragment wrapped with the `<style>` block. For users who want a self-contained HTML file.
- **`get_css()` becomes a public method** — returns the CSS string (no `<style>` tags) so consumers can inject it once per page however they need (e.g., mkdocs plugin adds it to `extra_css`, a web app puts it in a `<link>`, etc.).

This is a breaking change to `render()` — document it in CHANGELOG.

### 14. Namespace CSS Classes (Future-Proofing)

Current CSS classes use generic names: `.action`, `.character`, `.dialogue`, `.note`, `.centered`. These will collide with theme CSS in mkdocs, Material, Bootstrap, or any other CSS framework.

**Action:** Prefix all CSS classes with `fountain-`:
- `.action` → `.fountain-action`
- `.character` → `.fountain-character`
- `.dialogue` → `.fountain-dialogue`
- `.scene-heading` → `.fountain-scene-heading`
- etc.

The outer wrapper `.fountain-script` is already namespaced. Inner classes need the same treatment. This affects:
- `_render_element()` — all `class=` attributes
- `_render_title_page()` — all `class=` attributes
- `_render_dual_dialogue()` — all `class=` attributes
- `_get_css()` — all CSS selectors
- Test assertions that check for specific class names

This is a breaking change for anyone targeting the current CSS classes — do it now before the library is widely adopted.

---

## Items NOT Changing (Confirmed Good)

- **Architecture**: Two-pass parser, immutable elements, clean pipeline — excellent
- **Regex compilation**: All patterns compiled at class level — correct
- **Type hints**: Full coverage, strict mypy — excellent
- **Import organization**: Clean, absolute imports — correct
- **Naming**: Descriptive, evergreen, no generic names — excellent
- **Test suite**: 200+ behavioral tests, good TDD patterns, comprehensive spec coverage — excellent
- **Error handling**: Appropriate boundary validation, no silent swallowing — good
- **Dataclass/Enum usage**: Clean, proper patterns — good

---

## Implementation Plan

Steps are ordered so that the largest structural changes (renderer API, CSS namespacing) happen first, then smaller cleanups build on top.

### Step 1: Namespace CSS Classes (Finding #14)
**File:** `renderer.py`
Prefix all inner CSS classes with `fountain-`. This touches `_render_element`, `_render_title_page`, `_render_dual_dialogue`, and the CSS string. Do this first since later steps (DRY title page, fragment rendering) will build on the new class names.

### Step 2: Restructure `HTMLRenderer` — Fragment vs Page (Finding #13)
**File:** `renderer.py`
- Rename current `render()` → `render_page()` (full HTML with `<style>`)
- New `render()` returns fragment only (no `<style>`, just the `<div class="fountain-script">` tree)
- Make `get_css()` public — returns raw CSS string (no `<style>` tags) for external consumers
- Extract CSS string into a module-level constant `DEFAULT_CSS`
- This also resolves Finding #4 (`_get_css` theme fallback)

### Step 3: Replace `_escape_html` with `html.escape` (Finding #3)
**File:** `renderer.py` — add `import html`, replace method body

### Step 4: DRY Up Title Page Rendering (Findings #6, #7)
**File:** `renderer.py`
- Extract `TITLE_PAGE_FIELD_ORDER` as a module-level constant shared by both renderers
- Refactor `HTMLRenderer._render_title_page` to data-driven approach
- Refactor `FountainRenderer._render_title_page` to use the same constant

### Step 5: Remove Dead Code (Finding #2)
**File:** `renderer.py:984-1074` — delete commented-out example renderers

### Step 6: Simplify `_is_dialogue_following` (Finding #8)
**File:** `parser.py` — collect structural patterns into a tuple, use `any()`

### Step 7: Optimize `get_statistics` to Single Pass (Finding #5)
**File:** `document.py` — use `Counter`

### Step 8: Add `FormatType` Literal and `MetadataValue` Type Alias (Findings #10, #11)
**File:** `elements.py` — add type aliases, update `FormatSpan.format_type` annotation

### Step 9: Add Missing ABOUTME Comments (Finding #1)
**Files:** `renderer.py`, `__init__.py`, `conftest.py`, `test_parser.py`, `test_renderer.py`, `test_document.py`, `test_quickstart_examples.py`

### Step 10: Update Tests
All renderer tests will need CSS class name updates (`scene-heading` → `fountain-scene-heading`, etc.) and `render()` → `render_page()` where tests expect CSS output. Add new tests for `render()` fragment output and `get_css()`.

### Step 11: Update Documentation
- Update `docs/source/user-guide/rendering.rst` with new API (`render` vs `render_page` vs `get_css`)
- Update docstrings/doctests throughout `renderer.py`
- Update CHANGELOG.md with breaking changes

### Step 12: Run Full Test Suite
**Command:** `just test` — verify all changes pass tests, coverage, lint, type-check, format

---

## Verification

After all changes:
1. `just test` — must pass all tests, doctests, lint, type-check, format check
2. `just unit-test-cov` — coverage must remain at 99%+
3. Verify round-trip tests still pass (parse → render → parse)
4. Verify `render()` returns no `<style>` tags
5. Verify `render_page()` returns full HTML with CSS
6. Verify `get_css()` returns raw CSS string
7. Verify no CSS class collisions with generic names (grep for bare `.action`, `.character`, etc.)
