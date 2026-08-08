fountain-py
===========

.. image:: https://img.shields.io/badge/python-3.10%2B-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python versions

.. image:: https://img.shields.io/badge/coverage-99%25-brightgreen.svg
   :target: https://github.com/MasonEgger/fountain-py
   :alt: Test coverage

**fountain-py** is a Python library for parsing and rendering `Fountain <https://fountain.io/>`_, the plain-text screenwriting format.
It turns a Fountain script into structured Python objects you can analyze, and renders it back out as HTML or Fountain.

Features
--------

- Parses the Fountain syntax: scene headings, action, character cues, dialogue, dual dialogue, parentheticals, lyrics, transitions, centered text, sections, synopses, notes, and inline emphasis.
- Extracts characters, scenes, and statistics from a parsed script.
- Renders to HTML as a fragment, a standalone page with embedded CSS, or raw CSS, and round-trips back to clean Fountain.
- Reports parse problems (unclosed boneyard or notes, orphaned character cues) through a validation API.
- Pure Python, no runtime dependencies, fully type-hinted.

Quick Example
-------------

.. code-block:: python

   from fountain import FountainParser

   script = """Title: The Coffee Shop Connection
   Author: Jane Doe

   INT. COFFEE SHOP - DAY

   ALICE sits at a corner table, staring at her laptop.

   ALICE
   Come on, inspiration... where are you?
   """

   document = FountainParser().parse(script)

   print(document.metadata["title"])   # The Coffee Shop Connection
   print(document.get_characters())    # ['ALICE']

   # Render a standalone HTML file with embedded CSS
   with open("coffee_shop.html", "w", encoding="utf-8") as f:
       f.write(document.to_html())

Start Here
----------

- :doc:`Installation <installation>`: install from source (PyPI publication is pending).
- :doc:`Quick Start <quickstart>`: parse a screenplay and render it to HTML in a few minutes.
- :doc:`What Is Fountain? <explanation/what-is-fountain>`: the format, and what fountain-py does with it.
- :doc:`How fountain-py Works <explanation/pipeline>`: the parse, structure, and render pipeline.
- :doc:`API Reference <api/parser>`: the class and method reference.

Project Links
-------------

- **GitHub Repository**: `github.com/MasonEgger/fountain-py <https://github.com/MasonEgger/fountain-py>`_
- **Documentation**: `masonegger.github.io/fountain-py <https://masonegger.github.io/fountain-py/>`_
- **Issue Tracker**: `Report bugs or request features <https://github.com/MasonEgger/fountain-py/issues>`_

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   Home <self>
   installation
   quickstart

.. toctree::
   :maxdepth: 1
   :caption: How-to Guides

   how-to/validate-a-file

.. toctree::
   :maxdepth: 2
   :caption: Explanation

   explanation/what-is-fountain
   explanation/pipeline
   explanation/roundtrip-and-notes

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user-guide/parsing
   user-guide/elements
   user-guide/rendering

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/parser
   api/document
   api/elements
   api/renderer

.. toctree::
   :maxdepth: 2
   :caption: Contributing

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
