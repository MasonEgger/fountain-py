Installation
============

**fountain-py** is on PyPI, so install it with your usual package manager.

Requirements
------------

- **Python 3.10 or higher** (3.10, 3.11, 3.12, 3.13, 3.14 supported)
- No external dependencies for core features

Install
-------

.. code-block:: bash

   pip install fountain-py

Or with `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: bash

   uv add fountain-py

Verify the install:

.. code-block:: bash

   python -c "import fountain; print('fountain-py ready')"

Install the Latest Unreleased Code
----------------------------------

To install straight from the main branch on GitHub, ahead of the next release:

.. code-block:: bash

   pip install git+https://github.com/MasonEgger/fountain-py.git

Development Installation
------------------------

To contribute or work against a local checkout:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/MasonEgger/fountain-py.git
   cd fountain-py

   # Install all development and docs dependencies (uv recommended)
   uv sync --dev && uv sync --group docs

   # Install in editable mode
   uv pip install -e .

With pip instead of uv:

.. code-block:: bash

   pip install -e ".[dev,docs]"
