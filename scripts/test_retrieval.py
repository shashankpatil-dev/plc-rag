#!/usr/bin/env python3
"""
Test Retrieval Script

Tests similarity search by querying the vector database with sample logic.

Usage:
    python scripts/test_retrieval.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.parser.csv_parser import parse_csv_file
from src.core.rag.retriever import get_retriever
from src.utils.logger import logger


def main():
    """Test retrieval with sample data"""
    logger.info("=" * 60)
    logger.info("Testing Similarity Retrieval")
    logger.info("=" * 60)

    # Load test CSV
    csv_path = Path("data/training/example_01/logic.csv")
    if not csv_path.exists():
        logger.error(f"Test CSV not found: {csv_path}")
        return

    logger.info(f"Loading test CSV: {csv_path}")

    with open(csv_path, 'r') as f:
        csv_content = f.read()

    # Parse CSV
    parsed = parse_csv_file(csv_content)
    logger.info(f"Parsed {parsed.total_machines} machines")

    # Get retriever
    retriever = get_retriever()

    # Show stats
    stats = retriever.get_statistics()
    logger.info(f"\nVector Database Stats:")
    logger.info(f"  Total indexed: {stats['total_machines_indexed']}")
    logger.info(f"  Collection: {stats['collection_name']}")

    if stats['total_machines_indexed'] == 0:
        logger.warning("\nNo data indexed! Run: python scripts/index_training_data.py")
        return

    # Test retrieval for first machine
    test_machine = parsed.machines[0]
    logger.info(f"\nQuerying for similar machines to: {test_machine.name}")
    logger.info(f"  States: {test_machine.state_count}")
    logger.info(f"  Interlocks: {test_machine.total_interlock_count}")

    # Retrieve similar
    results = retriever.retrieve_similar(test_machine, n_results=3)

    logger.info(f"\nFound {len(results)} similar machines:")
    logger.info("")

    for i, result in enumerate(results, 1):
        logger.info(f"{i}. {result.machine_name}")
        logger.info(f"   Similarity: {result.similarity_score:.3f}")
        logger.info(f"   States: {result.metadata.get('state_count', 'N/A')}")
        logger.info(f"   Interlocks: {result.metadata.get('interlock_count', 'N/A')}")
        logger.info(f"   Source: {result.metadata.get('source_csv', 'N/A')}")
        logger.info("")

    logger.info("=" * 60)
    logger.info("Retrieval test complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
