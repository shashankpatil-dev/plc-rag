#!/usr/bin/env python3
"""
Index Training Data Script

Indexes all CSV+L5X pairs from data/training/ into the vector database.
Run this script after adding new training examples.

Usage:
    python scripts/index_training_data.py [--reset]

Options:
    --reset: Reset the vector database before indexing (deletes all existing data)
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.knowledge.indexer import get_indexer
from src.core.knowledge.vector_store import get_vector_store
from src.utils.logger import logger


def main():
    """Main indexing function"""
    parser = argparse.ArgumentParser(description="Index PLC training data into vector database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the database before indexing (WARNING: deletes all data)"
    )
    parser.add_argument(
        "--training-dir",
        type=str,
        default="data/training",
        help="Path to training data directory"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("PLC Training Data Indexer")
    logger.info("=" * 60)

    # Reset database if requested
    if args.reset:
        logger.warning("Resetting vector database...")
        response = input("Are you sure? This will delete all indexed data (y/N): ")
        if response.lower() == 'y':
            vector_store = get_vector_store()
            vector_store.reset()
            logger.info("Database reset complete")
        else:
            logger.info("Reset cancelled")
            return

    # Create indexer
    indexer = get_indexer(training_dir=args.training_dir)

    # Show current stats
    stats_before = indexer.get_stats()
    logger.info(f"Database stats before indexing:")
    logger.info(f"  Total embeddings: {stats_before['total_embeddings']}")
    logger.info(f"  Collection: {stats_before['collection_name']}")

    # Index all training data
    logger.info("")
    logger.info("Starting indexing...")
    logger.info("")

    try:
        total_indexed = indexer.index_all()

        logger.info("")
        logger.info("=" * 60)
        logger.info("Indexing Complete!")
        logger.info("=" * 60)
        logger.info(f"Total machines indexed: {total_indexed}")

        # Show final stats
        stats_after = indexer.get_stats()
        logger.info(f"Total embeddings in database: {stats_after['total_embeddings']}")

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
