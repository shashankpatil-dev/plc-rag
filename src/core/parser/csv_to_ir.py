"""
CSV to IR Converter

Converts parsed CSV data (from csv_parser.py) into Intermediate Representation (IR).

This module bridges the gap between raw CSV parsing and structured IR, performing:
- State grouping into routines (Safety, StartStop, Auto, Fault)
- Tag extraction from conditions
- Routine priority assignment
- Logic transformation from CSV to IR format
"""

from typing import List, Dict, Optional
from src.api.models.csv_models import ParsedCSV, MachineLogic, State, ConditionType
from src.core.ir.ir_builder import (
    L5XProject,
    Program,
    Routine,
    Rung,
    RoutineType
)
from src.utils.logger import logger


class CSVToIRConverter:
    """
    Converts parsed CSV data into Intermediate Representation

    Takes the output from CSVParser and creates a structured IR
    that can be used for L5X generation.
    """

    def __init__(self):
        self.routine_type_mapping = {
            'safety': RoutineType.SAFETY,
            'start': RoutineType.START_STOP,
            'stop': RoutineType.START_STOP,
            'auto': RoutineType.AUTO,
            'fault': RoutineType.FAULT,
            'manual': RoutineType.MANUAL,
        }

    def convert(self, parsed_csv: ParsedCSV, project_name: Optional[str] = None) -> L5XProject:
        """
        Convert parsed CSV to IR

        Args:
            parsed_csv: Output from CSVParser
            project_name: Optional project name (defaults to first machine name)

        Returns:
            L5XProject IR structure
        """
        logger.info(f"Converting {len(parsed_csv.machines)} machine(s) to IR...")

        # Create project
        if not project_name and parsed_csv.machines:
            project_name = f"{parsed_csv.machines[0].name}_Project"

        project = L5XProject(
            project_name=project_name or "Generated_PLC_Project",
            source_files=["input.csv"]  # Can be updated by caller
        )

        # Convert each machine to a program
        for machine in parsed_csv.machines:
            program = self._convert_machine_to_program(machine)
            project.add_program(program)

        # Extract all tags
        project.extract_all_tags()

        logger.info(f"✅ IR created: {project.program_count} programs, "
                   f"{project.total_routines} routines, {project.total_rungs} rungs")

        return project

    def _convert_machine_to_program(self, machine: MachineLogic) -> Program:
        """
        Convert a single machine to a Program

        Groups states into routines based on description patterns.
        """
        logger.info(f"Converting machine '{machine.name}' with {len(machine.states)} states")

        program = Program(
            name=self._sanitize_name(machine.name),
            description=f"Auto-generated logic for {machine.name}"
        )

        # Group states into routines
        routine_groups = self._group_states_into_routines(machine.states)

        # Convert each group to a routine
        for routine_type, states in routine_groups.items():
            if states:
                routine = self._create_routine(
                    machine_name=machine.name,
                    routine_type=routine_type,
                    states=states
                )
                program.add_routine(routine)

        logger.info(f"  Created {program.routine_count} routines for '{machine.name}'")

        return program

    def _group_states_into_routines(self, states: List[State]) -> Dict[RoutineType, List[State]]:
        """
        Group states into routines based on logic patterns

        Analyzes state descriptions to determine routine type:
        - Safety checks → Safety routine
        - Start/Stop conditions → StartStop routine
        - Sequential operations → Auto routine
        - Error handling → Fault routine
        """
        groups = {
            RoutineType.SAFETY: [],
            RoutineType.START_STOP: [],
            RoutineType.AUTO: [],
            RoutineType.FAULT: [],
        }

        for state in states:
            routine_type = self._classify_state(state)
            groups[routine_type].append(state)

        return groups

    def _classify_state(self, state: State) -> RoutineType:
        """
        Classify a state into a routine type based on description

        Uses pattern matching on the description string.
        """
        desc_lower = state.description.lower()

        # Safety patterns
        if any(keyword in desc_lower for keyword in
               ['safety', 'estop', 'e-stop', 'door', 'guard', 'interlock']):
            return RoutineType.SAFETY

        # Start/Stop patterns
        if any(keyword in desc_lower for keyword in
               ['start', 'stop', 'enable', 'disable', 'reset']):
            return RoutineType.START_STOP

        # Fault patterns
        if any(keyword in desc_lower for keyword in
               ['fault', 'error', 'alarm', 'jam', 'timeout']):
            return RoutineType.FAULT

        # Default to Auto for sequential operations
        return RoutineType.AUTO

    def _create_routine(
        self,
        machine_name: str,
        routine_type: RoutineType,
        states: List[State]
    ) -> Routine:
        """
        Create a Routine from a group of states

        Converts each state into one or more rungs.
        """
        routine_name = f"{self._sanitize_name(machine_name)}_{routine_type.display_name}"

        routine = Routine(
            name=routine_name,
            type=routine_type,
            description=f"{routine_type.display_name} logic for {machine_name}"
        )

        # Convert each state to rung(s)
        for state in states:
            rungs = self._convert_state_to_rungs(state)
            for rung in rungs:
                routine.add_rung(rung)

        # Estimate lines for token budgeting
        routine.expected_lines = len(routine.rungs) * 18  # ~18 lines per rung in L5X

        logger.debug(f"    Routine '{routine_name}': {routine.rung_count} rungs")

        return routine

    def _convert_state_to_rungs(self, state: State) -> List[Rung]:
        """
        Convert a single CSV state into one or more ladder logic rungs

        A state might generate multiple rungs if it has complex logic.
        """
        rungs = []

        # Build condition string from interlocks
        condition = self._build_condition_string(state)

        # Build action string based on next_step
        action = self._build_action_string(state)

        # Create main rung
        rung = Rung(
            number=len(rungs),
            comment=state.description,
            condition=condition,
            action=action,
            instruction="",  # Will be generated by LLM
            safety_critical=(state.description.lower().find('safety') >= 0)
        )

        rungs.append(rung)

        # Additional rungs for complex logic (future enhancement)
        # Could add timer rungs, counter rungs, etc.

        return rungs

    def _build_condition_string(self, state: State) -> str:
        """
        Build human-readable condition string from state

        Combines interlocks with AND logic.
        """
        conditions = []

        # Add interlocks
        for interlock in state.interlocks:
            # Simple tag name (could be enhanced with NOT logic detection)
            conditions.append(interlock)

        # Add condition type logic
        if state.condition == ConditionType.NO:
            conditions.append("Condition_False")
        elif state.condition == ConditionType.NO_YES:
            conditions.append("Condition_Toggle")

        if not conditions:
            return "AlwaysOn"

        # Combine with AND
        return " AND ".join(conditions)

    def _build_action_string(self, state: State) -> str:
        """
        Build action string from state

        Determines what happens when conditions are met.
        """
        if state.next_step == 0:
            # End state
            return "Sequence_Complete"
        else:
            # Transition to next step
            return f"Step_{state.next_step}_Enable"

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize name for PLC use

        Removes invalid characters and ensures valid PLC naming.
        """
        # Replace spaces and special chars with underscores
        sanitized = name.replace(' ', '_')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')

        # Ensure doesn't start with number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"M_{sanitized}"

        return sanitized


def csv_to_ir(parsed_csv: ParsedCSV, project_name: Optional[str] = None) -> L5XProject:
    """
    Convenience function to convert CSV to IR

    Args:
        parsed_csv: Parsed CSV data
        project_name: Optional project name

    Returns:
        L5XProject IR structure
    """
    converter = CSVToIRConverter()
    return converter.convert(parsed_csv, project_name)
