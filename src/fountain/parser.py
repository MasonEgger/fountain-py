"""ABOUTME: Fountain markup parser for converting Fountain screenwriting format to structured elements.
ABOUTME: Implements a two-pass parsing strategy with comprehensive regex-based element classification.

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
from typing import Any, Optional

from fountain.document import FountainDocument
from fountain.elements import ElementType, FormatSpan, FountainElement


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
    # Matches standard scene heading prefixes: INT., EXT., EST., I/E., INTERIOR., EXTERIOR., INT/EXT., INT./EXT.
    # Case-insensitive matching allows for "int." or "Int." variations
    # Examples: "INT. COFFEE SHOP - DAY", "EXT. PARK - NIGHT", "I/E. CAR - CONTINUOUS"
    SCENE_HEADING_PATTERN = re.compile(
        r"^(INT\s*\.|EXT\s*\.|EST\s*\.|I/E\s*\.|INTERIOR\s*\.|EXTERIOR\s*\.|INT/EXT\s*\.|INT\./EXT\s*\.)",
        re.IGNORECASE,
    )

    # Matches scene numbers in format #SCENE_NUMBER# at end of scene headings
    # Captures the scene number content between the hash marks
    # Example: "INT. HOUSE - DAY #1A#" captures "1A"
    SCENE_NUMBER_PATTERN = re.compile(r"\s*#([^#]+)#\s*$")

    # Forced scene heading starts with period (.) to override natural scene detection
    # Used when a line should be a scene heading but doesn't match standard prefixes
    # Example: ".FLASHBACK - 10 YEARS AGO" becomes "FLASHBACK - 10 YEARS AGO"
    FORCED_SCENE_HEADING_PATTERN = re.compile(r"^\.")
    # Character Name Patterns
    # Standard character names: ALL CAPS, may include numbers, spaces, underscores
    # Must start with letter, prevents false positives from action lines
    # Examples: "JOHN", "MARY JANE", "ROBOT_1", "DR SMITH"
    CHARACTER_PATTERN = re.compile(r"^[A-Z][A-Z0-9\s_]*$")

    # Dual dialogue character: standard character name followed by caret (^)
    # Indicates this character speaks simultaneously with previous character
    # Example: "MARY^" for dual dialogue with preceding character
    DUAL_CHARACTER_PATTERN = re.compile(r"^[A-Z][A-Z0-9\s_]*\^\s*$")

    # Forced character name: prefixed with @ to override natural character detection
    # Captures the character name after the @ symbol
    # Example: "@john" forces "john" to be treated as character (even lowercase)
    FORCED_CHARACTER_PATTERN = re.compile(r"^@(.+)$")

    # Character with extensions: CHARACTER_NAME (extension) with optional dual dialogue caret
    # Captures character name, extension (V.O., O.S., CONT'D, etc.), and dual dialogue marker
    # Examples: "JOHN (V.O.)", "MARY (O.S.)^", "NARRATOR (CONT'D)"
    CHARACTER_EXTENSION_PATTERN = re.compile(
        r"^([A-Z][A-Z0-9\s_]*)\s*\(([^)]+)\)\s*(\^)?\s*$"
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
    NOTE_PATTERN = re.compile(r"\[\[[^\]]*\]\]")

    # Boneyard (Comment) Patterns
    # Single-line boneyard: /* comment */ on one line (DOTALL allows newlines in content)
    # Used for comments that should not appear in final output
    BONEYARD_PATTERN = re.compile(r"^/\*.*?\*/$", re.DOTALL)

    # Multi-line boneyard start: line beginning with /*
    # Starts a comment block that continues until */
    MULTILINE_BONEYARD_START = re.compile(r"^/\*")

    # Multi-line boneyard end: line ending with */
    # Ends a comment block started with /*
    MULTILINE_BONEYARD_END = re.compile(r"\*/$")
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

        # First pass: extract title page
        metadata = self._parse_title_page()

        # Second pass: parse body elements
        previous_line_was_blank = False
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].rstrip()

            if not line:  # Empty line
                previous_line_was_blank = True
                self.current_line += 1
                continue

            element = self._parse_line(line, previous_line_was_blank)
            if element:
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
            producer, director. Additional fields are ignored as potential script body.
        """
        metadata = {}
        current_key = None

        # Expanded list of supported title page fields
        supported_fields = {
            "title",
            "author",
            "credit",
            "source",
            "draft date",
            "contact",
            "authors",
            "notes",
            "copyright",
            "date",
            "revised",
            "version",
            "format",
            "created",
            "writers",
            "producer",
            "director",
        }

        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()

            if not line:
                # Empty line might end title page or continue multi-line value
                if current_key is None:
                    self.current_line += 1
                    continue
                else:
                    # Check if next non-empty line is title page or body
                    next_line_idx = self.current_line + 1
                    while (
                        next_line_idx < len(self.lines)
                        and not self.lines[next_line_idx].strip()
                    ):
                        next_line_idx += 1

                    if next_line_idx < len(self.lines):
                        next_line = self.lines[next_line_idx].strip()
                        # If next line starts with scene heading, end title page
                        if (
                            next_line.startswith(("INT.", "EXT.", "EST.", "I/E."))
                            or next_line.startswith(".")  # forced scene heading
                            or (":" not in next_line and current_key)
                        ):  # likely script body
                            break

                    # Continue with current key (multi-line value)
                    self.current_line += 1
                    continue

            # Check for title page key-value pairs
            if ":" in line and not line.startswith(("INT.", "EXT.", "EST.", "I/E.")):
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key in supported_fields:
                    if current_key and current_key in metadata:
                        # Finalize previous multi-line value
                        metadata[current_key] = metadata[current_key].strip()

                    current_key = key
                    metadata[key] = value
                    self.current_line += 1
                    continue
                else:
                    # Unknown field, might be end of title page
                    break

            # Check if this is a continuation of multi-line value
            elif current_key and not line.startswith(
                ("INT.", "EXT.", "EST.", "I/E.", ".")
            ):
                # This is a continuation line for the current key
                if metadata[current_key]:
                    metadata[current_key] += " " + line
                else:
                    metadata[current_key] = line
                self.current_line += 1
                continue

            # If we hit a non-title-page line, stop parsing title page
            break

        # Clean up any trailing multi-line value
        if current_key and current_key in metadata:
            metadata[current_key] = metadata[current_key].strip()

        return metadata

    def _parse_line(
        self, line: str, had_blank_line_before: bool = False
    ) -> Optional[FountainElement]:
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
            if self.MULTILINE_BONEYARD_END.search(line):
                self.in_boneyard = False
            return None  # Skip all lines inside boneyard

        # Check for single-line boneyard (block comments) - handle before multiline start
        if self.BONEYARD_PATTERN.match(line):
            return FountainElement(
                type=ElementType.BONEYARD,
                text=line,
                formatting=[],
                line_number=self.current_line + 1,
            )

        if self.MULTILINE_BONEYARD_START.match(line):
            if not self.MULTILINE_BONEYARD_END.search(line):
                self.in_boneyard = True
            return None  # Skip boneyard start line

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
        if (
            note_matches
            and line.strip().startswith("[[")
            and line.strip().endswith("]]")
        ):
            # Line is entirely a note
            return FountainElement(
                type=ElementType.NOTE,
                text=line,
                formatting=[],
                line_number=self.current_line + 1,
            )

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
            text = self.SECTION_PATTERN.sub("", line).strip()
            return FountainElement(
                type=ElementType.SECTION,
                text=text,
                formatting=self._extract_formatting(text),
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
            metadata: dict[str, Any] = {"forced": True}
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

        # Check for scene heading
        if self.SCENE_HEADING_PATTERN.match(line):
            scene_metadata: dict[str, Any] = {}
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

        # Check for transition
        if self.TRANSITION_PATTERN.match(line):
            return FountainElement(
                type=ElementType.TRANSITION,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1,
            )

        # Check for forced character (@character)
        if self.FORCED_CHARACTER_PATTERN.match(line):
            character_name = self.FORCED_CHARACTER_PATTERN.sub(r"\1", line).strip()
            if self._is_dialogue_following():
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata={"forced": True},
                )

        # Check for dual dialogue character (CHARACTER^)
        if self.DUAL_CHARACTER_PATTERN.match(line):
            character_name = line.replace("^", "").strip()
            if self._is_dialogue_following():
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata={"dual_dialogue": True},
                )

        # Check for character with extensions (CHARACTER (V.O.))
        char_ext_match = self.CHARACTER_EXTENSION_PATTERN.match(line)
        if char_ext_match:
            character_name = char_ext_match.group(1).strip()
            extension = char_ext_match.group(2).strip()
            is_dual = char_ext_match.group(3) is not None
            if self._is_dialogue_following():
                char_metadata: dict[str, Any] = {"extension": extension}
                if is_dual:
                    char_metadata["dual_dialogue"] = True
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata=char_metadata,
                )

        # Check for regular character (must be all caps)
        if self.CHARACTER_PATTERN.match(line):
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
            text=original_line.rstrip(),  # Preserve leading tabs/spaces
            formatting=self._extract_formatting(line),
            line_number=self.current_line + 1,
        )

    def _is_dialogue_following(self) -> bool:
        """Check if the next non-empty line is dialogue.

        Lookahead method that examines subsequent lines to determine if the current line
        should be classified as a character name. This prevents false positive character
        detection when ALL CAPS text appears in action lines.

        The method skips empty lines and checks if the next non-empty line matches any
        structural element patterns. If no structural patterns match, the line is
        considered potential dialogue, confirming the current line as a character.

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
        next_line_idx = self.current_line + 1
        while next_line_idx < len(self.lines):
            next_line = self.lines[next_line_idx].strip()
            if next_line:
                # It's dialogue if it's not another structural element
                return not (
                    self.SCENE_HEADING_PATTERN.match(next_line)
                    or self.FORCED_SCENE_HEADING_PATTERN.match(next_line)
                    or self.TRANSITION_PATTERN.match(next_line)
                    or self.FORCED_TRANSITION_PATTERN.match(next_line)
                    or self.CHARACTER_PATTERN.match(next_line)
                    or self.DUAL_CHARACTER_PATTERN.match(next_line)
                    or self.FORCED_CHARACTER_PATTERN.match(next_line)
                    or self.CHARACTER_EXTENSION_PATTERN.match(next_line)
                    or self.SECTION_PATTERN.match(next_line)
                    or self.SYNOPSIS_PATTERN.match(next_line)
                    or self.PAGE_BREAK_PATTERN.match(next_line)
                    or self.CENTERED_PATTERN.match(next_line)
                    or self.FORCED_ACTION_PATTERN.match(next_line)
                    or (next_line.startswith("[[") and next_line.endswith("]]"))
                )
            next_line_idx += 1
        return False

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

        # Always dialogue after CHARACTER or PARENTHETICAL
        if prev_element.type in (ElementType.CHARACTER, ElementType.PARENTHETICAL):
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

    def _extract_formatting(self, text: str) -> list[FormatSpan]:
        """Extract formatting spans from text using Fountain's inline formatting syntax.

        Parses Fountain's Markdown-like formatting markers to identify bold, italic,
        underline, and combined formatting within text. Handles precedence to avoid
        conflicts between overlapping patterns (e.g., ***text*** vs **text**).

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
        formatting = []

        # Find bold-italic formatting first (***text***)
        for match in self.BOLD_ITALIC_PATTERN.finditer(text):
            formatting.append(FormatSpan(match.start(), match.end(), "bold_italic"))

        # Find bold formatting
        for match in self.BOLD_PATTERN.finditer(text):
            # Skip if already covered by bold-italic
            overlap = any(
                span.start <= match.start() < span.end
                or span.start < match.end() <= span.end
                for span in formatting
                if span.format_type == "bold_italic"
            )
            if not overlap:
                formatting.append(FormatSpan(match.start(), match.end(), "bold"))

        # Find italic formatting
        for match in self.ITALIC_PATTERN.finditer(text):
            # Skip if already covered by bold-italic
            overlap = any(
                span.start <= match.start() < span.end
                or span.start < match.end() <= span.end
                for span in formatting
                if span.format_type in ("bold_italic", "bold")
            )
            if not overlap:
                formatting.append(FormatSpan(match.start(), match.end(), "italic"))

        # Find underline formatting
        for match in self.UNDERLINE_PATTERN.finditer(text):
            formatting.append(FormatSpan(match.start(), match.end(), "underline"))

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
            if (
                element.type == ElementType.CHARACTER
                and element.metadata
                and element.metadata.get("dual_dialogue")
            ):
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
