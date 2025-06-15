"""
Fountain document representation and manipulation.
"""

import json
from typing import List, Dict, Any, Optional
from .elements import FountainElement, ElementType


class FountainDocument:
    """Represents a complete Fountain document."""
    
    def __init__(self, elements: List[FountainElement], metadata: Optional[Dict[str, str]] = None):
        self.elements = elements
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            "metadata": self.metadata,
            "elements": [
                {
                    "type": element.type.value,
                    "text": element.text,
                    "formatting": [
                        {
                            "start": span.start,
                            "end": span.end,
                            "format_type": span.format_type
                        }
                        for span in element.formatting
                    ],
                    "line_number": element.line_number,
                    "metadata": element.metadata
                }
                for element in self.elements
            ]
        }
    
    def to_json(self) -> str:
        """Convert document to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def get_characters(self) -> List[str]:
        """Extract all character names from the document."""
        characters = set()
        for element in self.elements:
            if element.type == ElementType.CHARACTER:
                # Clean up character name (remove parentheticals, etc.)
                name = element.text.strip().upper()
                if name.endswith('^'):
                    name = name[:-1].strip()
                characters.add(name)
        return sorted(list(characters))
    
    def get_scenes(self) -> List[str]:
        """Extract all scene headings from the document."""
        scenes = []
        for element in self.elements:
            if element.type == ElementType.SCENE_HEADING:
                scenes.append(element.text.strip())
        return scenes
    
    def get_statistics(self) -> Dict[str, int]:
        """Get document statistics."""
        stats = {
            "total_elements": len(self.elements),
            "characters": len(self.get_characters()),
            "scenes": len(self.get_scenes()),
        }
        
        # Count by element type
        for element_type in ElementType:
            count = sum(1 for el in self.elements if el.type == element_type)
            stats[f"{element_type.value}_count"] = count
            
        return stats
    
    def to_html(self, theme: str = "default") -> str:
        """Convert document to HTML representation."""
        from .renderer import HTMLRenderer
        renderer = HTMLRenderer(theme)
        return renderer.render(self)