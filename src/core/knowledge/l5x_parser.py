"""
L5X File Parser

Parses Rockwell L5X files to extract routines, rungs, and metadata
for building the knowledge base.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from src.utils.logger import logger


@dataclass
class ParsedRung:
    """Single rung extracted from L5X"""
    number: int
    comment: str
    text: str  # Ladder logic text
    type: str  # N, R, etc.

    # Metadata
    instructions: List[str] = field(default_factory=list)  # XIC, XIO, OTE, etc.
    tags_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'number': self.number,
            'comment': self.comment,
            'text': self.text,
            'type': self.type,
            'instructions': self.instructions,
            'tags_used': self.tags_used
        }


@dataclass
class ParsedRoutine:
    """Single routine extracted from L5X"""
    name: str
    type: str  # RLL, SFC, ST
    description: str
    rungs: List[ParsedRung] = field(default_factory=list)

    # Metadata
    source_file: str = ""
    rung_count: int = 0
    instructions_used: List[str] = field(default_factory=list)
    tags_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'rung_count': self.rung_count,
            'source_file': self.source_file,
            'instructions_used': list(set(self.instructions_used)),
            'tags_used': list(set(self.tags_used)),
            'rungs': [rung.to_dict() for rung in self.rungs]
        }

    def to_text(self) -> str:
        """Convert routine to searchable text"""
        lines = []
        lines.append(f"Routine: {self.name}")
        lines.append(f"Description: {self.description}")
        lines.append(f"Type: {self.type}")
        lines.append(f"Rungs: {self.rung_count}")
        lines.append("")

        for rung in self.rungs:
            lines.append(f"Rung {rung.number}: {rung.comment}")
            lines.append(f"  Logic: {rung.text}")
            lines.append("")

        return "\n".join(lines)


class L5XParser:
    """
    Parses L5X files to extract routines and rungs

    Handles:
    - Full PLC projects
    - Exported routines
    - AOI definitions
    """

    def __init__(self):
        self.routines: List[ParsedRoutine] = []

    def parse_file(self, file_path: str) -> List[ParsedRoutine]:
        """
        Parse an L5X file

        Args:
            file_path: Path to L5X file

        Returns:
            List of parsed routines
        """
        logger.info(f"Parsing L5X file: {Path(file_path).name}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            self.routines = []

            # Find all routines in the file
            # Routines can be in different locations depending on export type
            routines = root.findall('.//Routine')

            for routine_elem in routines:
                routine = self._parse_routine(routine_elem, Path(file_path).name)
                if routine and routine.rungs:  # Only add routines with rungs
                    self.routines.append(routine)

            logger.info(f"✅ Extracted {len(self.routines)} routine(s) from {Path(file_path).name}")

            return self.routines

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []

    def _parse_routine(self, routine_elem: ET.Element, source_file: str) -> Optional[ParsedRoutine]:
        """Parse a single Routine element"""
        try:
            # Get routine attributes
            name = routine_elem.get('Name', 'Unknown')
            routine_type = routine_elem.get('Type', 'RLL')

            # Get description
            desc_elem = routine_elem.find('Description')
            description = ""
            if desc_elem is not None:
                cdata = desc_elem.find('.')
                if cdata is not None and cdata.text:
                    description = cdata.text.strip()

            # Create routine
            routine = ParsedRoutine(
                name=name,
                type=routine_type,
                description=description,
                source_file=source_file
            )

            # Parse RLL content (ladder logic)
            if routine_type == 'RLL':
                rll_content = routine_elem.find('RLLContent')
                if rll_content is not None:
                    rungs = rll_content.findall('Rung')
                    for rung_elem in rungs:
                        rung = self._parse_rung(rung_elem)
                        if rung:
                            routine.rungs.append(rung)

                            # Collect metadata
                            routine.instructions_used.extend(rung.instructions)
                            routine.tags_used.extend(rung.tags_used)

            routine.rung_count = len(routine.rungs)

            return routine

        except Exception as e:
            logger.warning(f"Failed to parse routine: {e}")
            return None

    def _parse_rung(self, rung_elem: ET.Element) -> Optional[ParsedRung]:
        """Parse a single Rung element"""
        try:
            # Get rung attributes
            number = int(rung_elem.get('Number', 0))
            rung_type = rung_elem.get('Type', 'N')

            # Get comment
            comment_elem = rung_elem.find('Comment')
            comment = ""
            if comment_elem is not None:
                cdata = comment_elem.find('.')
                if cdata is not None and cdata.text:
                    comment = cdata.text.strip()

            # Get ladder logic text
            text_elem = rung_elem.find('Text')
            text = ""
            if text_elem is not None:
                cdata = text_elem.find('.')
                if cdata is not None and cdata.text:
                    text = cdata.text.strip()

            # Create rung
            rung = ParsedRung(
                number=number,
                comment=comment,
                text=text,
                type=rung_type
            )

            # Extract instructions and tags
            if text:
                rung.instructions = self._extract_instructions(text)
                rung.tags_used = self._extract_tags(text)

            return rung

        except Exception as e:
            logger.warning(f"Failed to parse rung: {e}")
            return None

    def _extract_instructions(self, ladder_text: str) -> List[str]:
        """Extract PLC instructions from ladder logic text"""
        import re

        # Common Rockwell instructions
        instructions = []

        # Pattern: INSTRUCTION(tag) or INSTRUCTION
        patterns = [
            r'\b(XIC|XIO|OTE|OTL|OTU|OSR|OSF)\b',  # Basic
            r'\b(TON|TOF|RTO|CTU|CTD|RES)\b',       # Timers/Counters
            r'\b(EQU|NEQ|GRT|GEQ|LES|LEQ)\b',       # Compares
            r'\b(ADD|SUB|MUL|DIV|MOD)\b',           # Math
            r'\b(MOV|CLR|CPT|COP)\b',               # Data movement
            r'\b(JSR|RET|SBR|JMP|LBL)\b',           # Program control
        ]

        for pattern in patterns:
            matches = re.findall(pattern, ladder_text)
            instructions.extend(matches)

        return list(set(instructions))  # Unique instructions

    def _extract_tags(self, ladder_text: str) -> List[str]:
        """Extract tag names from ladder logic text"""
        import re

        # Pattern: matches tags in parentheses
        # Example: XIC(Motor_Run) → Motor_Run
        pattern = r'\(([A-Za-z_][A-Za-z0-9_\.]*)\)'
        matches = re.findall(pattern, ladder_text)

        return list(set(matches))  # Unique tags


def parse_l5x_directory(directory_path: str) -> List[ParsedRoutine]:
    """
    Parse all L5X files in a directory

    Args:
        directory_path: Path to directory containing L5X files

    Returns:
        List of all parsed routines from all files
    """
    parser = L5XParser()
    all_routines = []

    l5x_files = list(Path(directory_path).glob('*.L5X'))

    logger.info(f"Found {len(l5x_files)} L5X file(s)")

    for l5x_file in l5x_files:
        routines = parser.parse_file(str(l5x_file))
        all_routines.extend(routines)

    logger.info(f"✅ Total routines extracted: {len(all_routines)}")

    return all_routines
