# ABOUTME: Task runner recipes; `just check` is the local gate, and CI runs the same steps.
# `just test-all` runs the supported Python version matrix locally; the docs recipes build and serve Sphinx.

default:
    @just --list

# Sync dev and docs dependencies (mypy reads docs/source/conf.py, which imports sphinx)
dev:
    uv sync --group docs

# The gate: lint, format check, strict type check, tests (doctests included)
check:
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy .
    uv run pytest

# Format and auto-fix lint issues
fmt:
    uv run ruff format .
    uv run ruff check --fix .

test:
    uv run pytest

# Tests with a coverage report (informational, never a gate)
test-cov:
    uv run pytest --cov=fountain --cov-report=html --cov-report=term

test-all:
    #!/usr/bin/env bash
    set -euo pipefail
    for python_version in 3.11 3.12 3.13 3.14 3.15; do
        uv run --python "$python_version" -m pytest
    done

# Serve documentation locally with live reload
docs:
    uv run sphinx-autobuild docs/source docs/build/html

docs-build:
    uv run sphinx-build -b html docs/source docs/build/html

# Run the Sphinx doctests in the .rst pages (module doctests run under `just test`)
doctest:
    uv run sphinx-build -b doctest docs/source docs/build/doctest

docs-linkcheck:
    uv run sphinx-build -b linkcheck docs/source docs/build/linkcheck

docs-clean:
    rm -rf docs/build/

# Clean up caches and build artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
    rm -rf build/ dist/ *.egg-info/
    rm -rf docs/build/
