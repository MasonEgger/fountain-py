Installation
============

**fountain-py** is available on PyPI and can be installed using pip or any Python package manager. This guide covers all installation methods, platform-specific considerations, and troubleshooting tips.

Requirements
------------

- **Python 3.9 or higher** (3.9, 3.10, 3.11, 3.12 supported)
- No external dependencies for core functionality
- Optional development dependencies for testing and documentation

Quick Install
-------------

The simplest way to install fountain-py is using pip:

.. code-block:: bash

   pip install fountain-py

To verify your installation:

.. code-block:: python

   import fountain
   print(fountain.__version__)  # Should print the version number

Installation Methods
--------------------

Using pip (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~

For most users, pip installation is the recommended approach:

.. code-block:: bash

   # Install the latest stable version
   pip install fountain-py
   
   # Install a specific version
   pip install fountain-py==0.1.0
   
   # Upgrade to the latest version
   pip install --upgrade fountain-py

Using uv (Fast Alternative)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

`uv <https://github.com/astral-sh/uv>`_ is a fast Python package installer written in Rust:

.. code-block:: bash

   # Install fountain-py using uv
   uv pip install fountain-py
   
   # Add to an existing project
   uv add fountain-py

Using Poetry
~~~~~~~~~~~~

If your project uses Poetry for dependency management:

.. code-block:: bash

   poetry add fountain-py

Using Pipenv
~~~~~~~~~~~~

For Pipenv users:

.. code-block:: bash

   pipenv install fountain-py

Development Installation
------------------------

To contribute to fountain-py or work with the latest development version:

Clone the Repository
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/MasonEgger/fountain-py.git
   cd fountain-py

Install with uv (Recommended for Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install all development dependencies
   uv sync --dev
   
   # Install in editable mode
   uv pip install -e .

Install with pip
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   
   # Install in editable mode with dev dependencies
   pip install -e ".[dev,docs]"

Platform-Specific Notes
-----------------------

Windows
~~~~~~~

Windows users may need to ensure Python is added to their PATH:

1. Download Python from `python.org <https://www.python.org/downloads/>`_
2. During installation, check "Add Python to PATH"
3. Open a new Command Prompt or PowerShell window
4. Verify installation: ``python --version``

For script execution permissions on Windows:

.. code-block:: powershell

   # If you encounter execution policy errors
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

macOS
~~~~~

macOS users should use Python 3, not the system Python 2:

.. code-block:: bash

   # Install Python 3 using Homebrew
   brew install python@3.12
   
   # Use pip3 explicitly if needed
   pip3 install fountain-py

Some macOS users may need to install certificates:

.. code-block:: bash

   # If you encounter SSL certificate errors
   pip install --upgrade certifi

Linux
~~~~~

Most Linux distributions include Python 3. Ensure pip is installed:

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3-pip
   
   # Fedora
   sudo dnf install python3-pip
   
   # Arch Linux
   sudo pacman -S python-pip

Virtual Environment Best Practices
----------------------------------

We strongly recommend using virtual environments to avoid dependency conflicts:

Using venv (Built-in)
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create a virtual environment
   python -m venv fountain-env
   
   # Activate it
   # On Linux/macOS:
   source fountain-env/bin/activate
   # On Windows:
   fountain-env\Scripts\activate
   
   # Install fountain-py
   pip install fountain-py
   
   # When done, deactivate
   deactivate

Using virtualenv
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install virtualenv if needed
   pip install virtualenv
   
   # Create and activate environment
   virtualenv fountain-env
   source fountain-env/bin/activate  # Linux/macOS
   fountain-env\Scripts\activate     # Windows
   
   # Install fountain-py
   pip install fountain-py

Using conda
~~~~~~~~~~~

.. code-block:: bash

   # Create a conda environment
   conda create -n fountain python=3.12
   conda activate fountain
   
   # Install fountain-py
   pip install fountain-py

Verifying Your Installation
---------------------------

After installation, verify everything is working correctly:

Basic Import Test
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Test basic import
   import fountain
   from fountain import FountainParser
   from fountain.renderer import HTMLRenderer
   
   print(f"fountain-py version: {fountain.__version__}")

Parse a Simple Script
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fountain import FountainParser
   
   # Create a parser
   parser = FountainParser()
   
   # Parse a simple script
   script = """
   FADE IN:
   
   INT. COFFEE SHOP - DAY
   
   SARAH enters, looking tired.
   
   SARAH
   One coffee, please. Make it strong.
   """
   
   document = parser.parse(script)
   print(f"Elements parsed: {len(document.elements)}")
   print(f"Characters found: {document.get_characters()}")

Check Available Features
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import fountain
   
   # List available classes and functions
   print("Available classes:")
   for item in dir(fountain):
       if not item.startswith('_'):
           print(f"  - {item}")

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

If you encounter ``ModuleNotFoundError: No module named 'fountain'``:

1. Ensure fountain-py is installed: ``pip show fountain-py``
2. Check you're using the correct Python: ``which python``
3. Verify your virtual environment is activated
4. Try reinstalling: ``pip install --force-reinstall fountain-py``

Version Conflicts
~~~~~~~~~~~~~~~~~

If you have version conflicts with other packages:

.. code-block:: bash

   # Create a fresh virtual environment
   python -m venv fresh-env
   source fresh-env/bin/activate  # or fresh-env\Scripts\activate on Windows
   pip install fountain-py

Permission Errors
~~~~~~~~~~~~~~~~~

If you encounter permission errors during installation:

.. code-block:: bash

   # Install for current user only
   pip install --user fountain-py
   
   # Or use sudo (Linux/macOS) - not recommended
   sudo pip install fountain-py

SSL Certificate Errors
~~~~~~~~~~~~~~~~~~~~~~

For SSL certificate verification errors:

.. code-block:: bash

   # Upgrade certificates
   pip install --upgrade certifi
   
   # Or temporarily disable SSL (not recommended)
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org fountain-py

Uninstalling
------------

To remove fountain-py:

.. code-block:: bash

   pip uninstall fountain-py

To remove all traces including dependencies (be careful):

.. code-block:: bash

   pip freeze | grep -E "fountain" | xargs pip uninstall -y

Next Steps
----------

Now that you have fountain-py installed:

- :doc:`Follow the Quick Start tutorial <quickstart>` to parse your first script
- :doc:`Read the User Guide <user-guide/index>` for comprehensive documentation
- :doc:`Browse Examples <examples/index>` for practical use cases
- :doc:`Check the API Reference <api/index>` for detailed documentation

Getting Help
------------

If you encounter issues:

1. Check the :doc:`troubleshooting section <#troubleshooting>` above
2. Search `existing issues <https://github.com/MasonEgger/fountain-py/issues>`_ on GitHub
3. Create a `new issue <https://github.com/MasonEgger/fountain-py/issues/new>`_ with:
   
   - Your Python version (``python --version``)
   - Your pip version (``pip --version``)
   - Complete error message
   - Steps to reproduce the issue