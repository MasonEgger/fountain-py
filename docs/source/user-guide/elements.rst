Understanding Fountain Elements
==============================

The element system is the foundation of fountain-py's document representation. Every piece of a Fountain screenplay is parsed into structured :class:`~fountain.elements.FountainElement` objects with specific types, text content, formatting information, and metadata.

Overview of the Element System
------------------------------

Each element in a parsed document has four core properties:

- **Type**: An :class:`~fountain.elements.ElementType` enum value indicating what kind of screenplay element this is
- **Text**: The clean text content with Fountain markup removed
- **Formatting**: A list of :class:`~fountain.elements.FormatSpan` objects describing inline formatting like bold, italic
- **Metadata**: A dictionary containing element-specific information and attributes

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import ElementType
    >>> 
    >>> parser = FountainParser()
    >>> script = """INT. COFFEE SHOP - DAY #1#
    ... 
    ... SARAH (V.O.)
    ... I **love** this place!
    ... 
    ... She takes a sip of her coffee."""
    >>> 
    >>> document = parser.parse(script)
    >>> len(document.elements)
    4
    >>> 
    >>> # Examine the scene heading
    >>> scene = document.elements[0]
    >>> scene.type
    <ElementType.SCENE_HEADING: 'scene_heading'>
    >>> scene.text
    'INT. COFFEE SHOP - DAY'
    >>> scene.metadata['scene_number']
    '1'

Element Types Reference
-----------------------

Fountain supports 15 distinct element types through the :class:`~fountain.elements.ElementType` enum:

Scene Structure Elements
~~~~~~~~~~~~~~~~~~~~~~~~

**SCENE_HEADING**
    Location and time indicators that establish where and when action takes place.
    
    - Standard prefixes: ``INT.``, ``EXT.``, ``EST.``, ``I/E.``
    - Can include scene numbers: ``INT. HOUSE - DAY #1#``
    - Forced with period: ``.FLASHBACK SEQUENCE``

    .. doctest::

        >>> from fountain.parser import FountainParser
        >>> from fountain.elements import ElementType
        >>> 
        >>> parser = FountainParser()
        >>> script = """INT. KITCHEN - MORNING #2A#
        ... 
        ... .FLASHBACK - 10 YEARS AGO"""
        >>> 
        >>> document = parser.parse(script)
        >>> scenes = [el for el in document.elements if el.type == ElementType.SCENE_HEADING]
        >>> 
        >>> # Standard scene heading
        >>> scenes[0].text
        'INT. KITCHEN - MORNING'
        >>> scenes[0].metadata.get('scene_number')
        '2A'
        >>> 
        >>> # Forced scene heading
        >>> scenes[1].text
        'FLASHBACK - 10 YEARS AGO'
        >>> scenes[1].metadata.get('forced')
        True

**ACTION**
    Narrative description of what happens on screen. This is the default element type.
    
    - General narrative text
    - Stage directions and descriptions
    - Can be forced with exclamation: ``!This is definitely action``

    .. doctest::

        >>> script = """The doorbell rings.
        ... 
        ... !DEFINITELY ACTION (even though it's caps)
        ... 
        ... John **slowly** walks to the door."""
        >>> 
        >>> document = parser.parse(script)
        >>> actions = [el for el in document.elements if el.type == ElementType.ACTION]
        >>> 
        >>> actions[0].text
        'The doorbell rings.'
        >>> actions[1].text
        "DEFINITELY ACTION (even though it's caps)"
        >>> 
        >>> # Action with formatting
        >>> len(actions[2].formatting)
        1
        >>> actions[2].formatting[0].format_type
        'bold'

**TRANSITION**
    Scene transitions like cuts, fades, and dissolves.
    
    - Standard patterns: ``CUT TO:``, ``FADE IN:``, ``FADE OUT.``
    - Can be forced with ``>CUSTOM TRANSITION``

    .. doctest::

        >>> script = """FADE IN:
        ... 
        ... >SMASH CUT TO:"""
        >>> 
        >>> document = parser.parse(script)
        >>> transitions = [el for el in document.elements if el.type == ElementType.TRANSITION]
        >>> 
        >>> transitions[0].text
        'FADE IN:'
        >>> transitions[1].text
        'SMASH CUT TO:'

Dialogue Elements
~~~~~~~~~~~~~~~~~

**CHARACTER**
    Character names that introduce dialogue blocks.
    
    - Must be ALL CAPS: ``JOHN``, ``MARY JANE``, ``ROBOT_1``
    - Can include extensions: ``SARAH (V.O.)``, ``JOHN (O.S.)``
    - Can be forced with ``@`` for lowercase: ``@narrator``
    - Dual dialogue marked with ``^``: ``MARY^``

    .. doctest::

        >>> script = """JOHN
        ... Hello there!
        ... 
        ... SARAH (V.O.)
        ... I can hear you."""
        >>> 
        >>> document = parser.parse(script)
        >>> characters = [el for el in document.elements if el.type == ElementType.CHARACTER]
        >>> 
        >>> characters[0].text
        'JOHN'
        >>> characters[1].text
        'SARAH'
        >>> characters[1].metadata['extension']
        'V.O.'

**DIALOGUE**
    The words spoken by characters.
    
    - Always follows CHARACTER or PARENTHETICAL elements
    - Can span multiple lines without blank line separation
    - Supports inline formatting

    .. doctest::

        >>> script = """JOHN
        ... I have something *important* to tell you.
        ... This is still dialogue.
        ... 
        ... MARY
        ... What is it?"""
        >>> 
        >>> document = parser.parse(script)
        >>> dialogue = [el for el in document.elements if el.type == ElementType.DIALOGUE]
        >>> 
        >>> len(dialogue)
        3
        >>> dialogue[0].text
        'I have something *important* to tell you.'
        >>> len(dialogue[0].formatting)
        1

**PARENTHETICAL**
    Stage directions within dialogue, enclosed in parentheses.
    
    - Appears between CHARACTER and DIALOGUE
    - Format: ``(nervously)``, ``(to Mary)``, ``(beat)``

    .. doctest::

        >>> script = """JOHN
        ... (nervously)
        ... I need to tell you something.
        ... (beat)
        ... I'm moving to Paris."""
        >>> 
        >>> document = parser.parse(script)
        >>> parentheticals = [el for el in document.elements if el.type == ElementType.PARENTHETICAL]
        >>> 
        >>> len(parentheticals)
        2
        >>> parentheticals[0].text
        '(nervously)'
        >>> parentheticals[1].text
        '(beat)'

**DUAL_DIALOGUE**
    Special element for characters speaking simultaneously.
    
    - Created when a character is marked with ``^``
    - Contains metadata for both characters and their dialogue
    - Replaces individual character/dialogue elements

    .. doctest::

        >>> script = """JOHN
        ... Did you see that?
        ... 
        ... MARY^
        ... I can't believe it!"""
        >>> 
        >>> document = parser.parse(script)
        >>> dual = [el for el in document.elements if el.type == ElementType.DUAL_DIALOGUE][0]
        >>> 
        >>> dual.metadata['left_character'].text
        'JOHN'
        >>> dual.metadata['right_character'].text
        'MARY'
        >>> len(dual.metadata['left_dialogue'])
        1
        >>> dual.metadata['left_dialogue'][0].text
        'Did you see that?'

Document Structure Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**SECTION**
    Hierarchical section headings for document organization.
    
    - Format: ``# Act I``, ``## Scene 1``, ``### Subplot``
    - Similar to Markdown headers

    .. doctest::

        >>> script = """# Act I
        ... 
        ... ## Opening Scene
        ... 
        ... ### Character Introduction"""
        >>> 
        >>> document = parser.parse(script)
        >>> sections = [el for el in document.elements if el.type == ElementType.SECTION]
        >>> 
        >>> len(sections)
        3
        >>> sections[0].text
        'Act I'
        >>> sections[1].text
        'Opening Scene'

**SYNOPSIS**
    Plot summaries and scene descriptions for planning.
    
    - Format: ``= John meets Mary for the first time``
    - Used for outlining and structure notes

    .. doctest::

        >>> script = """= The hero's journey begins
        ... 
        ... INT. HOUSE - DAY"""
        >>> 
        >>> document = parser.parse(script)
        >>> synopsis = [el for el in document.elements if el.type == ElementType.SYNOPSIS][0]
        >>> synopsis.text
        "The hero's journey begins"

**PAGE_BREAK**
    Forced page breaks in formatted output.
    
    - Format: ``===`` (three or more equals signs)

    .. doctest::

        >>> script = """End of Act I.
        ... 
        ... ===
        ... 
        ... # Act II"""
        >>> 
        >>> document = parser.parse(script)
        >>> page_break = [el for el in document.elements if el.type == ElementType.PAGE_BREAK][0]
        >>> page_break.text
        '==='

Special Elements
~~~~~~~~~~~~~~~~

**CENTERED**
    Text that should be centered on the page.
    
    - Format: ``>THE END<``
    - Often used for titles or special announcements

    .. doctest::

        >>> script = """>FIVE YEARS LATER<
        ... 
        ... >THE END<"""
        >>> 
        >>> document = parser.parse(script)
        >>> centered = [el for el in document.elements if el.type == ElementType.CENTERED]
        >>> 
        >>> len(centered)
        2
        >>> centered[0].text
        'FIVE YEARS LATER'
        >>> centered[1].text
        'THE END'

**LYRICS**
    Song lyrics or musical elements.
    
    - Format: ``~Happy birthday to you``

    .. doctest::

        >>> script = """~Happy birthday to you
        ... ~Happy birthday dear Sarah
        ... ~Happy birthday to you"""
        >>> 
        >>> document = parser.parse(script)
        >>> lyrics = [el for el in document.elements if el.type == ElementType.LYRICS]
        >>> 
        >>> len(lyrics)
        3
        >>> lyrics[0].text
        'Happy birthday to you'

**NOTE**
    Inline comments that don't appear in final output.
    
    - Format: ``[[This is a note]]``
    - Used for production notes and reminders

    .. doctest::

        >>> script = """[[Remember to check continuity here]]
        ... 
        ... JOHN
        ... Hello there!"""
        >>> 
        >>> document = parser.parse(script)
        >>> note = [el for el in document.elements if el.type == ElementType.NOTE][0]
        >>> 'continuity' in note.text
        True

**BONEYARD**
    Commented-out content that's preserved but not rendered.
    
    - Format: ``/* This is boneyard content */``
    - Used for deleted scenes or alternate versions

    .. doctest::

        >>> script = """/* This scene was cut from final version */
        ... 
        ... MARY
        ... This dialogue remains."""
        >>> 
        >>> document = parser.parse(script)
        >>> boneyard = [el for el in document.elements if el.type == ElementType.BONEYARD][0]
        >>> 'cut from final' in boneyard.text
        True

Element Structure Deep Dive
----------------------------

Understanding FormatSpan Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inline formatting is represented by :class:`~fountain.elements.FormatSpan` objects that define regions of formatted text:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> from fountain.elements import FormatSpan
    >>> 
    >>> script = """JOHN
    ... This is **bold** and *italic* and _underlined_ text!"""
    >>> 
    >>> document = parser.parse(script)
    >>> dialogue = [el for el in document.elements if el.type.value == 'dialogue'][0]
    >>> 
    >>> # Examine formatting spans
    >>> len(dialogue.formatting)
    3
    >>> 
    >>> # Bold formatting
    >>> bold_span = dialogue.formatting[0]
    >>> bold_span.format_type
    'bold'
    >>> bold_span.start, bold_span.end
    (8, 16)
    >>> dialogue.text[bold_span.start:bold_span.end]
    '**bold**'
    >>> 
    >>> # Italic formatting
    >>> italic_span = dialogue.formatting[1]
    >>> italic_span.format_type
    'italic'
    >>> dialogue.text[italic_span.start:italic_span.end]
    '*italic*'

Working with Element Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Different element types store specific information in their metadata dictionary:

.. doctest::

    >>> script = """INT. HOUSE - DAY #1A#
    ... 
    ... SARAH (V.O.)
    ... I **love** this place!
    ... 
    ... JOHN^
    ... Me too!"""
    >>> 
    >>> document = parser.parse(script)
    >>> 
    >>> # Scene heading metadata
    >>> scene = document.elements[0]
    >>> scene.metadata['scene_number']
    '1A'
    >>> 
    >>> # Character extension metadata (accessing through dual dialogue)
    >>> dual = [el for el in document.elements if el.type.value == 'dual_dialogue'][0]
    >>> dual.metadata['left_character'].metadata['extension']
    'V.O.'
    >>> 
    >>> # Dual dialogue metadata
    >>> dual = [el for el in document.elements if el.type.value == 'dual_dialogue'][0]
    >>> dual.metadata['left_character'].text
    'SARAH'
    >>> dual.metadata['right_character'].text
    'JOHN'

Common Element Patterns
-----------------------

Filtering Elements by Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use list comprehensions to filter elements by type:

.. doctest::

    >>> script = """INT. COFFEE SHOP - DAY
    ... 
    ... SARAH
    ... Good morning!
    ... 
    ... JOHN
    ... (sleepily)
    ... Morning..."""
    >>> 
    >>> document = parser.parse(script)
    >>> 
    >>> # Get all dialogue
    >>> dialogue = [el for el in document.elements if el.type.value == 'dialogue']
    >>> len(dialogue)
    2
    >>> 
    >>> # Get characters and their dialogue
    >>> characters = [el for el in document.elements if el.type.value == 'character']
    >>> len(characters)
    2

Finding Elements by Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Search elements by their text content:

.. doctest::

    >>> script = """INT. HOUSE - DAY"""
    >>> 
    >>> document = parser.parse(script)
    >>> 
    >>> # Find specific scenes
    >>> house_scenes = [el for el in document.elements 
    ...                 if el.type.value == 'scene_heading' and 'HOUSE' in el.text]
    >>> len(house_scenes)
    1
    >>> house_scenes[0].text
    'INT. HOUSE - DAY'

Extracting Character Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Build character lists and dialogue mappings:

.. doctest::

    >>> script = """JOHN
    ... Hello there!
    ... 
    ... SARAH
    ... Hi back!"""
    >>> 
    >>> document = parser.parse(script)
    >>> 
    >>> # Extract unique character names
    >>> character_names = set()
    >>> for element in document.elements:
    ...     if element.type.value == 'character':
    ...         character_names.add(element.text)
    >>> 
    >>> sorted(character_names)
    ['JOHN', 'SARAH']

Creating Element Collections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Group related elements together:

.. doctest::

    >>> script = """INT. KITCHEN - MORNING
    ... 
    ... JOHN
    ... Good morning!
    ... 
    ... SARAH
    ... Morning to you too!"""
    >>> 
    >>> document = parser.parse(script)
    >>> 
    >>> # Group dialogue blocks (character + dialogue + parentheticals)
    >>> dialogue_blocks = []
    >>> current_block = None
    >>> 
    >>> for element in document.elements:
    ...     if element.type.value == 'character':
    ...         if current_block:
    ...             dialogue_blocks.append(current_block)
    ...         current_block = {'character': element, 'dialogue': [], 'parentheticals': []}
    ...     elif current_block and element.type.value == 'dialogue':
    ...         current_block['dialogue'].append(element)
    ...     elif current_block and element.type.value == 'parenthetical':
    ...         current_block['parentheticals'].append(element)
    ...     else:
    ...         if current_block:
    ...             dialogue_blocks.append(current_block)
    ...             current_block = None
    >>> 
    >>> if current_block:
    ...     dialogue_blocks.append(current_block)
    >>> 
    >>> len(dialogue_blocks)
    2

Advanced Element Usage
----------------------

Working with Forced Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Identify elements that were forced with special syntax:

.. doctest::

    >>> script = """.FLASHBACK SEQUENCE
    ... 
    ... @narrator
    ... This is a voiceover."""
    >>> 
    >>> document = parser.parse(script)
    >>> 
    >>> # Find forced elements
    >>> forced_elements = [el for el in document.elements 
    ...                   if el.metadata and el.metadata.get('forced')]
    >>> 
    >>> len(forced_elements)
    2
    >>> forced_elements[0].type.value
    'scene_heading'
    >>> forced_elements[1].type.value
    'character'

Processing Inline Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extract and process formatted text:

.. doctest::

    >>> script = """JOHN
    ... This is ***very important*** information!"""
    >>> 
    >>> document = parser.parse(script)
    >>> dialogue = [el for el in document.elements if el.type.value == 'dialogue'][0]
    >>> 
    >>> # Find bold-italic text
    >>> for span in dialogue.formatting:
    ...     if span.format_type == 'bold_italic':
    ...         formatted_text = dialogue.text[span.start:span.end]
    ...         print(f"Bold-italic text: '{formatted_text}'")
    Bold-italic text: '***very important***'

Element Line Numbers
~~~~~~~~~~~~~~~~~~~~

Track source locations for debugging or editing:

.. doctest::

    >>> script = """Title: My Script
    ... 
    ... INT. HOUSE - DAY"""
    >>> 
    >>> document = parser.parse(script)
    >>> 
    >>> # Find element source lines
    >>> for element in document.elements:
    ...     if element.type.value == 'scene_heading':
    ...         print(f"Scene at line {element.line_number}: {element.text}")
    Scene at line 3: INT. HOUSE - DAY

Best Practices
--------------

1. **Use ElementType enum values**: Always compare against ``ElementType.SCENE_HEADING`` rather than string literals
2. **Check metadata safely**: Use ``.get()`` method when accessing optional metadata fields
3. **Handle formatting spans carefully**: Remember that start/end positions are relative to the clean text, not the original Fountain markup
4. **Process dual dialogue specially**: Dual dialogue elements contain other elements in their metadata, requiring recursive processing

Next Steps
----------

Now that you understand the element system, learn how to:

- :doc:`rendering` - Convert elements to HTML output
- :doc:`../api/elements` - Complete API reference for element classes
