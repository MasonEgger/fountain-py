Changelog
=========

All notable changes to fountain-py will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Version 0.1.0 — 2026-04-09
----------------------------

Parser — Full Fountain Spec Compliance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Two-pass parser: title page metadata extraction, then line-by-line element classification
* All 15 Fountain element types: scene headings, action, character, dialogue, parenthetical, transitions, notes, boneyard, sections, synopses, dual dialogue, page breaks, centered text, lyrics
* Forced element prefixes (``.``, ``!``, ``@``, ``>``) override natural detection rules
* Scene number extraction (``#1#``, ``#2A#``)
* Character extensions (``V.O.``, ``O.S.``, ``CONT'D``) and automatic continuation detection
* Section level metadata (``# Act`` = level 1, ``## Scene`` = level 2, etc.)
* Ellipsis protection on forced scene headings (``.`` + alphanumeric only)
* Arbitrary title page keys (any ``Key: Value`` pair accepted)
* Blank-line-before requirement for natural scene headings, character names, and transitions
* Blank-line-after requirement for transitions
* Inline note stripping (``[[notes]]`` removed from element text in non-note elements)
* Multi-line note support
* Dialogue continuation with whitespace-only lines
* Backslash escaping for emphasis markers (``\*`` → literal ``*``, ``\_`` → literal ``_``)
* Tab preservation in action elements (rendered as 4 spaces in HTML)
* Inline formatting: bold, italic, underline, bold-italic

Renderers
~~~~~~~~~

* ``HTMLRenderer`` with three output modes:

  * ``render(doc)`` — pure HTML fragment for embedding (no ``<style>`` tags)
  * ``render_page(doc)`` — standalone HTML with embedded CSS
  * ``get_css()`` — raw CSS string for external stylesheet use

* ``FountainRenderer`` for round-trip conversion back to Fountain markup
* All CSS classes namespaced with ``fountain-`` prefix to prevent framework collisions
* Screenplay-formatted CSS: Courier font, proper margins, centered dialogue, hidden boneyard
* Dual dialogue side-by-side layout via flexbox
* Title page rendering with all standard and custom metadata fields

Document Analysis
~~~~~~~~~~~~~~~~~

* ``FountainDocument`` container with element access and metadata
* ``get_characters()`` — extract unique character names
* ``get_scenes()`` — list scene heading elements
* ``get_statistics()`` — element counts by type, character count, scene count
* ``to_html()`` — convenience method for standalone HTML output
* ``to_json()`` — JSON serialization
* ``to_dict()`` — dictionary conversion

Type System
~~~~~~~~~~~

* Full type hints throughout, strict mypy compliance
* ``FormatType`` literal type (``"bold"``, ``"italic"``, ``"underline"``, ``"bold_italic"``)
* ``MetadataValue`` union type for element metadata documentation
* PEP 561 ``py.typed`` marker for downstream type checking

Quality
~~~~~~~

* 280 tests with 99% code coverage
* 38 module-level doctests + 446 Sphinx doctests
* Supports Python 3.10, 3.11, 3.12, 3.13, 3.14
* Zero runtime dependencies
* CI with GitHub Actions across all supported Python versions
