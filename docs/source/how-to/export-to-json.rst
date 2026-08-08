Export a Screenplay to JSON
===========================

To hand a parsed script to another program (a web front end, a data pipeline, a
different language), export it as JSON or a plain dictionary.

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
