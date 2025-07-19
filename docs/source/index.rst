fountain-py Documentation
=========================

**fountain-py** is a Python library for parsing Fountain markup, the screenwriting format used by writers and filmmakers worldwide.

Features
--------

✨ **Complete Fountain Support**: Parse all Fountain elements including scenes, dialogue, action, transitions, and formatting

🎭 **Element Analysis**: Extract characters, analyze dialogue patterns, and generate script statistics

🎨 **Multiple Output Formats**: Render to HTML with customizable CSS styling or back to Fountain format

🔧 **Developer Friendly**: Clean API with comprehensive type hints and detailed documentation

🧪 **Well Tested**: 99%+ test coverage with extensive edge case handling

Quick Example
-------------

.. code-block:: python

   from fountain import FountainParser
   
   # Parse a Fountain script
   parser = FountainParser()
   document = parser.parse_file("script.fountain")
   
   # Extract characters
   characters = document.get_characters()
   
   # Render to HTML
   from fountain.renderer import HTMLRenderer
   renderer = HTMLRenderer()
   html = renderer.render(document)

Getting Started
---------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

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
   :caption: Examples

   examples/index
   examples/basic-usage
   examples/script-analysis
   examples/custom-renderer
   examples/real-world

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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`