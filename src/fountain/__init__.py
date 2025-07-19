"""
Fountain-py: A Python library for parsing Fountain markup.

This library provides tools for parsing Fountain screenplay format and converting
it to various output formats including HTML and structured data.
"""

from fountain.document import FountainDocument
from fountain.elements import ElementType, FountainElement
from fountain.parser import FountainParser

__all__ = [
    "FountainParser",
    "FountainDocument",
    "ElementType",
    "FountainElement",
]
