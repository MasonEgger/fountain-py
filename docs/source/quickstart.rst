Quick Start
===========

.. note::
   This documentation section will be completed in Phase 3.2 of the documentation plan.

Basic Example
-------------

.. code-block:: python

   from fountain import FountainParser
   
   parser = FountainParser()
   document = parser.parse_string("""
   FADE IN:
   
   INT. COFFEE SHOP - DAY
   
   ALICE sits at a small table, typing on her laptop.
   
   ALICE
   This is just a simple example.
   """)
   
   # Get all elements
   for element in document.elements:
       print(f"{element.element_type}: {element.text}")
   
   # Render to HTML
   from fountain.renderer import HTMLRenderer
   renderer = HTMLRenderer()
   html = renderer.render(document)