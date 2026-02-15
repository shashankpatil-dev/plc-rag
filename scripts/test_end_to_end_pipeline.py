#!/usr/bin/env python3
"""
Test End-to-End Pipeline

Test the complete CSV → L5X generation pipeline.
This is the ultimate test that verifies all components work together.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.l5x.pipeline import L5XGenerationPipeline
from src.core.rag.generator import LLMGenerator


def test_simple_routine_generation():
    """Test generating a single simple routine"""
    print("=" * 60)
    print("TEST: Simple Routine Generation")
    print("=" * 60)

    from src.core.ir.ir_builder import Routine, Rung, RoutineType
    from src.core.l5x.routine_generator import RoutineGenerator

    # Create a simple routine
    routine = Routine(
        name="Test_Safety",
        type=RoutineType.SAFETY,
        description="Simple safety test"
    )

    # Add 2 simple rungs
    routine.add_rung(Rung(
        number=0,
        comment="Emergency Stop Check",
        condition="NOT EStop",
        action="Safety_OK := TRUE",
        safety_critical=True
    ))

    routine.add_rung(Rung(
        number=1,
        comment="Door Closed Check",
        condition="Door_Closed AND Safety_OK",
        action="Safety_Clear := TRUE",
        safety_critical=True
    ))

    print(f"\n📊 Test Routine:")
    print(f"   Name: {routine.name}")
    print(f"   Type: {routine.type.display_name}")
    print(f"   Rungs: {routine.rung_count}")

    # Generate rungs
    print(f"\n🤖 Calling Claude Sonnet to generate rungs...")

    try:
        generator = RoutineGenerator()
        generated_rungs = generator.generate_routine(routine)

        print(f"\n✅ Generation successful!")
        print(f"   Output size: {len(generated_rungs)} characters")

        # Show preview
        print(f"\n📄 Generated Output Preview:")
        print("-" * 60)
        lines = generated_rungs.split('\n')
        for line in lines[:20]:
            print(line)
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        print("-" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_minimal_csv_pipeline():
    """Test complete pipeline with minimal CSV"""
    print("\n" + "=" * 60)
    print("TEST: Minimal CSV Pipeline")
    print("=" * 60)

    # Create minimal CSV content
    minimal_csv = """Mat_Roll_Transfer_Conveyor_Test
Logic,LogicDescription,Interlock1,Interlock2,Condition,Logic
0,Waiting_For_Home,,,Yes,10
10,Check_For_Mat_Present,DI01,DI02,Yes,20
20,Start_Motor,DI03,,Yes,0
"""

    print(f"\n📄 Input CSV:")
    print("-" * 60)
    print(minimal_csv)
    print("-" * 60)

    print(f"\n🚀 Running complete pipeline...")

    try:
        pipeline = L5XGenerationPipeline()

        result = pipeline.generate_from_csv(
            csv_content=minimal_csv,
            project_name="Minimal_Test",
            validate_output=True
        )

        print(f"\n✅ Pipeline complete!")

        # Show statistics
        stats = result['statistics']
        print(f"\n📊 Statistics:")
        print(f"   CSV machines: {stats['csv_machines']}")
        print(f"   IR programs: {stats['ir_programs']}")
        print(f"   IR routines: {stats['ir_routines']}")
        print(f"   IR rungs: {stats['ir_rungs']}")
        print(f"   IR tags: {stats['ir_tags']}")
        print(f"   Final L5X size: {stats['final_size']:,} bytes")
        print(f"   Routines generated: {stats['routines_generated']}/{stats['ir_routines']}")
        print(f"   Estimated cost: ${stats['estimated_cost_usd']:.2f}")

        # Show validation
        if result['validation']:
            val = result['validation']
            print(f"\n✅ Validation: {'PASS' if val['valid'] else 'FAIL'}")

            if val['issues']:
                print(f"\n❌ Issues:")
                for issue in val['issues']:
                    print(f"   - {issue}")

            if val['warnings']:
                print(f"\n⚠️  Warnings:")
                for warning in val['warnings']:
                    print(f"   - {warning}")

        # Save output
        output_file = project_root / "logs" / "test_minimal_output.l5x"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(result['l5x_content'])

        print(f"\n💾 Saved to: {output_file}")

        return result['validation']['valid'] if result['validation'] else True

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_csv_pipeline():
    """Test complete pipeline with full LogicSheet03.csv"""
    print("\n" + "=" * 60)
    print("TEST: Full CSV Pipeline (LogicSheet03.csv)")
    print("=" * 60)

    csv_file = project_root / "assets" / "LogicSheet03.csv"

    if not csv_file.exists():
        print(f"⚠️  CSV file not found: {csv_file}")
        return None

    print(f"\n📄 Input: {csv_file.name}")

    print(f"\n🚀 Running complete pipeline...")
    print("   (This will take 2-3 minutes - generating 8 routines with Claude)")

    try:
        pipeline = L5XGenerationPipeline()

        result = pipeline.generate_from_file(
            csv_file_path=str(csv_file),
            output_path=str(project_root / "logs" / "test_full_output.l5x"),
            project_name="Full_Test"
        )

        print(f"\n✅ Pipeline complete!")

        # Show statistics
        stats = result['statistics']
        print(f"\n📊 Statistics:")
        print(f"   CSV machines: {stats['csv_machines']}")
        print(f"   IR programs: {stats['ir_programs']}")
        print(f"   IR routines: {stats['ir_routines']}")
        print(f"   IR rungs: {stats['ir_rungs']}")
        print(f"   IR tags: {stats['ir_tags']}")
        print(f"   Final L5X size: {stats['final_size']:,} bytes ({stats['final_size']/1024:.1f} KB)")
        print(f"   Routines generated: {stats['routines_generated']}/{stats['ir_routines']}")
        print(f"   Routines failed: {stats['routines_failed']}")
        print(f"   Estimated cost: ${stats['estimated_cost_usd']:.2f}")

        # Show validation
        if result['validation']:
            val = result['validation']
            print(f"\n{'✅' if val['valid'] else '❌'} Validation: {'PASS' if val['valid'] else 'FAIL'}")

            if val['issues']:
                print(f"\n❌ Issues:")
                for issue in val['issues']:
                    print(f"   - {issue}")

            if val['warnings']:
                print(f"\n⚠️  Warnings (first 5):")
                for warning in val['warnings'][:5]:
                    print(f"   - {warning}")
                if len(val['warnings']) > 5:
                    print(f"   ... and {len(val['warnings']) - 5} more warnings")

        print(f"\n💾 Output saved to: {result.get('output_file')}")

        return result['validation']['valid'] if result['validation'] else True

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end tests"""
    print("\n🧪 End-to-End Pipeline Test Suite\n")

    results = []

    # Test 1: Simple routine generation
    try:
        success = test_simple_routine_generation()
        results.append(("Simple Routine Generation", success))
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        results.append(("Simple Routine Generation", False))

    # Test 2: Minimal CSV pipeline
    try:
        success = test_minimal_csv_pipeline()
        results.append(("Minimal CSV Pipeline", success))
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        results.append(("Minimal CSV Pipeline", False))

    # Test 3: Full CSV pipeline (optional - takes longer)
    user_input = input("\n\nRun full CSV test? (generates 8 routines, takes 2-3 min) [y/N]: ")
    if user_input.lower() == 'y':
        try:
            success = test_full_csv_pipeline()
            if success is not None:
                results.append(("Full CSV Pipeline", success))
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            results.append(("Full CSV Pipeline", False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed!")
        print("\n✨ The complete CSV → L5X pipeline is working!")
        print("\nYou can now:")
        print("  1. Generate L5X files from CSV input")
        print("  2. Review the generated files in logs/")
        print("  3. Import into Studio 5000 for testing")
        print("  4. Build embeddings for better RAG retrieval")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
