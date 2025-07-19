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
test:
    uv run pytest

# Run tests with coverage report
test-cov:
    uv run pytest --cov=fountain --cov-report=html --cov-report=term

# Run linting checks
lint:
    uv run ruff check src/ tests/

# Format code
format:
    uv run ruff format src/ tests/

# Run type checking
type-check:
    uv run mypy src/

# Serve documentation locally
docs:
    uv run mkdocs serve

# Clean up temporary files
clean:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
    rm -rf build/ dist/ *.egg-info/

# Run all quality checks (lint, format check, type check)
check: lint type-check
    uv run ruff format --check src/ tests/

# Install pre-commit hooks
pre-commit-install:
    pre-commit install

# Run pre-commit on all files
pre-commit-all:
    pre-commit run --all-files