Parsing Fountain Files
======================

The parsing module is the heart of fountain-py, providing a robust parser that converts Fountain-formatted text into structured, programmatically accessible elements. This guide covers everything you need to know about parsing Fountain scripts.

Overview
--------

The :class:`~fountain.parser.FountainParser` class implements a two-pass parsing strategy designed specifically for the Fountain screenplay format:

1. **First pass**: Extracts title page metadata (title, author, draft date, etc.)
2. **Second pass**: Parses the screenplay body into structured elements (scenes, dialogue, action, etc.)

The parser is designed to be forgiving and follows the Fountain specification's principle of "just write" - if something doesn't match a specific pattern, it defaults to action text.

Basic Usage
-----------

Parsing from a String
~~~~~~~~~~~~~~~~~~~~~

The most straightforward way to parse Fountain text is from a string:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> 
    >>> parser = FountainParser()
    >>> script_text = """Title: My Great Screenplay
    ... Author: Jane Writer
    ... 
    ... FADE IN:
    ... 
    ... EXT. COFFEE SHOP - DAY
    ... 
    ... A busy coffee shop on a warm summer day.
    ... 
    ... SARAH
    ... One large cappuccino, please!
    ... 
    ... FADE OUT."""
    >>> 
    >>> document = parser.parse(script_text)
    >>> document.metadata['title']
    'My Great Screenplay'
    >>> document.metadata['author']
    'Jane Writer'
    >>> len(document.elements)
    6

Parsing from a File
~~~~~~~~~~~~~~~~~~~

To parse a Fountain file from disk, use the :meth:`~fountain.parser.FountainParser.parse_file` method:

.. code-block:: python

    parser = FountainParser()
    document = parser.parse_file("screenplay.fountain")
    
    # Access metadata
    print(f"Title: {document.metadata.get('title', 'Untitled')}")
    print(f"Author: {document.metadata.get('author', 'Unknown')}")
    
    # Access elements
    print(f"Total elements: {len(document.elements)}")

The file is expected to be UTF-8 encoded, which is standard for Fountain files.

Understanding the Parsing Process
---------------------------------

Title Page Parsing
~~~~~~~~~~~~~~~~~~

The parser first extracts metadata from the title page. Title page fields are key-value pairs at the beginning of the document:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> 
    >>> script = """Title: The Amazing Story
    ... Author: John Doe
    ... Credit: Written by
    ... Source: Based on a true story
    ... Draft Date: 2025-01-20
    ... Contact:
    ...     John Doe
    ...     john@example.com
    ...     555-1234
    ... 
    ... FADE IN:"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # All metadata is stored in lowercase keys
    >>> sorted(document.metadata.keys())
    ['author', 'contact', 'credit', 'draft date', 'source', 'title']
    >>> document.metadata['source']
    'Based on a true story'
    >>> 'john@example.com' in document.metadata['contact']
    True

Multi-line values are supported - subsequent lines without colons are appended to the current field.

Element Classification
~~~~~~~~~~~~~~~~~~~~~~

After the title page, the parser classifies each line into one of 14 element types:

- **Scene Headings**: Lines starting with INT., EXT., EST., I/E., or forced with ``.``
- **Characters**: ALL CAPS names followed by dialogue
- **Dialogue**: Lines following character names
- **Parentheticals**: Dialogue instructions in parentheses
- **Transitions**: Lines ending with ``TO:`` or specific patterns like ``FADE IN:``
- **Action**: General narrative text (the default)
- **Centered**: Text enclosed in ``>text<``
- **Sections**: Markdown-style headers with ``#``
- **Synopsis**: Lines starting with ``=``
- **Notes**: Text in ``[[double brackets]]``
- **Boneyard**: Comments in ``/* comment */``
- **Page Breaks**: Three or more equals signs ``===``
- **Lyrics**: Lines starting with ``~``
- **Dual Dialogue**: Characters marked with ``^`` for simultaneous speech

Working with Parsed Documents
-----------------------------

Accessing Elements
~~~~~~~~~~~~~~~~~~

The parsed document contains a list of :class:`~fountain.elements.FountainElement` objects:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> 
    >>> script = """INT. HOUSE - DAY
    ... 
    ... JOHN
    ... Hello there!
    ... 
    ... MARY
    ... (surprised)
    ... Oh, hi!"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # Access all elements
    >>> len(document.elements)
    6
    >>> 
    >>> # Access specific element
    >>> first_element = document.elements[0]
    >>> first_element.type
    <ElementType.SCENE_HEADING: 'scene_heading'>
    >>> first_element.text
    'INT. HOUSE - DAY'
    >>> first_element.line_number
    1

Filtering Elements by Type
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can filter elements to find specific types:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> 
    >>> script = """INT. KITCHEN - MORNING
    ... 
    ... CHEF
    ... Let's make breakfast!
    ... 
    ... He cracks some eggs.
    ... 
    ... CHEF (CONT'D)
    ... Perfect!"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # Filter by type
    >>> scenes = [el for el in document.elements if el.type == ElementType.SCENE_HEADING]
    >>> len(scenes)
    1
    >>> 
    >>> dialogue = [el for el in document.elements if el.type == ElementType.DIALOGUE]
    >>> len(dialogue)
    2
    >>> dialogue[0].text
    "Let's make breakfast!"
    >>> 
    >>> # Find characters with extensions
    >>> characters = [el for el in document.elements if el.type == ElementType.CHARACTER]
    >>> chef_contd = [c for c in characters if c.metadata and 'extension' in c.metadata]
    >>> len(chef_contd)
    1
    >>> chef_contd[0].metadata['extension']
    "CONT'D"

Extracting Character Dialogue
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A common pattern is pairing characters with their dialogue:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> 
    >>> script = """SARAH
    ... I have something to tell you.
    ... 
    ... JOHN
    ... (nervously)
    ... What is it?
    ... 
    ... SARAH
    ... I'm moving to Paris!"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # Extract character-dialogue pairs
    >>> dialogue_pairs = []
    >>> for i, element in enumerate(document.elements):
    ...     if element.type == ElementType.CHARACTER:
    ...         # Collect all dialogue/parentheticals until next character
    ...         char_name = element.text
    ...         dialogue_text = []
    ...         j = i + 1
    ...         while j < len(document.elements):
    ...             next_elem = document.elements[j]
    ...             if next_elem.type == ElementType.DIALOGUE:
    ...                 dialogue_text.append(next_elem.text)
    ...             elif next_elem.type == ElementType.PARENTHETICAL:
    ...                 dialogue_text.append(next_elem.text)
    ...             else:
    ...                 break
    ...             j += 1
    ...         if dialogue_text:
    ...             dialogue_pairs.append((char_name, ' '.join(dialogue_text)))
    >>> 
    >>> len(dialogue_pairs)
    3
    >>> dialogue_pairs[0]
    ('SARAH', 'I have something to tell you.')
    >>> dialogue_pairs[1]
    ('JOHN', '(nervously) What is it?')

Special Elements and Forced Formatting
--------------------------------------

The Fountain format includes special syntax for forcing element types:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> 
    >>> script = """.FORCED SCENE HEADING
    ... 
    ... > FORCED TRANSITION
    ... 
    ... @john
    ... Even though this is lowercase, it's forced to be a character.
    ... 
    ... !This is forced to be action, not dialogue.
    ... 
    ... >CENTERED TEXT<
    ... 
    ... [[This is a note that won't appear in the final script]]"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # Check forced elements
    >>> scene = document.elements[0]
    >>> scene.type
    <ElementType.SCENE_HEADING: 'scene_heading'>
    >>> scene.text
    'FORCED SCENE HEADING'
    >>> scene.metadata['forced']
    True
    >>> 
    >>> # Centered text
    >>> centered = [el for el in document.elements if el.type == ElementType.CENTERED][0]
    >>> centered.text
    'CENTERED TEXT'
    >>> 
    >>> # Notes
    >>> note = [el for el in document.elements if el.type == ElementType.NOTE][0]
    >>> 'note that' in note.text
    True

Inline Formatting
-----------------

The parser extracts inline formatting (bold, italic, underline) from text:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> 
    >>> script = """Action with **bold text** and *italic text* and _underlined text_.
    ... 
    ... JOHN
    ... I can speak in ***bold and italic*** too!"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # Check action formatting
    >>> action = document.elements[0]
    >>> len(action.formatting)
    3
    >>> [f.format_type for f in action.formatting]
    ['bold', 'italic', 'underline']
    >>> 
    >>> # Check dialogue formatting
    >>> dialogue = [el for el in document.elements if el.type.value == 'dialogue'][0]
    >>> len(dialogue.formatting)
    1
    >>> dialogue.formatting[0].format_type
    'bold_italic'

Advanced Features
-----------------

Scene Numbers
~~~~~~~~~~~~~

Scene numbers can be included in scene headings using ``#number#`` syntax:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> 
    >>> script = """INT. HOUSE - DAY #1#
    ... 
    ... INT. KITCHEN - LATER #2A#
    ... 
    ... .FLASHBACK SEQUENCE #FB-1#"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> scenes = [el for el in document.elements if el.type.value == 'scene_heading']
    >>> 
    >>> # Scene numbers are extracted to metadata
    >>> scenes[0].metadata.get('scene_number')
    '1'
    >>> scenes[1].metadata.get('scene_number')
    '2A'
    >>> scenes[2].metadata.get('scene_number')
    'FB-1'
    >>> 
    >>> # Text doesn't include the number
    >>> scenes[0].text
    'INT. HOUSE - DAY'

Dual Dialogue
~~~~~~~~~~~~~

Characters speaking simultaneously are marked with ``^``:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> 
    >>> script = """JOHN
    ... Did you see that?
    ... 
    ... MARY^
    ... I can't believe it!"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # Dual dialogue is processed into a special element
    >>> dual = [el for el in document.elements if el.type == ElementType.DUAL_DIALOGUE][0]
    >>> dual.metadata['left_character'].text
    'JOHN'
    >>> dual.metadata['right_character'].text
    'MARY'
    >>> len(dual.metadata['left_dialogue'])
    1
    >>> dual.metadata['left_dialogue'][0].text
    'Did you see that?'

Error Handling
--------------

The parser is designed to be forgiving. Malformed or ambiguous text defaults to action:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> 
    >>> script = """This isn't proper Fountain formatting
    ... But the parser handles it gracefully
    ... Without throwing errors"""
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> 
    >>> # All lines become action elements
    >>> len(document.elements)
    3
    >>> all(el.type == ElementType.ACTION for el in document.elements)
    True

For files that don't exist or have encoding issues, appropriate exceptions are raised:

.. code-block:: python

    try:
        document = parser.parse_file("nonexistent.fountain")
    except FileNotFoundError:
        print("File not found")
    except UnicodeDecodeError:
        print("File encoding issue - expected UTF-8")

Performance Considerations
-------------------------

The parser is optimized for efficiency:

- **Streaming**: Processes scripts line by line, maintaining minimal memory footprint
- **Single-pass element parsing**: Each line is classified once
- **Immutable elements**: Elements are created once and never modified
- **Regex compilation**: All patterns are pre-compiled as class constants

For large scripts (100+ pages), parsing typically completes in milliseconds:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> 
    >>> # Generate a large script
    >>> large_script = "Title: Large Script\n\n"
    >>> for i in range(100):
    ...     large_script += f"INT. LOCATION {i} - DAY\n\nCHARACTER_{i}\nDialogue {i}.\n\n"
    >>> 
    >>> parser = FountainParser()
    >>> document = parser.parse(large_script)
    >>> 
    >>> # Verify it parsed correctly
    >>> scenes = [el for el in document.elements if el.type.value == 'scene_heading']
    >>> len(scenes)
    100

Best Practices
--------------

1. **Reuse parser instances**: The parser can be reused for multiple documents
2. **Handle metadata safely**: Use ``.get()`` for optional metadata fields
3. **Filter efficiently**: Use list comprehensions for element filtering
4. **Validate element types**: Check element types before accessing type-specific metadata

Example: Complete Parsing Workflow
----------------------------------

Here's a complete example showing a typical parsing workflow:

.. code-block:: python

    from fountain.parser import FountainParser
    from fountain.elements import ElementType
    
    # Initialize parser (can be reused)
    parser = FountainParser()
    
    # Parse a file
    document = parser.parse_file("my_screenplay.fountain")
    
    # Extract metadata
    print(f"Title: {document.metadata.get('title', 'Untitled')}")
    print(f"Author: {document.metadata.get('author', 'Unknown')}")
    print(f"Draft Date: {document.metadata.get('draft date', 'Undated')}")
    
    # Analyze structure
    scenes = [el for el in document.elements if el.type == ElementType.SCENE_HEADING]
    characters = document.get_character_names()  # Uses document's built-in method
    
    print(f"\nScript Statistics:")
    print(f"- Scenes: {len(scenes)}")
    print(f"- Characters: {len(characters)}")
    print(f"- Total elements: {len(document.elements)}")
    
    # Extract first scene's content
    if scenes:
        first_scene = scenes[0]
        scene_idx = document.elements.index(first_scene)
        
        print(f"\nFirst Scene: {first_scene.text}")
        print("Content:")
        
        # Get elements until next scene
        for i in range(scene_idx + 1, len(document.elements)):
            element = document.elements[i]
            if element.type == ElementType.SCENE_HEADING:
                break
            
            if element.type == ElementType.CHARACTER:
                print(f"\n{element.text}")
            elif element.type == ElementType.DIALOGUE:
                print(f"  {element.text}")
            elif element.type == ElementType.ACTION:
                print(f"\n{element.text}")

Next Steps
----------

Now that you understand parsing, explore:

- :doc:`elements` - Detailed guide to working with parsed elements
- :doc:`rendering` - Converting parsed documents to HTML
- :doc:`../api/parser` - Complete API reference for the parser module