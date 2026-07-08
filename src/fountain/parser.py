# ABOUTME: Fountain markup parser for converting Fountain screenwriting format to structured elements.
# Implements a two-pass parsing strategy with comprehensive regex-based element classification.
"""
Fountain markup parser for converting Fountain screenwriting format to structured elements.

The parser architecture follows a structured two-pass approach designed to handle
Fountain's unique title page format followed by screenplay body content:

**Pass 1: Title Page Metadata Extraction**
- Parses key-value pairs from document header (Title:, Author:, etc.)
- Handles multi-line values and continuation lines
- Stops when encountering the first body element (scene heading, action, etc.)
- Supports all standard Fountain title page fields

**Pass 2: Body Element Classification**
- Line-by-line parsing using regex pattern matching
- Precedence-based classification (forced elements > natural patterns > context-dependent)
- Context-aware dialogue detection using lookahead and element history
- Dual dialogue post-processing to pair simultaneous character speech

**Regex Classification Hierarchy:**
1. Forced elements (!, @, >, .) - highest precedence override
2. Special markers (boneyard, page breaks, notes)
3. Natural structural patterns (scene headings, transitions)
4. Character name detection with dialogue lookahead
5. Context-dependent elements (dialogue, parentheticals)
6. Default fallback to action text

**Key Design Principles:**
- Immutable element creation - elements are created once and never modified
- Minimal memory footprint - streaming line-by-line processing
- Robust error handling - invalid patterns fall back to action text
- Extensible pattern system - regex patterns are class constants for easy customization
"""

import re

from fountain.document import FountainDocument
from fountain.elements import ElementType, FormatSpan, FountainElement, MetadataValue, ValidationIssue

# Diagnostic codes emitted by FountainParser.validate(). Each string is a stable
# machine-readable contract; keep them here as the single source of truth so the
# growing diagnostic set stays consistent across the parser and its consumers.
CODE_UNCLOSED_BONEYARD = "unclosed-boneyard"
CODE_UNCLOSED_NOTE = "unclosed-note"
CODE_ORPHAN_CHARACTER_CUE = "orphan-character-cue"
CODE_EMPTY_DOCUMENT = "empty-document"


class FountainParser:
    """Parser for Fountain markup format.

    This parser implements a two-pass parsing strategy for Fountain screenplay format:
    1. First pass: Extract title page metadata from document header
    2. Second pass: Parse body elements using regex pattern matching

    The parser handles all Fountain specification elements including scene headings,
    character names, dialogue, action lines, transitions, and special formatting.

    Attributes:
        lines: List of text lines being parsed
        current_line: Current line index during parsing
        elements: List of parsed FountainElement objects
        in_boneyard: Flag tracking if parser is inside a multi-line comment block

    Examples:
        >>> parser = FountainParser()
        >>> doc = parser.parse("INT. COFFEE SHOP - DAY\\n\\nJOHN\\nHello world.")
        >>> len(doc.elements)
        3
        >>> doc.elements[0].type
        <ElementType.SCENE_HEADING: 'scene_heading'>
    """

    # Scene Heading Patterns
    # Matches standard scene heading prefixes: INT, EXT, EST, I/E, INTERIOR, EXTERIOR, INT/EXT, INT./EXT
    # Each prefix is followed by a separator: a period (dot form, optional space before it) or a
    # space (space form). Requiring a separator provides a prefix boundary so a word that merely
    # starts with the prefix letters, like "INTERNAL", stays ACTION rather than matching on "INT".
    # Case-insensitive matching allows for "int." or "Int." variations.
    # Examples: "INT. COFFEE SHOP - DAY", "EXT PARK - NIGHT", "I/E. CAR - CONTINUOUS"
    SCENE_HEADING_PATTERN = re.compile(
        r"^(?:INT|EXT|EST|I/E|INTERIOR|EXTERIOR|INT/EXT|INT\./EXT)(?:\s*\.|\s)",
        re.IGNORECASE,
    )

    # Matches scene numbers in format #SCENE_NUMBER# at end of scene headings
    # Captures the scene number content between the hash marks. The content is
    # restricted to alphanumerics, dashes, and periods (B4); a group holding any
    # other character is not a scene number and is left verbatim in the heading.
    # Example: "INT. HOUSE - DAY #1A#" captures "1A"
    SCENE_NUMBER_PATTERN = re.compile(r"\s*#([A-Za-z0-9.-]+)#\s*$")

    # Forced scene heading starts with period (.) to override natural scene detection
    # Used when a line should be a scene heading but doesn't match standard prefixes
    # Example: ".FLASHBACK - 10 YEARS AGO" becomes "FLASHBACK - 10 YEARS AGO"
    FORCED_SCENE_HEADING_PATTERN = re.compile(r"^\.(?!\.)(?=[A-Za-z0-9])")
    # Character Name Patterns
    # Standard character names: ALL CAPS, may include numbers, spaces, underscores, and
    # cue punctuation (C1): a period, apostrophe, or hyphen, plus ``#`` for numbered
    # extras. The first character may be a letter or a digit so a digit-first cue like
    # "23 SKIDOO" is recognized (C2), but the leading ``(?=...)`` lookahead requires at
    # least one uppercase letter somewhere in the cue so a purely numeric line such as
    # "23", "007", or "42" stays ACTION. The class deliberately excludes lowercase
    # letters so a cue stays recognizably uppercase; recognition is further gated by a
    # blank line before and a dialogue lookahead after, so an all-caps action sentence
    # still falls through to action.
    # Examples: "JOHN", "MARY JANE", "ROBOT_1", "MR. SMITH", "O'BRIEN", "JEAN-CLAUDE",
    # "DEALER #2", "23 SKIDOO"
    CHARACTER_PATTERN = re.compile(r"^(?=[A-Z0-9\s_.'#-]*[A-Z])[A-Z0-9][A-Z0-9\s_.'#-]*$")

    # Dual dialogue character: standard character name followed by caret (^)
    # Indicates this character speaks simultaneously with previous character
    # Shares the C1/C2 name rules: digit-first allowed, at least one letter required.
    # Example: "MARY^" for dual dialogue with preceding character
    DUAL_CHARACTER_PATTERN = re.compile(r"^(?=[A-Z0-9\s_.'#-]*[A-Z])[A-Z0-9][A-Z0-9\s_.'#-]*\^\s*$")

    # Forced character name: prefixed with @ to override natural character detection
    # Captures the character name after the @ symbol
    # Example: "@john" forces "john" to be treated as character (even lowercase)
    FORCED_CHARACTER_PATTERN = re.compile(r"^@(.+)$")

    # Trailing extension suffix on a forced cue (C7). Lifts a "(extension)" off the end
    # of a forced ``@`` name so it lands in metadata like a natural cue. The forced path
    # needs its own regex because a forced name may be any case (``@mcclane``), so the
    # uppercase-gated CHARACTER_EXTENSION_PATTERN cannot match it. The name group is
    # non-greedy so the trailing paren group binds to the last "(...)" before end.
    # Example: "McClane (O.S.)" captures name "McClane" and extension "O.S.".
    FORCED_EXTENSION_PATTERN = re.compile(r"^(.*?)\s*\(([^)]+)\)$")

    # Character with extensions: CHARACTER_NAME (extension) with optional dual dialogue caret
    # Captures character name, extension (V.O., O.S., CONT'D, etc.), and dual dialogue marker
    # The name portion shares the C1/C2 rules: digit-first allowed, at least one letter
    # required (the lookahead scans the name, stopping at the extension's open paren).
    # Examples: "JOHN (V.O.)", "MARY (O.S.)^", "NARRATOR (CONT'D)", "MR. SMITH (V.O.)"
    CHARACTER_EXTENSION_PATTERN = re.compile(
        r"^(?=[A-Z0-9\s_.'#-]*[A-Z])([A-Z0-9][A-Z0-9\s_.'#-]*)\s*\(([^)]+)\)\s*(\^)?\s*$"
    )
    # Transition Patterns
    # Standard transitions: ALL CAPS ending with colon, or specific fade patterns
    # Matches common screenplay transitions like "CUT TO:", "FADE IN:", "FADE OUT."
    # Pattern is quite restrictive to avoid false positives
    TRANSITION_PATTERN = re.compile(r"^[A-Z\s]+TO:$|^FADE IN:$|^FADE OUT\.$|^CUT TO:$")

    # Forced transition: prefixed with > to override natural transition detection
    # Example: ">SPECIAL TRANSITION" forces transition treatment
    FORCED_TRANSITION_PATTERN = re.compile(r"^>")

    # Special Element Patterns
    # Forced action: prefixed with ! to ensure line is treated as action
    # Captures the action text after the ! symbol
    # Example: "!This is definitely action" becomes "This is definitely action"
    FORCED_ACTION_PATTERN = re.compile(r"^!(.+)$")

    # Centered text: enclosed in >text< for center alignment
    # Must start with > and end with < with no other < characters inside
    # Example: ">THE END<" creates centered text
    CENTERED_PATTERN = re.compile(r"^>[^<]*<$")
    # Notes: inline comments in format [[note text]]
    # Can appear anywhere in text, captured for special handling
    # Example: "John walks [[this needs work]] to the door"
    # Content allows any character except a bare "]]": a single "]" not followed by
    # another "]" stays part of the note text, so only "]]" closes a note (E10). The
    # content can never span a "]]", which keeps "[[a]] middle [[b]]" from matching as
    # one note and preserves the E13 fullmatch guard and per-note inline stripping.
    NOTE_PATTERN = re.compile(r"\[\[(?:[^\]]|\](?!\]))*\]\]")

    # Boneyard (Comment) Patterns
    # Single-line boneyard: /* comment */ on one line (DOTALL allows newlines in content)
    # Used for comments that should not appear in final output
    BONEYARD_PATTERN = re.compile(r"^/\*.*?\*/$", re.DOTALL)
    # Document Structure Patterns
    # Section headings: one or more # symbols followed by optional whitespace
    # Used for document organization, similar to Markdown headers
    # Examples: "# Act I", "## Scene 1", "### Subplot"
    SECTION_PATTERN = re.compile(r"^#+\s*")

    # Synopsis: prefixed with = for scene/section summaries
    # Removes the = prefix to get synopsis content
    # Example: "= John meets Mary for the first time"
    SYNOPSIS_PATTERN = re.compile(r"^=\s*")

    # Page breaks: three or more equals signs on a line
    # Forces a page break in formatted output
    # Example: "===" or "================="
    PAGE_BREAK_PATTERN = re.compile(r"^===+$")

    # Lyrics: prefixed with ~ for song lyrics or musical elements
    # Captures the lyric text after the ~ symbol
    # Example: "~Happy birthday to you" for lyrics
    LYRICS_PATTERN = re.compile(r"^~(.+)$")

    # Structural patterns used by _is_dialogue_following to detect non-dialogue elements.
    # Hard-structural patterns always disqualify a preceding cue: if the next line
    # matches one of these, it is unambiguously not dialogue.
    HARD_STRUCTURAL_PATTERNS: tuple[re.Pattern[str], ...] = (
        SCENE_HEADING_PATTERN,
        FORCED_SCENE_HEADING_PATTERN,
        TRANSITION_PATTERN,
        FORCED_TRANSITION_PATTERN,
        SECTION_PATTERN,
        SYNOPSIS_PATTERN,
        PAGE_BREAK_PATTERN,
        CENTERED_PATTERN,
        FORCED_ACTION_PATTERN,
    )

    # Cue patterns are ambiguous: an all-caps line matching one of these is only a
    # rival structural element (disqualifying a preceding cue) if it is ITSELF a real
    # cue — that is, its own next non-empty line is dialogue. Otherwise it is dialogue
    # for the preceding cue. This keeps punctuated shouts like ``NO. NEVER.`` and
    # all-caps dialogue like ``I SAID NO`` from demoting the cue above them to action.
    CUE_PATTERNS: tuple[re.Pattern[str], ...] = (
        CHARACTER_PATTERN,
        DUAL_CHARACTER_PATTERN,
        FORCED_CHARACTER_PATTERN,
        CHARACTER_EXTENSION_PATTERN,
    )

    # Inline Formatting Patterns
    # These patterns handle Fountain's inline text formatting similar to Markdown

    # Bold + Italic: ***text*** - three asterisks on each side
    # Highest precedence formatting, captures text between triple asterisks
    # Example: "***very important***" renders as bold and italic
    BOLD_ITALIC_PATTERN = re.compile(r"\*\*\*([^*]+)\*\*\*")

    # Bold: **text** - two asterisks on each side
    # Captures text between double asterisks, excludes if part of triple asterisks
    # Example: "**important**" renders as bold text
    BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")

    # Italic: *text* - single asterisks, with complex lookahead/lookbehind
    # Negative lookbehind (?<!\*) ensures not preceded by asterisk (avoids **text** collision)
    # Negative lookahead (?!\*) ensures not followed by asterisk
    # Requires non-whitespace start/end to avoid false positives
    # Example: "*emphasis*" renders as italic text
    ITALIC_PATTERN = re.compile(r"(?<!\*)\*([^*\s](?:[^*]*[^*\s])?)\*(?!\*)")

    # Underline: _text_ - underscores on each side
    # Captures text between underscores for underline formatting
    # Example: "_underlined_" renders as underlined text
    UNDERLINE_PATTERN = re.compile(r"_([^_]+)_")

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.current_line = 0
        self.elements: list[FountainElement] = []
        self.in_boneyard = False
        self.boneyard_start_line = 0
        self.in_note = False
        self.note_buffer: list[str] = []
        self.note_start_line = 0
        # Diagnostics collected during a validate() scan. parse() leaves this
        # untouched (it only records when _validating is True), so a plain
        # parse() call never depends on or mutates validation state.
        self._validating = False
        self.diagnostics: list[ValidationIssue] = []

    def parse(self, text: str) -> FountainDocument:
        """Parse Fountain text and return a FountainDocument.

        Implements a two-pass parsing strategy:
        1. First pass: Extract title page metadata from document header
        2. Second pass: Parse body elements line by line using regex classification

        The parser processes elements in order, maintaining context for dialogue
        detection and handling special cases like dual dialogue pairing.

        Args:
            text: Raw Fountain markup text to parse

        Returns:
            FountainDocument containing parsed elements and metadata

        Basic parsing with title page and dialogue:

            >>> parser = FountainParser()
            >>> script = "Title: My Script\\n\\nINT. HOUSE - DAY\\n\\nJOHN\\nHello there."
            >>> doc = parser.parse(script)
            >>> doc.metadata['title']
            'My Script'
            >>> len(doc.elements)
            3
            >>> doc.elements[0].type.value
            'scene_heading'

        Complex parsing with forced elements and formatting:
            >>> complex_script = '''Title: Complex Script
            ... Author: Test Author
            ...
            ... .FLASHBACK - TITLE SEQUENCE
            ...
            ... @narrator
            ... This is **bold** and *italic* text.
            ...
            ... >THE END<'''
            >>> doc = parser.parse(complex_script)
            >>> doc.metadata['author']
            'Test Author'
            >>> doc.elements[0].metadata['forced']
            True
            >>> doc.elements[1].metadata['forced']
            True
            >>> len(doc.elements[2].formatting)
            2
            >>> doc.elements[3].type.value
            'centered'

        Complex dual dialogue with extensions and formatting:
            >>> dual_script = '''Title: Dual Dialogue Test
            ...
            ... INT. RESTAURANT - NIGHT
            ...
            ... JOHN (V.O.)
            ... This is my **inner voice**.
            ...
            ... MARY (PHONE)^
            ... I can hear you from _here_.
            ...
            ... >THE END<'''
            >>> doc = parser.parse(dual_script)
            >>> doc.elements[0].type.value  # Scene heading
            'scene_heading'
            >>> doc.elements[1].type.value  # Dual dialogue element (characters combined)
            'dual_dialogue'
            >>> doc.elements[1].metadata['left_character'].metadata['extension']
            'V.O.'
            >>> doc.elements[1].metadata['right_character'].metadata['extension']
            'PHONE'
            >>> len(doc.elements[1].metadata['left_dialogue'])  # Bold formatting preserved
            1
            >>> doc.elements[2].type.value  # Centered text
            'centered'

        Boneyard comments and special elements:
            >>> boneyard_script = '''/* This is a comment */
            ... INT. HOUSE - DAY
            ...
            ... [[This is a note]]
            ...
            ... JOHN
            ... Hello /* inline comment */ world.
            ...
            ... ===
            ...
            ... # Act Two
            ...
            ... = Synopsis of next scene'''
            >>> doc = parser.parse(boneyard_script)
            >>> doc.elements[0].type.value
            'boneyard'
            >>> doc.elements[2].type.value
            'note'
            >>> doc.elements[5].type.value
            'page_break'
            >>> doc.elements[6].type.value
            'section'
            >>> doc.elements[7].type.value
            'synopsis'
        """
        self.lines = text.split("\n")
        self.current_line = 0
        self.elements = []
        self.in_boneyard = False
        self.boneyard_start_line = 0
        self.in_note = False
        self.note_buffer = []
        self.note_start_line = 0
        self.diagnostics = []

        # First pass: extract title page
        metadata = self._parse_title_page()

        # Second pass: parse body elements
        previous_line_was_blank = False
        while self.current_line < len(self.lines):
            raw_line = self.lines[self.current_line]
            line = raw_line.rstrip()

            if not line:  # Empty after rstrip
                # Check for whitespace-only line in dialogue context (spec: two spaces continues dialogue)
                is_whitespace_only = bool(raw_line) and raw_line != raw_line.lstrip()
                if self.in_note:
                    if is_whitespace_only:
                        # E6: a two-space connector line keeps an open note open and
                        # preserves an empty interior line, so the note text carries a
                        # blank line (a "\n\n") between its surrounding lines.
                        self.note_buffer.append("")
                        self.current_line += 1
                        continue
                    # E7: a genuinely blank line breaks an open note. The buffered
                    # bracket lines never closed, so they fall back to action text
                    # rather than surviving as one NOTE.
                    self._flush_open_note_as_text()
                    previous_line_was_blank = True
                    self.current_line += 1
                    continue
                in_dialogue_context = self.elements and self.elements[-1].type in (
                    ElementType.DIALOGUE,
                    ElementType.PARENTHETICAL,
                    ElementType.CHARACTER,
                )
                if is_whitespace_only and in_dialogue_context:
                    # Whitespace-only line preserves a blank line within dialogue
                    self.elements.append(
                        FountainElement(
                            type=ElementType.DIALOGUE,
                            text="",
                            formatting=[],
                            line_number=self.current_line + 1,
                        )
                    )
                    self.current_line += 1
                    continue
                previous_line_was_blank = True
                self.current_line += 1
                continue

            element = self._parse_line(line, previous_line_was_blank, raw_line)
            if element:
                element.text = self._strip_escapes(element.text)
                self.elements.append(element)

            previous_line_was_blank = False
            self.current_line += 1

        # Post-process for dual dialogue pairing
        self._process_dual_dialogue()

        return FountainDocument(self.elements, metadata)

    def parse_file(self, filepath: str) -> FountainDocument:
        """Parse a Fountain file and return a FountainDocument.

        Convenience method that reads a Fountain file from disk and parses it into
        a structured FountainDocument. Handles file encoding as UTF-8 and properly
        closes file handles.

        Args:
            filepath: Path to the Fountain file to parse. Can be absolute or relative.

        Returns:
            FountainDocument containing the parsed screenplay elements and metadata

        Raises:
            FileNotFoundError: If the specified file does not exist
            IOError: If the file cannot be read
            UnicodeDecodeError: If the file is not valid UTF-8

        Examples:
            >>> parser = FountainParser()
            >>> doc = parser.parse_file("screenplay.fountain")  # doctest: +SKIP
            >>> print(f"Title: {doc.metadata.get('title', 'Untitled')}")  # doctest: +SKIP
            Title: My Great Screenplay
            >>> len(doc.elements)  # doctest: +SKIP
            42

        Note:
            This method assumes UTF-8 encoding, which is standard for Fountain files.
            If you need to handle other encodings, read the file manually and use
            the parse() method instead.
        """
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
        return self.parse(text)

    def validate(self, text: str) -> list[ValidationIssue]:
        """Validate Fountain text and return a list of diagnostics.

        Runs the same two-pass analysis as :meth:`parse`, but collects diagnostics
        about structural problems instead of discarding the information. :meth:`parse`
        stays lenient and non-raising; :meth:`validate` reports what a lenient parse
        silently tolerated. Calling validate() does not change what a later parse()
        of the same text returns, because parse() fully resets parser state on entry.

        The initial diagnostic set covers:

        - ``unclosed-boneyard`` (error): a ``/*`` comment opened but never closed
        - ``unclosed-note`` (error): a ``[[`` note opened but never closed
        - ``orphan-character-cue`` (warning): an uppercase cue demoted to action
          because no dialogue follows it
        - ``empty-document`` (warning): input that parses to zero elements

        Args:
            text: Raw Fountain markup text to validate

        Returns:
            List of :class:`~fountain.elements.ValidationIssue` diagnostics. Empty
            when the document is well formed.

        Examples:
            >>> parser = FountainParser()
            >>> parser.validate("INT. HOUSE - DAY\\n\\nJOHN\\nHello.")
            []
            >>> issues = parser.validate("INT. HOUSE - DAY\\n\\n/* open")
            >>> issues[0].code
            'unclosed-boneyard'
            >>> issues[0].severity
            'error'
        """
        self._validating = True
        try:
            document = self.parse(text)
        finally:
            self._validating = False

        # Diagnostics recorded mid-scan (orphan character cues) come first, in
        # document order. End-of-document diagnostics are derived from the parser
        # state left over after the scan completes.
        issues = list(self.diagnostics)

        if self.in_boneyard:
            issues.append(
                ValidationIssue(
                    line_number=self.boneyard_start_line,
                    severity="error",
                    code=CODE_UNCLOSED_BONEYARD,
                    message="Boneyard comment opened with '/*' but never closed",
                )
            )

        if self.in_note:
            issues.append(
                ValidationIssue(
                    line_number=self.note_start_line,
                    severity="error",
                    code=CODE_UNCLOSED_NOTE,
                    message="Note opened with '[[' but never closed",
                )
            )

        # Only report an empty document when nothing else already explains the
        # emptiness (e.g. an unclosed boneyard that swallowed the whole body).
        if not document.elements and not issues:
            issues.append(
                ValidationIssue(
                    line_number=1,
                    severity="warning",
                    code=CODE_EMPTY_DOCUMENT,
                    message="Document parsed to zero elements",
                )
            )

        return issues

    def _parse_title_page(self) -> dict[str, str]:
        """Parse title page metadata from the beginning of the document.

        Extracts key-value pairs from the document header using Fountain's title page format.
        Supports multi-line values and handles common title page fields like title, author,
        credit, source, draft date, contact information, and custom fields.

        The title page ends when a scene heading or other body element is encountered.
        Multi-line values are supported by continuing on subsequent lines without a colon.

        Returns:
            Dict mapping field names (lowercase) to their string values

        Examples:
            >>> parser = FountainParser()
            >>> parser.lines = ["Title: My Great Script", "Author: John Doe", "", "INT. HOUSE - DAY"]
            >>> parser.current_line = 0
            >>> metadata = parser._parse_title_page()
            >>> metadata['title']
            'My Great Script'
            >>> metadata['author']
            'John Doe'

        Note:
            Supported fields include: title, author, credit, source, draft date, contact,
            authors, notes, copyright, date, revised, version, format, created, writers,
            producer, director. Per the Fountain spec, any key ending with a colon is valid.
        """
        metadata = {}
        current_key = None

        while self.current_line < len(self.lines):
            raw_line = self.lines[self.current_line]
            line = raw_line.strip()

            if not line:
                # Empty line ends title page when we have at least one key
                if current_key is not None:
                    break
                # Skip leading blank lines before title page content
                self.current_line += 1
                continue

            # Indentation is tested on the raw (unstripped) line so we can see it:
            # a leading tab or 3+ leading spaces marks a continuation (A2). The
            # stripped ``line`` used above cannot carry this information.
            leading_spaces = len(raw_line) - len(raw_line.lstrip(" "))
            is_indented = raw_line.startswith("\t") or leading_spaces >= 3

            # An indented line is always a value/continuation of the current key,
            # even when it contains a colon (A2): an indented ``Draft 3: final``
            # stays the current key's value rather than opening a ``draft 3`` key.
            # Join with a newline (not a space) so a multi-line value keeps its
            # line structure (A1); the HTML renderer converts these newlines to
            # <br> for multiline fields like contact and notes.
            if is_indented and current_key is not None:
                if metadata[current_key]:
                    metadata[current_key] += "\n" + line
                else:
                    metadata[current_key] = line
                self.current_line += 1
                continue

            # A non-indented line with a colon (and not a scene heading) starts a
            # new key. The scene-heading guard reuses SCENE_HEADING_PATTERN so it is
            # case-insensitive and space-form aware (B3): a line like
            # "int. house - day - 3:00 pm" contains a colon (from the time) but is a
            # scene heading, so it must fall through to body classification rather
            # than opening a bogus "int. house - day - 3" key.
            if ":" in line and not self.SCENE_HEADING_PATTERN.match(line):
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if current_key and current_key in metadata:
                    # Finalize previous multi-line value
                    metadata[current_key] = metadata[current_key].strip()

                current_key = key
                metadata[key] = value
                self.current_line += 1
                continue

            # Any other non-indented line ends the title page (A2): an unindented
            # non-key line is body content, not a continuation of the prior value.
            break

        # Clean up any trailing multi-line value
        if current_key and current_key in metadata:
            metadata[current_key] = metadata[current_key].strip()

        return metadata

    def _flush_open_note_as_text(self) -> None:
        """Break an open multi-line note and re-emit its buffered lines as action.

        When a genuinely blank line interrupts a note that opened with ``[[`` but never
        closed, the note does not survive as a single NOTE element (E7). The buffered
        bracket lines fall back to action text instead. Empty buffered lines (left by
        two-space connector lines under E6) carry no content and are dropped, so only
        real bracket text is re-emitted.

        This mutates parser state: it clears the open-note flag and buffer, then appends
        one ACTION element per non-empty buffered line to :attr:`elements`.
        """
        buffered_lines = self.note_buffer
        note_start = self.note_start_line
        self.in_note = False
        self.note_buffer = []
        for line_offset, buffered_line in enumerate(buffered_lines):
            if not buffered_line.strip():
                continue
            element = FountainElement(
                type=ElementType.ACTION,
                text=buffered_line,
                formatting=self._extract_formatting(buffered_line),
                line_number=note_start + line_offset,
            )
            element.text = self._strip_escapes(element.text)
            self.elements.append(element)

    def _parse_line(
        self, line: str, had_blank_line_before: bool = False, raw_line: str | None = None
    ) -> FountainElement | None:
        """Parse a single line and return the appropriate FountainElement.

        Classifies a single line of Fountain text into the appropriate element type using
        regex pattern matching. Handles precedence rules and context-sensitive parsing
        for elements like dialogue vs. action lines.

        The parsing follows Fountain's precedence rules:
        1. Forced elements (prefixed with !, @, >, .) take highest precedence
        2. Special markers (boneyard, notes, page breaks) are checked early
        3. Natural patterns (scene headings, characters, transitions) are matched
        4. Context-dependent elements (dialogue, parentheticals) use previous elements
        5. Default fallback is action text

        Args:
            line: The text line to parse (may include leading/trailing whitespace)
            had_blank_line_before: Whether there was a blank line before this one,
                                  affects dialogue continuation detection
            raw_line: The untrimmed source line, when available. Used so the natural
                     transition rule can see trailing whitespace (D1); recursive
                     callers that pass a stripped remainder omit it.

        Returns:
            FountainElement instance for the parsed line, or None if line should be skipped
            (e.g., inside boneyard comments, empty lines)

        Examples:
            Scene heading with scene number:
            >>> parser = FountainParser()
            >>> parser.current_line = 0
            >>> element = parser._parse_line("INT. COFFEE SHOP - DAY #1#")
            >>> element.type.value
            'scene_heading'
            >>> element.text
            'INT. COFFEE SHOP - DAY'
            >>> element.metadata['scene_number']
            '1'

            Forced character:
            >>> parser.lines = ["@john", "Hello there"]
            >>> parser.current_line = 0
            >>> element = parser._parse_line("@john")
            >>> element.type.value
            'character'
            >>> element.text
            'john'
            >>> element.metadata['forced']
            True

            Character with extension and dual dialogue:
            >>> parser.lines = ["MARY (V.O.)^", "Hello there"]
            >>> parser.current_line = 0
            >>> element = parser._parse_line("MARY (V.O.)^")
            >>> element.type.value
            'character'
            >>> element.text
            'MARY'
            >>> element.metadata['extension']
            'V.O.'
            >>> element.metadata['dual_dialogue']
            True

            Centered text:
            >>> element = parser._parse_line(">THE END<")
            >>> element.type.value
            'centered'
            >>> element.text
            'THE END'
        """
        original_line = line
        line = line.strip()

        if not line:
            return None

        # Handle multi-line boneyard comments
        if self.in_boneyard:
            close_index = line.find("*/")
            if close_index != -1:
                # The first */ closes the boneyard. Everything up to and including
                # it is comment; the remainder of the line is reprocessed as body so
                # trailing content on the close line is not dropped.
                self.in_boneyard = False
                remainder = line[close_index + 2 :].strip()
                if remainder:
                    return self._parse_line(remainder, had_blank_line_before)
            return None  # Skip all lines inside boneyard

        # Check for single-line boneyard (block comments) - handle before multiline start.
        # A whole-line /* ... */ stays a BONEYARD element.
        if self.BONEYARD_PATTERN.match(line):
            return FountainElement(
                type=ElementType.BONEYARD,
                text=line,
                formatting=[],
                line_number=self.current_line + 1,
            )

        # A line containing /* somewhere other than a whole-line span. Two cases,
        # both handled here so a line with leading body text never truncates the
        # document. If a */ also appears on the line the span opens and closes
        # here (e.g. "/* cut */ keep this"): strip the span and reprocess the
        # surrounding remainder as body. Otherwise the /* opens a multi-line
        # boneyard that closes on a later line.
        open_index = line.find("/*")
        if open_index != -1:
            close_index = line.find("*/", open_index + 2)
            if close_index != -1:
                # Strip the span and rejoin. When both sides carry text the removed
                # span leaves a whitespace seam ("Hello  world."); collapse just that
                # seam to a single space without touching internal whitespace elsewhere.
                before = line[:open_index]
                after = line[close_index + 2 :]
                if before.strip() and after.strip():
                    remainder = f"{before.rstrip()} {after.lstrip()}".strip()
                else:
                    remainder = (before + after).strip()
                if remainder:
                    return self._parse_line(remainder, had_blank_line_before)
                return None
            # The /* opens a boneyard that does not close on this line. Anything
            # before it (e.g. "He waves" in "He waves /* begin cut") is body and
            # must be emitted; the /* and every following line is comment until a
            # */ closes it. Reprocess the pre-text before entering boneyard state
            # so the recursive call is not itself swallowed by the in_boneyard
            # branch above. boneyard_start_line feeds the unclosed-boneyard
            # diagnostic in validate() when no */ ever arrives.
            self.boneyard_start_line = self.current_line + 1
            pre_text = line[:open_index].strip()
            if pre_text:
                pre_element = self._parse_line(pre_text, had_blank_line_before)
                self.in_boneyard = True
                return pre_element
            self.in_boneyard = True
            return None  # Skip boneyard start line

        # Handle multi-line notes
        if self.in_note:
            self.note_buffer.append(original_line)
            if "]]" in line:
                self.in_note = False
                note_text = "\n".join(self.note_buffer)
                return FountainElement(
                    type=ElementType.NOTE,
                    text=note_text,
                    formatting=[],
                    line_number=self.note_start_line,
                )
            return None

        # Check for page breaks
        if self.PAGE_BREAK_PATTERN.match(line):
            return FountainElement(
                type=ElementType.PAGE_BREAK,
                text=line,
                formatting=[],
                line_number=self.current_line + 1,
            )

        # Check for notes [[note]]
        note_matches = list(self.NOTE_PATTERN.finditer(line))
        # A whole-line note is a single complete [[...]] span covering the entire
        # line. Testing only startswith("[[")/endswith("]]") is too loose: a line
        # like "[[a]] middle [[b]]" also passes it while carrying real text between
        # two separate notes. Requiring a fullmatch keeps that case out so it falls
        # through to inline-note stripping (body rule 8) and the interior text
        # classifies normally (E13).
        if self.NOTE_PATTERN.fullmatch(line):
            # Line is entirely a single note
            return FountainElement(
                type=ElementType.NOTE,
                text=line,
                formatting=[],
                line_number=self.current_line + 1,
            )

        # Check for multi-line note start: line has [[ but no closing ]]
        if "[[" in line and "]]" not in line:
            self.in_note = True
            self.note_buffer = [original_line]
            self.note_start_line = self.current_line + 1
            return None

        # Strip inline notes from the line text
        if note_matches:
            line = self.NOTE_PATTERN.sub("", line).strip()
            # Removing a note leaves a whitespace seam. Always drop the trailing
            # seam. Only drop the leading seam when a note began the line (col 0 of
            # the stripped line): a front note (e.g. "[[a]] middle") leaves a leading
            # seam that is an artifact of the note. A line whose note is at the END
            # (e.g. "\tIndented action [[note]]") must keep its deliberate leading
            # indentation, so lstrip only when the first note starts the content.
            note_starts_line = note_matches[0].start() == 0
            original_line = self.NOTE_PATTERN.sub("", original_line).rstrip()
            if note_starts_line:
                original_line = original_line.lstrip()
            if not line:
                return None

        # Check for forced action (starts with !)
        if self.FORCED_ACTION_PATTERN.match(line):
            text = self.FORCED_ACTION_PATTERN.sub(r"\1", line).strip()
            return FountainElement(
                type=ElementType.ACTION,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
            )

        # Check for sections
        if self.SECTION_PATTERN.match(line):
            level = len(line) - len(line.lstrip("#"))
            text = self.SECTION_PATTERN.sub("", line).strip()
            return FountainElement(
                type=ElementType.SECTION,
                text=text,
                formatting=self._extract_formatting(text),
                metadata={"level": level},
                line_number=self.current_line + 1,
            )

        # Check for synopsis
        if self.SYNOPSIS_PATTERN.match(line):
            text = self.SYNOPSIS_PATTERN.sub("", line).strip()
            return FountainElement(
                type=ElementType.SYNOPSIS,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
            )

        # Check for lyrics
        lyrics_match = self.LYRICS_PATTERN.match(line)
        if lyrics_match:
            text = lyrics_match.group(1).strip()
            return FountainElement(
                type=ElementType.LYRICS,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
            )

        # Check for forced scene heading (must come before natural scene heading)
        if self.FORCED_SCENE_HEADING_PATTERN.match(line):
            text = line[1:].strip()  # Remove the '.'
            metadata: dict[str, MetadataValue] = {"forced": True}
            # Check for scene number
            scene_num_match = self.SCENE_NUMBER_PATTERN.search(text)
            if scene_num_match:
                metadata["scene_number"] = scene_num_match.group(1).strip()
                text = self.SCENE_NUMBER_PATTERN.sub("", text).strip()
            return FountainElement(
                type=ElementType.SCENE_HEADING,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
                metadata=metadata,
            )

        # Check for centered text (>text<) - must come before forced transition
        if self.CENTERED_PATTERN.match(line):
            text = line[1:-1].strip()  # Remove the '>' and '<'
            return FountainElement(
                type=ElementType.CENTERED,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
            )

        # Check for forced transition (>text - not enclosed)
        if self.FORCED_TRANSITION_PATTERN.match(line) and not line.endswith("<"):
            text = line[1:].strip()  # Remove the '>'
            return FountainElement(
                type=ElementType.TRANSITION,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
            )

        # Check for scene heading (requires a blank line before and after, or
        # first/last element). The blank-line-after rule mirrors the transition
        # branch below (B2): a natural heading immediately followed by a non-blank
        # line is really action, so it falls through. Forced `.` headings are
        # handled earlier and stay headings regardless of the following line.
        if (
            self.SCENE_HEADING_PATTERN.match(line)
            and (had_blank_line_before or not self.elements)
            and self._is_blank_line_after()
        ):
            scene_metadata: dict[str, MetadataValue] = {}
            text = line
            # Check for scene number
            scene_num_match = self.SCENE_NUMBER_PATTERN.search(text)
            if scene_num_match:
                scene_metadata["scene_number"] = scene_num_match.group(1).strip()
                text = self.SCENE_NUMBER_PATTERN.sub("", text).strip()
            return FountainElement(
                type=ElementType.SCENE_HEADING,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
                metadata=scene_metadata,
            )

        # Check for transition (requires blank line before and after, or first/last element).
        # D1: trailing whitespace after the colon defeats a natural transition. The pattern
        # is end-anchored, so matching it against the raw (leading-stripped only) line makes
        # `CUT TO: ` fall through to action. Recursive remainders carry no raw line and use
        # the already-stripped `line`.
        has_blank_before = had_blank_line_before or not self.elements
        transition_source = raw_line.lstrip() if raw_line is not None else line
        if self.TRANSITION_PATTERN.match(transition_source) and has_blank_before and self._is_blank_line_after():
            return FountainElement(
                type=ElementType.TRANSITION,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1,
            )

        # Check for forced character (@character)
        if self.FORCED_CHARACTER_PATTERN.match(line):
            character_name = self.FORCED_CHARACTER_PATTERN.sub(r"\1", line).strip()
            # A trailing caret marks dual dialogue (C5), mirroring natural NAME^ cues.
            # Strip the caret and the whitespace between the name and it, then flag the
            # cue so _process_dual_dialogue pairs it with the preceding character block.
            forced_metadata: dict[str, MetadataValue] = {"forced": True}
            if character_name.endswith("^"):
                character_name = character_name[:-1].strip()
                forced_metadata["dual_dialogue"] = True
            # C7: lift a trailing "(extension)" off the forced name after the caret is
            # handled, so "@McClane (O.S.)" and "@McClane (O.S.) ^" both keep only the bare
            # name in the text with the extension in metadata, mirroring natural cues.
            extension_match = self.FORCED_EXTENSION_PATTERN.match(character_name)
            if extension_match:
                character_name = extension_match.group(1).strip()
                forced_metadata["extension"] = extension_match.group(2).strip()
            # C6: the '@' is an explicit author override, so it forces a CHARACTER cue
            # unconditionally. Unlike natural cues (which stay gated on the dialogue
            # lookahead below), a forced cue is a cue whether dialogue, a blank line,
            # action, or EOF follows — never demote it back to ACTION with the '@' kept.
            return FountainElement(
                type=ElementType.CHARACTER,
                text=character_name,
                formatting=[],
                line_number=self.current_line + 1,
                metadata=forced_metadata,
            )

        # Check for dual dialogue character (CHARACTER^) — requires blank line before or first element.
        # A scene-heading form (INT./EXT. …) that degraded to here is action, never a cue (C1 guard).
        if (
            self.DUAL_CHARACTER_PATTERN.match(line)
            and (had_blank_line_before or not self.elements)
            and not self.SCENE_HEADING_PATTERN.match(line)
        ):
            character_name = line.replace("^", "").strip()
            if self._is_dialogue_following():
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata={"dual_dialogue": True},
                )

        # Check for character with extensions (CHARACTER (V.O.)) — requires blank line before or first element
        char_ext_match = self.CHARACTER_EXTENSION_PATTERN.match(line)
        if (
            char_ext_match
            and (had_blank_line_before or not self.elements)
            and not self.SCENE_HEADING_PATTERN.match(line)
        ):
            character_name = char_ext_match.group(1).strip()
            extension = char_ext_match.group(2).strip()
            is_dual = char_ext_match.group(3) is not None
            if self._is_dialogue_following():
                char_metadata: dict[str, MetadataValue] = {"extension": extension}
                if is_dual:
                    char_metadata["dual_dialogue"] = True
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata=char_metadata,
                )

        # Check for regular character (must be all caps) — requires blank line before or first element.
        # A scene-heading form (INT./EXT. …) that degraded to here is action, never a cue (C1 guard).
        if (
            self.CHARACTER_PATTERN.match(line)
            and (had_blank_line_before or not self.elements)
            and not self.SCENE_HEADING_PATTERN.match(line)
        ):
            # Look ahead to see if next line is dialogue or parenthetical
            if self._is_dialogue_following():
                metadata = {}

                # Check if this character is continuing from a previous appearance
                if self._is_character_continuation(line):
                    metadata["continuation"] = True

                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=line,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata=metadata if metadata else None,
                )
            # An uppercase line that looks like a character cue but has no dialogue
            # following is demoted to action below. During validation, flag it: a
            # writer who meant it as a cue has an orphaned character with no lines.
            if self._validating:
                self.diagnostics.append(
                    ValidationIssue(
                        line_number=self.current_line + 1,
                        severity="warning",
                        code=CODE_ORPHAN_CHARACTER_CUE,
                        message=f"Character cue '{line}' has no dialogue following it",
                    )
                )

        # Check if this is dialogue (follows character or parenthetical)
        # BUT check for parenthetical first since it has higher precedence
        if self._is_dialogue_line(had_blank_line_before):
            # Check for parenthetical within dialogue context
            if line.startswith("(") and line.endswith(")"):
                return FountainElement(
                    type=ElementType.PARENTHETICAL,
                    text=line,
                    formatting=self._extract_formatting(line),
                    line_number=self.current_line + 1,
                )
            # Otherwise it's regular dialogue
            return FountainElement(
                type=ElementType.DIALOGUE,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1,
            )

        # Default to action
        return FountainElement(
            type=ElementType.ACTION,
            # Preserve leading indentation, converting each tab to four spaces (A5)
            # so the stored text carries spaces rather than a raw tab. This keeps
            # indentation consistent with the space-based offsets D8 computes.
            text=original_line.rstrip().replace("\t", "    "),
            formatting=self._extract_formatting(line),
            line_number=self.current_line + 1,
        )

    def _is_dialogue_following(self) -> bool:
        """Check if the next non-empty line is dialogue.

        Lookahead method that examines subsequent lines to determine if the current line
        should be classified as a character name. This prevents false positive character
        detection when ALL CAPS text appears in action lines.

        The cue must be immediately followed by its dialogue: a blank line (or EOF)
        directly after the cue disqualifies it (C3). Otherwise the method checks if
        the immediate next line matches any structural element patterns. If no
        structural patterns match, the line is considered potential dialogue,
        confirming the current line as a character.

        Returns:
            bool: True if the next non-empty line appears to be dialogue, parenthetical,
                  or other non-structural text. False if it matches scene headings,
                  transitions, or other structural elements.

        Examples:
            >>> parser = FountainParser()
            >>> parser.lines = ["JOHN", "Hello there", "How are you?"]
            >>> parser.current_line = 0
            >>> parser._is_dialogue_following()
            True

            >>> parser.lines = ["FADE IN", "INT. HOUSE - DAY"]
            >>> parser.current_line = 0
            >>> parser._is_dialogue_following()
            False

        Note:
            This method is critical for distinguishing between character names and
            action text that happens to be in ALL CAPS (like "FADE IN" or "THE END").
        """
        # The cue must be immediately followed by its dialogue: a blank line (or
        # EOF) directly after the cue disqualifies it (C3). Do not skip the blank
        # to reach a later non-empty line, or "JOHN\n\nHe walks..." would wrongly
        # treat JOHN as a cue for the later action.
        if self._is_blank_line_after():
            return False

        next_line_idx = self.current_line + 1
        while next_line_idx < len(self.lines):
            next_line = self.lines[next_line_idx].strip()
            if next_line:
                # A hard-structural line (scene heading, transition, section, etc.)
                # or standalone note is never this cue's dialogue.
                is_hard_structural = any(p.match(next_line) for p in self.HARD_STRUCTURAL_PATTERNS)
                is_standalone_note = next_line.startswith("[[") and next_line.endswith("]]")
                if is_hard_structural or is_standalone_note:
                    return False
                # An all-caps line that merely looks like a cue is only a rival cue
                # (and thus not dialogue) if it is itself followed by its own dialogue.
                # Otherwise it is dialogue for the preceding cue.
                matches_cue = any(p.match(next_line) for p in self.CUE_PATTERNS)
                if matches_cue and self._line_is_cue(next_line_idx):
                    return False
                return True
            next_line_idx += 1
        return False

    def _line_is_cue(self, line_idx: int) -> bool:
        """Check whether the line at ``line_idx`` is itself a real character cue.

        A line is a real cue when its own next non-empty line is dialogue: not a
        hard-structural element, not a standalone note, and not another line that
        merely looks like a cue. This lets :meth:`_is_dialogue_following` tell a
        genuine second cue (``JOHN`` then ``MARY`` then dialogue) apart from an
        all-caps dialogue line (``JOHN`` then ``NO. NEVER.``).

        Args:
            line_idx: Index into ``self.lines`` of the candidate cue line.

        Returns:
            bool: True if the candidate line is followed by its own dialogue.

        Examples:
            >>> parser = FountainParser()
            >>> parser.lines = ["JOHN", "MARY", "Hello there"]
            >>> parser._line_is_cue(1)
            True

            >>> parser.lines = ["JOHN", "NO. NEVER."]
            >>> parser._line_is_cue(1)
            False
        """
        scan_idx = line_idx + 1
        while scan_idx < len(self.lines):
            candidate = self.lines[scan_idx].strip()
            if candidate:
                is_hard_structural = any(p.match(candidate) for p in self.HARD_STRUCTURAL_PATTERNS)
                is_standalone_note = candidate.startswith("[[") and candidate.endswith("]]")
                matches_cue = any(p.match(candidate) for p in self.CUE_PATTERNS)
                return not (is_hard_structural or is_standalone_note or matches_cue)
            scan_idx += 1
        return False

    def _is_blank_line_after(self) -> bool:
        """Check if there is a blank line (or EOF) after the current line.

        Returns:
            bool: True if the next line is empty or we are at the end of the document.
        """
        next_idx = self.current_line + 1
        if next_idx >= len(self.lines):
            return True  # EOF counts as blank after
        return not self.lines[next_idx].strip()

    def _is_dialogue_line(self, had_blank_line_before: bool = False) -> bool:
        """Check if current line is dialogue based on previous elements.

        Determines if the current line should be classified as dialogue by examining
        the context provided by previously parsed elements. Uses Fountain's dialogue
        rules: dialogue always follows character names or parentheticals, and can
        continue across multiple lines without blank line separation.

        Args:
            had_blank_line_before: Whether there was a blank line before this line.
                                   Used to determine dialogue continuation vs new element.

        Returns:
            bool: True if this line should be classified as dialogue

        Examples:
            >>> parser = FountainParser()
            >>> parser.elements = [FountainElement(ElementType.CHARACTER, "JOHN", [], 1)]
            >>> parser._is_dialogue_line()
            True

            >>> parser.elements = [FountainElement(ElementType.ACTION, "John walks", [], 1)]
            >>> parser._is_dialogue_line()
            False

            Dialogue continuation example:
            >>> dialogue1 = FountainElement(ElementType.DIALOGUE, "Hello there.", [], 1)
            >>> parser.elements = [FountainElement(ElementType.CHARACTER, "JOHN", [], 1), dialogue1]
            >>> parser._is_dialogue_line(had_blank_line_before=False)  # Continuation
            True
            >>> parser._is_dialogue_line(had_blank_line_before=True)   # New element
            False

        Note:
            This method implements Fountain's dialogue continuation rules where dialogue
            can span multiple lines as long as there are no blank lines between them.
        """
        if not self.elements:
            return False

        prev_element = self.elements[-1]

        # Dialogue follows a CHARACTER or PARENTHETICAL cue, but only when it comes
        # immediately after (no blank line between). Per the Fountain spec a blank line
        # ends the dialogue block, so the not-had_blank_line_before guard applies to any
        # CHARACTER/PARENTHETICAL block, natural or forced. A natural cue can reach here
        # with a blank line after (e.g. JOHN / (softly) / blank / Hi.: prev is
        # PARENTHETICAL and had_blank_line_before is True), and Hi. correctly classifies
        # as action. It also covers forced '@' cues (C6), which force a CHARACTER even
        # with no dialogue after them: a line past the blank is action, not dialogue.
        if prev_element.type in (ElementType.CHARACTER, ElementType.PARENTHETICAL) and not had_blank_line_before:
            return True

        # Dialogue continuation: follows DIALOGUE with NO blank line separation
        if prev_element.type == ElementType.DIALOGUE and not had_blank_line_before:
            return True

        return False

    def _is_character_continuation(self, character_name: str) -> bool:
        """Check if this character is continuing from a previous appearance.

        Determines if a character's dialogue is a continuation from an earlier scene
        within the same sequence. This is used to detect when a character returns
        to speaking after action lines, which may warrant a (CONT'D) extension in
        some screenplay formats.

        The method searches backwards for the most recent appearance of the same
        character, then checks if there has been intervening action without scene
        breaks. Scene headings reset the continuation context.

        Args:
            character_name: The character name to check for continuation

        Returns:
            bool: True if this character spoke earlier in the same scene with
                  intervening action, False otherwise

        Examples:
            >>> parser = FountainParser()
            >>> char1 = FountainElement(ElementType.CHARACTER, "JOHN", [], 1)
            >>> dialogue1 = FountainElement(ElementType.DIALOGUE, "Hello.", [], 2)
            >>> action = FountainElement(ElementType.ACTION, "John stands up.", [], 3)
            >>> parser.elements = [char1, dialogue1, action]
            >>> parser._is_character_continuation("JOHN")
            True

            >>> # With scene break - no continuation
            >>> scene = FountainElement(ElementType.SCENE_HEADING, "INT. KITCHEN - DAY", [], 4)
            >>> parser.elements = [char1, dialogue1, action, scene]
            >>> parser._is_character_continuation("JOHN")
            False

            >>> # Different character - no continuation
            >>> parser.elements = [char1, dialogue1, action]
            >>> parser._is_character_continuation("MARY")
            False

        Note:
            This method helps identify when screenwriting software might automatically
            add (CONT'D) extensions to character names, though fountain-py doesn't
            automatically add these extensions.
        """
        if not self.elements or len(self.elements) < 2:
            return False

        # Look backwards for the last character appearance
        last_character_idx = None
        for i in range(len(self.elements) - 1, -1, -1):
            if self.elements[i].type == ElementType.CHARACTER:
                last_character_idx = i
                break

        if last_character_idx is None:
            return False

        last_character = self.elements[last_character_idx]

        # Check if it's the same character
        if last_character.text.strip() != character_name.strip():
            return False

        # Check if there's been action between the last character appearance and now
        # AND no scene headings between them (which would indicate a scene break)
        has_action = False
        has_scene_break = False

        for i in range(last_character_idx + 1, len(self.elements)):
            element = self.elements[i]
            # If we find another character, stop looking
            if element.type == ElementType.CHARACTER:
                break
            # If we find a scene heading, it's a scene break
            elif element.type == ElementType.SCENE_HEADING:
                has_scene_break = True
            # If we find action (and it's not just dialogue/parentheticals), mark it
            elif element.type == ElementType.ACTION:
                has_action = True

        # Only return True if there's action AND no scene break
        return has_action and not has_scene_break

    @staticmethod
    def _strip_escapes(text: str) -> str:
        """Replace backslash escapes with their literal characters."""
        if "\\" not in text:
            return text
        return text.replace("\\*", "*").replace("\\_", "_").replace("\\\\", "\\")

    def _process_escapes(self, text: str) -> tuple[str, str]:
        """Process backslash escapes for emphasis markers.

        Returns:
            Tuple of (display_text, formatting_text) where:
            - display_text: text with escapes resolved to literal characters
            - formatting_text: text with escapes replaced by placeholders that won't trigger formatting
        """
        if "\\" not in text:
            return text, text

        display_text = text.replace("\\*", "*").replace("\\_", "_").replace("\\\\", "\\")
        formatting_text = text.replace("\\*", "\x00").replace("\\_", "\x01").replace("\\\\", "\x02")
        return display_text, formatting_text

    def _extract_formatting(self, text: str) -> list[FormatSpan]:
        """Extract formatting spans from text, handling backslash escapes.

        Parses Fountain's Markdown-like formatting markers to identify bold, italic,
        underline, and combined formatting within text. Handles precedence to avoid
        conflicts between overlapping patterns (e.g., ***text*** vs **text**).

        Backslash escapes (\\*, \\_) are replaced with placeholders before pattern
        matching so they don't trigger formatting. Returned span positions are
        adjusted to match the display text (with escapes resolved).

        Formatting precedence (highest to lowest):
        1. Bold-italic (***text***)
        2. Bold (**text**)
        3. Italic (*text*)
        4. Underline (_text_)

        Args:
            text: Text string to scan for formatting markers

        Returns:
            List of FormatSpan objects indicating start/end positions and format types

        Examples:
            >>> parser = FountainParser()
            >>> spans = parser._extract_formatting("This is **bold** and *italic* text")
            >>> len(spans)
            2
            >>> spans[0].format_type
            'bold'
            >>> spans[1].format_type
            'italic'

            >>> spans = parser._extract_formatting("***bold and italic***")
            >>> spans[0].format_type
            'bold_italic'

        Note:
            Overlapping spans are avoided by checking for existing coverage before
            adding new spans. Bold-italic spans prevent extraction of separate bold
            or italic spans within the same range.
        """
        # Process escapes: use placeholders for pattern matching
        _, formatting_text = self._process_escapes(text)

        formatting = []

        # Find bold-italic formatting first (***text***)
        for match in self.BOLD_ITALIC_PATTERN.finditer(formatting_text):
            formatting.append(FormatSpan(match.start(), match.end(), "bold_italic"))

        # Find bold formatting
        for match in self.BOLD_PATTERN.finditer(formatting_text):
            # Skip if already covered by bold-italic
            overlap = any(
                span.start <= match.start() < span.end or span.start < match.end() <= span.end
                for span in formatting
                if span.format_type == "bold_italic"
            )
            if not overlap:
                formatting.append(FormatSpan(match.start(), match.end(), "bold"))

        # Find italic formatting
        for match in self.ITALIC_PATTERN.finditer(formatting_text):
            # Skip if already covered by bold-italic
            overlap = any(
                span.start <= match.start() < span.end or span.start < match.end() <= span.end
                for span in formatting
                if span.format_type in ("bold_italic", "bold")
            )
            if not overlap:
                formatting.append(FormatSpan(match.start(), match.end(), "italic"))

        # Find underline formatting
        for match in self.UNDERLINE_PATTERN.finditer(formatting_text):
            formatting.append(FormatSpan(match.start(), match.end(), "underline"))

        # Adjust span positions if escapes were present
        if formatting_text != text:
            escape_positions = []
            i = 0
            while i < len(text):
                if text[i] == "\\" and i + 1 < len(text) and text[i + 1] in ("*", "_", "\\"):
                    escape_positions.append(i)
                    i += 2
                else:
                    i += 1

            adjusted = []
            for span in formatting:
                offset_start = sum(1 for ep in escape_positions if ep < span.start)
                offset_end = sum(1 for ep in escape_positions if ep < span.end)
                adjusted.append(FormatSpan(span.start - offset_start, span.end - offset_end, span.format_type))
            formatting = adjusted

        return formatting

    def _process_dual_dialogue(self) -> None:
        """Post-process elements to pair dual dialogue characters and their dialogue.

        Identifies characters marked with dual dialogue (^) and pairs them with the
        immediately preceding character and their respective dialogue blocks. Creates
        DUAL_DIALOGUE elements that contain both character/dialogue pairs for
        side-by-side rendering.

        The algorithm:
        1. Finds characters marked with dual_dialogue metadata (ending with ^)
        2. Locates the most recent previous character (must be adjacent)
        3. Collects dialogue and parentheticals for both characters
        4. Creates a single DUAL_DIALOGUE element containing both character blocks
        5. Replaces the original elements with the dual dialogue element

        Examples:
            Before processing:
            - CHARACTER: "JOHN"
            - DIALOGUE: "Hello there."
            - CHARACTER: "MARY" (metadata: dual_dialogue=True)
            - DIALOGUE: "Hi back!"

            After processing:
            - DUAL_DIALOGUE: metadata contains left_character, left_dialogue,
              right_character, right_dialogue for simultaneous rendering

        Note:
            Only processes characters that are immediately adjacent (no scene headings
            or action lines between them). Characters separated by structural elements
            are not paired as dual dialogue.
        """
        i = 0
        while i < len(self.elements):
            element = self.elements[i]

            # Look for characters marked as dual dialogue
            if element.type == ElementType.CHARACTER and element.metadata and element.metadata.get("dual_dialogue"):
                # Find the previous character and its dialogue block
                prev_char_idx = None
                for j in range(i - 1, -1, -1):
                    if self.elements[j].type == ElementType.CHARACTER:
                        # Check if this character is immediately adjacent (no other characters in between)
                        if prev_char_idx is None:
                            prev_char_idx = j
                        break
                    elif self.elements[j].type in (
                        ElementType.SCENE_HEADING,
                        ElementType.ACTION,
                    ):
                        # Too far back, no valid pairing
                        break

                if prev_char_idx is not None:
                    # Collect dialogue for both characters
                    prev_dialogue = []
                    curr_dialogue = []

                    # Get previous character's dialogue
                    k = prev_char_idx + 1
                    while k < i and self.elements[k].type in (
                        ElementType.DIALOGUE,
                        ElementType.PARENTHETICAL,
                    ):
                        prev_dialogue.append(self.elements[k])
                        k += 1

                    # Get current character's dialogue
                    k = i + 1
                    while k < len(self.elements) and self.elements[k].type in (
                        ElementType.DIALOGUE,
                        ElementType.PARENTHETICAL,
                    ):
                        curr_dialogue.append(self.elements[k])
                        k += 1

                    # Create dual dialogue element
                    if prev_dialogue and curr_dialogue:
                        dual_element = FountainElement(
                            type=ElementType.DUAL_DIALOGUE,
                            text="",  # Dual dialogue doesn't have direct text
                            formatting=[],
                            line_number=element.line_number,
                            metadata={
                                "left_character": self.elements[prev_char_idx],
                                "left_dialogue": prev_dialogue,
                                "right_character": element,
                                "right_dialogue": curr_dialogue,
                            },
                        )

                        # Replace the range with the dual dialogue element
                        start_idx = prev_char_idx
                        end_idx = i + len(curr_dialogue) + 1
                        self.elements[start_idx:end_idx] = [dual_element]

                        # Adjust index
                        i = start_idx + 1
                        continue

            i += 1
