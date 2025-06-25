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
    SCENE_NUMBER_PATTERN = re.compile(r'\s*#([^#]+)#\s*$')
    FORCED_SCENE_HEADING_PATTERN = re.compile(r'^\.')
    CHARACTER_PATTERN = re.compile(r'^[A-Z][A-Z0-9\s]*$')
    DUAL_CHARACTER_PATTERN = re.compile(r'^[A-Z][A-Z0-9\s]*\^\s*$')
    FORCED_CHARACTER_PATTERN = re.compile(r'^@(.+)$')
    CHARACTER_EXTENSION_PATTERN = re.compile(r'^([A-Z][A-Z0-9\s]*)\s*\(([^)]+)\)\s*(\^)?\s*$')
    TRANSITION_PATTERN = re.compile(r'^[A-Z\s]+TO:$|^FADE IN:$|^FADE OUT\.$|^CUT TO:$')
    FORCED_TRANSITION_PATTERN = re.compile(r'^>')
    FORCED_ACTION_PATTERN = re.compile(r'^!(.+)$')
    CENTERED_PATTERN = re.compile(r'^>[^<]*<$')
    NOTE_PATTERN = re.compile(r'\[\[[^\]]*\]\]')
    BONEYARD_PATTERN = re.compile(r'^/\*.*?\*/$', re.DOTALL)
    MULTILINE_BONEYARD_START = re.compile(r'^/\*')
    MULTILINE_BONEYARD_END = re.compile(r'\*/$')
    SECTION_PATTERN = re.compile(r'^#+\s*')
    SYNOPSIS_PATTERN = re.compile(r'^=\s*')
    PAGE_BREAK_PATTERN = re.compile(r'^===+$')
    
    # Formatting patterns
    BOLD_ITALIC_PATTERN = re.compile(r'\*\*\*([^*]+)\*\*\*')
    BOLD_PATTERN = re.compile(r'\*\*([^*]+)\*\*')
    ITALIC_PATTERN = re.compile(r'(?<!\*)\*([^*\s][^*]*[^*\s])\*(?!\*)')
    UNDERLINE_PATTERN = re.compile(r'_([^_]+)_')
    
    def __init__(self):
        self.lines = []
        self.current_line = 0
        self.elements = []
        self.in_boneyard = False
    
    def parse(self, text: str) -> FountainDocument:
        """Parse Fountain text and return a FountainDocument."""
        self.lines = text.split('\n')
        self.current_line = 0
        self.elements = []
        self.in_boneyard = False
        
        # First pass: extract title page
        metadata = self._parse_title_page()
        
        # Second pass: parse body elements
        previous_line_was_blank = False
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].rstrip()
            
            if not line:  # Empty line
                previous_line_was_blank = True
                self.current_line += 1
                continue
                
            element = self._parse_line(line, previous_line_was_blank)
            if element:
                self.elements.append(element)
            
            previous_line_was_blank = False
            self.current_line += 1
        
        # Post-process for dual dialogue pairing
        self._process_dual_dialogue()
        
        return FountainDocument(self.elements, metadata)
    
    def parse_file(self, filepath: str) -> FountainDocument:
        """Parse a Fountain file and return a FountainDocument."""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        return self.parse(text)
    
    def _parse_title_page(self) -> Dict[str, str]:
        """Parse title page metadata from the beginning of the document."""
        metadata = {}
        current_key = None
        
        # Expanded list of supported title page fields
        supported_fields = {
            'title', 'author', 'credit', 'source', 'draft date', 'contact',
            'authors', 'notes', 'copyright', 'date', 'revised', 'version',
            'format', 'created', 'writers', 'producer', 'director'
        }
        
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()
            
            if not line:
                # Empty line might end title page or continue multi-line value
                if current_key is None:
                    self.current_line += 1
                    continue
                else:
                    # Check if next non-empty line is title page or body
                    next_line_idx = self.current_line + 1
                    while next_line_idx < len(self.lines) and not self.lines[next_line_idx].strip():
                        next_line_idx += 1
                    
                    if next_line_idx < len(self.lines):
                        next_line = self.lines[next_line_idx].strip()
                        # If next line starts with scene heading, end title page
                        if (next_line.startswith(('INT.', 'EXT.', 'EST.', 'I/E.')) or
                            next_line.startswith('.') or  # forced scene heading
                            (':' not in next_line and current_key)):  # likely script body
                            break
                    
                    # Continue with current key (multi-line value)
                    self.current_line += 1
                    continue
                
            # Check for title page key-value pairs
            if ':' in line and not line.startswith(('INT.', 'EXT.', 'EST.', 'I/E.')):
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in supported_fields:
                    if current_key and current_key in metadata:
                        # Finalize previous multi-line value
                        metadata[current_key] = metadata[current_key].strip()
                    
                    current_key = key
                    metadata[key] = value
                    self.current_line += 1
                    continue
                else:
                    # Unknown field, might be end of title page
                    break
            
            # Check if this is a continuation of multi-line value
            elif current_key and not line.startswith(('INT.', 'EXT.', 'EST.', 'I/E.', '.')):
                # This is a continuation line for the current key
                if metadata[current_key]:
                    metadata[current_key] += ' ' + line
                else:
                    metadata[current_key] = line
                self.current_line += 1
                continue
            
            # If we hit a non-title-page line, stop parsing title page
            break
        
        # Clean up any trailing multi-line value
        if current_key and current_key in metadata:
            metadata[current_key] = metadata[current_key].strip()
        
        return metadata
    
    def _parse_line(self, line: str, had_blank_line_before: bool = False) -> Optional[FountainElement]:
        """Parse a single line and return the appropriate FountainElement."""
        original_line = line
        line = line.strip()
        
        if not line:
            return None
        
        # Handle multi-line boneyard comments
        if self.in_boneyard:
            if self.MULTILINE_BONEYARD_END.search(line):
                self.in_boneyard = False
            return None  # Skip all lines inside boneyard
        
        if self.MULTILINE_BONEYARD_START.match(line):
            if not self.MULTILINE_BONEYARD_END.search(line):
                self.in_boneyard = True
            return None  # Skip boneyard start line
        
        # Check for single-line boneyard (block comments)
        if self.BONEYARD_PATTERN.match(line):
            return FountainElement(
                type=ElementType.BONEYARD,
                text=line,
                formatting=[],
                line_number=self.current_line + 1
            )
        
        # Check for page breaks
        if self.PAGE_BREAK_PATTERN.match(line):
            return FountainElement(
                type=ElementType.PAGE_BREAK,
                text=line,
                formatting=[],
                line_number=self.current_line + 1
            )
        
        # Check for notes [[note]]
        note_matches = list(self.NOTE_PATTERN.finditer(line))
        if note_matches and line.strip().startswith('[[') and line.strip().endswith(']]'):
            # Line is entirely a note
            return FountainElement(
                type=ElementType.NOTE,
                text=line,
                formatting=[],
                line_number=self.current_line + 1
            )
        
        # Check for forced action (starts with !)
        if self.FORCED_ACTION_PATTERN.match(line):
            text = self.FORCED_ACTION_PATTERN.sub(r'\1', line).strip()
            return FountainElement(
                type=ElementType.ACTION,
                text=text,
                formatting=self._extract_formatting(text),
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
        
        # Check for forced scene heading (must come before natural scene heading)
        if self.FORCED_SCENE_HEADING_PATTERN.match(line):
            text = line[1:].strip()  # Remove the '.'
            metadata = {}
            # Check for scene number
            scene_num_match = self.SCENE_NUMBER_PATTERN.search(text)
            if scene_num_match:
                metadata['scene_number'] = scene_num_match.group(1).strip()
                text = self.SCENE_NUMBER_PATTERN.sub('', text).strip()
            return FountainElement(
                type=ElementType.SCENE_HEADING,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
                metadata=metadata
            )
        
        # Check for centered text (>text<) - must come before forced transition
        if self.CENTERED_PATTERN.match(line):
            text = line[1:-1].strip()  # Remove the '>' and '<'
            return FountainElement(
                type=ElementType.CENTERED,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1
            )
        
        # Check for forced transition (>text - not enclosed)
        if self.FORCED_TRANSITION_PATTERN.match(line) and not line.endswith('<'):
            text = line[1:].strip()  # Remove the '>'
            return FountainElement(
                type=ElementType.TRANSITION,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1
            )
        
        # Check for scene heading
        if self.SCENE_HEADING_PATTERN.match(line):
            metadata = {}
            text = line
            # Check for scene number
            scene_num_match = self.SCENE_NUMBER_PATTERN.search(text)
            if scene_num_match:
                metadata['scene_number'] = scene_num_match.group(1).strip()
                text = self.SCENE_NUMBER_PATTERN.sub('', text).strip()
            return FountainElement(
                type=ElementType.SCENE_HEADING,
                text=text,
                formatting=self._extract_formatting(text),
                line_number=self.current_line + 1,
                metadata=metadata
            )
        
        # Check for transition
        if self.TRANSITION_PATTERN.match(line):
            return FountainElement(
                type=ElementType.TRANSITION,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1
            )
        
        # Check for forced character (@character)
        if self.FORCED_CHARACTER_PATTERN.match(line):
            character_name = self.FORCED_CHARACTER_PATTERN.sub(r'\1', line).strip()
            if self._is_dialogue_following():
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata={'forced': True}
                )
        
        # Check for dual dialogue character (CHARACTER^)
        if self.DUAL_CHARACTER_PATTERN.match(line):
            character_name = line.replace('^', '').strip()
            if self._is_dialogue_following():
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata={'dual_dialogue': True}
                )
        
        # Check for character with extensions (CHARACTER (V.O.))
        char_ext_match = self.CHARACTER_EXTENSION_PATTERN.match(line)
        if char_ext_match:
            character_name = char_ext_match.group(1).strip()
            extension = char_ext_match.group(2).strip()
            is_dual = char_ext_match.group(3) is not None
            if self._is_dialogue_following():
                metadata = {'extension': extension}
                if is_dual:
                    metadata['dual_dialogue'] = True
                return FountainElement(
                    type=ElementType.CHARACTER,
                    text=character_name,
                    formatting=[],
                    line_number=self.current_line + 1,
                    metadata=metadata
                )
        
        # Check for regular character (must be all caps)
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
        if self._is_dialogue_line(had_blank_line_before):
            return FountainElement(
                type=ElementType.DIALOGUE,
                text=line,
                formatting=self._extract_formatting(line),
                line_number=self.current_line + 1
            )
        
        # Default to action
        return FountainElement(
            type=ElementType.ACTION,
            text=original_line.rstrip(),  # Preserve leading tabs/spaces, remove trailing whitespace
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
                    self.DUAL_CHARACTER_PATTERN.match(next_line) or
                    self.FORCED_CHARACTER_PATTERN.match(next_line) or
                    self.CHARACTER_EXTENSION_PATTERN.match(next_line) or
                    self.SECTION_PATTERN.match(next_line) or
                    self.SYNOPSIS_PATTERN.match(next_line) or
                    self.PAGE_BREAK_PATTERN.match(next_line) or
                    self.CENTERED_PATTERN.match(next_line) or
                    self.FORCED_ACTION_PATTERN.match(next_line) or
                    (next_line.startswith('[[') and next_line.endswith(']]'))
                )
            next_line_idx += 1
        return False
    
    def _is_dialogue_line(self, had_blank_line_before: bool = False) -> bool:
        """Check if current line is dialogue based on previous elements and blank line separation."""
        if not self.elements:
            return False
        
        prev_element = self.elements[-1]
        
        # Always dialogue after CHARACTER or PARENTHETICAL
        if prev_element.type in (ElementType.CHARACTER, ElementType.PARENTHETICAL):
            return True
        
        # Dialogue continuation: follows DIALOGUE with NO blank line separation
        if prev_element.type == ElementType.DIALOGUE and not had_blank_line_before:
            return True
        
        return False
    
    def _extract_formatting(self, text: str) -> List[FormatSpan]:
        """Extract formatting spans from text."""
        formatting = []
        
        # Find bold-italic formatting first (***text***)
        for match in self.BOLD_ITALIC_PATTERN.finditer(text):
            formatting.append(FormatSpan(match.start(), match.end(), 'bold_italic'))
        
        # Find bold formatting
        for match in self.BOLD_PATTERN.finditer(text):
            # Skip if already covered by bold-italic
            overlap = any(
                span.start <= match.start() < span.end or 
                span.start < match.end() <= span.end
                for span in formatting if span.format_type == 'bold_italic'
            )
            if not overlap:
                formatting.append(FormatSpan(match.start(), match.end(), 'bold'))
        
        # Find italic formatting
        for match in self.ITALIC_PATTERN.finditer(text):
            # Skip if already covered by bold-italic
            overlap = any(
                span.start <= match.start() < span.end or 
                span.start < match.end() <= span.end
                for span in formatting if span.format_type in ('bold_italic', 'bold')
            )
            if not overlap:
                formatting.append(FormatSpan(match.start(), match.end(), 'italic'))
        
        # Find underline formatting
        for match in self.UNDERLINE_PATTERN.finditer(text):
            formatting.append(FormatSpan(match.start(), match.end(), 'underline'))
        
        return formatting
    
    def _process_dual_dialogue(self):
        """Post-process elements to pair dual dialogue characters and their dialogue."""
        i = 0
        while i < len(self.elements):
            element = self.elements[i]
            
            # Look for characters marked as dual dialogue
            if (element.type == ElementType.CHARACTER and 
                element.metadata and element.metadata.get('dual_dialogue')):
                
                # Find the previous character and its dialogue block
                prev_char_idx = None
                for j in range(i - 1, -1, -1):
                    if self.elements[j].type == ElementType.CHARACTER:
                        prev_char_idx = j
                        break
                    elif self.elements[j].type in (ElementType.SCENE_HEADING, ElementType.ACTION):
                        # Too far back, no valid pairing
                        break
                
                if prev_char_idx is not None:
                    # Collect dialogue for both characters
                    prev_dialogue = []
                    curr_dialogue = []
                    
                    # Get previous character's dialogue
                    k = prev_char_idx + 1
                    while k < i and self.elements[k].type in (ElementType.DIALOGUE, ElementType.PARENTHETICAL):
                        prev_dialogue.append(self.elements[k])
                        k += 1
                    
                    # Get current character's dialogue
                    k = i + 1
                    while k < len(self.elements) and self.elements[k].type in (ElementType.DIALOGUE, ElementType.PARENTHETICAL):
                        curr_dialogue.append(self.elements[k])
                        k += 1
                    
                    # Create dual dialogue element
                    if prev_dialogue and curr_dialogue:
                        dual_element = FountainElement(
                            type=ElementType.DUAL_DIALOGUE,
                            text="",  # Dual dialogue doesn't have direct text
                            formatting=[],
                            line_number=element.line_number,
                            metadata={
                                'left_character': self.elements[prev_char_idx],
                                'left_dialogue': prev_dialogue,
                                'right_character': element,
                                'right_dialogue': curr_dialogue
                            }
                        )
                        
                        # Replace the range with the dual dialogue element
                        start_idx = prev_char_idx
                        end_idx = i + len(curr_dialogue) + 1
                        self.elements[start_idx:end_idx] = [dual_element]
                        
                        # Adjust index
                        i = start_idx + 1
                        continue
            
            i += 1