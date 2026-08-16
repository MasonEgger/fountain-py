# ABOUTME: Public API for the fountain screenplay parser library.
# Exports FountainParser, FountainDocument, ElementType, FountainElement, renderers, and type aliases.
"""
Fountain-py: A Python library for parsing Fountain markup.

This library provides tools for parsing Fountain screenplay format and converting
it to various output formats including HTML and structured data.
"""

from fountain.document import FountainDocument
from fountain.elements import ElementType, FormatType, FountainElement, MetadataValue, ValidationIssue
from fountain.parser import FountainParser
from fountain.renderer import FountainRenderer, HTMLRenderer
from fountain.renderers.base import BinaryRenderer, TextRenderer

__all__ = [
    "FountainParser",
    "FountainDocument",
    "ElementType",
    "FountainElement",
    "FormatType",
    "MetadataValue",
    "HTMLRenderer",
    "FountainRenderer",
    "ValidationIssue",
    "TextRenderer",
    "BinaryRenderer",
]
