"""
CSV Parser for PLC Logic Sheets

Parses CSV files containing state machine definitions for PLC conveyors.
Handles the LogicSheet format with multiple machines per file.
"""
import csv
import io
from typing import List, Optional
from src.api.models.csv_models import State, MachineLogic, ParsedCSV, ConditionType
from src.config.constants import ALWAYS_ON, NO_INTERLOCK_VALUES
from src.utils.logger import logger


class CSVParserError(Exception):
    """Custom exception for CSV parsing errors"""
    pass


class CSVParser:
    """
    Parser for PLC logic sheet CSV files

    Expected CSV format:
    - Machine name on first line
    - Header row: Logic, LogicDescription, Interlock1, Interlock2, ..., Condition, Logic
    - Data rows: step_number, description, interlock1, ..., condition, next_step
    - Empty rows separate machines
    """

    def __init__(self):
        self.machines: List[MachineLogic] = []
        self.current_machine_name: Optional[str] = None
        self.current_states: List[State] = []

    def parse(self, csv_content: str) -> ParsedCSV:
        """
        Parse CSV content and return structured data

        Args:
            csv_content: String content of the CSV file

        Returns:
            ParsedCSV object with all machines and their states

        Raises:
            CSVParserError: If CSV format is invalid
        """
        logger.info("Starting CSV parsing...")
        self.machines = []
        self.current_machine_name = None
        self.current_states = []

        try:
            # Parse CSV content
            csv_file = io.StringIO(csv_content)
            reader = csv.reader(csv_file)

            for row_num, row in enumerate(reader, start=1):
                try:
                    self._process_row(row, row_num)
                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {e}")
                    # Continue processing other rows
                    continue

            # Save last machine if exists
            self._save_current_machine()

            if not self.machines:
                raise CSVParserError("No valid machines found in CSV")

            logger.info(f"Successfully parsed {len(self.machines)} machine(s)")
            return ParsedCSV(
                machines=self.machines,
                total_machines=len(self.machines)
            )

        except Exception as e:
            logger.error(f"CSV parsing failed: {e}")
            raise CSVParserError(f"Failed to parse CSV: {str(e)}")

    def _process_row(self, row: List[str], row_num: int):
        """Process a single CSV row"""
        # Skip empty rows
        if not row or all(not cell.strip() for cell in row):
            # Empty row might indicate end of machine - save if we have data
            if self.current_states:
                self._save_current_machine()
            return

        first_col = row[0].strip() if row else ""

        # Check if this is a machine name row
        if first_col and not first_col.isdigit() and first_col.lower() != "logic":
            # New machine starting
            if self.current_states:
                self._save_current_machine()
            self.current_machine_name = first_col
            logger.debug(f"Found machine: {self.current_machine_name}")
            return

        # Skip header rows
        if first_col.lower() == "logic":
            return

        # Parse state data row
        if first_col.isdigit():
            try:
                state = self._parse_state_row(row)
                if state and self.current_machine_name:
                    self.current_states.append(state)
                    logger.debug(f"Parsed state {state.step}: {state.description}")
            except Exception as e:
                logger.warning(f"Could not parse state from row {row_num}: {e}")

    def _parse_state_row(self, row: List[str]) -> Optional[State]:
        """
        Parse a single state from a CSV row

        Expected CSV format (with trailing comma):
        Logic,LogicDescription,Interlock1,Interlock2,Interlock3,Interlock4,Condition,Logic,
        0,Waiting_For_Home,,,,,Yes,10,

        Row indices:
        [0]: step number
        [1]: description
        [2-5]: interlocks (4 columns) - may have 5 interlocks in some machines
        [6 or 7]: condition (depends on number of interlock columns)
        [7 or 8]: next_step
        [8 or 9]: empty (trailing comma)
        """
        if len(row) < 3:
            return None

        try:
            # Extract step number
            step = int(row[0].strip())

            # Extract description
            description = row[1].strip() if len(row) > 1 else f"Step_{step}"

            # Determine format based on row length
            # Standard format: 9 columns (4 interlocks) or 10 columns (5 interlocks)
            if len(row) >= 9:
                # Interlocks are in columns 2-5 (or 2-6 for 5 interlocks)
                # Find where condition starts (it's always "Yes", "No", or "No/Yes")
                condition_idx = None
                for i in range(len(row) - 3, 1, -1):  # Search backwards from end
                    if row[i].strip() in ["Yes", "No", "No/Yes"]:
                        condition_idx = i
                        break

                if condition_idx is None:
                    # Assume standard 4-interlock format
                    condition_idx = 6

                # Extract interlocks (from column 2 up to condition column)
                interlocks_raw = row[2:condition_idx]
                interlocks = [
                    interlock.strip()
                    for interlock in interlocks_raw
                    if interlock and interlock.strip() and interlock.strip().lower() != 'alwayson'
                ]

                # Extract condition
                condition_str = row[condition_idx].strip()
                try:
                    condition = ConditionType(condition_str)
                except ValueError:
                    logger.warning(f"Invalid condition '{condition_str}', defaulting to 'Yes'")
                    condition = ConditionType.YES

                # Extract next step (one column after condition)
                next_step_str = row[condition_idx + 1].strip() if len(row) > condition_idx + 1 else "0"
                try:
                    next_step = int(next_step_str) if next_step_str else 0
                except ValueError:
                    logger.warning(f"Invalid next_step '{next_step_str}', defaulting to 0")
                    next_step = 0

            else:
                # Fallback for shorter rows
                logger.warning(f"Row too short ({len(row)} columns), using defaults")
                interlocks = []
                condition = ConditionType.YES
                next_step = 0

            return State(
                step=step,
                description=description,
                interlocks=interlocks,
                condition=condition,
                next_step=next_step
            )

        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing state row: {e}")
            return None

    def _save_current_machine(self):
        """Save the current machine being processed"""
        if self.current_machine_name and self.current_states:
            try:
                machine = MachineLogic(
                    name=self.current_machine_name,
                    states=self.current_states
                )
                self.machines.append(machine)
                logger.info(f"Saved machine '{machine.name}' with {len(machine.states)} states")

                # Reset for next machine
                self.current_machine_name = None
                self.current_states = []
            except Exception as e:
                logger.error(f"Error creating machine '{self.current_machine_name}': {e}")
                self.current_machine_name = None
                self.current_states = []


def parse_csv_file(csv_content: str) -> ParsedCSV:
    """
    Convenience function to parse CSV content

    Args:
        csv_content: String content of CSV file

    Returns:
        ParsedCSV object with all parsed machines

    Raises:
        CSVParserError: If parsing fails
    """
    parser = CSVParser()
    return parser.parse(csv_content)


def parse_csv_bytes(csv_bytes: bytes) -> ParsedCSV:
    """
    Parse CSV from bytes (e.g., uploaded file)

    Args:
        csv_bytes: Bytes content of CSV file

    Returns:
        ParsedCSV object with all parsed machines

    Raises:
        CSVParserError: If parsing fails
    """
    try:
        csv_content = csv_bytes.decode('utf-8')
        return parse_csv_file(csv_content)
    except UnicodeDecodeError:
        # Try other encodings
        try:
            csv_content = csv_bytes.decode('latin-1')
            return parse_csv_file(csv_content)
        except Exception as e:
            raise CSVParserError(f"Could not decode CSV file: {e}")
