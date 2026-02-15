"""
Prompt Templates for L5X Generation

Carefully crafted prompts for generating PLC L5X code from CSV logic patterns.
"""

L5X_GENERATION_PROMPT = """You are an expert PLC programmer specializing in Rockwell/Allen-Bradley ControlLogix systems.

Your task is to generate a complete L5X XML file for a PLC state machine based on CSV logic definitions.

## Machine Information
**Machine Name**: {machine_name}

## CSV Logic Pattern
{csv_logic}

## Similar Examples from Database
{similar_examples}

## Requirements

### 1. L5X File Structure
Generate a complete L5X XML file with:
- Proper XML declaration and RSLogix5000Content root
- Controller configuration (use 1769-L18ER-BB1B processor)
- DataTypes section with UDT_Sequencer
- Tags section for all inputs/outputs
- Programs section with MainProgram
- Routines with ladder logic

### 2. UDT_Sequencer Structure
Create a User Defined Type for the sequencer with these members:
- Hold (BIT): Hold the sequence
- Continue (BIT): Continue after hold
- Reset (BIT): Reset to step 0
- Interlocks (BIT): All interlocks OK
- Active (BIT): Sequence is running
- StepNumber (DINT): Current step number
- StepComplete (BIT): Current step finished

### 3. Ladder Logic Generation
For each state in the CSV:
- Create a rung for the step logic
- Use XIC (Examine If Closed) for interlocks
- Use EQU (Equal) to check current step number
- Use MOV (Move) to advance to next step
- Include all safety interlocks from CSV

### 4. Tag Definitions
Create tags for:
- All digital inputs (DI01, DI02, etc.) as BOOL
- Sequencer tag as UDT_Sequencer type
- Any other required control tags

### 5. Important Rules
- Use exact tag names from CSV (DI01, DI02, etc.)
- Maintain state sequence from CSV (0→10→20→...)
- Include proper XML escaping
- Follow Rockwell L5X schema version 1.0
- Set ExportDate to current date
- Use descriptive comments in ladder logic

## Output Format
Generate ONLY the complete L5X XML code. Do not include explanations before or after.
Start directly with: <?xml version="1.0" encoding="UTF-8" standalone="yes"?>

Begin generation now:
"""


L5X_SIMPLE_PROMPT = """Generate a Rockwell L5X file for this PLC state machine:

Machine: {machine_name}

States:
{csv_logic}

Create a complete L5X XML file with:
1. Proper XML structure
2. UDT_Sequencer data type
3. Ladder logic for each state
4. All required tags

Output only the L5X XML code, no explanations.
"""


L5X_REFINEMENT_PROMPT = """You are refining a generated L5X file for quality and correctness.

## Original L5X
{original_l5x}

## Issues Found
{issues}

## Instructions
Fix the issues while maintaining:
- All original functionality
- Proper XML structure
- Rockwell L5X schema compliance
- Tag naming conventions

Output only the corrected L5X XML code.
"""


def create_generation_prompt(
    machine_name: str,
    csv_logic: str,
    similar_examples: str,
    template: str = "detailed"
) -> str:
    """
    Create a prompt for L5X generation

    Args:
        machine_name: Name of the machine
        csv_logic: Structured CSV logic description
        similar_examples: Formatted similar examples
        template: Template type ("detailed" or "simple")

    Returns:
        Complete prompt string
    """
    if template == "simple":
        return L5X_SIMPLE_PROMPT.format(
            machine_name=machine_name,
            csv_logic=csv_logic
        )
    else:
        return L5X_GENERATION_PROMPT.format(
            machine_name=machine_name,
            csv_logic=csv_logic,
            similar_examples=similar_examples
        )


def create_refinement_prompt(original_l5x: str, issues: str) -> str:
    """
    Create a prompt for L5X refinement

    Args:
        original_l5x: The original L5X code
        issues: List of issues to fix

    Returns:
        Refinement prompt
    """
    return L5X_REFINEMENT_PROMPT.format(
        original_l5x=original_l5x,
        issues=issues
    )
