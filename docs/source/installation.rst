Installation
============

**fountain-py** is available on PyPI and can be installed using standard Python package managers.

Requirements
------------

- **Python 3.9 or higher** (3.9, 3.10, 3.11, 3.12, 3.13 supported)
- No external dependencies for core functionality

Quick Install
-------------

.. code-block:: bash

   pip install fountain-py

Installation Methods
--------------------

Using pip
~~~~~~~~~

.. code-block:: bash

   # Install the latest stable version
   pip install fountain-py
   
   # Install a specific version
   pip install fountain-py==0.1.0
   
   # Upgrade to the latest version
   pip install --upgrade fountain-py

Using uv
~~~~~~~~~

.. code-block:: bash

   # Install fountain-py using uv
   uv pip install fountain-py
   
   # Add to an existing project
   uv add fountain-py

Using Poetry
~~~~~~~~~~~~

.. code-block:: bash

   poetry add fountain-py

Using Pipenv
~~~~~~~~~~~~

.. code-block:: bash

   pipenv install fountain-py

Development Installation
------------------------

To contribute to fountain-py or work with the latest development version:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/MasonEgger/fountain-py.git
   cd fountain-py

Using uv (Recommended for Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install all development dependencies
   uv sync --dev
   
   # Install in editable mode
   uv pip install -e .

Using pip
~~~~~~~~~

.. code-block:: bash

   # Install in editable mode with dev dependencies
   pip install -e ".[dev,docs]"