Parsing Behavior
================

This page is the reference for how :class:`~fountain.parser.FountainParser` classifies Fountain text, including the edge cases that trip people up.
For the design behind it (the two-pass strategy and the "just write" principle), see :doc:`../explanation/pipeline`.

Basic Usage
-----------

Parsing from a String
~~~~~~~~~~~~~~~~~~~~~

To parse Fountain text from a string:

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

Line-One Title Page Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The title page pass decides whether a document has a title page by looking at the first meaningful line.
A colon-bearing line opens a title-page key only when it looks like one: it must carry a non-empty value or an indented continuation, and it must name a recognized field (``Title``, ``Author``, ``Contact``, and so on) or be a capitalized label such as ``Custom Field:``.

A colon on line one is therefore not enough on its own.
Prose like ``He opens the card: a threat.`` has a lowercase label, so it stays body action rather than becoming a phantom field:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> parser = FountainParser()
    >>> document = parser.parse("He opens the card: a threat.")
    >>> document.metadata
    {}
    >>> [element.type.value for element in document.elements]
    ['action']

A bare ``FADE IN:`` or ``CUT TO:`` has an empty value and no indented continuation, so it parses as a body transition instead of a ``fade in`` field:

.. doctest::

    >>> document = parser.parse("FADE IN:\n\nINT. HOUSE - DAY")
    >>> document.metadata
    {}
    >>> [element.type.value for element in document.elements]
    ['transition', 'scene_heading']

A forced ``>CUT TO:`` on the first line is likewise a body transition, not a metadata key:

.. doctest::

    >>> document = parser.parse(">CUT TO:\n\nINT. HOUSE - DAY")
    >>> document.metadata
    {}
    >>> [element.type.value for element in document.elements]
    ['transition', 'scene_heading']

A recognized field or a capitalized custom label opens the title page as expected, and a real title page followed by a blank line works normally:

.. doctest::

    >>> document = parser.parse("Title: My Script\n\n>CUT TO:\n\nINT. HOUSE - DAY")
    >>> document.metadata.get('title')
    'My Script'
    >>> [element.type.value for element in document.elements]
    ['transition', 'scene_heading']

Element Classification
~~~~~~~~~~~~~~~~~~~~~~

After the title page, the parser classifies each body line into one of 14 element types (the :class:`~fountain.elements.ElementType` enum also defines ``TITLE_PAGE`` for title-page metadata, so the enum has 15 members in total):

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

Lyrics Inside a Dialogue Block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A lyric line (a line beginning with ``~``) inside a dialogue block does not end the block.
A standalone note (``[[ ... ]]`` on its own line) behaves the same way.
A character who sings, or carries an editorial note, mid-speech keeps speaking: the block ends only at a blank line.

Consider this input:

.. code-block:: text

    JOHN
    ~Willy Wonka!
    Wasn't that great?

The parser produces three elements: a ``CHARACTER`` (``JOHN``), a ``LYRICS`` element (``Willy Wonka!``, with the tilde stripped), and a ``DIALOGUE`` element (``Wasn't that great?``).
The trailing line continues as dialogue because the lyric did not close the block.

A blank line still ends the dialogue block, so an ordinary line after a blank falls back to action as usual.

FADE IN: and FADE OUT. as Transitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Fountain spec's natural-transition rule recognizes a line as a transition only when it ends in ``TO:`` (for example ``CUT TO:`` or ``SMASH-CUT TO:``).
fountain-py deliberately extends that rule to also recognize ``FADE IN:`` and ``FADE OUT.`` as transitions, even though neither ends in ``TO:``.
These two are the canonical opening and closing transitions of a screenplay, so treating them as transitions matches what writers expect.

This is a deliberate extension, not a spec requirement:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>>
    >>> script = """The screen is black.
    ...
    ... FADE IN:
    ...
    ... INT. HOUSE - DAY
    ...
    ... FADE OUT."""
    >>>
    >>> parser = FountainParser()
    >>> document = parser.parse(script)
    >>> [element.text for element in document.elements if element.type == ElementType.TRANSITION]
    ['FADE IN:', 'FADE OUT.']

A leading ``FADE IN:`` is a special case, because of its trailing colon.
On the very first line, ``FADE IN:`` is consumed as a title-page key (yielding ``{'fade in': ''}`` and no body element), under the line-one title-page rule described in the "Line-One Title Page Detection" section above.
A leading ``>`` does not rescue it: ``> FADE IN:`` on line one is captured as the metadata key ``> fade in`` for the same reason, and a leading blank line does not help either.
To keep a first-line ``FADE IN:`` in the body, precede it with an action line, as the doctest above does.
Because ``FADE OUT.`` has no colon, a first-line ``FADE OUT.`` is not claimed by the title page and is classified as a transition.

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

Notes: Inline Are Stripped, Standalone Are Kept
-----------------------------------------------

Fountain notes in ``[[double brackets]]`` behave asymmetrically depending on where they sit.
An inline note embedded in a line of action has its content stripped out of the line text and is unrecoverable from the parse: neither the note content nor its brackets survive.
The whitespace seam left where the note stood collapses to a single space, so the surrounding words do not run together or leave a doubled gap.
A standalone note on its own line, by contrast, becomes a NOTE element whose text keeps the content verbatim, brackets included.

This asymmetry is a documented contract, not a defect.
If you need a note to survive the parse, put it on its own line.

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> parser = FountainParser()
    >>>
    >>> # Inline note: content stripped, unrecoverable, seam collapsed to one space
    >>> inline = parser.parse("INT. HOUSE - DAY\n\nHe waves [[secret]] hello.")
    >>> action = [el for el in inline.elements if el.type == ElementType.ACTION][0]
    >>> action.text
    'He waves hello.'
    >>> "secret" in action.text
    False
    >>>
    >>> # Standalone note: kept as a NOTE element, verbatim with brackets
    >>> standalone = parser.parse("INT. HOUSE - DAY\n\n[[remember this]]")
    >>> note = [el for el in standalone.elements if el.type == ElementType.NOTE][0]
    >>> note.text
    '[[remember this]]'

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
    >>> # The three adjacent lines merge into one action paragraph
    >>> len(document.elements)
    1
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

Performance
-----------

The parser reads the script once, line by line, so even a full-length screenplay parses in milliseconds:

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
    characters = document.get_characters()  # Uses document's built-in method
    
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