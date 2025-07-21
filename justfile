# List available commands
default:
    @just --list

# Install the package
install:
    uv pip install -e .

# Install the package in development mode with dev dependencies
dev:
    uv sync --dev

# Run tests
unit-test:
    uv run pytest

# Run tests with coverage report
unit-test-cov:
    uv run pytest --cov=fountain --cov-report=html --cov-report=term

# Run linting checks
lint:
    uv run ruff check src/ tests/

# Fix linting issues automatically
fix:
    uv run ruff check src/ tests/ --fix

# Format code
format:
    uv run ruff format src/ tests/

# Run type checking
type-check:
    uv run mypy src/

# Serve documentation locally
docs:
    uv run sphinx-autobuild docs/source docs/build/html

# Build documentation
docs-build:
    uv run sphinx-build -b html docs/source docs/build/html

# Run doctests (both pytest doctest modules and Sphinx doctests)
doctest:
    uv run pytest --doctest-modules src/
    uv run sphinx-build -b doctest docs/source docs/build/doctest

# Run doctests with coverage 
doctest-cov:
    uv run pytest --doctest-modules src/ --cov=fountain --cov-report=html --cov-report=term
    uv run sphinx-build -b doctest docs/source docs/build/doctest

# Check documentation links
docs-linkcheck:
    uv run sphinx-build -b linkcheck docs/source docs/build/linkcheck

# Clean documentation build artifacts
docs-clean:
    rm -rf docs/build/

# Clean up temporary files
clean:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
    rm -rf build/ dist/ *.egg-info/
    rm -rf docs/build/

# Run ruff format check only
check:
    uv run ruff format --check src/ tests/

# Run all quality checks (tests, coverage, lint, type check, fix, format check, doctests)
test: unit-test-cov doctest lint type-check fix check

# Install pre-commit hooks
pre-commit-install:
    pre-commit install

# Run pre-commit on all files
pre-commit-all:
    pre-commit run --all-files