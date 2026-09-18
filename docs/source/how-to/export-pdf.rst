Export a Screenplay to PDF
============================

Render a parsed script straight to a PDF file, laid out with the same margins,
indents, and monospace font a printed screenplay uses.

Install the Extra
-------------------

PDF export depends on `fpdf2 <https://pypi.org/project/fpdf2/>`_, which fountain-py
ships as an optional extra rather than a core dependency:

.. code-block:: console

   $ pip install "fountain-py[pdf]"

:class:`~fountain.renderers.pdf.renderer.PDFRenderer` raises ``ImportError`` at
construction time if fpdf2 is not installed.
The error message names the preceding install command.

Render a File
--------------

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderers.pdf.renderer import PDFRenderer

   document = FountainParser().parse_file("screenplay.fountain")

   pdf_bytes = PDFRenderer().render_bytes(document)

   with open("screenplay.pdf", "wb") as f:
       f.write(pdf_bytes)

``render_bytes()`` returns PDF bytes, not text, so open the output file in binary
mode.
With no arguments, ``PDFRenderer()`` uses the Letter page size and a standard
screenplay layout.

Choose a Page Size
--------------------

:mod:`fountain.renderers.pdf.geometry` ships three presets.
``LETTER`` (8.5" x 11") is the default, ``A4`` is 210mm x 297mm, and
``HALF_LETTER`` (5.5" x 8.5") is a half-size booklet page.
Pass one to the ``geometry`` argument:

.. doctest::

   >>> from fountain import FountainParser
   >>> from fountain.renderers.pdf.renderer import PDFRenderer
   >>> from fountain.renderers.pdf.geometry import HALF_LETTER
   >>> document = FountainParser().parse("INT. HOUSE - DAY\n\nJohn enters.")
   >>> pdf_bytes = PDFRenderer(geometry=HALF_LETTER).render_bytes(document)
   >>> pdf_bytes.startswith(b"%PDF")
   True

If none of the presets fit, build a custom size with
:class:`~fountain.renderers.pdf.geometry.PageGeometry` directly.
Here is a 6" x 9" trade paperback page with a binding offset reserved on the
left margin:

.. code-block:: python

   from fountain.renderers.pdf.geometry import PageGeometry

   geometry = PageGeometry(width_in=6, height_in=9, margin_in=1, binding_offset_in=0.25)
   pdf_bytes = PDFRenderer(geometry=geometry).render_bytes(document)

``geometry.text_width_in`` must work out positive; a margin and binding offset
that consume the whole page width raises ``ValueError`` when you render.

Choose a Layout Profile
--------------------------

:mod:`fountain.renderers.pdf.profile` carries the font and the per-element
indent/width.
It positions scene headings, action, character cues, parentheticals, dialogue,
and transitions on the page.
``PDFRenderer()`` defaults to the ``SCREENPLAY`` profile: Courier 12pt, with
character cues indented 2.5" from the text block's left edge and dialogue
indented 1.5":

.. doctest::

   >>> from fountain.elements import ElementType
   >>> from fountain.renderers.pdf.profile import SCREENPLAY
   >>> SCREENPLAY.element_layout[ElementType.CHARACTER].left_indent_in
   2.5
   >>> SCREENPLAY.element_layout[ElementType.DIALOGUE].left_indent_in
   1.5

To change the font or retarget an indent, build a custom profile.
Use :class:`~fountain.renderers.pdf.profile.LayoutProfile` and
:class:`~fountain.renderers.pdf.profile.ElementLayout`, then pass it to the
``profile`` argument:

.. code-block:: python

   from types import MappingProxyType
   from fountain.elements import ElementType
   from fountain.renderers.pdf.profile import ElementLayout, LayoutProfile

   profile = LayoutProfile(
       font_name="Courier",
       font_size_pt=10,
       element_layout=MappingProxyType(
           {
               ElementType.CHARACTER: ElementLayout(left_indent_in=2.0, width_in=3.0),
               ElementType.DIALOGUE: ElementLayout(left_indent_in=1.0, width_in=4.0),
           }
       ),
   )

   pdf_bytes = PDFRenderer(profile=profile).render_bytes(document)

Element types missing from a custom profile's ``element_layout`` fall back to a
zero-indent block spanning the full text width.

What Gets Omitted
--------------------

Notes, sections, synopses, and boneyard comments are writer-only tools, so
PDF export omits them, matching the other renderers.
A forced page break (``===``) starts a new PDF page.
Dual dialogue renders as two single-column blocks in sequence, the left side
first and the right side second.
It matches :class:`~fountain.renderers.plaintext.PlainTextRenderer` rather than
laying the two sides out side by side.
