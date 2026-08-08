How fountain-py Works: Parse, Structure, Render
===============================================

fountain-py is a pipeline with three stages:

.. code-block:: text

   Fountain text  ->  FountainParser  ->  FountainDocument  ->  Renderer  ->  HTML or Fountain

Understanding these three stages explains where each part of the API fits.

Parse
-----

:class:`~fountain.parser.FountainParser` reads raw Fountain text in two passes.

The first pass reads the title page: the ``Key: Value`` lines at the top of the
file (title, author, draft date, and any custom keys) up to the first blank line.

The second pass walks the rest of the file line by line and classifies each line
into an element type.
Because Fountain infers meaning from context, classification follows a fixed order
of precedence:

1. Forced elements, where a leading marker overrides everything else: ``!`` for
   action, ``@`` for a character cue, ``>`` for a transition, ``.`` for a scene
   heading.
2. Special markers: the boneyard (``/* */``), notes (``[[ ]]``), and page breaks
   (``===``).
3. Natural patterns: scene headings and transitions recognized by their shape.
4. Character and dialogue detection, which looks ahead to decide whether an
   uppercase line is a character cue or just action.
5. Action, the fallback when nothing else matches.

Parsing is lenient by design.
``parse()`` never raises; it makes a reasonable choice for ambiguous input and
moves on.
When you need to know what it let through (an unclosed comment, an orphaned
cue), :meth:`~fountain.parser.FountainParser.validate` reports the same run as a
list of diagnostics.
See :doc:`../how-to/validate-a-file`.

Structure
---------

The parser produces a :class:`~fountain.document.FountainDocument`: the title-page
metadata plus an ordered list of :class:`~fountain.elements.FountainElement`
objects.

Each element carries its type (from the :class:`~fountain.elements.ElementType`
enum), its text, any inline formatting spans (bold, italic, underline), its line
number, and a small metadata dictionary.
This list is the heart of the library.
Analysis methods such as
:meth:`~fountain.document.FountainDocument.get_characters`,
:meth:`~fountain.document.FountainDocument.get_scenes`, and
:meth:`~fountain.document.FountainDocument.get_statistics` are queries over it, and
both renderers walk it in order.

Render
------

A document renders two ways.

:class:`~fountain.renderer.HTMLRenderer` produces HTML in three modes: a bare
fragment (``render``), a standalone page with embedded CSS (``render_page``, which
is what :meth:`~fountain.document.FountainDocument.to_html` calls), and the raw CSS
on its own (``get_css``).
Every CSS class it emits carries a ``fountain-`` prefix.

:class:`~fountain.renderer.FountainRenderer` goes the other direction and writes the
document back out as Fountain text.
Parsing and then rendering with ``FountainRenderer`` is a round trip.
:doc:`roundtrip-and-notes` covers what that round trip preserves and where it loses
information.
