"""
RAG Retrieval Methods for Routine Generator

Extends the routine generator with RAG retrieval capabilities.
"""

from typing import List
from src.core.ir.ir_builder import Routine
from src.utils.logger import logger


def retrieve_similar_routines(
    routine: Routine,
    embedder,
    collection,
    n_similar: int = 3
) -> List[str]:
    """
    Retrieve similar routines from ChromaDB

    Args:
        routine: Routine to find similar examples for
        embedder: Embedding generator instance
        collection: ChromaDB collection
        n_similar: Number of similar routines to retrieve

    Returns:
        List of similar routine texts
    """
    try:
        # Build query from routine metadata
        query_parts = []

        # Add routine type
        query_parts.append(f"{routine.type.display_name} routine")

        # Add description if available
        if routine.description:
            query_parts.append(routine.description)

        # Add rung descriptions
        for rung in routine.rungs[:3]:  # First 3 rungs
            if rung.comment:
                query_parts.append(rung.comment)

        query_text = " ".join(query_parts)

        logger.info(f"RAG query: {query_text[:100]}...")

        # Create embedding for query
        query_embedding = embedder.embed_text(query_text)

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_similar
        )

        # Extract documents (similar routine texts)
        similar_routines = results['documents'][0] if results['documents'] else []
        distances = results['distances'][0] if results['distances'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []

        # Log retrieval results
        logger.info(f"Retrieved {len(similar_routines)} similar routines:")
        for i, (meta, dist) in enumerate(zip(metadatas, distances), 1):
            logger.info(f"  {i}. {meta.get('routine_name', 'Unknown')} (distance: {dist:.4f})")

        return similar_routines

    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return []


# Add this method to RoutineGenerator class
def _retrieve_similar_routines(self, routine: Routine, n_similar: int = 3) -> List[str]:
    """
    Retrieve similar routines using RAG

    This method is added to RoutineGenerator class.
    """
    if not self.use_rag:
        return []

    return retrieve_similar_routines(
        routine=routine,
        embedder=self.embedder,
        collection=self.collection,
        n_similar=n_similar
    )
