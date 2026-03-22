Rendering Fountain Documents
============================

Once you've parsed a Fountain document, the next step is usually to render it into a specific output format. The fountain-py library provides flexible rendering capabilities through the :class:`~fountain.renderer.HTMLRenderer` and :class:`~fountain.renderer.FountainRenderer` classes.

Overview of the Rendering System
---------------------------------

The rendering architecture follows a strategy pattern design that makes it easy to add new output formats:

- **HTMLRenderer**: Converts documents to HTML with traditional screenplay formatting
- **FountainRenderer**: Converts documents back to Fountain markup (round-trip conversion)
- **Extensible Design**: Custom renderers can be created for any output format

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
    >>> '<h1 class="title">My Screenplay</h1>' in html
    True

HTML Rendering
--------------

The :class:`~fountain.renderer.HTMLRenderer` is the primary renderer for web display and print output. It generates complete HTML with embedded CSS that follows industry-standard screenplay formatting conventions.

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
    >>> '<div class="scene-heading">INT. KITCHEN - MORNING</div>' in html
    True
    >>> '<div class="character">JOHN</div>' in html
    True
    >>> '<div class="dialogue">Good morning!</div>' in html
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
    >>> '<div class="title-page">' in html
    True
    >>> '<h1 class="title">The Amazing Story</h1>' in html
    True
    >>> '<p class="author">by John Doe</p>' in html
    True
    >>> '<p class="draft-date">2025-01-20</p>' in html
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
    >>> '<span class="scene-number">#1#</span>' in html
    True
    >>> 
    >>> # Character extensions
    >>> '<span class="character-extension">(V.O.)</span>' in html
    True
    >>> 
    >>> # Dual dialogue (side-by-side layout)
    >>> '<div class="dual-dialogue">' in html
    True
    >>> 
    >>> # Inline formatting (preserves original markup)
    >>> '<strong>**love**</strong>' in html
    True
    >>> 
    >>> # Centered text
    >>> '<div class="centered">THE END</div>' in html
    True

CSS Classes and Styling
~~~~~~~~~~~~~~~~~~~~~~~~

The HTMLRenderer generates CSS classes for each element type:

============== ============================= ================================================
Element Type   CSS Class                     Description
============== ============================= ================================================
Title Page     ``.title-page``               Container for all title page metadata
               ``.title``                    Main screenplay title (24pt, uppercase)
               ``.author``                   Author name(s)
               ``.draft-date``               Draft date and version info
Script Body    ``.fountain-script``          Main container (Courier font, 70% width)
               ``.script-body``              Container for screenplay elements
Scenes         ``.scene-heading``            Scene headers (bold, uppercase)
               ``.scene-number``             Scene numbers (#1#, smaller font)
Dialogue       ``.character``                Character names (centered, bold, uppercase)
               ``.dialogue``                 Spoken words (centered)
               ``.parenthetical``            Stage directions (centered, italic)
               ``.character-extension``      V.O., O.S., etc. (smaller font)
               ``.dual-dialogue``            Container for simultaneous dialogue
               ``.dual-dialogue-left``       Left column for dual dialogue
               ``.dual-dialogue-right``      Right column for dual dialogue
Action/Other   ``.action``                   Narrative text (left-aligned)
               ``.transition``               Scene transitions (right-aligned, bold, uppercase)
               ``.note``                     Production notes (italic, gray)
               ``.boneyard``                 Deleted content (hidden by default)
               ``.section``                  Section headers (bold, 14pt, uppercase)
               ``.synopsis``                 Scene synopsis (italic, gray)
               ``.page-break``               Forced page breaks
               ``.centered``                 Centered text
               ``.lyrics``                   Song lyrics (centered, italic)
============== ============================= ================================================

The default theme uses Courier New font with traditional screenplay spacing and can be customized through CSS.

Understanding the Rendering Pipeline
-------------------------------------

The rendering process follows these steps:

1. **Document Analysis**: Examine document structure and metadata
2. **Element Processing**: Convert each FountainElement to output format
3. **Formatting Application**: Apply inline formatting (bold, italic, underline)
4. **Template Generation**: Wrap elements in appropriate containers and styling
5. **Output Assembly**: Combine all parts into final output string

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
    >>> '<strong>**bold**</strong>' in html
    True
    >>> '<em>*italic*</em>' in html
    True

Saving Rendered Content
-----------------------

HTML output can be saved to files for viewing or printing:

.. code-block:: python

    from fountain.parser import FountainParser
    from fountain.renderer import HTMLRenderer
    
    # Parse and render document
    parser = FountainParser()
    document = parser.parse_file("screenplay.fountain")
    renderer = HTMLRenderer()
    html = renderer.render(document)
    
    # Save as HTML file
    with open("screenplay.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # The generated HTML is self-contained with embedded CSS
    print("Screenplay saved as screenplay.html")

The generated HTML includes all necessary CSS and can be:

- Opened in any web browser
- Printed with proper screenplay formatting
- Embedded in web pages or documentation
- Used as input for PDF conversion tools

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

**Limitations:**

- Exact whitespace formatting may differ
- Inline formatting positions are not perfectly preserved
- Original capitalization in natural elements is maintained
- Comments in boneyard are preserved but may be reformatted

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

Working with Renderer Configuration
------------------------------------

The HTMLRenderer supports basic theming and configuration:

.. doctest::

    >>> # Initialize with default theme
    >>> renderer = HTMLRenderer(theme="default")
    >>> renderer.theme
    'default'
    >>> 
    >>> # All themes currently resolve to default
    >>> custom_renderer = HTMLRenderer(theme="custom")
    >>> custom_renderer.theme
    'custom'

Currently, only the "default" theme is implemented, but the architecture supports future theme additions.

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

Complete Rendering Workflow Example
------------------------------------

Here's a comprehensive example showing the full rendering workflow:

.. code-block:: python

    from fountain.parser import FountainParser
    from fountain.renderer import HTMLRenderer, FountainRenderer
    
    # Parse screenplay
    parser = FountainParser()
    document = parser.parse_file("my_screenplay.fountain")
    
    # Generate HTML for web display
    html_renderer = HTMLRenderer()
    html = html_renderer.render(document)
    
    # Save HTML version
    with open("my_screenplay.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # Generate clean Fountain for archival
    fountain_renderer = FountainRenderer()
    clean_fountain = fountain_renderer.render(document)
    
    # Save clean Fountain version
    with open("my_screenplay_clean.fountain", "w", encoding="utf-8") as f:
        f.write(clean_fountain)
    
    # Extract statistics
    stats = document.get_statistics()
    characters = document.get_character_names()
    
    print(f"Rendered screenplay with {stats['total_elements']} elements")
    print(f"Characters: {', '.join(sorted(characters))}")
    print(f"Generated HTML: my_screenplay.html")
    print(f"Generated Fountain: my_screenplay_clean.fountain")

Best Practices
--------------

1. **Use appropriate encoding**: Always save files with UTF-8 encoding to preserve special characters
2. **Validate round-trips**: When converting formats, verify that essential information is preserved
3. **Customize CSS carefully**: If modifying HTML output, test with various screenplay elements
4. **Handle large documents**: For very large screenplays, consider streaming or chunked processing
5. **Preview before printing**: HTML output is optimized for screen display; test print formatting

Error Handling in Rendering
----------------------------

Renderers are designed to be robust and handle edge cases gracefully:

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
    >>> '<h1 class="title">Empty Script</h1>' in html
    True

Next Steps
----------

Now that you understand rendering, explore:

- :doc:`../api/renderer` - Complete API reference for renderer classes
- :doc:`parsing` - Review parsing concepts to better understand the document structure
- :doc:`elements` - Deep dive into element types and their rendering requirements