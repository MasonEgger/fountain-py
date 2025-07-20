fountain-py: Professional Fountain Script Parser
================================================

.. image:: https://img.shields.io/pypi/v/fountain-py.svg
   :target: https://pypi.org/project/fountain-py/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/fountain-py.svg
   :target: https://pypi.org/project/fountain-py/
   :alt: Python versions

.. image:: https://img.shields.io/badge/coverage-99%25-brightgreen.svg
   :target: https://github.com/MasonEgger/fountain-py
   :alt: Test coverage

**fountain-py** is a robust Python library for parsing and rendering Fountain markup, the plain-text screenwriting format embraced by writers and filmmakers worldwide. Transform your scripts into structured data, analyze character dynamics, and export to multiple formats with ease.

Why fountain-py?
----------------

Fountain is the markdown of screenwriting—a simple, human-readable format that lets writers focus on storytelling. **fountain-py** makes it easy to:

- **Parse** Fountain scripts into structured, analyzable data
- **Extract** insights about characters, dialogue, and scene structure
- **Render** scripts to HTML with professional screenplay formatting
- **Build** custom tools for script analysis and production workflows

Key Features
------------

✨ **Complete Fountain 1.1 Support**
   Full implementation of the Fountain specification including scenes, dialogue, action, transitions, dual dialogue, and inline formatting

🎭 **Script Intelligence**
   Extract character lists, analyze dialogue distribution, calculate scene statistics, and identify structural patterns

🎨 **Flexible Rendering**
   Generate HTML with customizable CSS, preserve round-trip formatting, or create custom renderers for any output format

🚀 **Production Ready**
   Type-safe API with comprehensive annotations, 99%+ test coverage, and battle-tested parsing engine

🔧 **Developer Experience**
   Clean, intuitive API design with detailed documentation, practical examples, and extensible architecture

Quick Example
-------------

Parse a script and extract insights in just a few lines:

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderer import HTMLRenderer
   
   # Parse a Fountain script
   parser = FountainParser()
   document = parser.parse_file("big_fish.fountain")
   
   # Analyze the script
   characters = document.get_characters()
   stats = document.get_statistics()
   print(f"Pages: {stats['pages']:.1f}")
   print(f"Scenes: {stats['scenes']}")
   print(f"Characters: {', '.join(characters[:5])}")
   
   # Render to HTML
   renderer = HTMLRenderer()
   html = renderer.render(document)
   
   # Save the formatted screenplay
   with open("big_fish.html", "w") as f:
       f.write(html)

Start Here
----------

**🚀 Installation**
   Get fountain-py up and running with pip or uv. Includes platform-specific guides and troubleshooting.
   :doc:`Read the installation guide <installation>`

**⚡ Quick Start**
   Learn the basics in 10 minutes. Parse your first script, extract character data, and render to HTML.
   :doc:`Start the tutorial <quickstart>`

**📖 User Guide**
   Comprehensive guide to parsing, elements, rendering, and advanced features.
   :doc:`Browse the user guide <user-guide/index>`

**🛠️ API Reference**
   Complete API documentation with detailed class and method references.
   :doc:`View API docs <api/index>`

Project Links
-------------

- **GitHub Repository**: `github.com/MasonEgger/fountain-py <https://github.com/MasonEgger/fountain-py>`_
- **PyPI Package**: `pypi.org/project/fountain-py <https://pypi.org/project/fountain-py/>`_
- **Issue Tracker**: `Report bugs or request features <https://github.com/MasonEgger/fountain-py/issues>`_

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   Home <self>
   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user-guide/index
   user-guide/parsing
   user-guide/elements
   user-guide/rendering
   user-guide/advanced

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/parser
   api/document
   api/elements
   api/renderer

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   contributing/index
   contributing/development
   contributing/testing
   contributing/documentation

.. toctree::
   :maxdepth: 1
   :caption: Reference

   changelog

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`