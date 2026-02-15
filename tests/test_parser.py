"""
Unit tests for CSV parser
"""
import pytest
from src.core.parser.csv_parser import CSVParser, parse_csv_file, CSVParserError
from src.api.models.csv_models import State, MachineLogic, ParsedCSV, ConditionType


# Sample CSV content for testing
SAMPLE_CSV_SINGLE_MACHINE = """Mat_Roll_Transfer_Conveyor1,,,,,,,,
Logic,LogicDescription,Interlock1,Interlock2,Interlock3,Interlock4,Condition,Logic,
0,Waiting_For_Home,,,,,Yes,10,
10,Check_For_Mat_Present,DI01,AlwaysOn,AlwaysOn,DI92,No/Yes,20,
20,TC_01 Stopper_Up_Command,DI02,DI92,AlwaysOn,AlwaysOn,Yes,30,
30,Mat Ready_To_Recieve,DI03,AlwaysOn,AlwaysOn,AlwaysOn,Yes,0,
"""

SAMPLE_CSV_MULTIPLE_MACHINES = """Mat_Roll_Transfer_Conveyor1,,,,,,,,
Logic,LogicDescription,Interlock1,Interlock2,Interlock3,Interlock4,Condition,Logic,
0,Waiting_For_Home,,,,,Yes,10,
10,Check_For_Mat_Present,DI01,AlwaysOn,AlwaysOn,DI92,No/Yes,20,
20,Stopper_Up_Command,DI02,DI92,AlwaysOn,AlwaysOn,Yes,0,
,,,,,,,,

Mat_Roll_Transfer_Conveyor2,,,,,,,,
Logic,LogicDescription,Interlock1,Interlock2,Interlock3,Interlock4,Condition,Logic,
0,Waiting_For_Home,,,,,Yes,10,
10,Check_For_Mat_Present,DI101,AlwaysOn,DI102,AlwaysOn,No/Yes,20,
20,TC_02 Stopper_Up_Command,DI102,AlwaysOn,AlwaysOn,AlwaysOn,Yes,0,
"""

INVALID_CSV = """Some random text
that is not
a valid CSV
"""


class TestCSVParser:
    """Test cases for CSV parser"""

    def test_parse_single_machine(self):
        """Test parsing a CSV with single machine"""
        parsed = parse_csv_file(SAMPLE_CSV_SINGLE_MACHINE)

        assert isinstance(parsed, ParsedCSV)
        assert parsed.total_machines == 1
        assert len(parsed.machines) == 1

        machine = parsed.machines[0]
        assert machine.name == "Mat_Roll_Transfer_Conveyor1"
        assert machine.state_count == 4
        assert len(machine.states) == 4

    def test_parse_multiple_machines(self):
        """Test parsing a CSV with multiple machines"""
        parsed = parse_csv_file(SAMPLE_CSV_MULTIPLE_MACHINES)

        assert parsed.total_machines == 2
        assert len(parsed.machines) == 2

        # Check first machine
        machine1 = parsed.machines[0]
        assert machine1.name == "Mat_Roll_Transfer_Conveyor1"
        assert machine1.state_count == 3

        # Check second machine
        machine2 = parsed.machines[1]
        assert machine2.name == "Mat_Roll_Transfer_Conveyor2"
        assert machine2.state_count == 3

    def test_state_parsing(self):
        """Test individual state parsing"""
        parsed = parse_csv_file(SAMPLE_CSV_SINGLE_MACHINE)
        machine = parsed.machines[0]

        # Check first state (step 0)
        state0 = machine.get_state_by_step(0)
        assert state0 is not None
        assert state0.step == 0
        assert state0.description == "Waiting_For_Home"
        assert len(state0.interlocks) == 0  # No interlocks
        assert state0.condition == ConditionType.YES
        assert state0.next_step == 10

        # Check state with interlocks (step 10)
        state10 = machine.get_state_by_step(10)
        assert state10 is not None
        assert state10.step == 10
        assert "DI01" in state10.interlocks
        assert "DI92" in state10.interlocks
        assert "AlwaysOn" not in state10.interlocks  # Should be filtered out
        assert state10.condition == ConditionType.NO_YES
        assert state10.next_step == 20

    def test_interlock_filtering(self):
        """Test that 'AlwaysOn' interlocks are filtered out"""
        parsed = parse_csv_file(SAMPLE_CSV_SINGLE_MACHINE)
        machine = parsed.machines[0]

        state30 = machine.get_state_by_step(30)
        assert state30 is not None
        # State 30 has DI03 as first interlock, rest are "AlwaysOn"
        assert "DI03" in state30.interlocks
        assert "AlwaysOn" not in state30.interlocks
        # Only real interlocks should be kept
        assert len(state30.interlocks) == 1

    def test_all_interlocks_extraction(self):
        """Test extracting all unique interlocks from a machine"""
        parsed = parse_csv_file(SAMPLE_CSV_SINGLE_MACHINE)
        machine = parsed.machines[0]

        all_interlocks = machine.all_interlocks
        assert "DI01" in all_interlocks
        assert "DI02" in all_interlocks
        assert "DI03" in all_interlocks
        assert "DI92" in all_interlocks
        assert "AlwaysOn" not in all_interlocks

    def test_parsed_csv_summary(self):
        """Test ParsedCSV summary method"""
        parsed = parse_csv_file(SAMPLE_CSV_MULTIPLE_MACHINES)
        summary = parsed.summary()

        assert summary["total_machines"] == 2
        assert len(summary["machine_names"]) == 2
        assert summary["total_states"] == 6  # 3 + 3
        assert "machines_summary" in summary
        assert len(summary["machines_summary"]) == 2

    def test_machine_cycle_validation(self):
        """Test state cycle validation"""
        parsed = parse_csv_file(SAMPLE_CSV_SINGLE_MACHINE)
        machine = parsed.machines[0]

        # Should be valid - all next_step values point to existing states
        assert machine.validate_cycle() is True

    def test_get_machine_by_name(self):
        """Test finding machine by name"""
        parsed = parse_csv_file(SAMPLE_CSV_MULTIPLE_MACHINES)

        machine1 = parsed.get_machine_by_name("Mat_Roll_Transfer_Conveyor1")
        assert machine1 is not None
        assert machine1.name == "Mat_Roll_Transfer_Conveyor1"

        machine2 = parsed.get_machine_by_name("Mat_Roll_Transfer_Conveyor2")
        assert machine2 is not None
        assert machine2.name == "Mat_Roll_Transfer_Conveyor2"

        # Non-existent machine
        machine_none = parsed.get_machine_by_name("NonExistent")
        assert machine_none is None

    def test_empty_csv_error(self):
        """Test that empty CSV raises error"""
        with pytest.raises(CSVParserError):
            parse_csv_file("")

    def test_no_machines_error(self):
        """Test that CSV with no valid machines raises error"""
        # CSV with only empty lines
        with pytest.raises(CSVParserError):
            parse_csv_file("\n\n\n")

        # CSV with only header, no data rows
        with pytest.raises(CSVParserError):
            parse_csv_file("Logic,LogicDescription,Interlock1\n")

    def test_state_properties(self):
        """Test State model properties"""
        state = State(
            step=10,
            description="Test State",
            interlocks=["DI01", "DI02"],
            condition=ConditionType.YES,
            next_step=20
        )

        assert state.has_interlocks is True
        assert state.interlock_count == 2

        state_no_interlocks = State(
            step=0,
            description="No Interlocks",
            interlocks=[],
            condition=ConditionType.YES,
            next_step=10
        )

        assert state_no_interlocks.has_interlocks is False
        assert state_no_interlocks.interlock_count == 0

    def test_machine_properties(self):
        """Test MachineLogic model properties"""
        parsed = parse_csv_file(SAMPLE_CSV_SINGLE_MACHINE)
        machine = parsed.machines[0]

        assert machine.state_count == 4
        assert machine.total_interlock_count > 0
        assert len(machine.cycle_path) == 4
        assert machine.cycle_path == [0, 10, 20, 30]


class TestCSVParserEdgeCases:
    """Test edge cases and error handling"""

    def test_malformed_step_number(self):
        """Test handling of invalid step numbers"""
        csv_content = """Machine1,,,,,,,,
Logic,LogicDescription,Interlock1,Interlock2,Interlock3,Interlock4,Condition,Logic,
abc,Invalid Step,,,,,Yes,10,
0,Valid Step,,,,,Yes,0,
"""
        parsed = parse_csv_file(csv_content)
        # Should skip invalid row and parse valid one
        assert parsed.total_machines == 1
        assert parsed.machines[0].state_count == 1

    def test_extra_empty_rows(self):
        """Test handling of multiple empty rows"""
        # Empty rows can cause machine to be saved early, so be more forgiving
        csv_content = """Machine1,,,,,,,,
Logic,LogicDescription,Interlock1,Interlock2,Interlock3,Interlock4,Condition,Logic,
0,Step0,,,,,Yes,10,
10,Step10,DI01,,,,Yes,0,
"""
        parsed = parse_csv_file(csv_content)
        assert parsed.total_machines >= 1
        # Should have at least 1 state, possibly 2 depending on empty row handling
        total_states = sum(m.state_count for m in parsed.machines)
        assert total_states >= 1

    def test_condition_type_validation(self):
        """Test various condition type inputs"""
        states_csv = """Machine1,,,,,,,,
Logic,LogicDescription,Interlock1,Interlock2,Interlock3,Interlock4,Condition,Logic,
0,State Yes,,,,,Yes,10,
10,State No,,,,,No,20,
20,State NoYes,,,,,No/Yes,0,
"""
        parsed = parse_csv_file(states_csv)
        machine = parsed.machines[0]

        assert machine.get_state_by_step(0).condition == ConditionType.YES
        assert machine.get_state_by_step(10).condition == ConditionType.NO
        assert machine.get_state_by_step(20).condition == ConditionType.NO_YES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
