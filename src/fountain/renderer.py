# ABOUTME: HTML and Fountain-format renderers for parsed screenplay documents.
# Converts FountainDocument/FountainElement trees into formatted HTML or round-trip Fountain markup.
"""
Renderers for Fountain documents.

This module provides renderers for converting parsed Fountain documents into various
output formats. The primary renderers are HTMLRenderer for web display and
FountainRenderer for round-trip conversion back to Fountain markup.

Classes:
    HTMLRenderer: Converts Fountain documents to HTML with screenplay formatting.
    FountainRenderer: Converts Fountain documents back to Fountain markup format.

Example:
    Basic rendering of a Fountain document to HTML:

    >>> from fountain.parser import FountainParser
    >>> from fountain.renderer import HTMLRenderer
    >>> parser = FountainParser()
    >>> doc = parser.parse("INT. HOUSE - DAY\\n\\nAction here.")
    >>> renderer = HTMLRenderer()
    >>> html = renderer.render(doc)
    >>> '<div class="fountain-scene-heading">INT. HOUSE - DAY</div>' in html
    True
"""

import html as html_module
from typing import cast

from fountain.document import FountainDocument
from fountain.elements import ElementType, FormatSpan, FountainElement

DEFAULT_CSS = """\
.fountain-script {
    font-family: 'Courier New', 'Courier', monospace;
    font-size: 12pt;
    line-height: 1.2;
    max-width: 70%;
    margin: 0 auto;
    padding: 1in;
    background: white;
    color: black;
}

.fountain-title-page {
    text-align: center;
    margin-bottom: 3in;
}

.fountain-title-page .fountain-title {
    font-size: 24pt;
    font-weight: bold;
    margin-bottom: 1in;
    text-transform: uppercase;
}

.fountain-title-page .fountain-author {
    font-size: 14pt;
    margin-bottom: 0.5in;
}

.fountain-title-page .fountain-credit,
.fountain-title-page .fountain-source,
.fountain-title-page .fountain-draft-date,
.fountain-title-page .fountain-contact,
.fountain-title-page .fountain-writers,
.fountain-title-page .fountain-producer,
.fountain-title-page .fountain-director,
.fountain-title-page .fountain-date,
.fountain-title-page .fountain-revised,
.fountain-title-page .fountain-version,
.fountain-title-page .fountain-format,
.fountain-title-page .fountain-created,
.fountain-title-page .fountain-copyright,
.fountain-title-page .fountain-notes {
    font-size: 12pt;
    margin-bottom: 0.25in;
}

.fountain-title-page .fountain-notes,
.fountain-title-page .fountain-contact {
    white-space: pre-line;
}

.fountain-script-body {
    page-break-before: always;
}

.fountain-scene-heading {
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 2em;
    margin-bottom: 1em;
}

.fountain-action {
    margin-bottom: 1em;
    text-align: left;
}

.fountain-character {
    text-align: center;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 1em;
    margin-bottom: 0;
}

.fountain-dialogue {
    text-align: center;
    margin: 0 auto 1em auto;
}

.fountain-parenthetical {
    text-align: center;
    font-style: italic;
    margin: 0 auto;
}

.fountain-transition {
    text-align: right;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 1em;
    margin-bottom: 1em;
}

.fountain-scene-number {
    font-weight: normal;
    color: #888;
    font-size: 10pt;
}

.fountain-character-extension,
.fountain-character-continuation {
    font-weight: normal;
    font-size: 10pt;
}

.fountain-dual-dialogue {
    display: flex;
    margin: 1em 0;
}

.fountain-dual-dialogue-left,
.fountain-dual-dialogue-right {
    flex: 1;
    padding: 0 1em;
}

.fountain-dual-dialogue-left {
    border-right: 1px solid #ddd;
}

.fountain-page-break {
    page-break-before: always;
    border-top: 2px solid #ccc;
    margin: 2em 0;
    height: 0;
}

.fountain-centered {
    text-align: center;
    margin: 1em 0;
}

.fountain-lyrics {
    text-align: center;
    font-style: italic;
    margin: 0.5em auto;
    color: #444;
}"""


# Each entry: (metadata_key, css_class, html_tag, prefix, multiline)
TITLE_PAGE_FIELD_ORDER: list[tuple[str, str, str, str, bool]] = [
    ("title", "fountain-title", "h1", "", False),
    ("author", "fountain-author", "p", "by ", False),
    ("authors", "fountain-author", "p", "by ", False),
    ("credit", "fountain-credit", "p", "", False),
    ("source", "fountain-source", "p", "", False),
    ("writers", "fountain-writers", "p", "Writers: ", False),
    ("producer", "fountain-producer", "p", "Producer: ", False),
    ("director", "fountain-director", "p", "Director: ", False),
    ("draft date", "fountain-draft-date", "p", "", False),
    ("date", "fountain-date", "p", "", False),
    ("revised", "fountain-revised", "p", "Revised: ", False),
    ("version", "fountain-version", "p", "Version: ", False),
    ("format", "fountain-format", "p", "Format: ", False),
    ("created", "fountain-created", "p", "Created: ", False),
    ("contact", "fountain-contact", "p", "", True),
    ("copyright", "fountain-copyright", "p", "", False),
    ("notes", "fountain-notes", "p", "", True),
]

# Set of known field keys for quick lookup
_KNOWN_TITLE_FIELDS = {field[0] for field in TITLE_PAGE_FIELD_ORDER}


class HTMLRenderer:
    """Renders Fountain documents as HTML with screenplay formatting.

    The HTMLRenderer converts parsed Fountain documents into HTML with proper
    screenplay formatting, including CSS styles that follow industry-standard
    screenplay layout conventions. It handles all Fountain element types and
    preserves formatting marks like bold, italic, and underline.

    The renderer provides three output modes:

    - ``render(doc)`` — Pure HTML fragment for embedding (no CSS)
    - ``render_page(doc)`` — Standalone HTML with embedded CSS
    - ``get_css()`` — Raw CSS string for external stylesheet use

    CSS Classes Generated:
        - fountain-script: Main container for the entire screenplay
        - fountain-title-page: Container for title page metadata
        - fountain-script-body: Container for the main screenplay content
        - fountain-scene-heading: Scene headers (INT/EXT)
        - fountain-action: Action/description paragraphs
        - fountain-character: Character names before dialogue
        - fountain-dialogue: Spoken dialogue text
        - fountain-parenthetical: Stage directions within dialogue
        - fountain-transition: Scene transitions (CUT TO:, etc.)
        - fountain-dual-dialogue: Container for simultaneous dialogue
        - fountain-page-break: Page break markers
        - fountain-centered: Centered text
        - fountain-lyrics: Song lyrics with special formatting

    Notes, sections, synopses, and boneyard are writer tools. They are hidden
    from the formatted output by default and emit no markup, so no CSS classes
    are generated for them.

    Example:
        Render a simple screenplay to HTML:

        >>> from fountain.parser import FountainParser
        >>> from fountain.renderer import HTMLRenderer
        >>> parser = FountainParser()
        >>> doc = parser.parse('''Title: My Screenplay
        ... Author: Jane Doe
        ...
        ... INT. COFFEE SHOP - DAY
        ...
        ... JOHN enters, looking tired.
        ...
        ... JOHN
        ... I need coffee.
        ... ''')
        >>> renderer = HTMLRenderer()
        >>> html = renderer.render(doc)
        >>> '<h1 class="fountain-title">My Screenplay</h1>' in html
        True
        >>> '<div class="fountain-character">JOHN</div>' in html
        True
    """

    def render(self, document: FountainDocument) -> str:
        """Render a FountainDocument as an HTML fragment.

        Returns a pure HTML fragment suitable for embedding in web pages,
        documentation systems, or any context where CSS is managed externally.
        Use ``render_page()`` for standalone HTML with embedded CSS.

        Args:
            document: The FountainDocument to render, containing parsed elements
                and optional title page metadata.

        Returns:
            An HTML fragment string containing the screenplay markup wrapped in a
            ``<div class="fountain-script">`` container. Does not include
            ``<style>`` tags or CSS.

        Example:
            >>> from fountain.parser import FountainParser
            >>> parser = FountainParser()
            >>> doc = parser.parse("INT. ROOM - DAY\\n\\nAction here.")
            >>> renderer = HTMLRenderer()
            >>> html = renderer.render(doc)
            >>> '<div class="fountain-script">' in html
            True
            >>> '<style>' not in html
            True
        """
        html_parts = []

        # Add document wrapper
        html_parts.append('<div class="fountain-script">')

        # Add title page if metadata exists
        if document.metadata:
            html_parts.append(self._render_title_page(document.metadata))

        # Add script body
        html_parts.append('<div class="fountain-script-body">')

        for element in document.elements:
            html_parts.append(self._render_element(element))

        html_parts.append("</div>")  # script-body
        html_parts.append("</div>")  # fountain-script

        return "\n".join(html_parts)

    def render_page(self, document: FountainDocument) -> str:
        """Render a FountainDocument as a standalone HTML page with embedded CSS.

        Returns a complete HTML string with a ``<style>`` block and the screenplay
        fragment. Suitable for saving as a self-contained HTML file.

        Args:
            document: The FountainDocument to render.

        Returns:
            A complete HTML string with embedded CSS styling followed by the
            screenplay markup.

        Example:
            >>> from fountain.parser import FountainParser
            >>> parser = FountainParser()
            >>> doc = parser.parse("INT. ROOM - DAY\\n\\nAction here.")
            >>> renderer = HTMLRenderer()
            >>> html = renderer.render_page(doc)
            >>> '<style>' in html
            True
            >>> '<div class="fountain-script">' in html
            True
        """
        css_block = f"<style>\n{DEFAULT_CSS}\n</style>"
        fragment = self.render(document)
        return f"{css_block}\n{fragment}"

    def get_css(self) -> str:
        """Return the raw CSS string for screenplay formatting.

        Returns the CSS rules without ``<style>`` tags, so consumers can inject
        the styles however they need (e.g., into an external stylesheet, a
        ``<link>`` tag, or a build system's CSS pipeline).

        Returns:
            A string containing CSS rules for all Fountain element types.

        Example:
            >>> renderer = HTMLRenderer()
            >>> css = renderer.get_css()
            >>> '.fountain-script' in css
            True
            >>> '<style>' not in css
            True
        """
        return DEFAULT_CSS

    def _render_title_page(self, metadata: dict[str, str]) -> str:
        """Render the title page metadata as HTML.

        Converts title page metadata fields into formatted HTML elements.
        Handles all standard Fountain title page fields including title,
        author(s), credit, source, contact information, and dates.

        Args:
            metadata: Dictionary of title page fields and their values.
                Common fields include: title, author/authors, credit, source,
                draft date, contact, copyright, notes, etc.

        Returns:
            HTML string representing the formatted title page with appropriate
            CSS classes for each metadata field.

        Note:
            Multi-line fields like 'contact' and 'notes' are preserved with
            line breaks converted to HTML <br> tags.
        """
        html_parts = ['<div class="fountain-title-page">']

        # Render known fields in defined order
        rendered_keys: set[str] = set()
        for key, css_class, tag, prefix, multiline in TITLE_PAGE_FIELD_ORDER:
            if key not in metadata:
                continue
            # Skip 'authors' if 'author' was already rendered (they share a slot)
            if key == "authors" and "author" in metadata:
                continue
            rendered_keys.add(key)
            value_html = self._escape_html(metadata[key])
            if multiline:
                value_html = value_html.replace("\n", "<br>")
            html_parts.append(f'<{tag} class="{css_class}">{prefix}{value_html}</{tag}>')

        # Render any custom/unknown metadata fields after known fields
        for key, value in metadata.items():
            if key in _KNOWN_TITLE_FIELDS:
                continue
            css_class = key.replace(" ", "-")
            field_label = key.replace("_", " ").title()
            value_html = self._escape_html(value).replace("\n", "<br>")
            html_parts.append(f'<p class="fountain-custom-field {css_class}">{field_label}: {value_html}</p>')

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _render_element(self, element: FountainElement) -> str:
        """Render a single FountainElement as HTML.

        Converts a parsed Fountain element into its HTML representation with
        appropriate CSS classes and formatting. Handles all element types
        including scenes, dialogue, action, transitions, and special elements
        like dual dialogue and page breaks.

        Args:
            element: The FountainElement to render, containing type, text,
                formatting spans, and optional metadata.

        Returns:
            HTML string for the element with appropriate CSS classes and
            structure. Includes any inline formatting (bold, italic, underline)
            and element-specific features like scene numbers or character extensions.

        Example:
            >>> from fountain.elements import FountainElement, ElementType
            >>> element = FountainElement(
            ...     type=ElementType.CHARACTER,
            ...     text="SARAH",
            ...     formatting=[],
            ...     line_number=1,
            ...     metadata={"extension": "V.O."}
            ... )
            >>> renderer = HTMLRenderer()
            >>> html = renderer._render_element(element)
            >>> expected = '<div class="fountain-character">SARAH '
            >>> expected += '<span class="fountain-character-extension">(V.O.)</span></div>'
            >>> expected == html
            True
        """
        css_class = element.type.value.replace("_", "-")
        text = self._apply_formatting(element.text, element.formatting)

        if element.type == ElementType.SCENE_HEADING:
            scene_html = f'<div class="fountain-scene-heading">{text}'
            if element.metadata and "scene_number" in element.metadata:
                scene_html += f' <span class="fountain-scene-number">#{element.metadata["scene_number"]}#</span>'
            scene_html += "</div>"
            return scene_html
        elif element.type == ElementType.ACTION:
            # Convert tabs to spaces and preserve leading whitespace
            text_with_spacing = text.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
            text_with_br = text_with_spacing.replace("\n", "<br>")
            return f'<div class="fountain-action">{text_with_br}</div>'
        elif element.type == ElementType.CHARACTER:
            char_html = f'<div class="fountain-character">{text}'
            if element.metadata and "extension" in element.metadata:
                char_html += f' <span class="fountain-character-extension">({element.metadata["extension"]})</span>'
            elif element.metadata and element.metadata.get("continuation"):
                char_html += ' <span class="fountain-character-continuation">(CONT\'D)</span>'
            char_html += "</div>"
            return char_html
        elif element.type == ElementType.DIALOGUE:
            return f'<div class="fountain-dialogue">{text}</div>'
        elif element.type == ElementType.PARENTHETICAL:
            return f'<div class="fountain-parenthetical">{text}</div>'
        elif element.type == ElementType.TRANSITION:
            return f'<div class="fountain-transition">{text}</div>'
        elif element.type == ElementType.NOTE:
            # Notes are a writer-only tool omitted from formatted output entirely,
            # so they never ship in either the fragment or the standalone page (E5).
            return ""
        elif element.type == ElementType.BONEYARD:
            # Boneyard is a writer-only tool; its content is omitted from formatted
            # output entirely so it never ships in the CSS-free HTML fragment (E11).
            # This keeps single-line boneyards consistent with multi-line ones, whose
            # interior lines the parser already drops.
            return ""
        elif element.type == ElementType.SECTION:
            # Sections are a writer-only structural tool omitted from formatted output (E5).
            return ""
        elif element.type == ElementType.SYNOPSIS:
            # Synopses are a writer-only tool omitted from formatted output (E5).
            return ""
        elif element.type == ElementType.DUAL_DIALOGUE:
            return self._render_dual_dialogue(element)
        elif element.type == ElementType.PAGE_BREAK:
            return '<div class="fountain-page-break"></div>'
        elif element.type == ElementType.CENTERED:
            return f'<div class="fountain-centered">{text}</div>'
        elif element.type == ElementType.LYRICS:
            return f'<div class="fountain-lyrics">{text}</div>'
        else:
            return f'<div class="fountain-{css_class}">{text}</div>'

    def _apply_formatting(self, text: str, formatting: list[FormatSpan]) -> str:
        """Apply formatting spans to text and escape HTML.

        Processes formatting spans (bold, italic, underline) and converts them
        to HTML tags while properly escaping the text content. Handles overlapping
        formatting spans correctly by processing them in reverse order.

        Args:
            text: The raw text content to format.
            formatting: List of FormatSpan objects indicating which parts of the
                text should have formatting applied (bold, italic, underline, or
                bold_italic combination).

        Returns:
            HTML-escaped text with formatting tags applied. Special characters
            are escaped to prevent XSS vulnerabilities.

        Example:
            >>> from fountain.elements import FormatSpan
            >>> renderer = HTMLRenderer()
            >>> text = "This is bold text"
            >>> formatting = [FormatSpan(start=8, end=12, format_type="bold")]
            >>> result = renderer._apply_formatting(text, formatting)
            >>> result == 'This is <strong>bold</strong> text'
            True
        """
        if not formatting:
            return self._escape_html(text)

        # Sort formatting spans by start position (reversed for easier processing)
        sorted_formatting = sorted(formatting, key=lambda x: x.start, reverse=True)

        # Build list of text segments with their formatting
        segments: list[tuple[str, str | None]] = []
        last_end = len(text)

        for span in sorted_formatting:
            # Add text after this span (if any)
            if last_end > span.end:
                segments.append((text[span.end : last_end], None))

            # Add the formatted span
            segments.append((text[span.start : span.end], span.format_type))
            last_end = span.start

        # Add any remaining text at the beginning
        if last_end > 0:
            segments.append((text[:last_end], None))

        # Reverse to get correct order
        segments.reverse()

        # Build final HTML
        result_parts = []
        for segment_text, format_type in segments:
            escaped_text = self._escape_html(segment_text)

            if format_type == "bold":
                result_parts.append(f"<strong>{escaped_text}</strong>")
            elif format_type == "italic":
                result_parts.append(f"<em>{escaped_text}</em>")
            elif format_type == "underline":
                result_parts.append(f"<u>{escaped_text}</u>")
            elif format_type == "bold_italic":
                result_parts.append(f"<strong><em>{escaped_text}</em></strong>")
            else:
                result_parts.append(escaped_text)

        return "".join(result_parts)

    def _render_dual_dialogue(self, element: FountainElement) -> str:
        """Render dual dialogue as side-by-side columns.

        Creates a two-column layout for simultaneous dialogue, with each
        character and their dialogue displayed side by side. This is used
        in screenplays when two characters speak at the same time.

        Args:
            element: A FountainElement of type DUAL_DIALOGUE containing
                metadata with left and right character/dialogue information.

        Returns:
            HTML string with dual-dialogue structure using CSS flexbox for
            side-by-side display. Returns empty string if metadata is missing.

        Note:
            The metadata should contain:
            - left_character: FountainElement for left character
            - left_dialogue: List of dialogue elements for left side
            - right_character: FountainElement for right character
            - right_dialogue: List of dialogue elements for right side
        """
        metadata = element.metadata
        if not metadata:
            return ""

        left_char = cast(FountainElement, metadata["left_character"])
        left_dialogue = cast("list[FountainElement]", metadata["left_dialogue"])
        right_char = cast(FountainElement, metadata["right_character"])
        right_dialogue = cast("list[FountainElement]", metadata["right_dialogue"])

        html_parts = ['<div class="fountain-dual-dialogue">']

        # Left column
        html_parts.append('<div class="fountain-dual-dialogue-left">')
        html_parts.append(self._render_element(left_char))
        for dialogue_element in left_dialogue:
            html_parts.append(self._render_element(dialogue_element))
        html_parts.append("</div>")

        # Right column
        html_parts.append('<div class="fountain-dual-dialogue-right">')
        html_parts.append(self._render_element(right_char))
        for dialogue_element in right_dialogue:
            html_parts.append(self._render_element(dialogue_element))
        html_parts.append("</div>")

        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text for safe display.

        Prevents XSS attacks and ensures special characters display correctly
        by converting HTML entities to their escaped equivalents.

        Args:
            text: Raw text that may contain HTML special characters.

        Returns:
            Text with HTML special characters escaped:
            - & becomes &amp;
            - < becomes &lt;
            - > becomes &gt;
            - " becomes &quot;
            - ' becomes &#x27;

        Example:
            >>> renderer = HTMLRenderer()
            >>> renderer._escape_html("<script>alert('XSS')</script>")
            '&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;'
        """
        return html_module.escape(text, quote=True)


class FountainRenderer:
    """Renders FountainDocument back to Fountain markup format.

    The FountainRenderer provides round-trip conversion from parsed Fountain
    documents back to Fountain markup text. This is useful for programmatic
    manipulation of screenplays, formatting cleanup, or conversion workflows.

    Round-Trip Capabilities:
        - Preserves all Fountain element types and structure
        - Maintains title page metadata fields
        - Handles forced elements (scenes, action, transitions)
        - Preserves scene numbers and character extensions
        - Supports special elements (notes, sections, synopses)

    Round-Trip Limitations:
        - Exact whitespace formatting may differ from original
        - Original formatting markup positions are not preserved
        - Comments in boneyard sections are maintained but may be reformatted
        - Line breaks within elements are preserved but spacing may normalize
        - Original capitalization in scene headings is preserved

    The renderer attempts to produce valid Fountain markup that will parse
    back to an equivalent document structure, though the exact text representation
    may differ from the original due to normalization during parsing.

    Example:
        Basic round-trip conversion:

        >>> from fountain.parser import FountainParser
        >>> from fountain.renderer import FountainRenderer
        >>> parser = FountainParser()
        >>> original = "INT. HOUSE - DAY\\n\\nJohn enters.\\n\\nJOHN\\nHello!"
        >>> doc = parser.parse(original)
        >>> renderer = FountainRenderer()
        >>> fountain_text = renderer.render(doc)
        >>> # Re-parse to verify round-trip
        >>> doc2 = parser.parse(fountain_text)
        >>> len(doc.elements) == len(doc2.elements)
        True
    """

    def render(self, document: FountainDocument) -> str:
        """Render a FountainDocument as Fountain markup.

        Converts a parsed Fountain document back into Fountain markup text format.
        This enables round-trip conversion and programmatic screenplay manipulation.

        Args:
            document: The FountainDocument to render, containing parsed elements
                and optional title page metadata.

        Returns:
            A string containing valid Fountain markup that represents the document.
            The output can be saved as a .fountain file or parsed again.

        Example:
            >>> from fountain.parser import FountainParser
            >>> parser = FountainParser()
            >>> doc = parser.parse("Title: My Script\\n\\nFADE IN:")
            >>> renderer = FountainRenderer()
            >>> fountain = renderer.render(doc)
            >>> fountain.startswith("Title: My Script")
            True
            >>> "FADE IN:" in fountain
            True
        """
        fountain_parts = []

        # Render title page metadata if exists
        if document.metadata:
            fountain_parts.append(self._render_title_page(document.metadata))

        # Render script body elements
        for element in document.elements:
            rendered = self._render_element(element)
            if rendered:
                fountain_parts.append(rendered)

        return "\n".join(fountain_parts)

    def _render_title_page(self, metadata: dict[str, str]) -> str:
        """Render title page metadata as Fountain markup.

        Converts title page metadata back to Fountain format with proper
        field formatting. Fields are output in a logical order matching
        common screenplay conventions.

        Args:
            metadata: Dictionary of title page fields and their values.
                Keys should be lowercase (e.g., 'title', 'author').

        Returns:
            Fountain-formatted title page with "Field: Value" format for
            each metadata field, followed by an empty line.

        Note:
            Field names are title-cased in output (e.g., 'draft date' becomes
            'Draft Date'). The order follows screenplay conventions with title
            and author first, then other fields.
        """
        title_parts = []

        # Render known fields in the shared ordering
        for key, _css_class, _tag, _prefix, _multiline in TITLE_PAGE_FIELD_ORDER:
            if key in metadata:
                value = metadata[key]
                field_name = key.replace("_", " ").title()
                title_parts.append(f"{field_name}: {value}")

        # Render any custom/unknown metadata fields
        for key, value in metadata.items():
            if key not in _KNOWN_TITLE_FIELDS:
                field_name = key.replace("_", " ").title()
                title_parts.append(f"{field_name}: {value}")

        # Add empty line after title page
        if title_parts:
            title_parts.append("")

        return "\n".join(title_parts)

    def _render_element(self, element: FountainElement) -> str:
        """Render a single FountainElement as Fountain markup.

        Converts a parsed element back to its Fountain text representation,
        including any special syntax markers (forced elements, scene numbers,
        character extensions, etc.).

        Args:
            element: The FountainElement to render with its type, text,
                and metadata.

        Returns:
            Fountain markup string for the element. Returns empty string for
            DUAL_DIALOGUE elements as they are handled through CHARACTER
            elements with dual_dialogue metadata.

        Example:
            >>> from fountain.elements import FountainElement, ElementType
            >>> element = FountainElement(
            ...     type=ElementType.SCENE_HEADING,
            ...     text="INT. OFFICE - DAY",
            ...     formatting=[],
            ...     line_number=1,
            ...     metadata={"scene_number": "42"}
            ... )
            >>> renderer = FountainRenderer()
            >>> renderer._render_element(element)
            'INT. OFFICE - DAY #42#'
        """
        text = self._apply_formatting_removal(element.text, element.formatting)

        if element.type == ElementType.SCENE_HEADING:
            # Check if this was a forced scene heading
            if element.metadata and element.metadata.get("forced"):
                scene_text = f".{text}"
            else:
                scene_text = text

            # Add scene number if present
            if element.metadata and "scene_number" in element.metadata:
                scene_text += f" #{element.metadata['scene_number']}#"

            return scene_text

        elif element.type == ElementType.ACTION:
            # Check if this was forced action
            if element.metadata and element.metadata.get("forced"):
                return f"!{text}"
            return text

        elif element.type == ElementType.CHARACTER:
            char_text = text

            # Add extension if present
            if element.metadata and "extension" in element.metadata:
                char_text += f" ({element.metadata['extension']})"
            elif element.metadata and element.metadata.get("continuation"):
                char_text += " (CONT'D)"

            # Check if forced character
            if element.metadata and element.metadata.get("forced"):
                char_text = f"@{char_text}"

            # Check if dual dialogue
            if element.metadata and element.metadata.get("dual_dialogue"):
                char_text += "^"

            return char_text

        elif element.type == ElementType.DIALOGUE:
            return text

        elif element.type == ElementType.PARENTHETICAL:
            return text

        elif element.type == ElementType.TRANSITION:
            # Check if this was a forced transition
            if element.metadata and element.metadata.get("forced"):
                return f">{text}"
            return text

        elif element.type == ElementType.NOTE:
            return text

        elif element.type == ElementType.BONEYARD:
            return text

        elif element.type == ElementType.SECTION:
            # Count the level based on metadata or default to single #
            level = cast(int, element.metadata.get("level", 1)) if element.metadata else 1
            return f"{'#' * level} {text}"

        elif element.type == ElementType.SYNOPSIS:
            return f"= {text}"

        elif element.type == ElementType.DUAL_DIALOGUE:
            # Dual dialogue is handled by rendering the individual character elements
            # with dual_dialogue metadata, so we return empty here
            return ""

        elif element.type == ElementType.PAGE_BREAK:
            return "==="

        elif element.type == ElementType.CENTERED:
            return f">{text}<"

        elif element.type == ElementType.LYRICS:
            return f"~{text}~"

        else:
            # Fallback for unknown element types
            return text

    def _apply_formatting_removal(self, text: str, formatting: list[FormatSpan]) -> str:
        """Remove HTML formatting and restore Fountain markup formatting.

        Currently returns the original text without modification. This is a
        known limitation of the round-trip conversion process.

        Args:
            text: The text content of the element.
            formatting: List of formatting spans detected during parsing.

        Returns:
            The original text without formatting markup restoration.

        Limitation:
            The current parser strips formatting markers (*bold*, _italic_, etc.)
            during parsing and tracks their positions in FormatSpan objects.
            However, to achieve true round-trip fidelity, we would need to store
            the original markup characters and their positions. This is a design
            trade-off that prioritizes clean parsed output over perfect round-trip
            conversion of formatting.

        Future Enhancement:
            A future version could store original formatting markers in metadata
            to enable perfect round-trip conversion of formatted text.
        """
        if not formatting:
            return text

        # For simplicity in the export renderer, we'll just return the original text
        # The formatting spans indicate where formatting was detected, but for
        # a true round-trip we'd need to store the original markup positions
        # This is a limitation of the current approach - we lose the exact
        # original formatting markup positions during parsing
        return text
