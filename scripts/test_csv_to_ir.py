#!/usr/bin/env python3
"""
Test CSV to IR Converter

Test converting real CSV files to IR structures.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.parser.csv_parser import parse_csv_file
from src.core.parser.csv_to_ir import csv_to_ir
from src.core.ir.ir_builder import validate_ir


def test_csv_to_ir_conversion():
    """Test converting LogicSheet03.csv to IR"""
    print("=" * 60)
    print("TEST: CSV to IR Conversion")
    print("=" * 60)

    csv_file = project_root / "assets" / "LogicSheet03.csv"

    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return None

    # Read CSV
    with open(csv_file, 'r') as f:
        csv_content = f.read()

    print(f"\n📄 Reading: {csv_file.name}")

    # Parse CSV
    parsed_csv = parse_csv_file(csv_content)

    print(f"✅ Parsed {parsed_csv.total_machines} machine(s)")
    for machine in parsed_csv.machines:
        print(f"   - {machine.name}: {len(machine.states)} states")

    # Convert to IR
    print("\n🔄 Converting to IR...")
    ir_project = csv_to_ir(parsed_csv, project_name="LogicSheet_Test")

    print(f"✅ IR created")
    print(f"   Project: {ir_project.project_name}")
    print(f"   Programs: {ir_project.program_count}")
    print(f"   Routines: {ir_project.total_routines}")
    print(f"   Rungs: {ir_project.total_rungs}")
    print(f"   Tags: {len(ir_project.tags)}")

    return ir_project


def test_ir_structure(ir_project):
    """Test the structure of generated IR"""
    print("\n" + "=" * 60)
    print("TEST: IR Structure")
    print("=" * 60)

    for program in ir_project.programs:
        print(f"\nProgram: {program.name}")
        print(f"  Description: {program.description}")
        print(f"  Routines: {program.routine_count}")

        for routine in program.sorted_routines:
            print(f"\n  Routine: {routine.name}")
            print(f"    Type: {routine.type.display_name}")
            print(f"    Priority: {routine.priority}")
            print(f"    Rungs: {routine.rung_count}")
            print(f"    Expected lines: {routine.expected_lines}")
            print(f"    Estimated tokens: {routine.estimated_tokens:,}")

            # Show first few rungs
            if routine.rungs:
                print(f"\n    Sample rungs:")
                for rung in routine.rungs[:3]:
                    print(f"      [{rung.number}] {rung.comment}")
                    print(f"          Condition: {rung.condition}")
                    print(f"          Action: {rung.action}")

                if routine.rung_count > 3:
                    print(f"      ... and {routine.rung_count - 3} more rungs")

    return True


def test_ir_validation(ir_project):
    """Test IR validation"""
    print("\n" + "=" * 60)
    print("TEST: IR Validation")
    print("=" * 60)

    validation = validate_ir(ir_project)

    print(f"\n✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")

    if validation['issues']:
        print("\n❌ Issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")

    if validation['warnings']:
        print("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")

    print(f"\nStatistics:")
    for key, value in validation['statistics'].items():
        print(f"  {key}: {value}")

    return validation['valid']


def test_ir_export(ir_project):
    """Test IR JSON export"""
    print("\n" + "=" * 60)
    print("TEST: IR Export")
    print("=" * 60)

    # Export to JSON
    output_file = project_root / "logs" / "test_ir_output.json"
    output_file.parent.mkdir(exist_ok=True)

    ir_project.save_json(str(output_file))

    print(f"\n✅ IR exported to: {output_file}")
    print(f"   File size: {output_file.stat().st_size:,} bytes")

    # Show statistics
    stats = ir_project.to_dict()['statistics']

    print(f"\nProject Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return True


def main():
    """Run all tests"""
    print("\n🧪 CSV to IR Converter Test Suite\n")

    results = []

    # Test 1: Conversion
    try:
        ir_project = test_csv_to_ir_conversion()
        if ir_project:
            results.append(("CSV to IR Conversion", True))
        else:
            results.append(("CSV to IR Conversion", False))
            return 1
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("CSV to IR Conversion", False))
        return 1

    # Test 2: Structure
    try:
        test_ir_structure(ir_project)
        results.append(("IR Structure", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("IR Structure", False))

    # Test 3: Validation
    try:
        valid = test_ir_validation(ir_project)
        results.append(("IR Validation", valid))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("IR Validation", False))

    # Test 4: Export
    try:
        test_ir_export(ir_project)
        results.append(("IR Export", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("IR Export", False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! CSV to IR converter is working.")
        print("\nNext step: Build L5X skeleton generator")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
