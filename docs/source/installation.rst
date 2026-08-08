Installation
============

**fountain-py** is not on PyPI yet (the 0.1.0 release is pending), so install it from source for now.
Once it is published, ``pip install fountain-py`` will be the one-line option.

Requirements
------------

- **Python 3.10 or higher** (3.10, 3.11, 3.12, 3.13, 3.14 supported)
- No external dependencies for core functionality

Install from Source
-------------------

Install the latest code straight from GitHub:

.. code-block:: bash

   pip install git+https://github.com/MasonEgger/fountain-py.git

Or with `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: bash

   uv pip install git+https://github.com/MasonEgger/fountain-py.git

Verify the install:

.. code-block:: bash

   python -c "import fountain; print('fountain-py ready')"

After Publication
-----------------

Once fountain-py is on PyPI, install it with your usual package manager:

.. code-block:: bash

   pip install fountain-py
   # or
   uv add fountain-py

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
