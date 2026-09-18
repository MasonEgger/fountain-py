Use the Command Line
=====================

fountain-py installs a ``fountain`` command alongside the library.
Use it to validate or render a script without writing any Python.

It has two subcommands: ``validate`` and ``render``.
Both accept a path or ``-`` to read from stdin.

Validate a File
----------------

``fountain validate`` runs the same checks as :meth:`~fountain.parser.FountainParser.validate` and prints one diagnostic line per issue:

.. code-block:: console

   $ fountain validate screenplay.fountain
   3:warning:orphan-character-cue:Character cue 'JOHN' has no dialogue following it

Each line has the shape ``line:severity:code:message``.
The exit code is ``1`` if any issue has severity ``error``, and ``0`` otherwise.
Wire it into a CI check or a commit-time Git hook:

.. code-block:: console

   $ fountain validate screenplay.fountain && echo "clean"

Pipe a script through stdin with ``-`` instead of writing a temp file:

.. code-block:: console

   $ cat screenplay.fountain | fountain validate -

Render to Another Format
--------------------------

``fountain render`` parses a file and writes it out in a different format, chosen with ``--format``:

.. code-block:: console

   $ fountain render screenplay.fountain --format html > screenplay.html

Each format maps to one of the library's renderers:

.. list-table::
   :header-rows: 1
   :widths: 15 40

   * - Format
     - Renderer
   * - ``html``
     - :class:`~fountain.renderer.HTMLRenderer`
   * - ``text``
     - :class:`~fountain.renderers.plaintext.PlainTextRenderer`
   * - ``fountain``
     - :class:`~fountain.renderer.FountainRenderer`
   * - ``json``
     - :meth:`~fountain.document.FountainDocument.to_json`
   * - ``fdx``
     - :class:`~fountain.renderers.fdx.FDXRenderer`
   * - ``pdf``
     - :class:`~fountain.renderers.pdf.renderer.PDFRenderer`

Output goes to stdout by default.
Write it to a file with ``-o`` instead:

.. code-block:: console

   $ fountain render screenplay.fountain --format json -o screenplay.json

``render`` also reads from stdin:

.. code-block:: console

   $ cat screenplay.fountain | fountain render - --format text

Render to PDF
--------------

PDF output needs the optional ``pdf`` extra, since it pulls in `fpdf2 <https://pypi.org/project/fpdf2/>`_:

.. code-block:: console

   $ pip install "fountain-py[pdf]"

With the extra installed, ``--format pdf`` works the same as any other format:

.. code-block:: console

   $ fountain render screenplay.fountain --format pdf -o screenplay.pdf

Without ``-o``, PDF bytes go to stdout, so redirect them to a file rather than printing them to your terminal:

.. code-block:: console

   $ fountain render screenplay.fountain --format pdf > screenplay.pdf

If the extra is not installed, the command exits with status ``1`` and prints an install hint to stderr instead of a traceback.
The command-line tool only exposes :data:`~fountain.renderers.pdf.geometry.LETTER` and the :data:`~fountain.renderers.pdf.profile.SCREENPLAY` layout profile.
For A4, HALF_LETTER, or a custom layout, call :class:`~fountain.renderers.pdf.renderer.PDFRenderer` from Python; see :doc:`export-pdf`.
