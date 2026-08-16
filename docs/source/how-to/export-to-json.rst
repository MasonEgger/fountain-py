Export a Screenplay to JSON
===========================

You can hand a parsed script to another program: a web front end, a data pipeline,
a different language.
Export it as JSON or a plain dictionary.

``to_json()`` returns a JSON string:

.. code-block:: python

   from fountain import FountainParser

   document = FountainParser().parse_file("screenplay.fountain")

   with open("screenplay.json", "w", encoding="utf-8") as f:
       f.write(document.to_json())

``to_dict()`` returns the same structure as a Python dictionary, if you want to
work with it in process or feed it to your own serializer:

.. code-block:: python

   data = document.to_dict()

   print(data.keys())              # dict_keys(['metadata', 'elements'])
   print(len(data["elements"]))    # number of parsed elements

Each entry in ``data["elements"]`` carries the element's ``type``, ``text``,
``formatting`` spans, ``line_number``, and ``metadata``, so the JSON is enough to
reconstruct the document's structure elsewhere.
:doc:`../reference/json-schema` pins the full shape, including the nested
dual-dialogue metadata, as a versioned contract.

Load a Screenplay Back from JSON
-----------------------------------

``from_json()`` is the inverse of ``to_json()``.
It reconstructs a full :class:`~fountain.document.FountainDocument` (elements
and metadata both) from a JSON string.
The string can come from another program, or from fountain-py itself:

.. doctest::

   >>> from fountain.document import FountainDocument
   >>> from fountain.parser import FountainParser
   >>> document = FountainParser().parse("INT. HOUSE - DAY\n\nJohn enters.")
   >>> restored = FountainDocument.from_json(document.to_json())
   >>> restored.to_dict() == document.to_dict()
   True

``from_dict()`` does the same from an in-memory dictionary, the inverse of
``to_dict()``:

.. code-block:: python

   data = document.to_dict()

   # ... hand data to another process, or store it, then later:

   restored = FountainDocument.from_dict(data)

Both methods check the ``schema_version`` field and raise ``ValueError`` if it
does not match the version this fountain-py release understands:

.. doctest::

   >>> FountainDocument.from_dict({"schema_version": 999, "metadata": {}, "elements": []})
   Traceback (most recent call last):
       ...
   ValueError: Unsupported schema_version 999; expected 1

``from_json()`` and ``from_dict()`` rebuild the same
:class:`~fountain.elements.FountainElement` objects ``parse()`` produces.
Every renderer and analysis method works on the restored document the same way
it works on a freshly parsed one.
