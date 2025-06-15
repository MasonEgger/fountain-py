"""
Fountain markup parser.
"""

import re
from typing import List, Dict, Optional, Tuple
from .elements import FountainElement, ElementType, FormatSpan
from .document import FountainDocument


class FountainParser:
    """Parser for Fountain markup."""
    
    # Regex patterns for Fountain elements
    SCENE_HEADING_PATTERN = re.compile(r'^(INT\.|EXT\.|EST\.|I/E\.|int\.|ext\.|est\.|i/e\.)', re.IGNORECASE)
    FORCED_SCENE_HEADING_PATTERN = re.compile(r'^\.')
    CHARACTER_PATTERN = re.compile(r'^[A-Z][A-Z0-9\s]*(\^)?$')
    TRANSITION_PATTERN = re.compile(r'^[A-Z\s]+TO:$|^FADE IN:$|^FADE OUT\.$|^CUT TO:$')
    FORCED_TRANSITION_PATTERN = re.compile(r'^>')
    CENTERED_PATTERN = re.compile(r'^>[^<]*<$')
    NOTE_PATTERN = re.compile(r'\[\[[^\]]*\]\]')
    BONEYARD_PATTERN = re.compile(r'^/\*.*?\*/$', re.DOTALL)
    SECTION_PATTERN = re.compile(r'^#+\s*')
    SYNOPSIS_PATTERN = re.compile(r'^=\s*')
    
    # Formatting patterns
    BOLD_PATTERN = re.compile(r'\*\*([^*]+)\*\*')
    ITALIC_PATTERN = re.compile(r'(?<!\*)\*([^*]+)\*(?!\*)')
    UNDERLINE_PATTERN = re.compile(r'_([^_]+)_')
    
    def __init__(self):
        self.lines = []
        self.current_line = 0
        self.elements = []
    
    def parse(self, text: str) -> FountainDocument:
        """Parse Fountain text and return a FountainDocument."""
        self.lines = text.split('\n')
        self.current_line = 0
        self.elements = []
        
        # First pass: extract title page
        metadata = self._parse_title_page()
        
        # Second pass: parse body elements
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].rstrip()
            
            if not line:  # Empty line
                self.current_line += 1
                continue
                
            element = self._parse_line(line)
            if element:
                self.elements.append(element)
            
            self.current_line += 1
        
        return FountainDocument(self.elements, metadata)
    
    def parse_file(self, filepath: str) -> FountainDocument:
        """Parse a Fountain file and return a FountainDocument."""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        return self.parse(text)
    
    def _parse_title_page(self) -> Dict[str, str]:
        """Parse title page metadata from the beginning of the document."""
        metadata = {}
        
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()
            
            if not line:
                self.current_line += 1
                continue
                
            # Check for title page key-value pairs
            if ':' in line and not line.startswith(('INT.', 'EXT.', 'EST.', 'I/E.')):
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ('title', 'author', 'credit', 'source', 'draft date', 'contact'):
                    metadata[key] = value
                    self.current_line += 1
                    continue
            
            # If we hit a non-title-page line, stop parsing title page
            break
        
        return metadata
    
    def _parse_line(self, line: str) -> Optional[FountainElement]:
        """Parse a single line and return the appropriate FountainElement."""
        original_line = line
        line = line.strip()
        
        if not line:
            return None
        
        # Check for boneyard (block comments)
        if self.BONEYARD_PATTERN.match(line):
            return FountainElement(
                type=ElementType.BONEYARD,
                text=line,
                formatting=[],
                line_number=self.current_line + 1
            )
        
        # Check for sections
        if self.SECTION_PATTERN.match(line):
            text = self.SECTION_PATTERN.sub('', line).strip()
            return FountainElement(
                type=ElementType.SECTION,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1
            )
        
        # Check for synopsis
        if self.SYNOPSIS_PATTERN.match(line):
            text = self.SYNOPSIS_PATTERN.sub('', line).strip()
            return FountainElement(
                type=ElementType.SYNOPSIS,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1
            )
        
        # Check for forced scene heading
        if self.FORCED_SCENE_HEADING_PATTERN.match(line):
            text = line[1:].strip()  # Remove the '.'
            return FountainElement(
                type=ElementType.SCENE_HEADING,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1
            )
        
        # Check for scene heading
        if self.SCENE_HEADING_PATTERN.match(line):
            return FountainElement(
                type=ElementType.SCENE_HEADING,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1
            )
        
        # Check for forced transition
        if self.FORCED_TRANSITION_PATTERN.match(line):
            text = line[1:].strip()  # Remove the '>'
            return FountainElement(
                type=ElementType.TRANSITION,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1
            )
        
        # Check for transition
        if self.TRANSITION_PATTERN.match(line):
            return FountainElement(
                type=ElementType.TRANSITION,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1
            )
        
        # Check for character (must be all caps)
        if self.CHARACTER_PATTERN.match(line):
            # Look ahead to see if next line is dialogue or parenthetical
            if self._is_dialogue_following():
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=line,
                    formatting=[],
                    line_number=self.current_line + 1
                )
        
        # Check for parenthetical
        if line.startswith('(') and line.endswith(')'):
            return FountainElement(
                type=ElementType.PARENTHETICAL,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1
            )
        
        # Check if this is dialogue (follows character or parenthetical)
        if self._is_dialogue_line():
            return FountainElement(
                type=ElementType.DIALOGUE,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1
            )
        
        # Default to action
        return FountainElement(
            type=ElementType.ACTION,
            text=line,
            formatting=self._extract_formatting(line),
            line_number=self.current_line + 1
        )
    
    def _is_dialogue_following(self) -> bool:
        """Check if the next non-empty line is dialogue."""
        next_line_idx = self.current_line + 1
        while next_line_idx < len(self.lines):
            next_line = self.lines[next_line_idx].strip()
            if next_line:
                # It's dialogue if it's not another structural element
                return not (
                    self.SCENE_HEADING_PATTERN.match(next_line) or
                    self.FORCED_SCENE_HEADING_PATTERN.match(next_line) or
                    self.TRANSITION_PATTERN.match(next_line) or
                    self.FORCED_TRANSITION_PATTERN.match(next_line) or
                    self.CHARACTER_PATTERN.match(next_line) or
                    self.SECTION_PATTERN.match(next_line) or
                    self.SYNOPSIS_PATTERN.match(next_line)
                )
            next_line_idx += 1
        return False
    
    def _is_dialogue_line(self) -> bool:
        """Check if current line is dialogue based on previous elements."""
        if not self.elements:
            return False
        
        # Check if previous element was character or parenthetical
        prev_element = self.elements[-1]
        return prev_element.type in (ElementType.CHARACTER, ElementType.PARENTHETICAL, ElementType.DIALOGUE)
    
    def _extract_formatting(self, text: str) -> List[FormatSpan]:
        """Extract formatting spans from text."""
        formatting = []
        
        # Find bold formatting
        for match in self.BOLD_PATTERN.finditer(text):
            formatting.append(FormatSpan(match.start(), match.end(), 'bold'))
        
        # Find italic formatting
        for match in self.ITALIC_PATTERN.finditer(text):
            formatting.append(FormatSpan(match.start(), match.end(), 'italic'))
        
        # Find underline formatting
        for match in self.UNDERLINE_PATTERN.finditer(text):
            formatting.append(FormatSpan(match.start(), match.end(), 'underline'))
        
        return formatting