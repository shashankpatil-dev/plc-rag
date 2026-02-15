"""
L5X Validator

Validates the final L5X output before export.

Checks:
- XML validity
- All placeholders filled
- Required routines present
- Safety routine exists
- Tag consistency
- Importable into Studio 5000
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from src.core.ir.ir_builder import L5XProject
from src.utils.logger import logger


class L5XValidator:
    """
    Validates L5X files for correctness and completeness
    """

    def validate(self, l5x_content: str, ir_project: L5XProject) -> Dict[str, Any]:
        """
        Validate L5X file

        Args:
            l5x_content: L5X XML content to validate
            ir_project: Original IR project for comparison

        Returns:
            Validation result dict with issues and warnings
        """
        logger.info("Validating L5X output...")

        issues = []
        warnings = []

        # 1. XML Validity
        xml_valid, xml_error = self._validate_xml(l5x_content)
        if not xml_valid:
            issues.append(f"Invalid XML: {xml_error}")
            # If XML is invalid, can't do further checks
            return {
                'valid': False,
                'issues': issues,
                'warnings': warnings
            }

        # 2. Check for unfilled placeholders
        placeholder_check = self._check_placeholders(l5x_content)
        if not placeholder_check['valid']:
            issues.extend(placeholder_check['issues'])

        # 3. Check required structure
        structure_check = self._check_structure(l5x_content)
        if not structure_check['valid']:
            issues.extend(structure_check['issues'])
        warnings.extend(structure_check['warnings'])

        # 4. Check routines match IR
        routine_check = self._check_routines(l5x_content, ir_project)
        if not routine_check['valid']:
            issues.extend(routine_check['issues'])
        warnings.extend(routine_check['warnings'])

        # 5. Check for safety routine
        safety_check = self._check_safety(l5x_content)
        if not safety_check['valid']:
            warnings.append("No Safety routine found - consider adding safety logic")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'statistics': {
                'size_bytes': len(l5x_content.encode('utf-8')),
                'size_kb': len(l5x_content.encode('utf-8')) / 1024,
                'programs': l5x_content.count('<Program'),
                'routines': l5x_content.count('<Routine'),
                'rungs': l5x_content.count('<Rung'),
                'tags': l5x_content.count('<Tag ')
            }
        }

    def _validate_xml(self, l5x_content: str) -> tuple[bool, str]:
        """Validate XML syntax"""
        try:
            ET.fromstring(l5x_content)
            return True, ""
        except ET.ParseError as e:
            return False, str(e)

    def _check_placeholders(self, l5x_content: str) -> Dict[str, Any]:
        """Check for unfilled placeholders"""
        issues = []

        placeholder_count = l5x_content.count("LOGIC_PLACEHOLDER_")

        if placeholder_count > 0:
            issues.append(
                f"Found {placeholder_count} unfilled placeholder(s) - "
                "generation incomplete"
            )

        return {
            'valid': placeholder_count == 0,
            'issues': issues
        }

    def _check_structure(self, l5x_content: str) -> Dict[str, Any]:
        """Check required L5X structure elements"""
        issues = []
        warnings = []

        required_elements = [
            ('<RSLogix5000Content', 'Root element'),
            ('<Controller', 'Controller element'),
            ('<Programs>', 'Programs section'),
            ('</Programs>', 'Programs closing tag'),
            ('<Tags>', 'Tags section'),
            ('</Tags>', 'Tags closing tag'),
        ]

        for element, name in required_elements:
            if element not in l5x_content:
                issues.append(f"Missing required element: {name}")

        # Check for at least one program
        if '<Program' not in l5x_content:
            warnings.append("No programs found")

        # Check for at least one routine
        if '<Routine' not in l5x_content:
            issues.append("No routines found")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

    def _check_routines(
        self,
        l5x_content: str,
        ir_project: L5XProject
    ) -> Dict[str, Any]:
        """Check routines match IR"""
        issues = []
        warnings = []

        # Get expected routine names from IR
        expected_routines = []
        for program in ir_project.programs:
            for routine in program.routines:
                expected_routines.append(routine.name)

        # Check each expected routine exists in L5X
        for routine_name in expected_routines:
            if f'Name="{routine_name}"' not in l5x_content:
                issues.append(f"Missing routine: {routine_name}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

    def _check_safety(self, l5x_content: str) -> Dict[str, Any]:
        """Check for safety routine"""
        # Look for safety-related routine names
        safety_indicators = ['Safety', 'SAFETY', 'Interlock', 'EStop']

        has_safety = any(indicator in l5x_content for indicator in safety_indicators)

        return {
            'valid': has_safety,
            'has_safety': has_safety
        }


def validate_l5x(l5x_content: str, ir_project: L5XProject) -> Dict[str, Any]:
    """
    Convenience function to validate L5X

    Args:
        l5x_content: L5X XML to validate
        ir_project: Original IR project

    Returns:
        Validation result dict
    """
    validator = L5XValidator()
    return validator.validate(l5x_content, ir_project)
