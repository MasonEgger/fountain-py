Testing
=======

The fountain-py test suite uses `pytest <https://docs.pytest.org/>`_ with strict markers and doctest integration.
It targets 99%+ code coverage.

Running Tests
-------------

.. code-block:: bash

   # Full quality check (tests + coverage + doctests + lint + type-check + format)
   just test

   # Unit tests only
   just unit-test

   # Unit tests with HTML coverage report
   just unit-test-cov

   # Run a specific test file
   uv run pytest tests/test_parser.py

   # Run a specific test method
   uv run pytest tests/test_edge_cases.py::TestSpecCompliance::test_section_level_1

   # Run doctests in source modules
   uv run pytest --doctest-modules src/

   # Run Sphinx doctests in documentation
   just doctest

Test Organization
-----------------

- ``tests/test_parser.py``: Core parser features
- ``tests/test_renderer.py``: HTML and Fountain renderers (``TestHTMLRenderer``, ``TestFountainRenderer``)
- ``tests/test_document.py``: Document analysis methods
- ``tests/test_edge_cases.py``: Edge cases and spec compliance (``TestSpecCompliance`` class)
- ``tests/test_quickstart_examples.py``: Validates all quickstart documentation examples
- ``tests/conftest.py``: Shared fixtures and sample ``.fountain`` file loading

Writing Tests
-------------

Follow test-driven development:

1. **RED**: Write a failing test that describes the expected behavior
2. **GREEN**: Write the minimal code to make it pass
3. **REFACTOR**: Clean up while keeping tests green

Guidelines:

- **Test your logic**, not frameworks.
  Don't test that pytest works or that Python dicts work.
- **Test behavior and outcomes**, not implementation details.
- **Spec compliance tests** go in ``TestSpecCompliance`` in ``test_edge_cases.py``.
- **Renderer-specific tests** go in the appropriate renderer test class in ``test_renderer.py``.
- Use descriptive test names that explain the scenario.

Example:

.. code-block:: python

   def test_forced_scene_heading_protects_ellipsis(self):
       """Ellipsis at line start should not trigger forced scene heading."""
       doc = self.parser.parse("...HELLO")
       assert doc.elements[0].type == ElementType.ACTION

Coverage
--------

The project maintains 99%+ code coverage.
After running ``just unit-test-cov``, open ``htmlcov/index.html`` to view the coverage report.
