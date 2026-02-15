#!/usr/bin/env python3
"""
Test L5X Skeleton Generator

Test generating valid L5X XML structure from IR.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.parser.csv_parser import parse_csv_file
from src.core.parser.csv_to_ir import csv_to_ir
from src.core.l5x.skeleton_generator import (
    generate_skeleton,
    validate_skeleton_xml,
    extract_placeholders
)


def test_skeleton_generation():
    """Test generating skeleton from real CSV data"""
    print("=" * 60)
    print("TEST: Skeleton Generation from CSV")
    print("=" * 60)

    # Load CSV
    csv_file = project_root / "assets" / "LogicSheet03.csv"

    with open(csv_file, 'r') as f:
        csv_content = f.read()

    # Parse and convert to IR
    parsed_csv = parse_csv_file(csv_content)
    ir_project = csv_to_ir(parsed_csv, project_name="Test_Project")

    print(f"\n📊 IR Summary:")
    print(f"   Programs: {ir_project.program_count}")
    print(f"   Routines: {ir_project.total_routines}")
    print(f"   Rungs: {ir_project.total_rungs}")
    print(f"   Tags: {len(ir_project.tags)}")

    # Generate skeleton
    print(f"\n🔨 Generating skeleton...")
    skeleton = generate_skeleton(ir_project)

    print(f"✅ Skeleton generated")
    print(f"   Size: {len(skeleton):,} characters ({len(skeleton) / 1024:.1f} KB)")

    return skeleton, ir_project


def test_skeleton_structure(skeleton):
    """Test the structure of generated skeleton"""
    print("\n" + "=" * 60)
    print("TEST: Skeleton Structure")
    print("=" * 60)

    # Check key sections
    sections = {
        'XML Declaration': '<?xml version',
        'Root Element': '<RSLogix5000Content',
        'Controller': '<Controller',
        'Tags Section': '<Tags>',
        'Programs Section': '<Programs>',
        'Routines': '<Routine',
        'RLL Content': '<RLLContent>',
        'Placeholders': 'LOGIC_PLACEHOLDER_',
    }

    print(f"\n✅ Checking structure:")
    for name, marker in sections.items():
        count = skeleton.count(marker)
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {name}: {count} occurrence(s)")

    # Extract placeholders
    placeholders = extract_placeholders(skeleton)
    print(f"\n📍 Placeholders found: {len(placeholders)}")
    for placeholder in placeholders[:5]:
        print(f"   - {placeholder}")
    if len(placeholders) > 5:
        print(f"   ... and {len(placeholders) - 5} more")

    return True


def test_skeleton_validation(skeleton):
    """Test skeleton XML validation"""
    print("\n" + "=" * 60)
    print("TEST: Skeleton Validation")
    print("=" * 60)

    validation = validate_skeleton_xml(skeleton)

    print(f"\n✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")

    if validation['issues']:
        print("\n❌ Issues:")
        for issue in validation['issues']:
            print(f"   - {issue}")

    print(f"\nValidation Details:")
    print(f"   Placeholders: {validation['placeholder_count']}")
    print(f"   Size: {validation['size_bytes']:,} bytes")

    return validation['valid']


def test_skeleton_preview(skeleton):
    """Show preview of generated skeleton"""
    print("\n" + "=" * 60)
    print("TEST: Skeleton Preview")
    print("=" * 60)

    lines = skeleton.split('\n')

    print(f"\nFirst 30 lines:")
    print("-" * 60)
    for i, line in enumerate(lines[:30], 1):
        print(f"{i:3d} | {line}")
    print("-" * 60)

    if len(lines) > 60:
        print(f"\n... ({len(lines) - 60} lines omitted) ...\n")

    print(f"Last 10 lines:")
    print("-" * 60)
    for i, line in enumerate(lines[-10:], len(lines) - 9):
        print(f"{i:3d} | {line}")
    print("-" * 60)

    return True


def test_skeleton_export(skeleton):
    """Export skeleton to file"""
    print("\n" + "=" * 60)
    print("TEST: Skeleton Export")
    print("=" * 60)

    output_file = project_root / "logs" / "test_skeleton_output.l5x"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(skeleton)

    print(f"\n✅ Skeleton exported to: {output_file}")
    print(f"   File size: {output_file.stat().st_size:,} bytes")

    # Also show where placeholders are
    placeholders = extract_placeholders(skeleton)
    print(f"\n📍 Placeholders that need to be filled:")
    for placeholder in placeholders:
        routine_name = placeholder.replace('LOGIC_PLACEHOLDER_', '')
        print(f"   - {routine_name}")

    return True


def main():
    """Run all tests"""
    print("\n🧪 L5X Skeleton Generator Test Suite\n")

    results = []

    # Test 1: Generation
    try:
        skeleton, ir_project = test_skeleton_generation()
        results.append(("Skeleton Generation", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Skeleton Generation", False))
        return 1

    # Test 2: Structure
    try:
        test_skeleton_structure(skeleton)
        results.append(("Skeleton Structure", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Skeleton Structure", False))

    # Test 3: Validation
    try:
        valid = test_skeleton_validation(skeleton)
        results.append(("Skeleton Validation", valid))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Skeleton Validation", False))

    # Test 4: Preview
    try:
        test_skeleton_preview(skeleton)
        results.append(("Skeleton Preview", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Skeleton Preview", False))

    # Test 5: Export
    try:
        test_skeleton_export(skeleton)
        results.append(("Skeleton Export", True))
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Skeleton Export", False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! Skeleton generator is working.")
        print("\nNext step: Build routine-level LLM generator")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
