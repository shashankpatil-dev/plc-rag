"""
L5X Validator

Validates generated L5X XML for correctness and Studio 5000 compatibility.
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from src.utils.logger import logger


class ValidationIssue:
    """Single validation issue"""

    def __init__(self, severity: str, message: str, location: str = ""):
        self.severity = severity  # "error", "warning", "info"
        self.message = message
        self.location = location

    def __repr__(self):
        return f"{self.severity.upper()}: {self.message}" + (f" ({self.location})" if self.location else "")

    def to_dict(self) -> Dict[str, str]:
        return {
            "severity": self.severity,
            "message": self.message,
            "location": self.location
        }


class L5XValidator:
    """
    Validate L5X XML files

    Checks:
    - XML well-formedness
    - Required L5X structure
    - Tag definitions
    - Basic Rockwell schema compliance
    """

    def validate(self, l5x_content: str) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate L5X content

        Args:
            l5x_content: L5X XML string

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check 1: XML well-formedness
        try:
            root = ET.fromstring(l5x_content)
        except ET.ParseError as e:
            issues.append(ValidationIssue(
                "error",
                f"Invalid XML: {str(e)}",
                "XML parsing"
            ))
            return False, issues

        # Check 2: Root element
        if root.tag != "RSLogix5000Content":
            issues.append(ValidationIssue(
                "error",
                f"Root element must be 'RSLogix5000Content', found '{root.tag}'",
                "Root"
            ))

        # Check 3: Required attributes
        required_attrs = ["SchemaRevision", "SoftwareRevision", "TargetName", "TargetType"]
        for attr in required_attrs:
            if attr not in root.attrib:
                issues.append(ValidationIssue(
                    "warning",
                    f"Missing recommended attribute: {attr}",
                    "Root"
                ))

        # Check 4: Controller element
        controller = root.find("Controller")
        if controller is None:
            issues.append(ValidationIssue(
                "error",
                "Missing Controller element",
                "Structure"
            ))
            return False, issues

        # Check 5: DataTypes section
        datatypes = controller.find("DataTypes")
        if datatypes is not None:
            logger.debug(f"Found {len(datatypes)} data types")
        else:
            issues.append(ValidationIssue(
                "info",
                "No DataTypes section found",
                "Structure"
            ))

        # Check 6: Tags section
        tags = controller.find("Tags")
        if tags is not None:
            logger.debug(f"Found {len(tags)} tags")
        else:
            issues.append(ValidationIssue(
                "warning",
                "No Tags section found",
                "Structure"
            ))

        # Check 7: Programs section
        programs = controller.find("Programs")
        if programs is None:
            issues.append(ValidationIssue(
                "warning",
                "No Programs section found",
                "Structure"
            ))

        # Determine if valid
        has_errors = any(issue.severity == "error" for issue in issues)
        is_valid = not has_errors

        logger.info(f"Validation complete: {'VALID' if is_valid else 'INVALID'} "
                   f"({len([i for i in issues if i.severity == 'error'])} errors, "
                   f"{len([i for i in issues if i.severity == 'warning'])} warnings)")

        return is_valid, issues

    def quick_check(self, l5x_content: str) -> bool:
        """
        Quick validation check (just XML well-formedness)

        Args:
            l5x_content: L5X XML string

        Returns:
            True if valid XML
        """
        try:
            ET.fromstring(l5x_content)
            return True
        except ET.ParseError:
            return False


def validate_l5x(l5x_content: str) -> Tuple[bool, List[ValidationIssue]]:
    """
    Validate L5X content

    Args:
        l5x_content: L5X XML string

    Returns:
        Tuple of (is_valid, issues)
    """
    validator = L5XValidator()
    return validator.validate(l5x_content)
