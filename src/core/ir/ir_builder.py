"""
Intermediate Representation (IR) Builder

Core data structures for the PLC-RAG system. These structures serve as the
single source of truth between CSV parsing and L5X generation.

Key Design Principles:
- Fully deterministic (no AI/LLM involved)
- Serializable (JSON export for debugging)
- Versioned (track changes)
- Testable (unit tests on structure)
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
import json
from datetime import datetime


class RoutineType(Enum):
    """PLC routine types with priority ordering"""
    SAFETY = ("Safety", 1)
    START_STOP = ("StartStop", 2)
    AUTO = ("Auto", 3)
    FAULT = ("Fault", 4)
    MANUAL = ("Manual", 5)
    CUSTOM = ("Custom", 99)

    def __init__(self, display_name: str, priority: int):
        self.display_name = display_name
        self.priority = priority


class TagType(Enum):
    """PLC tag data types"""
    BOOL = "BOOL"
    DINT = "DINT"
    REAL = "REAL"
    TIMER = "TIMER"
    COUNTER = "COUNTER"
    STRING = "STRING"


@dataclass
class Rung:
    """
    Single ladder logic rung

    Represents one line of logic in a PLC routine. Contains the condition
    (what to check), action (what to do), and the ladder logic instruction.
    """
    number: int
    comment: str
    condition: str      # Human-readable: "NOT EStop AND Safety_OK"
    action: str         # Human-readable: "Motor_Run := 1"
    instruction: str = ""  # L5X format: "XIC EStop XIO Safety_OK OTE Motor_Run"

    # Metadata
    tags_used: List[str] = field(default_factory=list)
    safety_critical: bool = False
    complexity: str = "simple"  # simple, medium, complex

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    def __post_init__(self):
        """Extract tags from condition and action if not provided"""
        if not self.tags_used:
            self.tags_used = self._extract_tags()

    def _extract_tags(self) -> List[str]:
        """Extract tag names from condition and action strings"""
        tags = set()

        # Extract from condition (simple pattern matching)
        import re
        # Match words that look like PLC tags (alphanumeric with underscores)
        pattern = r'\b[A-Z][A-Za-z0-9_]*\b'

        for text in [self.condition, self.action]:
            matches = re.findall(pattern, text)
            tags.update(matches)

        # Remove common keywords
        keywords = {'AND', 'OR', 'NOT', 'IF', 'THEN', 'YES', 'NO'}
        tags = tags - keywords

        return sorted(list(tags))


@dataclass
class Routine:
    """
    PLC Routine (collection of rungs)

    A routine is a grouping of ladder logic rungs that perform a specific
    function (e.g., safety checks, start/stop logic, automatic sequence).
    """
    name: str
    type: RoutineType
    rungs: List[Rung] = field(default_factory=list)

    # Metadata for generation
    priority: int = 99
    expected_lines: int = 0  # Estimated line count for token budget
    description: str = ""

    def __post_init__(self):
        """Set priority from routine type"""
        if isinstance(self.type, RoutineType):
            self.priority = self.type.priority

    @property
    def rung_count(self) -> int:
        """Number of rungs in this routine"""
        return len(self.rungs)

    @property
    def all_tags_used(self) -> List[str]:
        """Get all unique tags used across all rungs"""
        tags = set()
        for rung in self.rungs:
            tags.update(rung.tags_used)
        return sorted(list(tags))

    @property
    def estimated_tokens(self) -> int:
        """Estimate token budget needed for this routine"""
        # Rough estimation: 50-100 tokens per rung
        base_tokens = self.rung_count * 75

        # Add overhead for prompt context
        overhead = 500

        return base_tokens + overhead

    def add_rung(self, rung: Rung):
        """Add a rung to this routine"""
        self.rungs.append(rung)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'type': self.type.display_name,
            'priority': self.priority,
            'rung_count': self.rung_count,
            'expected_lines': self.expected_lines,
            'description': self.description,
            'rungs': [rung.to_dict() for rung in self.rungs],
            'tags_used': self.all_tags_used,
            'estimated_tokens': self.estimated_tokens
        }


@dataclass
class Program:
    """
    PLC Program (collection of routines)

    A program represents a complete machine or subsystem. Contains multiple
    routines organized by type and priority.
    """
    name: str
    routines: List[Routine] = field(default_factory=list)
    description: str = ""

    @property
    def routine_count(self) -> int:
        """Number of routines in this program"""
        return len(self.routines)

    @property
    def total_rungs(self) -> int:
        """Total number of rungs across all routines"""
        return sum(routine.rung_count for routine in self.routines)

    @property
    def sorted_routines(self) -> List[Routine]:
        """Get routines sorted by priority (Safety first, Fault last)"""
        return sorted(self.routines, key=lambda r: r.priority)

    @property
    def all_tags_used(self) -> Dict[str, str]:
        """Get all unique tags used across all routines"""
        tags = set()
        for routine in self.routines:
            tags.update(routine.all_tags_used)

        # Return as dict with inferred types (default to BOOL)
        return {tag: TagType.BOOL.value for tag in sorted(tags)}

    def add_routine(self, routine: Routine):
        """Add a routine to this program"""
        self.routines.append(routine)

    def get_routine_by_type(self, routine_type: RoutineType) -> List[Routine]:
        """Get all routines of a specific type"""
        return [r for r in self.routines if r.type == routine_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'description': self.description,
            'routine_count': self.routine_count,
            'total_rungs': self.total_rungs,
            'routines': [routine.to_dict() for routine in self.sorted_routines],
            'tags': self.all_tags_used
        }


@dataclass
class L5XProject:
    """
    Complete L5X project structure

    The top-level IR structure representing an entire PLC project.
    Contains all programs, routines, rungs, and metadata.
    """
    project_name: str
    programs: List[Program] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)  # {tag_name: tag_type}

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    source_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def program_count(self) -> int:
        """Number of programs in this project"""
        return len(self.programs)

    @property
    def total_routines(self) -> int:
        """Total number of routines across all programs"""
        return sum(program.routine_count for program in self.programs)

    @property
    def total_rungs(self) -> int:
        """Total number of rungs across all programs"""
        return sum(program.total_rungs for program in self.programs)

    @property
    def estimated_lines(self) -> int:
        """Estimate total lines of L5X code that will be generated"""
        # Rough estimation: 15-20 lines per rung (including XML tags)
        rung_lines = self.total_rungs * 18

        # Add overhead for structure (programs, routines, tags)
        overhead = 200 + (self.total_routines * 50) + (len(self.tags) * 5)

        return rung_lines + overhead

    @property
    def estimated_generation_cost(self) -> float:
        """Estimate cost for Claude Sonnet generation"""
        # Claude Sonnet 3.5 pricing
        INPUT_COST_PER_1M = 3.00
        OUTPUT_COST_PER_1M = 15.00

        # Estimate tokens per routine
        total_input_tokens = 0
        total_output_tokens = 0

        for program in self.programs:
            for routine in program.routines:
                # Input: prompt + context + examples (~5000 tokens)
                total_input_tokens += 5000

                # Output: generated rungs (~2000 tokens per routine)
                total_output_tokens += 2000

        input_cost = (total_input_tokens / 1_000_000) * INPUT_COST_PER_1M
        output_cost = (total_output_tokens / 1_000_000) * OUTPUT_COST_PER_1M

        return input_cost + output_cost

    def add_program(self, program: Program):
        """Add a program to this project"""
        self.programs.append(program)

    def extract_all_tags(self):
        """Extract all tags from all programs and update tags dict"""
        all_tags = {}
        for program in self.programs:
            all_tags.update(program.all_tags_used)

        self.tags = all_tags

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'project_name': self.project_name,
            'version': self.version,
            'created_at': self.created_at,
            'source_files': self.source_files,
            'statistics': {
                'programs': self.program_count,
                'routines': self.total_routines,
                'rungs': self.total_rungs,
                'tags': len(self.tags),
                'estimated_lines': self.estimated_lines,
                'estimated_cost_usd': round(self.estimated_generation_cost, 2)
            },
            'programs': [program.to_dict() for program in self.programs],
            'tags': self.tags,
            'metadata': self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Export to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    def save_json(self, filepath: str):
        """Save IR to JSON file for debugging"""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def from_json(cls, json_str: str) -> 'L5XProject':
        """Load IR from JSON string"""
        data = json.loads(json_str)

        # Reconstruct object (simplified - would need full deserialization logic)
        project = cls(
            project_name=data['project_name'],
            version=data.get('version', '1.0'),
            tags=data.get('tags', {}),
            metadata=data.get('metadata', {})
        )

        return project


def create_sample_ir() -> L5XProject:
    """
    Create a sample IR for testing

    Returns a simple L5X project with one program and basic routines.
    """
    # Create project
    project = L5XProject(
        project_name="Sample_Conveyor_System",
        source_files=["sample.csv"]
    )

    # Create program
    program = Program(
        name="Conveyor_C1",
        description="Conveyor belt control logic"
    )

    # Create safety routine
    safety_routine = Routine(
        name="C1_Safety",
        type=RoutineType.SAFETY,
        description="Safety interlock checks"
    )

    # Add safety rungs
    safety_routine.add_rung(Rung(
        number=0,
        comment="Emergency Stop Check",
        condition="NOT EStop",
        action="Safety_OK := TRUE",
        instruction="XIO EStop OTE Safety_OK",
        safety_critical=True
    ))

    safety_routine.add_rung(Rung(
        number=1,
        comment="Door Closed Check",
        condition="Door_Closed AND Safety_OK",
        action="Safety_Clear := TRUE",
        instruction="XIC Door_Closed XIC Safety_OK OTE Safety_Clear",
        safety_critical=True
    ))

    program.add_routine(safety_routine)

    # Create start/stop routine
    start_stop_routine = Routine(
        name="C1_StartStop",
        type=RoutineType.START_STOP,
        description="Manual start and stop controls"
    )

    start_stop_routine.add_rung(Rung(
        number=0,
        comment="Start Conveyor",
        condition="Start_Button AND Safety_Clear",
        action="Motor_Run := TRUE",
        instruction="XIC Start_Button XIC Safety_Clear OTE Motor_Run"
    ))

    start_stop_routine.add_rung(Rung(
        number=1,
        comment="Stop Conveyor",
        condition="Stop_Button",
        action="Motor_Run := FALSE",
        instruction="XIC Stop_Button OTU Motor_Run"
    ))

    program.add_routine(start_stop_routine)

    # Add program to project
    project.add_program(program)

    # Extract tags
    project.extract_all_tags()

    return project


# Validation functions
def validate_ir(project: L5XProject) -> Dict[str, Any]:
    """
    Validate IR structure

    Returns a validation report with any issues found.
    """
    issues = []
    warnings = []

    # Check project has programs
    if not project.programs:
        issues.append("Project has no programs")

    # Check each program
    for program in project.programs:
        # Check program has routines
        if not program.routines:
            issues.append(f"Program '{program.name}' has no routines")
            continue

        # Check for safety routine
        safety_routines = program.get_routine_by_type(RoutineType.SAFETY)
        if not safety_routines:
            warnings.append(f"Program '{program.name}' has no Safety routine")

        # Check each routine
        for routine in program.routines:
            # Check routine has rungs
            if not routine.rungs:
                issues.append(f"Routine '{routine.name}' has no rungs")

            # Check rung numbering
            for i, rung in enumerate(routine.rungs):
                if rung.number != i:
                    warnings.append(
                        f"Routine '{routine.name}' rung numbering mismatch: "
                        f"expected {i}, got {rung.number}"
                    )

    # Check tags are extracted
    if not project.tags:
        warnings.append("No tags extracted - call project.extract_all_tags()")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'statistics': {
            'programs': project.program_count,
            'routines': project.total_routines,
            'rungs': project.total_rungs,
            'tags': len(project.tags)
        }
    }
