fountain-py
===========

.. image:: https://img.shields.io/pypi/v/fountain-py.svg
   :target: https://pypi.org/project/fountain-py/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/fountain-py.svg
   :target: https://pypi.org/project/fountain-py/
   :alt: Python versions

**fountain-py** is a Python library for parsing and rendering `Fountain <https://fountain.io/>`_, the plain-text screenwriting format.
It turns a Fountain script into structured Python objects you can analyze, and renders it back out as HTML, plain text, Fountain, Final Draft (FDX), PDF, or JSON.

Features
--------

- Parses the Fountain syntax: scene headings, action, character cues, dialogue, dual dialogue, parentheticals, lyrics, transitions, centered text, sections, synopses, notes, and inline emphasis.
- Extracts characters, scenes, and statistics from a parsed script.
- Renders to HTML (fragment, standalone page, or raw CSS), plain text, Final Draft (FDX), or PDF, and round-trips back to clean Fountain.
- Serializes to JSON with ``to_json`` and rebuilds a document with ``from_json``, backed by a versioned schema.
- Ships a ``fountain`` command-line tool for validating and rendering scripts without writing any Python.
- Reports parse problems (unclosed boneyard or notes, orphaned character cues) through a validation API.
- Pure Python core with no runtime dependencies (PDF export is an optional ``pdf`` extra), fully type-hinted.

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

- :doc:`Installation <installation>`: install with ``pip install fountain-py``.
- :doc:`Quick Start <quickstart>`: parse a screenplay and render it to HTML in minutes.
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
   how-to/render-to-html-file
   how-to/embed-fragment
   how-to/style-the-html
   how-to/roundtrip-to-fountain
   how-to/export-to-json
   how-to/export-plain-text
   how-to/export-fdx
   how-to/export-pdf
   how-to/use-the-cli
   how-to/extract-character-dialogue

.. toctree::
   :maxdepth: 2
   :caption: Explanation

   explanation/what-is-fountain
   explanation/pipeline
   explanation/roundtrip-and-notes

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/parsing-behavior
   reference/elements
   reference/json-schema
   reference/rendering
   api/parser
   api/document
   api/elements
   api/renderer
   changelog

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   contributing/development
   contributing/testing
   contributing/documentation
   contributing/releasing

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
