"""
L5X Skeleton Generator

Generates valid L5X XML structure from IR without LLM involvement.
This is a deterministic, pure Python generator that creates the XML
framework with placeholders for ladder logic.

Key Features:
- Generates valid Rockwell L5X XML structure
- Creates Program/Routine/RLLContent hierarchy
- Inserts placeholders for logic generation
- Declares all tags used in the project
- No AI/LLM involved - 100% deterministic
"""

from typing import Dict, List
from datetime import datetime
from src.core.ir.ir_builder import L5XProject, Program, Routine, TagType
from src.utils.logger import logger


class SkeletonGenerator:
    """
    Generates L5X skeleton from IR

    Creates the complete XML structure with placeholders where
    the LLM will later insert generated ladder logic.
    """

    def __init__(self):
        self.indent_level = 0
        self.indent_str = "  "  # 2 spaces

    def generate(self, ir_project: L5XProject) -> str:
        """
        Generate L5X skeleton from IR

        Args:
            ir_project: Complete IR structure

        Returns:
            L5X XML string with placeholders for logic
        """
        logger.info(f"Generating L5X skeleton for project: {ir_project.project_name}")

        xml_parts = []

        # XML declaration
        xml_parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')

        # Root element
        xml_parts.append(self._generate_root_element(ir_project))

        # Controller element
        xml_parts.append(self._indent(1) + self._generate_controller_open(ir_project))

        # Tags section
        xml_parts.append(self._generate_tags_section(ir_project.tags))

        # Programs section
        xml_parts.append(self._indent(2) + '<Programs>')

        for program in ir_project.programs:
            xml_parts.append(self._generate_program(program))

        xml_parts.append(self._indent(2) + '</Programs>')

        # Close controller
        xml_parts.append(self._indent(1) + '</Controller>')

        # Close root
        xml_parts.append('</RSLogix5000Content>')

        skeleton = '\n'.join(xml_parts)

        logger.info(f"✅ Skeleton generated: {len(skeleton):,} characters")

        return skeleton

    def _generate_root_element(self, ir_project: L5XProject) -> str:
        """Generate RSLogix5000Content root element"""
        return (
            '<RSLogix5000Content '
            'SchemaRevision="1.0" '
            'SoftwareRevision="33.00" '
            f'TargetName="{ir_project.project_name}" '
            'TargetType="Controller" '
            'ContainsContext="false" '
            f'ExportDate="{datetime.now().strftime("%a %b %d %H:%M:%S %Y")}" '
            'ExportOptions="References NoRawData L5KData DecoratedData ForceProtectedEncoding AllProjDocTrans">'
        )

    def _generate_controller_open(self, ir_project: L5XProject) -> str:
        """Generate Controller opening tag"""
        return (
            f'<Controller Use="Target" Name="{ir_project.project_name}" '
            'ProcessorType="1769-L18ER-BB1B" '
            'MajorRev="33" MinorRev="11" TimeSlice="20" ShareUnusedTimeSlice="1" '
            f'ProjectCreationDate="{datetime.now().strftime("%a %b %d %H:%M:%S %Y")}" '
            f'LastModifiedDate="{datetime.now().strftime("%a %b %d %H:%M:%S %Y")}" '
            'SFCExecutionControl="CurrentActive" SFCRestartPosition="MostRecent" '
            'SFCLastScan="DontScan" ProjectSN="16#0000_0000" '
            'MatchProjectToController="false" CanUseRPIFromProducer="false" '
            'InhibitAutomaticFirmwareUpdate="0">'
        )

    def _generate_tags_section(self, tags: Dict[str, str]) -> str:
        """Generate tags section with all tag declarations"""
        lines = []

        lines.append(self._indent(2) + '<Tags>')

        for tag_name, tag_type in sorted(tags.items()):
            lines.append(
                self._indent(3) +
                f'<Tag Name="{tag_name}" TagType="Base" DataType="{tag_type}" '
                'Radix="Decimal" Constant="false" ExternalAccess="Read/Write">'
            )
            lines.append(self._indent(4) + '<Description>')
            lines.append(self._indent(5) + f'<![CDATA[Auto-generated tag for {tag_name}]]>')
            lines.append(self._indent(4) + '</Description>')
            lines.append(self._indent(4) + f'<Data Format="L5K">')
            lines.append(self._indent(5) + '<![CDATA[0]]>')  # Default value
            lines.append(self._indent(4) + '</Data>')
            lines.append(self._indent(3) + '</Tag>')

        lines.append(self._indent(2) + '</Tags>')

        return '\n'.join(lines)

    def _generate_program(self, program: Program) -> str:
        """Generate a single Program element"""
        lines = []

        # Program opening tag
        lines.append(
            self._indent(3) +
            f'<Program Use="Target" Name="{program.name}" '
            'TestEdits="false" MainRoutineName="" Disabled="false" UseAsFolder="false">'
        )

        # Description
        if program.description:
            lines.append(self._indent(4) + '<Description>')
            lines.append(self._indent(5) + f'<![CDATA[{program.description}]]>')
            lines.append(self._indent(4) + '</Description>')

        # Routines section
        lines.append(self._indent(4) + '<Routines>')

        for routine in program.sorted_routines:
            lines.append(self._generate_routine(routine))

        lines.append(self._indent(4) + '</Routines>')

        # Program closing tag
        lines.append(self._indent(3) + '</Program>')

        return '\n'.join(lines)

    def _generate_routine(self, routine: Routine) -> str:
        """Generate a single Routine element with placeholder for logic"""
        lines = []

        # Routine opening tag
        lines.append(
            self._indent(5) +
            f'<Routine Use="Target" Name="{routine.name}" Type="RLL">'
        )

        # Description
        if routine.description:
            lines.append(self._indent(6) + '<Description>')
            lines.append(self._indent(7) + f'<![CDATA[{routine.description}]]>')
            lines.append(self._indent(6) + '</Description>')

        # RLL Content with placeholder
        lines.append(self._indent(6) + '<RLLContent>')

        # PLACEHOLDER for LLM-generated rungs
        placeholder = f"LOGIC_PLACEHOLDER_{routine.name}"
        lines.append(self._indent(7) + f'<!-- {placeholder} -->')

        # Add comment about what will be generated here
        lines.append(
            self._indent(7) +
            f'<!-- This routine will contain {routine.rung_count} rung(s) -->'
        )
        lines.append(
            self._indent(7) +
            f'<!-- Type: {routine.type.display_name} | Priority: {routine.priority} -->'
        )

        lines.append(self._indent(6) + '</RLLContent>')

        # Routine closing tag
        lines.append(self._indent(5) + '</Routine>')

        return '\n'.join(lines)

    def _indent(self, level: int) -> str:
        """Generate indentation string"""
        return self.indent_str * level


def generate_skeleton(ir_project: L5XProject) -> str:
    """
    Convenience function to generate skeleton from IR

    Args:
        ir_project: Complete IR structure

    Returns:
        L5X XML skeleton string
    """
    generator = SkeletonGenerator()
    return generator.generate(ir_project)


def get_placeholder_name(routine_name: str) -> str:
    """
    Get the placeholder name for a routine

    Used by assembler to know what to replace.

    Args:
        routine_name: Name of the routine

    Returns:
        Placeholder string
    """
    return f"LOGIC_PLACEHOLDER_{routine_name}"


def extract_placeholders(skeleton: str) -> List[str]:
    """
    Extract all placeholder names from skeleton

    Args:
        skeleton: L5X skeleton XML

    Returns:
        List of placeholder names
    """
    import re

    pattern = r'<!-- (LOGIC_PLACEHOLDER_\w+) -->'
    matches = re.findall(pattern, skeleton)

    return matches


def validate_skeleton_xml(skeleton: str) -> Dict[str, any]:
    """
    Validate that skeleton is valid XML

    Args:
        skeleton: L5X skeleton string

    Returns:
        Validation result dict
    """
    import xml.etree.ElementTree as ET

    issues = []

    # Check XML validity
    try:
        ET.fromstring(skeleton)
    except ET.ParseError as e:
        issues.append(f"Invalid XML: {e}")

    # Check for required elements
    required_elements = [
        '<RSLogix5000Content',
        '<Controller',
        '<Programs>',
        '</Programs>',
        '</Controller>',
        '</RSLogix5000Content>'
    ]

    for element in required_elements:
        if element not in skeleton:
            issues.append(f"Missing required element: {element}")

    # Check for placeholders
    placeholders = extract_placeholders(skeleton)
    if not placeholders:
        issues.append("No placeholders found - skeleton cannot be used for generation")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'placeholder_count': len(placeholders),
        'placeholders': placeholders,
        'size_bytes': len(skeleton.encode('utf-8'))
    }
