Validate a Fountain File
========================

Fountain parsing is lenient: ``parse()`` never raises, and it silently tolerates
structural problems like an unclosed comment.
When you want to *know* about those problems (for a linter, an editor, or a
pre-commit check), use ``validate()``.

Check a String
--------------

``FountainParser.validate()`` runs the same analysis as ``parse()`` but returns
the problems it found instead of a document:

.. code-block:: python

   from fountain import FountainParser

   text = """INT. HOUSE - DAY

   /* this comment is never closed
   """

   parser = FountainParser()
   issues = parser.validate(text)

   for issue in issues:
       print(f"{issue.severity}: {issue.code} (line {issue.line_number}) - {issue.message}")

Output:

.. code-block:: text

   error: unclosed-boneyard (line 3) - Boneyard comment opened with '/*' but never closed

A well-formed document returns an empty list:

.. code-block:: python

   >>> FountainParser().validate("INT. HOUSE - DAY\n\nJOHN\nHello.")
   []

Check a File
------------

Read the file and validate its contents:

.. code-block:: python

   from pathlib import Path
   from fountain import FountainParser

   text = Path("screenplay.fountain").read_text(encoding="utf-8")
   issues = FountainParser().validate(text)

   if issues:
       for issue in issues:
           print(f"{issue.line_number}: {issue.severity} {issue.code}")
   else:
       print("No problems found.")

Get the Issues Alongside the Document
-------------------------------------

You do not have to parse twice.
Every parsed document carries the same diagnostics on ``document.issues``, so you
can render a script and report its problems from one parse:

.. code-block:: python

   document = parser.parse(text)

   html = document.to_html()
   for issue in document.issues:
       print(f"{issue.severity}: {issue.message}")

What Gets Reported
------------------

Each issue is a :class:`~fountain.elements.ValidationIssue` with four fields:
``line_number``, ``severity`` (``"error"`` or ``"warning"``), a stable ``code``,
and a human-readable ``message``.
The ``code`` is what you match on in your own tooling:

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Code
     - Severity
     - Meaning
   * - ``unclosed-boneyard``
     - error
     - A ``/*`` comment was opened but never closed.
   * - ``unclosed-note``
     - error
     - A ``[[`` note was opened but never closed.
   * - ``orphan-character-cue``
     - warning
     - An uppercase line looked like a character cue but no dialogue followed, so it was treated as action.
   * - ``empty-document``
     - warning
     - The input parsed to zero elements.

Fail a Build on Errors
----------------------

To gate a script on errors only, filter by severity and set the exit code:

.. code-block:: python

   import sys
   from pathlib import Path
   from fountain import FountainParser

   text = Path("screenplay.fountain").read_text(encoding="utf-8")
   errors = [i for i in FountainParser().validate(text) if i.severity == "error"]

   for error in errors:
       print(f"line {error.line_number}: {error.message}")

   sys.exit(1 if errors else 0)
