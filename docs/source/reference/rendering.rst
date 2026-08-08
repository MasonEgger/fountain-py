Rendering Reference
===================

fountain-py renders a parsed document two ways.
:class:`~fountain.renderer.HTMLRenderer` produces HTML, and :class:`~fountain.renderer.FountainRenderer` writes the document back out as Fountain.
For how rendering fits the pipeline, see :doc:`../explanation/pipeline`; for task-focused recipes, see the How-to Guides.

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.renderer import HTMLRenderer
    >>> 
    >>> parser = FountainParser()
    >>> script = """Title: My Screenplay
    ... Author: Jane Writer
    ... 
    ... INT. COFFEE SHOP - DAY
    ... 
    ... SARAH
    ... One large cappuccino, please!"""
    >>> 
    >>> document = parser.parse(script)
    >>> renderer = HTMLRenderer()
    >>> html = renderer.render(document)
    >>> 
    >>> # Check for basic HTML structure
    >>> '<div class="fountain-script">' in html
    True
    >>> '<h1 class="fountain-title">My Screenplay</h1>' in html
    True

HTML Rendering
--------------

The :class:`~fountain.renderer.HTMLRenderer` is the primary renderer for web display and print output.
It generates complete HTML with embedded CSS that follows industry-standard screenplay formatting conventions.

Basic HTML Rendering
~~~~~~~~~~~~~~~~~~~~

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.renderer import HTMLRenderer
    >>> 
    >>> parser = FountainParser()
    >>> script = """INT. KITCHEN - MORNING
    ... 
    ... JOHN
    ... Good morning!"""
    >>> 
    >>> document = parser.parse(script)
    >>> renderer = HTMLRenderer()
    >>> html = renderer.render(document)
    >>> 
    >>> # Scene heading with proper CSS class
    >>> '<div class="fountain-scene-heading">INT. KITCHEN - MORNING</div>' in html
    True
    >>> '<div class="fountain-character">JOHN</div>' in html
    True
    >>> '<div class="fountain-dialogue">Good morning!</div>' in html
    True

Title Page Rendering
~~~~~~~~~~~~~~~~~~~~

The renderer automatically formats title page metadata into a traditional screenplay title page:

.. doctest::

    >>> script = """Title: The Amazing Story
    ... Author: John Doe
    ... Credit: Written by
    ... Draft Date: 2025-01-20
    ... Contact:
    ...     John Doe
    ...     john@example.com
    ...     555-1234
    ... 
    ... FADE IN:"""
    >>> 
    >>> document = parser.parse(script)
    >>> html = renderer.render(document)
    >>> 
    >>> # Title page elements
    >>> '<div class="fountain-title-page">' in html
    True
    >>> '<h1 class="fountain-title">The Amazing Story</h1>' in html
    True
    >>> '<p class="fountain-author">by John Doe</p>' in html
    True
    >>> '<p class="fountain-draft-date">2025-01-20</p>' in html
    True

Advanced Element Rendering
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The renderer handles all Fountain element types with appropriate formatting:

.. doctest::

    >>> script = """INT. HOUSE - DAY #1#
    ... 
    ... SARAH (V.O.)
    ... I **love** this place!
    ... 
    ... JOHN^
    ... Me too!
    ... 
    ... >THE END<"""
    >>> 
    >>> document = parser.parse(script)
    >>> html = renderer.render(document)
    >>> 
    >>> # Scene numbers
    >>> '<span class="fountain-scene-number">#1#</span>' in html
    True
    >>>
    >>> # Character extensions
    >>> '<span class="fountain-character-extension">(V.O.)</span>' in html
    True
    >>>
    >>> # Dual dialogue (side-by-side layout)
    >>> '<div class="fountain-dual-dialogue">' in html
    True
    >>> 
    >>> # Inline formatting (emphasis delimiters stripped from the output)
    >>> '<strong>love</strong>' in html
    True
    >>> 
    >>> # Centered text
    >>> '<div class="fountain-centered">THE END</div>' in html
    True

CSS Classes and Styling
~~~~~~~~~~~~~~~~~~~~~~~~

The HTMLRenderer generates CSS classes for each element type it renders:

============== ====================================== ================================================
Element Type   CSS Class                              Description
============== ====================================== ================================================
Title Page     ``.fountain-title-page``               Container for all title page metadata
               ``.fountain-title``                    Main screenplay title (24pt, uppercase)
               ``.fountain-author``                   Author names
               ``.fountain-draft-date``               Draft date and version info
Script Body    ``.fountain-script``                   Main container (Courier font, 70% width)
               ``.fountain-script-body``              Container for screenplay elements
Scenes         ``.fountain-scene-heading``            Scene headers (bold, uppercase)
               ``.fountain-scene-number``             Scene numbers (#1#, smaller font)
Dialogue       ``.fountain-character``                Character names (centered, bold, uppercase)
               ``.fountain-dialogue``                 Spoken words (centered)
               ``.fountain-parenthetical``            Stage directions (centered, italic)
               ``.fountain-character-extension``      V.O., O.S., etc. (smaller font)
               ``.fountain-dual-dialogue``            Container for simultaneous dialogue
               ``.fountain-dual-dialogue-left``       Left column for dual dialogue
               ``.fountain-dual-dialogue-right``      Right column for dual dialogue
Action/Other   ``.fountain-action``                   Narrative text (left-aligned)
               ``.fountain-transition``               Scene transitions (right-aligned, bold, uppercase)
               ``.fountain-page-break``               Forced page breaks
               ``.fountain-centered``                 Centered text
               ``.fountain-lyrics``                   Song lyrics (centered, italic)
============== ====================================== ================================================

The default theme uses Courier New font with traditional screenplay spacing, and you can customize it through CSS.

Notes, sections, synopses, and boneyard are writer tools, so the formatted output omits them by default.
Both ``render()`` (the HTML fragment) and ``render_page()`` (the standalone page) drop them entirely.
They emit no markup and generate no CSS class, so there is no ``.fountain-note``, ``.fountain-section``, ``.fountain-synopsis``, or ``.fountain-boneyard`` rule to style.
The parser still records these elements on the :class:`~fountain.document.FountainDocument`, so you can read them from ``document.elements`` even though they never reach the rendered screenplay.

Inline Formatting in Output
---------------------------

The renderer walks the elements in order and applies each element's inline formatting spans (bold, italic, underline) as it emits HTML:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.renderer import HTMLRenderer
    >>> 
    >>> # Step-by-step rendering demonstration
    >>> parser = FountainParser()
    >>> script = """JOHN
    ... This has **bold** and *italic* text."""
    >>> 
    >>> document = parser.parse(script)
    >>> renderer = HTMLRenderer()
    >>> 
    >>> # The pipeline processes elements in order
    >>> len(document.elements)
    2
    >>> 
    >>> # First element: CHARACTER
    >>> document.elements[0].type.value
    'character'
    >>> 
    >>> # Second element: DIALOGUE with formatting
    >>> dialogue = document.elements[1]
    >>> dialogue.type.value
    'dialogue'
    >>> len(dialogue.formatting)
    2
    >>> 
    >>> # Renderer applies formatting and generates HTML
    >>> html = renderer.render(document)
    >>> '<strong>bold</strong>' in html
    True
    >>> '<em>italic</em>' in html
    True

Saving Rendered Content
-----------------------

You can save HTML output to files for viewing or printing:

.. code-block:: python

    from fountain.parser import FountainParser
    from fountain.renderer import HTMLRenderer
    
    # Parse and render document
    parser = FountainParser()
    document = parser.parse_file("screenplay.fountain")
    renderer = HTMLRenderer()
    # render_page() returns standalone HTML with embedded CSS
    html = renderer.render_page(document)

    # Save as HTML file
    with open("screenplay.html", "w", encoding="utf-8") as f:
        f.write(html)

    # render() returns a fragment for embedding (no CSS)
    fragment = renderer.render(document)

    # get_css() returns raw CSS for external stylesheets
    css = renderer.get_css()

The ``render_page()`` output includes all necessary CSS and can be:

- Opened in any web browser
- Printed with proper screenplay formatting
- Used as input for PDF conversion tools

The ``render()`` fragment is ideal for:

- Embedding in web pages or documentation
- Use with mkdocs or other static site generators
- Any context where CSS is managed externally

Fountain Round-Trip Conversion
------------------------------

The :class:`~fountain.renderer.FountainRenderer` enables round-trip conversion back to Fountain markup:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.renderer import FountainRenderer
    >>> 
    >>> parser = FountainParser()
    >>> original = """Title: My Script
    ... Author: Me
    ... 
    ... INT. HOUSE - DAY #1#
    ... 
    ... JOHN (V.O.)
    ... Hello world!"""
    >>> 
    >>> # Parse and render back to Fountain
    >>> document = parser.parse(original)
    >>> fountain_renderer = FountainRenderer()
    >>> regenerated = fountain_renderer.render(document)
    >>> 
    >>> # Verify round-trip preservation
    >>> 'Title: My Script' in regenerated
    True
    >>> 'Author: Me' in regenerated
    True
    >>> 'INT. HOUSE - DAY #1#' in regenerated
    True
    >>> 'JOHN (V.O.)' in regenerated
    True

Round-Trip Capabilities and Limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Preserved in Round-Trip:**

- All element types and structure
- Title page metadata
- Scene numbers and character extensions
- Forced elements (scenes, actions, transitions)
- Element order and hierarchy
- Inline emphasis (bold, italic, underline), including nesting and escaped literals

**Limitations:**

- Consecutive blank lines between paragraphs are normalized to one
- Original capitalization in natural elements is maintained
- Comments in boneyard are dropped from rendered output (a writer-only tool)

.. doctest::

    >>> # Demonstrate round-trip verification
    >>> original_script = """Title: Test
    ...
    ... !Action line here."""
    >>>
    >>> # Parse original
    >>> doc1 = parser.parse(original_script)
    >>>
    >>> # Convert to Fountain and parse again
    >>> fountain_text = fountain_renderer.render(doc1)
    >>> doc2 = parser.parse(fountain_text)
    >>>
    >>> # Structure should be preserved
    >>> len(doc1.elements) == len(doc2.elements)
    True
    >>> doc1.elements[0].type == doc2.elements[0].type
    True

Working with the Rendering API
-------------------------------

The HTMLRenderer provides three output modes for different use cases:

.. doctest::

    >>> renderer = HTMLRenderer()
    >>>
    >>> # get_css() returns raw CSS for external use
    >>> css = renderer.get_css()
    >>> '.fountain-script' in css
    True
    >>> '<style>' not in css
    True

Creating Custom Renderers
--------------------------

You can create custom renderers for any output format by following the renderer pattern:

.. code-block:: python

    class MarkdownRenderer:
        """Example custom renderer for Markdown output."""
        
        def render(self, document):
            md_parts = []
            
            # Render title page
            if document.metadata and "title" in document.metadata:
                md_parts.append(f"# {document.metadata['title']}")
                if "author" in document.metadata:
                    md_parts.append(f"*by {document.metadata['author']}*")
                md_parts.append("")
            
            # Render elements
            for element in document.elements:
                if element.type.value == 'scene_heading':
                    md_parts.append(f"## {element.text}")
                elif element.type.value == 'action':
                    md_parts.append(element.text)
                elif element.type.value == 'character':
                    md_parts.append(f"**{element.text}**")
                elif element.type.value == 'dialogue':
                    md_parts.append(f"> {element.text}")
                elif element.type.value == 'parenthetical':
                    md_parts.append(f"*{element.text}*")
                # ... handle other element types
                md_parts.append("")
            
            return "\\n".join(md_parts)

The key requirements for custom renderers:

1. **render(document)** method that accepts a FountainDocument
2. **Element handling** for all ElementType values you want to support
3. **Metadata processing** for title page information
4. **Return string** in your target format

Error Handling in Rendering
----------------------------

Renderers handle edge cases without raising errors:

.. doctest::

    >>> # Empty document rendering
    >>> empty_doc = parser.parse("")
    >>> html = renderer.render(empty_doc)
    >>> '<div class="fountain-script">' in html
    True
    >>> 
    >>> # Document with only metadata
    >>> metadata_only = parser.parse("Title: Empty Script\nAuthor: Test")
    >>> html = renderer.render(metadata_only)
    >>> '<h1 class="fountain-title">Empty Script</h1>' in html
    True

Next Steps
----------

Now that you understand rendering, explore:

- :doc:`../api/renderer` - Complete API reference for renderer classes
- :doc:`parsing-behavior` - How the parser classifies the elements you are rendering
- :doc:`elements` - The element types and their rendering requirements