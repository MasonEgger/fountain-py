Documentation
=============

fountain-py uses `Sphinx <https://www.sphinx-doc.org/>`_ with the `Furo <https://pradyunsg.me/furo/>`_ theme. Documentation is hosted on GitHub Pages.

Building Docs Locally
---------------------

.. code-block:: bash

   # Serve docs with live reload (auto-rebuilds on changes)
   just docs

   # Build docs once
   just docs-build

   # Run doctests in documentation
   just doctest

The built docs will be in ``docs/build/html/``. Open ``docs/build/html/index.html`` in a browser.

Documentation Structure
-----------------------

::

   docs/source/
   ├── index.rst              # Landing page
   ├── installation.rst       # Installation guide
   ├── quickstart.rst         # Tutorial
   ├── changelog.rst          # Release notes
   ├── how-to/                # Task-focused how-to guides
   ├── explanation/           # Concepts and design
   ├── reference/             # Parsing behavior, elements, rendering, CSS classes
   │   ├── parsing-behavior.rst
   │   ├── elements.rst
   │   └── rendering.rst
   ├── api/                   # Auto-generated API reference
   │   ├── parser.rst
   │   ├── document.rst
   │   ├── elements.rst
   │   └── renderer.rst
   └── contributing/          # Contributor guides
       ├── development.rst
       ├── testing.rst
       └── documentation.rst

Writing Doctests
----------------

All code examples in documentation should be valid doctests. Sphinx runs them during ``just doctest`` and they're part of CI.

In ``.rst`` files, use ``.. doctest::`` blocks:

.. code-block:: rst

   .. doctest::

       >>> from fountain import FountainParser
       >>> parser = FountainParser()
       >>> doc = parser.parse("INT. HOUSE - DAY")
       >>> doc.elements[0].type.value
       'scene_heading'

In Python source, doctests go in docstrings and are run by ``pytest --doctest-modules``.

RST Conventions
---------------

- Use ``:doc:`path``` for cross-references between pages
- Use ``:class:`~fountain.parser.FountainParser``` for API references
- Code examples use ``.. code-block:: python`` for non-tested code, ``.. doctest::`` for tested code
- Keep line length reasonable for readability in source
