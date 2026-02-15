#!/usr/bin/env python3
"""
Phase 3 End-to-End Test
Tests the complete L5X generation pipeline
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.rag.pipeline import get_pipeline
from src.core.rag.validator import validate_l5x
from src.utils.logger import logger

def test_generation():
    """Test L5X generation with sample CSV"""

    # Load sample CSV
    csv_path = project_root / "assets" / "LogicSheet03.csv"

    if not csv_path.exists():
        logger.error(f"Sample CSV not found: {csv_path}")
        return False

    logger.info(f"Loading CSV from: {csv_path}")
    csv_content = csv_path.read_text()

    # Initialize pipeline
    logger.info("Initializing RAG pipeline...")
    pipeline = get_pipeline()

    # Generate L5X for first machine
    logger.info("Generating L5X for machine 0...")
    result = pipeline.generate_from_csv(
        csv_content=csv_content,
        machine_index=0,
        n_similar=3
    )

    if not result.success:
        logger.error(f"Generation failed: {result.error}")
        return False

    logger.info(f"✓ Generated L5X for: {result.machine_name}")
    logger.info(f"  - Code length: {len(result.l5x_code)} characters")
    logger.info(f"  - Similar examples used: {result.similar_count}")

    # Validate generated L5X
    logger.info("Validating generated L5X...")
    is_valid, issues = validate_l5x(result.l5x_code)

    if is_valid:
        logger.info("✓ L5X is valid!")
    else:
        logger.warning("⚠ L5X has validation issues")

    # Display issues
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    if errors:
        logger.error(f"Errors ({len(errors)}):")
        for issue in errors:
            logger.error(f"  - {issue}")

    if warnings:
        logger.warning(f"Warnings ({len(warnings)}):")
        for issue in warnings:
            logger.warning(f"  - {issue}")

    if infos:
        logger.info(f"Info ({len(infos)}):")
        for issue in infos:
            logger.info(f"  - {issue}")

    # Preview L5X
    logger.info("\nL5X Preview (first 500 characters):")
    logger.info("-" * 60)
    logger.info(result.l5x_code[:500])
    logger.info("-" * 60)

    return True

if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("Phase 3 End-to-End Test")
        logger.info("=" * 60)

        success = test_generation()

        if success:
            logger.info("\n✓ Phase 3 test PASSED")
            sys.exit(0)
        else:
            logger.error("\n✗ Phase 3 test FAILED")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
