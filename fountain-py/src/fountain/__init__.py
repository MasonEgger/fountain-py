"""
Fountain-py: A Python library for parsing Fountain markup.

This library provides tools for parsing Fountain screenplay format and converting
it to various output formats including HTML and structured data.
"""

from .parser import FountainParser
from .document import FountainDocument
from .elements import ElementType, FountainElement

__version__ = "0.1.0"
__author__ = "Mason Egger"
__email__ = "mason@masonegger.com"

__all__ = [
    "FountainParser",
    "FountainDocument", 
    "ElementType",
    "FountainElement",
]