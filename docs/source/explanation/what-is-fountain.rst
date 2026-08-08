What Is Fountain?
=================

`Fountain <https://fountain.io/>`_ is a plain-text markup format for screenplays.
It lets you write a script in any text editor and have it read as a formatted
screenplay, without a word processor or specialized software.

The idea is the same one behind Markdown: the raw text is readable on its own, and
a tool can turn it into formatted output.
A blank line and an all-caps line become a scene heading; a name in caps followed
by a line of text becomes a character cue and their dialogue.
You write the words; the format follows from a small set of conventions.

A short example:

.. code-block:: text

   INT. COFFEE SHOP - DAY

   ALICE sits at a corner table, staring at her laptop.

   ALICE
   Come on, inspiration... where are you?

Here ``INT. COFFEE SHOP - DAY`` is a scene heading, the next line is action, and
``ALICE`` followed by a line is a character cue and their dialogue.

Fountain covers the elements a screenplay needs: a title page, scene headings,
action, character cues, dialogue, parentheticals, dual dialogue, lyrics,
transitions, centered text, notes, inline emphasis, and sections and synopses for
outlining.
The full syntax lives at `fountain.io/syntax <https://fountain.io/syntax/>`_.

What fountain-py Adds
---------------------

fountain-py reads Fountain text and gives you the structure behind it: a list of
typed elements you can iterate, query, and transform.
From there you can extract characters and scenes, compute statistics, render the
script to HTML, or write it back out as clean Fountain.

fountain-py teaches the API, not the format.
To learn the Fountain syntax itself, read the `official spec <https://fountain.io/syntax/>`_.
To learn how fountain-py turns that syntax into objects, read :doc:`pipeline`.
