#!/usr/bin/env python3
"""
Test IR Builder

Verify the Intermediate Representation data structures work correctly.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.ir.ir_builder import (
    create_sample_ir,
    validate_ir,
    Rung,
    Routine,
    Program,
    L5XProject,
    RoutineType
)


def test_ir_creation():
    """Test creating IR structures"""
    print("=" * 60)
    print("TEST: IR Creation")
    print("=" * 60)

    # Create sample IR
    project = create_sample_ir()

    print(f"\n✅ Project created: {project.project_name}")
    print(f"   Programs: {project.program_count}")
    print(f"   Routines: {project.total_routines}")
    print(f"   Rungs: {project.total_rungs}")
    print(f"   Tags: {len(project.tags)}")

    return project


def test_ir_validation(project):
    """Test IR validation"""
    print("\n" + "=" * 60)
    print("TEST: IR Validation")
    print("=" * 60)

    validation = validate_ir(project)

    print(f"\n✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")

    if validation['issues']:
        print("\nIssues:")
        for issue in validation['issues']:
            print(f"  ❌ {issue}")

    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")

    print(f"\nStatistics:")
    for key, value in validation['statistics'].items():
        print(f"  {key}: {value}")

    return validation


def test_ir_serialization(project):
    """Test IR JSON serialization"""
    print("\n" + "=" * 60)
    print("TEST: IR Serialization")
    print("=" * 60)

    # Convert to dict
    project_dict = project.to_dict()

    print(f"\n✅ Converted to dict")
    print(f"   Keys: {list(project_dict.keys())}")

    # Convert to JSON
    json_str = project.to_json()

    print(f"\n✅ Converted to JSON")
    print(f"   Size: {len(json_str)} characters")

    # Preview JSON
    print(f"\nJSON Preview (first 500 chars):")
    print("-" * 60)
    print(json_str[:500])
    print("...")
    print("-" * 60)

    return json_str


def test_ir_properties(project):
    """Test IR computed properties"""
    print("\n" + "=" * 60)
    print("TEST: IR Properties")
    print("=" * 60)

    print(f"\nProject Properties:")
    print(f"  Estimated lines: {project.estimated_lines:,}")
    print(f"  Estimated cost: ${project.estimated_generation_cost:.2f}")

    for program in project.programs:
        print(f"\nProgram '{program.name}':")
        print(f"  Routines: {program.routine_count}")
        print(f"  Total rungs: {program.total_rungs}")
        print(f"  Tags used: {len(program.all_tags_used)}")

        for routine in program.sorted_routines:
            print(f"\n  Routine '{routine.name}' ({routine.type.display_name}):")
            print(f"    Priority: {routine.priority}")
            print(f"    Rungs: {routine.rung_count}")
            print(f"    Tags: {routine.all_tags_used}")
            print(f"    Estimated tokens: {routine.estimated_tokens:,}")

    return True


def test_tag_extraction():
    """Test tag extraction from conditions"""
    print("\n" + "=" * 60)
    print("TEST: Tag Extraction")
    print("=" * 60)

    test_cases = [
        ("NOT EStop", ["EStop"]),
        ("Start_Button AND Safety_OK", ["Safety_OK", "Start_Button"]),
        ("DI01 OR DI02 OR DI03", ["DI01", "DI02", "DI03"]),
        ("Motor_Run := TRUE", ["Motor_Run", "TRUE"]),
    ]

    all_passed = True

    for condition, expected in test_cases:
        rung = Rung(
            number=0,
            comment="Test",
            condition=condition,
            action=""
        )

        extracted = rung.tags_used

        # Check if all expected tags are present (order doesn't matter)
        match = set(extracted) >= set(expected)

        status = "✅" if match else "❌"
        print(f"{status} '{condition}'")
        print(f"   Expected: {expected}")
        print(f"   Got:      {extracted}")

        if not match:
            all_passed = False

    return all_passed


def main():
    """Run all tests"""
    print("\n🧪 IR Builder Test Suite\n")

    results = []

    # Test 1: Creation
    try:
        project = test_ir_creation()
        results.append(("IR Creation", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        results.append(("IR Creation", False))
        return 1

    # Test 2: Validation
    try:
        validation = test_ir_validation(project)
        results.append(("IR Validation", validation['valid']))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        results.append(("IR Validation", False))

    # Test 3: Serialization
    try:
        json_str = test_ir_serialization(project)
        results.append(("IR Serialization", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        results.append(("IR Serialization", False))

    # Test 4: Properties
    try:
        test_ir_properties(project)
        results.append(("IR Properties", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        results.append(("IR Properties", False))

    # Test 5: Tag extraction
    try:
        tag_test = test_tag_extraction()
        results.append(("Tag Extraction", tag_test))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        results.append(("Tag Extraction", False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! IR builder is working correctly.")
        print("\nNext step: Build CSV → IR converter")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
