JSON Schema Reference
======================

``FountainDocument.to_dict()`` and ``FountainDocument.to_json()`` share one documented shape.
This page pins that shape as a versioned contract: the top-level document, the element dictionary, the formatting-span dictionary, and the nested dual-dialogue metadata.
For task-focused examples, see :doc:`../how-to/export-to-json`.

Top-Level Shape
----------------

``to_dict()`` returns a dictionary with three keys:

.. doctest::

    >>> from fountain.document import FountainDocument
    >>> FountainDocument([]).to_dict().keys()
    dict_keys(['schema_version', 'metadata', 'elements'])

``schema_version``
    An integer identifying the shape of this document.
    The current value is ``1``, exposed as the module constant ``fountain.document.JSON_SCHEMA_VERSION``.
    A future release that changes the shape below in a breaking way bumps this number.

``metadata``
    A dictionary of title page fields (``title``, ``author``, ``draft_date``, and so on), the same dictionary as ``document.metadata``.

``elements``
    A list of element dictionaries, one per :class:`~fountain.elements.FountainElement` in ``document.elements``, in document order.

Element Shape
--------------

Every element in the document, whether top-level or nested inside another element's metadata, serializes to the same five keys:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> document = FountainParser().parse("INT. KITCHEN - DAY\n\nJOHN\nHello.")
    >>> document.to_dict()["elements"][0].keys()
    dict_keys(['type', 'text', 'formatting', 'line_number', 'metadata'])

``type``
    The element's :class:`~fountain.elements.ElementType` value as a string, for example ``"scene_heading"`` or ``"dialogue"``.

``text``
    The element's clean text content, with Fountain markup removed.

``formatting``
    A list of formatting-span dictionaries; see `Formatting-Span Shape`_ below.

``line_number``
    The 1-based source line number the element started on.

``metadata``
    A dictionary of element-specific attributes.
    Most elements carry an empty or small metadata dictionary (``scene_number``, ``extension``, ``forced``, and similar flags).
    DUAL_DIALOGUE elements nest other elements here; see `Dual-Dialogue Metadata`_ below.

Formatting-Span Shape
-----------------------

Each entry in an element's ``formatting`` list describes one inline emphasis span:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> document = FountainParser().parse("JOHN\nThis is **bold** text.")
    >>> document.to_dict()["elements"][1]["formatting"][0]
    {'start': 8, 'end': 12, 'format_type': 'bold'}

``start``
    The zero-based character offset where the span begins, inclusive.

``end``
    The zero-based character offset where the span ends, exclusive.

``format_type``
    One of ``"bold"``, ``"italic"``, or ``"underline"``.

Dual-Dialogue Metadata
------------------------

A DUAL_DIALOGUE element's ``metadata`` nests the two character/dialogue blocks it pairs, using the same element shape as everywhere else:

.. doctest::

    >>> from fountain.parser import FountainParser
    >>> document = FountainParser().parse("BRICK\nHi.\n\nSTEEL^\nHello.")
    >>> dual = [element for element in document.to_dict()["elements"] if element["type"] == "dual_dialogue"][0]
    >>> sorted(dual["metadata"].keys())
    ['left_character', 'left_dialogue', 'right_character', 'right_dialogue']
    >>> dual["metadata"]["left_character"]["type"]
    'character'
    >>> dual["metadata"]["left_character"]["text"]
    'BRICK'
    >>> isinstance(dual["metadata"]["left_dialogue"], list)
    True
    >>> dual["metadata"]["left_dialogue"][0]["type"]
    'dialogue'

``left_character`` and ``right_character``
    Element dictionaries for the two CHARACTER cues, each with the same five keys documented in `Element Shape`_.

``left_dialogue`` and ``right_dialogue``
    Lists of element dictionaries for the DIALOGUE (and PARENTHETICAL) elements spoken under each character.

Because nested elements share the exact shape of top-level elements, code that walks ``document.to_dict()["elements"]`` can recurse into ``metadata["left_character"]`` or ``metadata["left_dialogue"]`` without a special case.
