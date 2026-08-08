Style the HTML Output
=====================

The rendered screenplay uses the default fountain-py theme (Courier, traditional
screenplay spacing).
To change how it looks, override the ``fountain-`` CSS classes with your own rules.

Start from the shipped CSS
--------------------------

``get_css()`` returns the default style sheet as a string, so you can see
which classes exist and what they set:

.. code-block:: python

   from fountain.renderer import HTMLRenderer

   print(HTMLRenderer().get_css())

:doc:`../reference/rendering` lists every class.

Override with Your Own Rules
----------------------------

Render a fragment, include the default CSS, then add your overrides *after* it so
they win:

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderer import HTMLRenderer

   document = FountainParser().parse_file("screenplay.fountain")
   renderer = HTMLRenderer()

   overrides = """
   .fountain-script { font-family: Georgia, serif; }
   .fountain-scene-heading { color: #663399; }
   """

   page = f"""<!doctype html>
   <html>
   <head><style>{renderer.get_css()}{overrides}</style></head>
   <body>{renderer.render(document)}</body>
   </html>"""

Because the overrides come after the default rules and target the same classes,
they take precedence.
Keep the ``fountain-`` class names; the renderer emits those, and your CSS has to
match them.
