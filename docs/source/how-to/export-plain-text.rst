Export a Screenplay to Plain Text
===================================

Turn a parsed script into monospace plain text.
Scene headings and action sit flush left; character cues and dialogue sit
indented and centered, the way a printed script reads.

Use :class:`~fountain.renderers.plaintext.PlainTextRenderer`:

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderers.plaintext import PlainTextRenderer

   document = FountainParser().parse_file("screenplay.fountain")

   text = PlainTextRenderer().render(document)

   with open("screenplay.txt", "w", encoding="utf-8") as f:
       f.write(text)

A short script renders like this:

.. doctest::

   >>> from fountain import FountainParser
   >>> from fountain.renderers.plaintext import PlainTextRenderer
   >>> script = """INT. COFFEE SHOP - DAY
   ...
   ... ALICE sits at a corner table, staring at her laptop.
   ...
   ... ALICE
   ... Come on, inspiration... where are you?"""
   >>> document = FountainParser().parse(script)
   >>> print(PlainTextRenderer().render(document))
   INT. COFFEE SHOP - DAY
   <BLANKLINE>
   ALICE sits at a corner table, staring at her laptop.
   <BLANKLINE>
                         ALICE
   <BLANKLINE>
             Come on, inspiration... where are you?

Notes, sections, synopses, and boneyard comments are writer-only tools.
The renderer omits them, matching :class:`~fountain.renderer.HTMLRenderer`.
Plain text has no side-by-side layout.
Dual dialogue renders as two single-column blocks in sequence: the left side
first, then the right side.

Adjust the Column Widths
--------------------------

The default layout wraps at 60 characters, with dialogue starting at column 10,
parentheticals at column 15, and character cues at column 22.
Pass different values to the constructor to target a narrower or wider page:

.. code-block:: python

   renderer = PlainTextRenderer(
       width=72,
       dialogue_indent=12,
       parenthetical_indent=18,
       cue_indent=26,
   )

   text = renderer.render(document)
