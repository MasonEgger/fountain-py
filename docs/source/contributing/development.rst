Development
===========

Setting Up Your Environment
---------------------------

The fountain-py project uses `uv <https://docs.astral.sh/uv/>`_ for dependency management and `just <https://github.com/casey/just>`_ as a command runner.

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/MasonEgger/fountain-py.git
   cd fountain-py

   # Install dev and docs dependencies
   just dev && uv sync --group docs

   # Verify everything works
   just test

Project Structure
-----------------

::

   fountain-py/
   ├── src/fountain/          # Library source code
   │   ├── __init__.py        # Public API exports
   │   ├── parser.py          # Two-pass Fountain parser
   │   ├── elements.py        # ElementType enum, FountainElement dataclass
   │   ├── document.py        # FountainDocument container
   │   ├── renderer.py        # HTMLRenderer and FountainRenderer
   │   └── py.typed           # PEP 561 type hint marker
   ├── tests/                 # Test suite
   │   ├── test_parser.py     # Parser tests
   │   ├── test_renderer.py   # Renderer tests
   │   ├── test_document.py   # Document analysis tests
   │   ├── test_edge_cases.py # Spec compliance and edge cases
   │   └── fixtures/          # Sample .fountain files
   ├── docs/source/           # Sphinx documentation
   └── pyproject.toml         # Project configuration

Code Style
----------

The project uses `ruff <https://docs.astral.sh/ruff/>`_ for linting and formatting, and `mypy <https://mypy.readthedocs.io/>`_ in strict mode for type checking.

.. code-block:: bash

   just lint         # Check for lint issues
   just fix          # Auto-fix lint issues
   just format       # Format code
   just type-check   # Run mypy strict

Key conventions:

- Line length: 120 characters
- Target: Python 3.10+
- All functions must have type annotations
- All code files start with a 2-line ``# ABOUTME:`` comment

Making Changes
--------------

1. Create a branch from ``main``
2. Write tests first (TDD, see :doc:`testing`)
3. Make your changes
4. Run ``just test`` to verify everything passes
5. Open a pull request against ``main``

Available Commands
------------------

Run ``just --list`` to see all commands.
Key ones:

.. code-block:: bash

   just test           # Full quality check (tests, lint, type-check, doctests)
   just unit-test      # Run only unit tests
   just unit-test-cov  # Tests with coverage report
   just lint           # Lint check
   just format         # Auto-format code
   just type-check     # mypy strict mode
   just docs           # Serve docs locally with live reload
   just docs-build     # Build docs once
