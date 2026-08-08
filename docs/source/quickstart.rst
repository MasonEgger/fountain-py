Quick Start
===========

This tutorial parses a screenplay, checks what fountain-py extracted, and renders it to an HTML file you can open in a browser.
It takes about five minutes.

Prerequisites
-------------

fountain-py installed. It is not on PyPI yet, so install it from source (see :doc:`installation` for details):

.. code-block:: bash

   pip install git+https://github.com/MasonEgger/fountain-py.git

Parse a Screenplay
------------------

Parse a Fountain script from a string.
This excerpt uses a title page, scene headings, action, character cues, dialogue, parentheticals, and a note:

.. code-block:: python

   from fountain import FountainParser

   screenplay_text = """
   Title: The Coffee Shop Connection
   Author: Jane Doe
   Draft date: 2024-01-15

   FADE IN:

   INT. COFFEE SHOP - DAY

   A bustling neighborhood COFFEE SHOP. The afternoon sun streams through
   large windows. Business people and students hunker over laptops.

   ALICE (28), creative but frazzled, sits at a corner table, staring at
   her laptop screen. She sighs and rubs her temples.

   ALICE
   (muttering to herself)
   Come on, inspiration... where are you?

   The door chimes. BOB (30s), confident but approachable, enters and
   scans the crowded shop. The only empty seat is across from Alice.

   BOB
   Excuse me, is this seat taken?

   ALICE
   (barely looking up)
   No, go ahead.

   Bob sits. They work in silence. Then:

   BOB
   Writer's block?

   ALICE
   (surprised)
   How did you--?

   BOB
   The temple rubbing. Dead giveaway.
   (extends hand)
   Bob. Fellow sufferer.

   [[Note: This is where their collaboration begins]]

   FADE OUT.
   """

   parser = FountainParser()
   document = parser.parse(screenplay_text)

   print(f"Parsed {len(document.elements)} elements")

Check What Was Parsed
---------------------

Read the title page metadata and the characters fountain-py found:

.. code-block:: python

   print(document.metadata["title"])    # The Coffee Shop Connection
   print(document.metadata["author"])   # Jane Doe
   print(document.get_characters())     # ['ALICE', 'BOB']

Render to HTML
--------------

Render the screenplay to a standalone HTML file with embedded CSS:

.. code-block:: python

   with open("coffee_shop.html", "w", encoding="utf-8") as f:
       f.write(document.to_html())

   print("Wrote coffee_shop.html")

Open ``coffee_shop.html`` in your browser to see the formatted screenplay.

Next Steps
----------

- :doc:`explanation/what-is-fountain`: the format and what fountain-py does with it.
- :doc:`how-to/render-to-html-file`: render a screenplay to a standalone HTML file.
- :doc:`reference/parsing-behavior`: how the parser classifies each line, including the edge cases.
- :doc:`api/parser`: the full API reference.
