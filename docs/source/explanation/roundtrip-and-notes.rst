Round-Tripping and the Inline-Note Contract
===========================================

Parsing a script and then rendering it with
:class:`~fountain.renderer.FountainRenderer` is a *round trip*: Fountain text goes
in, and Fountain text comes back out.

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderer import FountainRenderer

   document = FountainParser().parse(source_text)
   fountain_again = FountainRenderer().render(document)

The round trip is not a byte-for-byte copy.
It reproduces the *structure* of the script, not its exact original whitespace.
Knowing what it keeps and what it drops tells you when a round trip is safe to rely
on.

What the Round Trip Preserves
-----------------------------

- **Element types and their order.** Scene headings, action, character cues,
  parentheticals, dialogue, transitions, dual dialogue, lyrics, sections,
  synopses, and standalone notes all keep their type through
  ``parse(render(parse(text)))``.
- **The blank lines between blocks.** The separators that keep two blocks from
  merging survive, so a re-parse produces the same structure rather than fusing
  neighbors.
- **Inline emphasis.** The parser records bold (``**``), italic (``*``), and
  underline (``_``) as formatting spans, and ``FountainRenderer`` re-emits the
  markers, so ``**bold**`` round-trips as ``**bold**``, including nested emphasis
  and backslash-escaped literals.

What the Round Trip Drops
-------------------------

The round trip does not promise to preserve every character of the original text.
The most important case to understand is notes.

A **standalone note**, one that sits on its own between blank lines, is kept:

.. code-block:: text

   INT. HOUSE - DAY

   [[remember to fix this]]

   Action here.

An **inline note**, one embedded inside a line of action or dialogue, is dropped on
render:

.. code-block:: python

   >>> from fountain import FountainParser
   >>> from fountain.renderer import FountainRenderer
   >>> doc = FountainParser().parse("John enters [[check blocking]] and sits.")
   >>> FountainRenderer().render(doc)
   'John enters and sits.'

The note text is removed from the line, and the line round-trips without it.

Why Inline Notes Are Lossy
--------------------------

The two kinds of note are stored differently.
A standalone note becomes its own element, so the renderer can write it straight
back out.
An inline note is stripped from the surrounding text during parsing and recorded as
metadata on the element, and the renderer emits the cleaned line rather than
splicing the note back into it.

The practical rule: if you depend on notes surviving a round trip, keep them on
their own lines.
If you need the inline notes themselves, read them from the parsed elements before
you render, rather than expecting them in the rendered output.
