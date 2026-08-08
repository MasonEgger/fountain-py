Round-Trip Back to Clean Fountain
=================================

To write a parsed document back out as Fountain text (for example to normalize a
messy file, or to save a cleaned copy), use
:class:`~fountain.renderer.FountainRenderer`.

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderer import FountainRenderer

   document = FountainParser().parse_file("messy.fountain")

   clean = FountainRenderer().render(document)

   with open("clean.fountain", "w", encoding="utf-8") as f:
       f.write(clean)

The output keeps the element types and their order, the blank lines between
blocks, and inline emphasis (``**bold**``, ``*italic*``, ``_underline_``).
It does not reproduce the original whitespace byte for byte, and it drops inline
notes and boneyard comments.

If notes matter to you, keep them on their own lines so they survive the round
trip.
The full contract, and why inline notes are lost, is in
:doc:`../explanation/roundtrip-and-notes`.
