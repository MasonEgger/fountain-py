Embed a Screenplay in a Web Page
================================

To put a screenplay inside a page you already control (a site, a docs build, a
CMS), render a *fragment* rather than a standalone page.

``render()`` returns just the screenplay markup, with no ``<html>``, ``<head>``,
or ``<style>`` wrapper.
``get_css()`` returns the matching CSS as a plain string.
Drop the fragment into your page body and the CSS into your style sheet or a
``<style>`` block:

.. code-block:: python

   from fountain import FountainParser
   from fountain.renderer import HTMLRenderer

   document = FountainParser().parse_file("screenplay.fountain")
   renderer = HTMLRenderer()

   fragment = renderer.render(document)   # screenplay markup, no CSS
   css = renderer.get_css()               # the CSS, no <style> tag

   page = f"""<!doctype html>
   <html>
   <head><style>{css}</style></head>
   <body>
     <h1>My Site</h1>
     {fragment}
   </body>
   </html>"""

Every class the fragment uses is prefixed with ``fountain-``, so it will not
collide with your own styles.
If your site already ships the CSS once (for example in a static-site build), call
``get_css()`` a single time.
Reuse it across pages rather than inlining it into each fragment.

For the full list of CSS classes, see :doc:`../reference/rendering`.
To restyle the output, see :doc:`style-the-html`.
