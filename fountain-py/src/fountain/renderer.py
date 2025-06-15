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

        if "title" in metadata:
            html_parts.append(
                f'<h1 class="title">{self._escape_html(metadata["title"])}</h1>'
            )

        if "author" in metadata:
            html_parts.append(
                f'<p class="author">by {self._escape_html(metadata["author"])}</p>'
            )

        if "credit" in metadata:
            html_parts.append(
                f'<p class="credit">{self._escape_html(metadata["credit"])}</p>'
            )

        if "source" in metadata:
            html_parts.append(
                f'<p class="source">{self._escape_html(metadata["source"])}</p>'
            )

        if "draft date" in metadata:
            html_parts.append(
                f'<p class="draft-date">{self._escape_html(metadata["draft date"])}</p>'
            )

        if "contact" in metadata:
            html_parts.append(
                f'<p class="contact">{self._escape_html(metadata["contact"])}</p>'
            )

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _render_element(self, element: FountainElement) -> str:
        """Render a single FountainElement as HTML."""
        css_class = element.type.value.replace("_", "-")
        text = self._apply_formatting(element.text, element.formatting)

        if element.type == ElementType.SCENE_HEADING:
            return f'<div class="scene-heading">{text}</div>'
        elif element.type == ElementType.ACTION:
            return f'<div class="action">{text}</div>'
        elif element.type == ElementType.CHARACTER:
            return f'<div class="character">{text}</div>'
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
        else:
            return f'<div class="{css_class}">{text}</div>'

    def _apply_formatting(self, text: str, formatting) -> str:
        """Apply formatting spans to text."""
        if not formatting:
            return self._escape_html(text)

        # Sort formatting spans by start position (reversed for easier processing)
        sorted_formatting = sorted(formatting, key=lambda x: x.start, reverse=True)

        result = text
        for span in sorted_formatting:
            if span.format_type == "bold":
                result = (
                    result[: span.start]
                    + f"<strong>{result[span.start:span.end]}</strong>"
                    + result[span.end :]
                )
            elif span.format_type == "italic":
                result = (
                    result[: span.start]
                    + f"<em>{result[span.start:span.end]}</em>"
                    + result[span.end :]
                )
            elif span.format_type == "underline":
                result = (
                    result[: span.start]
                    + f"<u>{result[span.start:span.end]}</u>"
                    + result[span.end :]
                )

        return self._escape_html(result)

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
.title-page .contact {
    font-size: 12pt;
    margin-bottom: 0.25in;
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
</style>
"""
        else:
            return self._get_css()  # Fallback to default
