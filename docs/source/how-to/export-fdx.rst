Export a Screenplay to Final Draft (.fdx)
============================================

Final Draft is the industry-standard screenwriting app, and its native
``.fdx`` format is XML.
Export a parsed script to ``.fdx`` when a collaborator, a production office, or a
contest submission expects Final Draft rather than plain Fountain.

Use :class:`~fountain.renderers.fdx.FDXRenderer`:

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderers.fdx import FDXRenderer

   document = FountainParser().parse_file("screenplay.fountain")

   fdx = FDXRenderer().render(document)

   with open("screenplay.fdx", "w", encoding="utf-8") as f:
       f.write(fdx)

The output is a ``<FinalDraft>`` document with a ``<Content>`` section holding one
``<Paragraph Type="...">`` per screenplay element, plus a ``<TitlePage>`` section
built from the document's title page metadata:

.. doctest::

   >>> from fountain import FountainParser
   >>> from fountain.renderers.fdx import FDXRenderer
   >>> script = """Title: The Coffee Shop Connection
   ... Author: Jane Doe
   ...
   ... INT. COFFEE SHOP - DAY
   ...
   ... ALICE
   ... Come on, inspiration... where are you?"""
   >>> document = FountainParser().parse(script)
   >>> fdx = FDXRenderer().render(document)
   >>> "<FinalDraft" in fdx
   True
   >>> '<Paragraph Type="Scene Heading"><Text>INT. COFFEE SHOP - DAY</Text></Paragraph>' in fdx
   True
   >>> '<Paragraph Type="Title"><Text>The Coffee Shop Connection</Text></Paragraph>' in fdx
   True

The renderer uses only the standard library's :mod:`xml.etree.ElementTree`, so
FDX export adds no runtime dependency.

Element Mapping
-----------------

Every scene heading, action line, character cue, parenthetical, dialogue line, and
transition maps to the matching FDX paragraph type.
Centered text and lyrics have no dedicated FDX type, so they map to the nearest
match instead: centered text becomes an ``Action`` paragraph with
``Alignment="Center"``, and lyrics become a ``Dialogue`` paragraph.
Notes, sections, synopses, and boneyard comments are writer-only tools.
The renderer omits them, matching :class:`~fountain.renderer.HTMLRenderer` and
:class:`~fountain.renderers.plaintext.PlainTextRenderer`.

Dual dialogue renders as Final Draft expects it: one ``<Paragraph><DualDialogue>``
wrapper containing both characters' cue and dialogue paragraphs, so the two sides
stay linked instead of flattening to separate paragraphs.
