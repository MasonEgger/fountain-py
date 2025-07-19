# Fountain-Py Package Structure Refactor Plan

## Executive Summary

The current repository structure deviates from Python packaging best practices, with a confusing nested directory structure and missing essential files. This refactor plan outlines the steps to transform the repository into a professional, standards-compliant Python package.

## Current Issues

### 1. Structural Problems
- **Nested directory confusion**: `fountain-py/fountain-py/` creates unnecessary nesting
- **Scattered files**: Test scripts and examples are in the root directory
- **Missing standard directories**: No `docs/`, `examples/`, or `.github/` directories

### 2. Missing Essential Files
- **LICENSE**: Required for open-source distribution
- **CHANGELOG.md**: Version history tracking
- **CONTRIBUTING.md**: Contributor guidelines
- **Pre-commit configuration**: Code quality automation
- **CI/CD workflows**: Automated testing and deployment

### 3. Development Experience
- **No Makefile**: Common tasks require manual commands
- **Missing development tools**: No tox.ini or noxfile.py
- **Incomplete documentation structure**: No proper docs setup

## Proposed Structure

```
fountain-py/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── workflows/
│       ├── ci.yml
│       ├── publish.yml
│       └── docs.yml
├── docs/
│   ├── api/
│   │   ├── parser.md
│   │   ├── document.md
│   │   ├── renderer.md
│   │   └── elements.md
│   ├── examples/
│   │   ├── basic_usage.md
│   │   └── advanced_usage.md
│   ├── index.md
│   ├── installation.md
│   └── mkdocs.yml
├── examples/
│   ├── convert_macbeth.py
│   ├── simple_parse.py
│   ├── custom_renderer.py
│   └── README.md
├── src/
│   └── fountain/
│       ├── __init__.py
│       ├── document.py
│       ├── elements.py
│       ├── parser.py
│       ├── renderer.py
│       └── py.typed
├── tests/
│   ├── fixtures/
│   │   ├── simple_script.fountain
│   │   ├── complex_script.fountain
│   │   └── edge_cases.fountain
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_document.py
│   ├── test_elements.py
│   ├── test_parser.py
│   ├── test_renderer.py
│   └── test_integration.py
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── CLAUDE.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── pyproject.toml
└── uv.lock
```

## Implementation Steps

### Phase 1: Restructure Directories (Priority: Critical)

1. **Flatten the nested structure**
   ```bash
   # Move all contents from fountain-py/fountain-py/ to fountain-py/
   mv fountain-py/fountain-py/* fountain-py/
   mv fountain-py/fountain-py/.* fountain-py/ 2>/dev/null || true
   rmdir fountain-py/fountain-py/
   ```

2. **Create standard directories**
   ```bash
   mkdir -p .github/workflows
   mkdir -p .github/ISSUE_TEMPLATE
   mkdir -p docs/api
   mkdir -p docs/examples
   mkdir -p examples
   mkdir -p tests/fixtures
   ```

3. **Move files to appropriate locations**
   ```bash
   # Move example scripts
   mv convert_macbeth.py examples/
   mv test_macbeth_conversion.py examples/
   mv macbeth.* examples/ 2>/dev/null || true
   
   # Move documentation
   mv old-plan.md docs/archive/ 2>/dev/null || true
   mv scratchpad.md docs/archive/ 2>/dev/null || true
   ```

### Phase 2: Add Essential Files (Priority: High)

1. **Create LICENSE file**
   ```
   MIT License

   Copyright (c) 2024 Mason Egger

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction...
   ```

2. **Create CHANGELOG.md**
   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
   and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

   ## [Unreleased]

   ## [0.1.0] - 2024-06-15
   ### Added
   - Initial release of fountain-py
   - Basic Fountain parser implementation
   - HTML renderer
   - Support for all major Fountain elements
   ```

3. **Create CONTRIBUTING.md**
   ```markdown
   # Contributing to Fountain-Py

   We love your input! We want to make contributing to this project as easy and transparent as possible.

   ## Development Process
   1. Fork the repo and create your branch from `main`
   2. If you've added code that should be tested, add tests
   3. Ensure the test suite passes
   4. Make sure your code follows the style guidelines
   5. Issue that pull request!
   ```

4. **Create .pre-commit-config.yaml**
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.4.7
       hooks:
         - id: ruff
         - id: ruff-format
     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.10.0
       hooks:
         - id: mypy
           args: [--strict]
   ```

### Phase 3: Development Tools (Priority: Medium)

1. **Create Makefile**
   ```makefile
   .PHONY: install dev test lint format type-check docs clean

   install:
   	uv pip install -e .

   dev:
   	uv pip install -e ".[dev]"

   test:
   	uv run pytest

   test-cov:
   	uv run pytest --cov=fountain --cov-report=html --cov-report=term

   lint:
   	uv run ruff check src/ tests/

   format:
   	uv run ruff format src/ tests/

   type-check:
   	uv run mypy src/

   docs:
   	uv run mkdocs serve

   clean:
   	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
   	find . -type f -name "*.pyc" -delete
   	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
   ```

2. **Create py.typed marker**
   ```bash
   touch src/fountain/py.typed
   ```

3. **Create conftest.py for pytest**
   ```python
   """Pytest configuration and fixtures."""
   import pytest
   from pathlib import Path

   @pytest.fixture
   def fixtures_dir():
       """Return the path to the fixtures directory."""
       return Path(__file__).parent / "fixtures"
   ```

### Phase 4: CI/CD Setup (Priority: High)

1. **Create .github/workflows/ci.yml**
   ```yaml
   name: CI

   on:
     push:
       branches: [ main ]
     pull_request:
       branches: [ main ]

   jobs:
     test:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

       steps:
       - uses: actions/checkout@v4
       - name: Install uv
         uses: astral-sh/setup-uv@v3
       - name: Set up Python ${{ matrix.python-version }}
         run: uv python install ${{ matrix.python-version }}
       - name: Install dependencies
         run: |
           uv venv
           uv pip install -e ".[dev]"
       - name: Run tests
         run: uv run pytest --cov=fountain
       - name: Run linter
         run: uv run ruff check src/ tests/
       - name: Run type checker
         run: uv run mypy src/
   ```

2. **Create .github/workflows/publish.yml**
   ```yaml
   name: Publish to PyPI

   on:
     release:
       types: [published]

   jobs:
     publish:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v4
       - name: Install uv
         uses: astral-sh/setup-uv@v3
       - name: Build package
         run: uv build
       - name: Publish to PyPI
         env:
           UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
         run: uv publish
   ```

### Phase 5: Documentation Enhancement (Priority: Medium)

1. **Create mkdocs.yml**
   ```yaml
   site_name: Fountain-Py Documentation
   site_description: A Python library for parsing Fountain markup
   site_author: Mason Egger
   site_url: https://fountain-py.readthedocs.io

   theme:
     name: material
     features:
       - navigation.sections
       - navigation.expand
       - toc.integrate

   nav:
     - Home: index.md
     - Installation: installation.md
     - Examples:
       - Basic Usage: examples/basic_usage.md
       - Advanced Usage: examples/advanced_usage.md
     - API Reference:
       - Parser: api/parser.md
       - Document: api/document.md
       - Renderer: api/renderer.md
       - Elements: api/elements.md

   plugins:
     - search
     - mkdocstrings:
         handlers:
           python:
             paths: [src]
   ```

2. **Update pyproject.toml**
   - Add `py.typed` to package data
   - Update build configuration
   - Add additional tool configurations

### Phase 6: Update Documentation (Priority: Low)

1. **Enhance README.md**
   - Add badges (CI status, coverage, PyPI version)
   - Improve installation instructions
   - Add quick start guide
   - Link to full documentation

2. **Create examples/README.md**
   - Explain each example
   - Provide usage instructions
   - Include expected outputs

## Migration Checklist

- [ ] Backup current repository
- [ ] Create new branch for refactor
- [ ] Flatten directory structure
- [ ] Create standard directories
- [ ] Move files to appropriate locations
- [ ] Add LICENSE file
- [ ] Add CHANGELOG.md
- [ ] Add CONTRIBUTING.md
- [ ] Create Makefile
- [ ] Set up pre-commit
- [ ] Add py.typed marker
- [ ] Set up GitHub Actions
- [ ] Configure documentation
- [ ] Update README.md
- [ ] Test everything works
- [ ] Merge to main branch
- [ ] Tag release

## Benefits

1. **Professional Structure**: Follows Python packaging standards
2. **Better Developer Experience**: Easier to contribute and maintain
3. **Automated Quality**: Pre-commit hooks and CI/CD
4. **Clear Documentation**: Proper docs structure with mkdocs
5. **Type Safety**: py.typed marker for type checking
6. **Easy Publishing**: Automated PyPI releases

## Timeline

- **Week 1**: Complete Phase 1-3 (Critical restructuring)
- **Week 2**: Complete Phase 4-5 (CI/CD and docs)
- **Week 3**: Complete Phase 6 and testing
- **Week 4**: Review, refine, and release

## Conclusion

This refactor will transform fountain-py from a functional but non-standard structure into a professional Python package that follows community best practices. The changes will make the project more maintainable, easier to contribute to, and ready for wider adoption.