"""
Fountain element types and classes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, NamedTuple, Optional


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
    LYRICS = "lyrics"


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
    formatting: list[FormatSpan]
    line_number: int
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
