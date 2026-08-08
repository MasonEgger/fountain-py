Render a Screenplay to an HTML File
===================================

Turn a parsed script into a standalone HTML file you can open in a browser or
send to someone.

Use ``render_page()``, or the ``to_html()`` shortcut on the document.
It returns a full HTML page with the screenplay CSS embedded, so the file needs no
external style sheet:

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderer import HTMLRenderer

   document = FountainParser().parse_file("screenplay.fountain")

   html = HTMLRenderer().render_page(document)

   with open("screenplay.html", "w", encoding="utf-8") as f:
       f.write(html)

The document exposes the same thing directly, if you do not need the renderer for
anything else:

.. code-block:: python

   with open("screenplay.html", "w", encoding="utf-8") as f:
       f.write(document.to_html())

Open ``screenplay.html`` in a browser to view or print it.

:doc:`../reference/rendering` describes the three HTMLRenderer modes:
``render_page`` for a standalone page, ``render`` for a fragment, and
``get_css`` for the CSS on its own.
To embed the screenplay in an existing page instead of writing a standalone file,
see :doc:`embed-fragment`.
