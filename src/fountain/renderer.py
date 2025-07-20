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
    >>> '<div class="scene-heading">INT. HOUSE - DAY</div>' in html
    True
"""

from typing import Optional

from fountain.document import FountainDocument
from fountain.elements import ElementType, FormatSpan, FountainElement


class HTMLRenderer:
    """Renders Fountain documents as HTML with screenplay formatting.

    The HTMLRenderer converts parsed Fountain documents into HTML with proper
    screenplay formatting, including CSS styles that follow industry-standard
    screenplay layout conventions. It handles all Fountain element types and
    preserves formatting marks like bold, italic, and underline.

    The renderer supports theming through CSS customization and provides a
    default theme that mimics traditional screenplay appearance with Courier
    font and proper margins.

    Attributes:
        theme: The CSS theme to use. Currently supports "default" theme.

    CSS Classes Generated:
        - fountain-script: Main container for the entire screenplay
        - title-page: Container for title page metadata
        - script-body: Container for the main screenplay content
        - scene-heading: Scene headers (INT/EXT)
        - action: Action/description paragraphs
        - character: Character names before dialogue
        - dialogue: Spoken dialogue text
        - parenthetical: Stage directions within dialogue
        - transition: Scene transitions (CUT TO:, etc.)
        - note: Production notes (hidden by default)
        - boneyard: Deleted content (hidden)
        - section: Section headers for organization
        - synopsis: Scene synopsis (hidden by default)
        - dual-dialogue: Container for simultaneous dialogue
        - page-break: Page break markers
        - centered: Centered text
        - lyrics: Song lyrics with special formatting

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
        >>> '<h1 class="title">My Screenplay</h1>' in html
        True
        >>> '<div class="character">JOHN</div>' in html
        True
    """

    def __init__(self, theme: str = "default"):
        """Initialize the HTML renderer with a theme.

        Args:
            theme: The CSS theme to use. Currently only "default" is supported,
                which provides traditional screenplay formatting with Courier font
                and industry-standard margins and spacing.
        """
        self.theme = theme

    def render(self, document: FountainDocument) -> str:
        """Render a FountainDocument as HTML with screenplay formatting.

        Converts a parsed Fountain document into a complete HTML document with
        embedded CSS styling. The output includes proper screenplay formatting
        with title page, scene headings, dialogue, and all other Fountain elements.

        Args:
            document: The FountainDocument to render, containing parsed elements
                and optional title page metadata.

        Returns:
            A complete HTML string with embedded CSS that can be saved as an HTML
            file or embedded in a web page. The HTML includes all necessary styling
            for proper screenplay display.

        Example:
            >>> from fountain.parser import FountainParser
            >>> parser = FountainParser()
            >>> doc = parser.parse("FADE IN:\\n\\nINT. ROOM - DAY")
            >>> renderer = HTMLRenderer()
            >>> html = renderer.render(doc)
            >>> 'fountain-script' in html  # Check for main container
            True
            >>> '<div class="transition">FADE IN:</div>' in html
            True
        """
        html_parts = []

        # Add CSS
        html_parts.append(self._get_css())

        # Add document wrapper
        html_parts.append('<div class="fountain-script">')

        # Add title page if metadata exists
        if document.metadata:
            html_parts.append(self._render_title_page(document.metadata))

        # Add script body
        html_parts.append('<div class="script-body">')

        for element in document.elements:
            html_parts.append(self._render_element(element))

        html_parts.append("</div>")  # script-body
        html_parts.append("</div>")  # fountain-script

        return "\n".join(html_parts)

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
        html_parts = ['<div class="title-page">']

        # Primary title information
        if "title" in metadata:
            html_parts.append(f'<h1 class="title">{self._escape_html(metadata["title"])}</h1>')

        # Author information (handle both 'author' and 'authors')
        if "author" in metadata:
            html_parts.append(f'<p class="author">by {self._escape_html(metadata["author"])}</p>')
        elif "authors" in metadata:
            html_parts.append(f'<p class="author">by {self._escape_html(metadata["authors"])}</p>')

        # Credit and attribution
        if "credit" in metadata:
            html_parts.append(f'<p class="credit">{self._escape_html(metadata["credit"])}</p>')

        if "source" in metadata:
            html_parts.append(f'<p class="source">{self._escape_html(metadata["source"])}</p>')

        # Production information
        if "writers" in metadata:
            html_parts.append(f'<p class="writers">Writers: {self._escape_html(metadata["writers"])}</p>')

        if "producer" in metadata:
            html_parts.append(f'<p class="producer">Producer: {self._escape_html(metadata["producer"])}</p>')

        if "director" in metadata:
            html_parts.append(f'<p class="director">Director: {self._escape_html(metadata["director"])}</p>')

        # Version and date information
        if "draft date" in metadata:
            html_parts.append(f'<p class="draft-date">{self._escape_html(metadata["draft date"])}</p>')

        if "date" in metadata:
            html_parts.append(f'<p class="date">{self._escape_html(metadata["date"])}</p>')

        if "revised" in metadata:
            html_parts.append(f'<p class="revised">Revised: {self._escape_html(metadata["revised"])}</p>')

        if "version" in metadata:
            html_parts.append(f'<p class="version">Version: {self._escape_html(metadata["version"])}</p>')

        if "format" in metadata:
            html_parts.append(f'<p class="format">Format: {self._escape_html(metadata["format"])}</p>')

        if "created" in metadata:
            html_parts.append(f'<p class="created">Created: {self._escape_html(metadata["created"])}</p>')

        # Contact and legal information
        if "contact" in metadata:
            # Handle multi-line contact information
            contact_html = self._escape_html(metadata["contact"]).replace("\n", "<br>")
            html_parts.append(f'<p class="contact">{contact_html}</p>')

        if "copyright" in metadata:
            html_parts.append(f'<p class="copyright">{self._escape_html(metadata["copyright"])}</p>')

        if "notes" in metadata:
            # Handle multi-line notes
            notes_html = self._escape_html(metadata["notes"]).replace("\n", "<br>")
            html_parts.append(f'<p class="notes">{notes_html}</p>')

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
            >>> '<div class="character">SARAH <span class="character-extension">(V.O.)</span></div>' == html
            True
        """
        css_class = element.type.value.replace("_", "-")
        text = self._apply_formatting(element.text, element.formatting)

        if element.type == ElementType.SCENE_HEADING:
            scene_html = f'<div class="scene-heading">{text}'
            if element.metadata and "scene_number" in element.metadata:
                scene_html += f' <span class="scene-number">#{element.metadata["scene_number"]}#</span>'
            scene_html += "</div>"
            return scene_html
        elif element.type == ElementType.ACTION:
            # Convert tabs to spaces and preserve leading whitespace
            text_with_spacing = text.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
            text_with_br = text_with_spacing.replace("\n", "<br>")
            return f'<div class="action">{text_with_br}</div>'
        elif element.type == ElementType.CHARACTER:
            char_html = f'<div class="character">{text}'
            if element.metadata and "extension" in element.metadata:
                char_html += f' <span class="character-extension">({element.metadata["extension"]})</span>'
            elif element.metadata and element.metadata.get("continuation"):
                char_html += ' <span class="character-continuation">(CONT\'D)</span>'
            char_html += "</div>"
            return char_html
        elif element.type == ElementType.DIALOGUE:
            return f'<div class="dialogue">{text}</div>'
        elif element.type == ElementType.PARENTHETICAL:
            return f'<div class="parenthetical">{text}</div>'
        elif element.type == ElementType.TRANSITION:
            return f'<div class="transition">{text}</div>'
        elif element.type == ElementType.NOTE:
            return f'<div class="note">{text}</div>'
        elif element.type == ElementType.BONEYARD:
            return f'<div class="boneyard">{text}</div>'
        elif element.type == ElementType.SECTION:
            return f'<div class="section">{text}</div>'
        elif element.type == ElementType.SYNOPSIS:
            return f'<div class="synopsis">{text}</div>'
        elif element.type == ElementType.DUAL_DIALOGUE:
            return self._render_dual_dialogue(element)
        elif element.type == ElementType.PAGE_BREAK:
            return '<div class="page-break"></div>'
        elif element.type == ElementType.CENTERED:
            return f'<div class="centered">{text}</div>'
        elif element.type == ElementType.LYRICS:
            return f'<div class="lyrics">{text}</div>'
        else:
            return f'<div class="{css_class}">{text}</div>'

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
        segments: list[tuple[str, Optional[str]]] = []
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

        left_char = metadata["left_character"]
        left_dialogue = metadata["left_dialogue"]
        right_char = metadata["right_character"]
        right_dialogue = metadata["right_dialogue"]

        html_parts = ['<div class="dual-dialogue">']

        # Left column
        html_parts.append('<div class="dual-dialogue-left">')
        html_parts.append(self._render_element(left_char))
        for dialogue_element in left_dialogue:
            html_parts.append(self._render_element(dialogue_element))
        html_parts.append("</div>")

        # Right column
        html_parts.append('<div class="dual-dialogue-right">')
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
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def _get_css(self) -> str:
        """Get CSS styles for the chosen theme.

        Returns embedded CSS styles that format the HTML output to look like
        a traditional screenplay. The default theme uses Courier font and
        follows industry-standard screenplay formatting conventions.

        Returns:
            A string containing a complete <style> tag with CSS rules for all
            Fountain element types. The CSS includes:
            - Courier font family for authentic screenplay appearance
            - Proper margins and spacing (70% max-width, 1in padding)
            - Element-specific formatting (centered dialogue, uppercase scenes)
            - Special handling for notes and boneyard (hidden by default)
            - Responsive dual dialogue layout
            - Print-friendly page breaks

        Note:
            Currently only the "default" theme is implemented. Future versions
            may support additional themes for different screenplay formats or
            custom styling needs.

        CSS Customization:
            Users can override these styles by adding their own CSS after the
            generated HTML or by implementing a custom renderer subclass.
        """
        if self.theme == "default":
            return """
<style>
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

.title-page {
    text-align: center;
    margin-bottom: 3in;
}

.title-page .title {
    font-size: 24pt;
    font-weight: bold;
    margin-bottom: 1in;
    text-transform: uppercase;
}

.title-page .author {
    font-size: 14pt;
    margin-bottom: 0.5in;
}

.title-page .credit,
.title-page .source,
.title-page .draft-date,
.title-page .contact,
.title-page .writers,
.title-page .producer,
.title-page .director,
.title-page .date,
.title-page .revised,
.title-page .version,
.title-page .format,
.title-page .created,
.title-page .copyright,
.title-page .notes {
    font-size: 12pt;
    margin-bottom: 0.25in;
}

.title-page .notes,
.title-page .contact {
    white-space: pre-line;
}

.script-body {
    page-break-before: always;
}

.scene-heading {
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 2em;
    margin-bottom: 1em;
}

.action {
    margin-bottom: 1em;
    text-align: left;
}

.character {
    text-align: center;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 1em;
    margin-bottom: 0;
}

.dialogue {
    text-align: center;
    margin: 0 auto 1em auto;
}

.parenthetical {
    text-align: center;
    font-style: italic;
    margin: 0 auto;
}

.transition {
    text-align: right;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 1em;
    margin-bottom: 1em;
}

.note {
    font-style: italic;
    color: #666;
    margin: 0.5em 0;
}

.boneyard {
    display: none;
}

.section {
    font-weight: bold;
    font-size: 14pt;
    margin: 2em 0 1em 0;
    text-transform: uppercase;
}

.synopsis {
    font-style: italic;
    color: #666;
    margin: 0.5em 0;
}

.scene-number {
    font-weight: normal;
    color: #888;
    font-size: 10pt;
}

.character-extension,
.character-continuation {
    font-weight: normal;
    font-size: 10pt;
}

.dual-dialogue {
    display: flex;
    margin: 1em 0;
}

.dual-dialogue-left,
.dual-dialogue-right {
    flex: 1;
    padding: 0 1em;
}

.dual-dialogue-left {
    border-right: 1px solid #ddd;
}

.page-break {
    page-break-before: always;
    border-top: 2px solid #ccc;
    margin: 2em 0;
    height: 0;
}

.centered {
    text-align: center;
    margin: 1em 0;
}

.lyrics {
    text-align: center;
    font-style: italic;
    margin: 0.5em auto;
    color: #444;
}
</style>
"""
        else:
            # Fallback to default theme
            old_theme = self.theme
            self.theme = "default"
            css = self._get_css()
            self.theme = old_theme
            return css


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

        # Render supported title page fields in a logical order
        title_order = [
            "title",
            "author",
            "authors",
            "credit",
            "source",
            "writers",
            "producer",
            "director",
            "copyright",
            "notes",
            "contact",
            "draft date",
            "date",
            "revised",
            "version",
            "format",
            "created",
        ]

        for field in title_order:
            if field in metadata:
                value = metadata[field]
                # Capitalize first letter of field for display
                field_name = field.replace("_", " ").title()
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
            level = element.metadata.get("level", 1) if element.metadata else 1
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


# Example: Creating a Custom Renderer
# ===================================
#
# To create a custom renderer, inherit from a base class or create your own:
#
# Example of a Markdown renderer:
#
# class MarkdownRenderer:
#     \"\"\"Render Fountain documents as Markdown.
#
#     Example:
#         >>> from fountain.parser import FountainParser
#         >>> parser = FountainParser()
#         >>> doc = parser.parse("INT. HOUSE - DAY\\n\\nAction here.")
#         >>> renderer = MarkdownRenderer()
#         >>> md = renderer.render(doc)
#         >>> '## INT. HOUSE - DAY' in md
#         True
#         >>> 'Action here.' in md
#         True
#     \"\"\"
#
#     def render(self, document: FountainDocument) -> str:
#         \"\"\"Render document as Markdown.\"\"\"
#         md_parts = []
#
#         # Add title if present
#         if document.metadata and "title" in document.metadata:
#             md_parts.append(f"# {document.metadata['title']}")
#             if "author" in document.metadata:
#                 md_parts.append(f"*by {document.metadata['author']}*")
#             md_parts.append("")
#
#         # Render elements
#         for element in document.elements:
#             if element.type == ElementType.SCENE_HEADING:
#                 md_parts.append(f"## {element.text}")
#             elif element.type == ElementType.ACTION:
#                 md_parts.append(element.text)
#             elif element.type == ElementType.CHARACTER:
#                 md_parts.append(f"**{element.text}**")
#             elif element.type == ElementType.DIALOGUE:
#                 md_parts.append(f"> {element.text}")
#             elif element.type == ElementType.PARENTHETICAL:
#                 md_parts.append(f"*{element.text}*")
#             elif element.type == ElementType.TRANSITION:
#                 md_parts.append(f"### {element.text}")
#             elif element.type == ElementType.NOTE:
#                 md_parts.append(f"<!-- {element.text} -->")
#             else:
#                 md_parts.append(element.text)
#             md_parts.append("")
#
#         return "\\n".join(md_parts)
#
#
# Example of a JSON statistics renderer:
#
# class StatsRenderer:
#     \"\"\"Render document statistics as JSON.
#
#     Example:
#         >>> import json
#         >>> from fountain.parser import FountainParser
#         >>> parser = FountainParser()
#         >>> doc = parser.parse("INT. HOUSE\\n\\nJOHN\\nHello\\n\\nSARAH\\nHi\")
#         >>> renderer = StatsRenderer()
#         >>> stats_json = renderer.render(doc)
#         >>> stats = json.loads(stats_json)
#         >>> stats["total_elements"]
#         4
#         >>> sorted(stats["characters"])
#         ['JOHN', 'SARAH']
#     \"\"\"
#
#     def render(self, document: FountainDocument) -> str:
#         \"\"\"Generate statistics JSON.\"\"\"
#         import json
#
#         stats = document.get_statistics()
#         stats["characters"] = list(document.get_characters())
#
#         # Add scene list
#         scenes = []
#         for element in document.elements:
#             if element.type == ElementType.SCENE_HEADING:
#                 scenes.append(element.text)
#         stats["scenes"] = scenes
#
#         return json.dumps(stats, indent=2)
