"""
Fountain element types and classes.
"""

from enum import Enum
from typing import List, Optional, NamedTuple
from dataclasses import dataclass


class ElementType(Enum):
    """Types of Fountain elements."""
    TITLE_PAGE = "title_page"
    SCENE_HEADING = "scene_heading"
    ACTION = "action"
    CHARACTER = "character"
    DIALOGUE = "dialogue"
    PARENTHETICAL = "parenthetical"
    TRANSITION = "transition"
    NOTE = "note"
    BONEYARD = "boneyard"
    SECTION = "section"
    SYNOPSIS = "synopsis"
    DUAL_DIALOGUE = "dual_dialogue"
    PAGE_BREAK = "page_break"
    CENTERED = "centered"


class FormatSpan(NamedTuple):
    """Represents a formatting span within text."""
    start: int
    end: int
    format_type: str  # 'bold', 'italic', 'underline'


@dataclass
class FountainElement:
    """Represents a single element in a Fountain document."""
    type: ElementType
    text: str
    formatting: List[FormatSpan]
    line_number: int
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        if self.formatting is None:
            self.formatting = []
        if self.metadata is None:
            self.metadata = {}