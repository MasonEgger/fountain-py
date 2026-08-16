Changelog
=========

This file documents all notable changes to fountain-py.

This changelog follows `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and the project uses `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Version 0.2.0: Unreleased
----------------------------

JSON Interchange
~~~~~~~~~~~~~~~~~

* ``to_dict()`` recursively serializes nested elements, including dual-dialogue side elements, fixing a crash on ``to_json()`` for scripts with dual dialogue
* ``schema_version`` key in the serialized payload, backed by a versioned :doc:`reference/json-schema` reference doc
* ``from_dict()`` / ``from_json()`` reconstruct a full ``FountainDocument`` from serialized data, round-tripping through ``to_dict()`` / ``to_json()``; raise ``ValueError`` on an unrecognized ``schema_version``

Renderer Protocols
~~~~~~~~~~~~~~~~~~~

* ``TextRenderer`` and ``BinaryRenderer`` protocols in ``fountain.renderers.base``, formalizing the renderer contract; every existing renderer conforms

Plain-Text Renderer
~~~~~~~~~~~~~~~~~~~~

* ``PlainTextRenderer`` renders a parsed script to monospace plain text, with configurable width and indents; omits writer-only elements (notes, sections, synopses, boneyard)

Command-Line Interface
~~~~~~~~~~~~~~~~~~~~~~~

* ``fountain`` CLI with ``validate`` and ``render --format`` subcommands, installed via ``[project.scripts]``
* Reads from a file path or stdin (``-``); ``validate`` reports one diagnostic per line and exits non-zero on error-severity issues

FDX Export
~~~~~~~~~~

* ``FDXRenderer`` exports a parsed script to Final Draft's ``.fdx`` XML format using only the standard library, so it adds no runtime dependency
* Dual dialogue renders as a linked ``<DualDialogue>`` block, pinned against ``tests/fixtures/dual_dialogue.fdx``

PDF Export
~~~~~~~~~~

* ``PDFRenderer`` renders a parsed script to PDF bytes via the optional ``pdf`` extra (``fpdf2``), with a clear install hint when the extra is missing
* ``PageGeometry`` presets for Letter, A4, and Half Letter page sizes, plus custom dimensions and a binding offset
* ``SCREENPLAY`` layout profile controlling font and per-element indents; layouts are pluggable via ``LayoutProfile``
* CI verifies the core install stays dependency-free and runs the PDF suite separately under the ``pdf`` extra

Documentation
~~~~~~~~~~~~~

* How-to guides for the CLI, plain-text export, FDX export, and PDF export
* The JSON how-to now covers ``from_json()`` / ``from_dict()`` round-tripping alongside ``to_json()`` / ``to_dict()``

Version 0.1.0: 2026-04-09
----------------------------

Parser: Full Fountain Spec Compliance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Two-pass parser: title page metadata extraction, then line-by-line element classification
* All 15 Fountain element types: scene headings, action, character, dialogue, parenthetical, transitions, notes, boneyard, sections, synopses, dual dialogue, page breaks, centered text, lyrics
* Forced element prefixes (``.``, ``!``, ``@``, ``>``) override natural detection rules
* Scene number extraction (``#1#``, ``#2A#``)
* Character extensions (``V.O.``, ``O.S.``, ``CONT'D``) and automatic continuation detection
* Section level metadata (``# Act`` = level 1, ``## Scene`` = level 2, etc.)
* Ellipsis protection on forced scene headings (``.`` + alphanumeric only)
* Arbitrary title page keys (any ``Key: Value`` pair accepted)
* Requires a blank line before natural scene headings, character names, and transitions
* Requires a blank line after transitions
* Inline note stripping (``[[notes]]`` removed from element text in non-note elements)
* Multi-line note support
* Dialogue continuation with whitespace-only lines
* Backslash escaping for emphasis markers (``\*`` → literal ``*``, ``\_`` → literal ``_``)
* Tab preservation in action elements (rendered as 4 spaces in HTML)
* Inline formatting: bold, italic, underline, bold-italic

Renderers
~~~~~~~~~

* ``HTMLRenderer`` with three output modes:

  * ``render(doc)``: pure HTML fragment for embedding (no ``<style>`` tags)
  * ``render_page(doc)``: standalone HTML with embedded CSS
  * ``get_css()``: raw CSS string for external style sheet use

* ``FountainRenderer`` for round-trip conversion back to Fountain markup
* All CSS classes namespaced with ``fountain-`` prefix to prevent framework collisions
* Screenplay-formatted CSS: Courier font, proper margins, centered dialogue, hidden boneyard
* Dual dialogue side-by-side layout via flexbox
* Title page rendering with all standard and custom metadata fields

Document Analysis
~~~~~~~~~~~~~~~~~

* ``FountainDocument`` container with element access and metadata
* ``get_characters()``: extract unique character names
* ``get_scenes()``: list scene heading elements
* ``get_statistics()``: element counts by type, character count, scene count
* ``to_html()``: convenience method for standalone HTML output
* ``to_json()``: JSON serialization
* ``to_dict()``: dictionary conversion

Type System
~~~~~~~~~~~

* Full type hints throughout, strict mypy compliance
* ``FormatType`` literal type (``"bold"``, ``"italic"``, ``"underline"``, ``"bold_italic"``)
* ``MetadataValue`` union type for element metadata documentation
* PEP 561 ``py.typed`` marker for downstream type checking

Quality
~~~~~~~

* Unit tests and doctests across every module, with high coverage enforced in CI
* Supports Python 3.10, 3.11, 3.12, 3.13, 3.14
* Zero runtime dependencies
* CI with GitHub Actions across all supported Python versions
