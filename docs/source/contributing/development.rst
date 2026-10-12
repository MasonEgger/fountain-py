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
   just dev

   # Verify everything works
   just check

Project Structure
-----------------

::

   fountain-py/
   ├── src/fountain/          # Library source code
   │   ├── __init__.py        # Public API exports
   │   ├── parser.py          # Two-pass Fountain parser
   │   ├── elements.py        # ElementType enum, FountainElement dataclass
   │   ├── document.py        # FountainDocument container and JSON round trip
   │   ├── renderer.py        # HTMLRenderer and FountainRenderer
   │   ├── cli.py             # The ``fountain`` command-line interface
   │   ├── renderers/         # Plain text, FDX, and PDF renderers plus the renderer protocols
   │   └── py.typed           # PEP 561 type hint marker
   ├── tests/                 # Test suite
   │   ├── test_parser.py     # Parser tests
   │   ├── test_renderer.py   # HTML and Fountain renderer tests
   │   ├── test_document.py   # Document analysis and JSON tests
   │   ├── test_edge_cases.py # Spec compliance and edge cases
   │   ├── test_properties.py # Hypothesis property tests
   │   └── fixtures/          # Sample .fountain files
   ├── docs/source/           # Sphinx documentation
   └── pyproject.toml         # Project configuration

Code Style
----------

The project uses `ruff <https://docs.astral.sh/ruff/>`_ for linting and formatting, and `mypy <https://mypy.readthedocs.io/>`_ in strict mode for type checking.

.. code-block:: bash

   just fmt          # Format code and auto-fix lint issues
   just check        # Lint, format check, mypy strict, and tests

Key conventions:

- Line length: 120 characters
- Target: Python 3.11+ (tested on 3.11 through 3.15)
- All functions must have type annotations
- All code files start with a 2-line ``# ABOUTME:`` comment

Making Changes
--------------

1. Create a branch from ``main``
2. Write tests first (TDD, see :doc:`testing`)
3. Make your changes
4. Run ``just check`` to verify everything passes
5. Open a pull request against ``main``

Available Commands
------------------

Run ``just --list`` to see all commands.
Key ones:

.. code-block:: bash

   just check          # The gate: lint, format check, mypy strict, tests
   just test           # Run only the tests
   just test-cov       # Tests with coverage report
   just test-all       # Tests on every supported Python version
   just fmt            # Format code and auto-fix lint issues
   just doctest        # Sphinx doctests in the documentation pages
   just docs           # Serve docs locally with live reload
   just docs-build     # Build docs once
