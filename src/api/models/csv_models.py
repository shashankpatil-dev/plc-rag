"""
Pydantic models for CSV logic sheet data structures
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


class ConditionType(str, Enum):
    """Condition types for state transitions"""
    YES = "Yes"
    NO = "No"
    NO_YES = "No/Yes"


class State(BaseModel):
    """
    Represents a single state in the PLC state machine

    Each state has a step number, description, interlocks (sensor conditions),
    a condition flag, and the next step to transition to.
    """
    step: int = Field(..., description="Step number (0, 10, 20, etc.)", ge=0)
    description: str = Field(..., description="Human-readable description of this state")
    interlocks: List[str] = Field(
        default_factory=list,
        description="List of sensor/interlock tags (e.g., DI01, DI02). Empty if no interlocks."
    )
    condition: ConditionType = Field(..., description="Condition type for this state")
    next_step: int = Field(..., description="Next step number in sequence", ge=0)

    @field_validator('interlocks', mode='before')
    @classmethod
    def filter_interlocks(cls, v):
        """Remove 'AlwaysOn' and empty values from interlocks"""
        if not isinstance(v, list):
            return []
        # Filter out AlwaysOn, empty strings, and None values
        return [
            interlock for interlock in v
            if interlock and interlock.strip() and interlock.strip().lower() != "alwayson"
        ]

    @property
    def has_interlocks(self) -> bool:
        """Check if this state has any interlocks"""
        return len(self.interlocks) > 0

    @property
    def interlock_count(self) -> int:
        """Count of active interlocks"""
        return len(self.interlocks)


class MachineLogic(BaseModel):
    """
    Represents a complete state machine for one conveyor/machine

    Contains the machine name and all its states in sequence.
    """
    name: str = Field(..., description="Machine/conveyor name", min_length=1, max_length=100)
    states: List[State] = Field(..., description="List of all states in this machine", min_length=1)

    @property
    def state_count(self) -> int:
        """Total number of states"""
        return len(self.states)

    @property
    def all_interlocks(self) -> List[str]:
        """Get all unique interlock tags used across all states"""
        interlocks = set()
        for state in self.states:
            interlocks.update(state.interlocks)
        return sorted(list(interlocks))

    @property
    def total_interlock_count(self) -> int:
        """Count of unique interlocks"""
        return len(self.all_interlocks)

    @property
    def cycle_path(self) -> List[int]:
        """Get the sequence of step numbers in order"""
        return [state.step for state in self.states]

    def get_state_by_step(self, step: int) -> Optional[State]:
        """Get a state by its step number"""
        for state in self.states:
            if state.step == step:
                return state
        return None

    def validate_cycle(self) -> bool:
        """
        Validate that state transitions form a valid cycle
        Returns True if all next_step values point to existing states
        """
        step_numbers = {state.step for state in self.states}
        for state in self.states:
            if state.next_step not in step_numbers:
                return False
        return True


class ParsedCSV(BaseModel):
    """
    Represents the complete parsed CSV file containing multiple machines

    This is the top-level model returned by the parser.
    """
    machines: List[MachineLogic] = Field(..., description="List of all machines found in CSV")
    total_machines: int = Field(..., description="Total number of machines parsed")

    @field_validator('total_machines', mode='before')
    @classmethod
    def set_total_machines(cls, v, info):
        """Auto-calculate total machines from list"""
        machines = info.data.get('machines', [])
        return len(machines)

    @property
    def machine_names(self) -> List[str]:
        """Get list of all machine names"""
        return [machine.name for machine in self.machines]

    @property
    def total_states(self) -> int:
        """Total number of states across all machines"""
        return sum(machine.state_count for machine in self.machines)

    @property
    def all_interlocks(self) -> List[str]:
        """Get all unique interlocks across all machines"""
        interlocks = set()
        for machine in self.machines:
            interlocks.update(machine.all_interlocks)
        return sorted(list(interlocks))

    def get_machine_by_name(self, name: str) -> Optional[MachineLogic]:
        """Get a machine by its name"""
        for machine in self.machines:
            if machine.name == name:
                return machine
        return None

    def summary(self) -> dict:
        """Get a summary of the parsed CSV"""
        return {
            "total_machines": self.total_machines,
            "machine_names": self.machine_names,
            "total_states": self.total_states,
            "total_unique_interlocks": len(self.all_interlocks),
            "machines_summary": [
                {
                    "name": m.name,
                    "states": m.state_count,
                    "interlocks": m.total_interlock_count,
                    "cycle_valid": m.validate_cycle()
                }
                for m in self.machines
            ]
        }


class UploadResponse(BaseModel):
    """Response model for CSV upload endpoint"""
    status: str = Field(..., description="Upload status (success/error)")
    message: str = Field(..., description="Status message")
    filename: Optional[str] = Field(None, description="Uploaded filename")
    parsed_data: Optional[ParsedCSV] = Field(None, description="Parsed CSV data")
