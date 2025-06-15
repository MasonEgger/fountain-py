"""
HTML renderer for Fountain documents.
"""

from typing import Dict
from .document import FountainDocument
from .elements import ElementType, FountainElement


class HTMLRenderer:
    """Renders Fountain documents as HTML."""

    def __init__(self, theme: str = "default"):
        self.theme = theme

    def render(self, document: FountainDocument) -> str:
        """Render a FountainDocument as HTML."""
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

    def _render_title_page(self, metadata: Dict[str, str]) -> str:
        """Render the title page metadata."""
        html_parts = ['<div class="title-page">']

        # Primary title information
        if "title" in metadata:
            html_parts.append(
                f'<h1 class="title">{self._escape_html(metadata["title"])}</h1>'
            )

        # Author information (handle both 'author' and 'authors')
        if "author" in metadata:
            html_parts.append(
                f'<p class="author">by {self._escape_html(metadata["author"])}</p>'
            )
        elif "authors" in metadata:
            html_parts.append(
                f'<p class="author">by {self._escape_html(metadata["authors"])}</p>'
            )

        # Credit and attribution
        if "credit" in metadata:
            html_parts.append(
                f'<p class="credit">{self._escape_html(metadata["credit"])}</p>'
            )

        if "source" in metadata:
            html_parts.append(
                f'<p class="source">{self._escape_html(metadata["source"])}</p>'
            )

        # Production information
        if "writers" in metadata:
            html_parts.append(
                f'<p class="writers">Writers: {self._escape_html(metadata["writers"])}</p>'
            )

        if "producer" in metadata:
            html_parts.append(
                f'<p class="producer">Producer: {self._escape_html(metadata["producer"])}</p>'
            )

        if "director" in metadata:
            html_parts.append(
                f'<p class="director">Director: {self._escape_html(metadata["director"])}</p>'
            )

        # Version and date information
        if "draft date" in metadata:
            html_parts.append(
                f'<p class="draft-date">{self._escape_html(metadata["draft date"])}</p>'
            )

        if "date" in metadata:
            html_parts.append(
                f'<p class="date">{self._escape_html(metadata["date"])}</p>'
            )

        if "revised" in metadata:
            html_parts.append(
                f'<p class="revised">Revised: {self._escape_html(metadata["revised"])}</p>'
            )

        if "version" in metadata:
            html_parts.append(
                f'<p class="version">Version: {self._escape_html(metadata["version"])}</p>'
            )

        if "format" in metadata:
            html_parts.append(
                f'<p class="format">Format: {self._escape_html(metadata["format"])}</p>'
            )

        if "created" in metadata:
            html_parts.append(
                f'<p class="created">Created: {self._escape_html(metadata["created"])}</p>'
            )

        # Contact and legal information
        if "contact" in metadata:
            # Handle multi-line contact information
            contact_html = self._escape_html(metadata["contact"]).replace('\n', '<br>')
            html_parts.append(
                f'<p class="contact">{contact_html}</p>'
            )

        if "copyright" in metadata:
            html_parts.append(
                f'<p class="copyright">{self._escape_html(metadata["copyright"])}</p>'
            )

        if "notes" in metadata:
            # Handle multi-line notes
            notes_html = self._escape_html(metadata["notes"]).replace('\n', '<br>')
            html_parts.append(
                f'<p class="notes">{notes_html}</p>'
            )

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _render_element(self, element: FountainElement) -> str:
        """Render a single FountainElement as HTML."""
        css_class = element.type.value.replace("_", "-")
        text = self._apply_formatting(element.text, element.formatting)

        if element.type == ElementType.SCENE_HEADING:
            scene_html = f'<div class="scene-heading">{text}'
            if element.metadata and 'scene_number' in element.metadata:
                scene_html += f' <span class="scene-number">#{element.metadata["scene_number"]}#</span>'
            scene_html += '</div>'
            return scene_html
        elif element.type == ElementType.ACTION:
            # Convert tabs to spaces and preserve leading whitespace
            text_with_spacing = text.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
            text_with_br = text_with_spacing.replace('\n', '<br>')
            return f'<div class="action">{text_with_br}</div>'
        elif element.type == ElementType.CHARACTER:
            char_html = f'<div class="character">{text}'
            if element.metadata and 'extension' in element.metadata:
                char_html += f' <span class="character-extension">({element.metadata["extension"]})</span>'
            char_html += '</div>'
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
        else:
            return f'<div class="{css_class}">{text}</div>'

    def _apply_formatting(self, text: str, formatting) -> str:
        """Apply formatting spans to text."""
        if not formatting:
            return self._escape_html(text)

        # Sort formatting spans by start position (reversed for easier processing)
        sorted_formatting = sorted(formatting, key=lambda x: x.start, reverse=True)

        # Build list of text segments with their formatting
        segments = []
        last_end = len(text)
        
        for span in sorted_formatting:
            # Add text after this span (if any)
            if last_end > span.end:
                segments.append((text[span.end:last_end], None))
            
            # Add the formatted span
            segments.append((text[span.start:span.end], span.format_type))
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
                
        return ''.join(result_parts)

    def _render_dual_dialogue(self, element: FountainElement) -> str:
        """Render dual dialogue as side-by-side columns."""
        metadata = element.metadata
        
        left_char = metadata['left_character']
        left_dialogue = metadata['left_dialogue']
        right_char = metadata['right_character']
        right_dialogue = metadata['right_dialogue']
        
        html_parts = ['<div class="dual-dialogue">']
        
        # Left column
        html_parts.append('<div class="dual-dialogue-left">')
        html_parts.append(self._render_element(left_char))
        for dialogue_element in left_dialogue:
            html_parts.append(self._render_element(dialogue_element))
        html_parts.append('</div>')
        
        # Right column
        html_parts.append('<div class="dual-dialogue-right">')
        html_parts.append(self._render_element(right_char))
        for dialogue_element in right_dialogue:
            html_parts.append(self._render_element(dialogue_element))
        html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def _get_css(self) -> str:
        """Get CSS styles for the chosen theme."""
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

.character-extension {
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
</style>
"""
        else:
            return self._get_css()  # Fallback to default
