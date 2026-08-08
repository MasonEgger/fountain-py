Extract a Character's Dialogue
==============================

List the Characters
-------------------

For just the cast, use
:meth:`~fountain.document.FountainDocument.get_characters`:

.. code-block:: python

   from fountain import FountainParser

   document = FountainParser().parse_file("screenplay.fountain")
   print(document.get_characters())   # ['ALICE', 'BOB']

Pair Characters with Their Lines
--------------------------------

To collect what each character says, walk the elements: a
``CHARACTER`` element starts a speech, and the ``DIALOGUE`` and
``PARENTHETICAL`` elements that follow belong to it until the next non-dialogue
element:

.. code-block:: python

   from fountain import FountainParser, ElementType

   document = FountainParser().parse_file("screenplay.fountain")

   lines_by_character: dict[str, list[str]] = {}
   current = None

   for element in document.elements:
       if element.type == ElementType.CHARACTER:
           current = element.text
       elif element.type == ElementType.DIALOGUE and current is not None:
           lines_by_character.setdefault(current, []).append(element.text)
       elif element.type not in (ElementType.DIALOGUE, ElementType.PARENTHETICAL):
           current = None

   for line in lines_by_character.get("ALICE", []):
       print(line)

The final ``elif`` resets the current speaker when anything other than dialogue or
a parenthetical appears (an action line, a new scene), so lines are attributed to
the right character.

For how each of these element types is recognized, see
:doc:`../reference/parsing-behavior`.
