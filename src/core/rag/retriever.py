"""
Similarity Search Retriever

Queries the vector database to find similar PLC logic patterns.
Used in the RAG pipeline to find relevant examples for L5X generation.
"""
from typing import List, Dict, Any, Optional
from src.api.models.csv_models import MachineLogic, ParsedCSV
from src.core.rag.embedder import get_embedder
from src.core.knowledge.vector_store import get_vector_store
from src.utils.logger import logger


class RetrievalResult:
    """Single retrieval result with metadata"""

    def __init__(
        self,
        machine_name: str,
        description: str,
        similarity_score: float,
        metadata: Dict[str, Any]
    ):
        self.machine_name = machine_name
        self.description = description
        self.similarity_score = similarity_score
        self.metadata = metadata

    def __repr__(self):
        return (
            f"RetrievalResult(machine='{self.machine_name}', "
            f"score={self.similarity_score:.3f})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "machine_name": self.machine_name,
            "description": self.description,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata
        }


class LogicRetriever:
    """
    Retrieve similar PLC logic patterns from vector database

    Used in RAG pipeline to find relevant examples for code generation.
    """

    def __init__(self):
        """Initialize retriever"""
        self.embedder = get_embedder()
        self.vector_store = get_vector_store()
        logger.info("Initialized LogicRetriever")

    def retrieve_similar(
        self,
        machine: MachineLogic,
        n_results: int = 3,
        min_similarity: float = 0.0
    ) -> List[RetrievalResult]:
        """
        Find similar machines in the database

        Args:
            machine: MachineLogic to find similar examples for
            n_results: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of RetrievalResult objects, sorted by similarity
        """
        logger.info(f"Retrieving similar machines for: {machine.name}")

        # Generate embedding for query machine (using query-specific embedding for Gemini)
        description = self.embedder.create_semantic_description(machine)
        embedding = self.embedder.generate_query_embedding(description)

        # Query vector store
        results = self.vector_store.query(
            query_embeddings=[embedding],
            n_results=n_results
        )

        # Process results
        retrieval_results = []

        # Results structure: {ids: [[...]], distances: [[...]], documents: [[...]], metadatas: [[...]]}
        for i in range(len(results['ids'][0])):
            # ChromaDB returns distances (lower is better)
            # Convert to similarity score (higher is better, 0-1 range)
            distance = results['distances'][0][i]
            similarity = 1 / (1 + distance)  # Convert distance to similarity

            # Filter by minimum similarity
            if similarity < min_similarity:
                continue

            result = RetrievalResult(
                machine_name=results['metadatas'][0][i].get('machine_name', 'Unknown'),
                description=results['documents'][0][i],
                similarity_score=similarity,
                metadata=results['metadatas'][0][i]
            )

            retrieval_results.append(result)

        logger.info(f"Found {len(retrieval_results)} similar machines")

        return retrieval_results

    def retrieve_by_embedding(
        self,
        embedding: List[float],
        n_results: int = 3,
        min_similarity: float = 0.0
    ) -> List[RetrievalResult]:
        """
        Find similar machines using a raw embedding vector

        This is used by the ask assistant to search by query text.

        Args:
            embedding: Query embedding vector
            n_results: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of RetrievalResult objects, sorted by similarity
        """
        logger.info(f"Retrieving similar machines using direct embedding")

        # Query vector store
        results = self.vector_store.query(
            query_embeddings=[embedding],
            n_results=n_results
        )

        # Process results
        retrieval_results = []

        # Results structure: {ids: [[...]], distances: [[...]], documents: [[...]], metadatas: [[...]]}
        for i in range(len(results['ids'][0])):
            # ChromaDB returns distances (lower is better)
            # Convert to similarity score (higher is better, 0-1 range)
            distance = results['distances'][0][i]
            similarity = 1 / (1 + distance)  # Convert distance to similarity

            # Filter by minimum similarity
            if similarity < min_similarity:
                continue

            result = RetrievalResult(
                machine_name=results['metadatas'][0][i].get('machine_name', 'Unknown'),
                description=results['documents'][0][i],
                similarity_score=similarity,
                metadata=results['metadatas'][0][i]
            )

            retrieval_results.append(result)

        logger.info(f"Found {len(retrieval_results)} similar machines")

        return retrieval_results

    def retrieve_for_csv(
        self,
        parsed_csv: ParsedCSV,
        n_results_per_machine: int = 3
    ) -> Dict[str, List[RetrievalResult]]:
        """
        Retrieve similar examples for all machines in a CSV

        Args:
            parsed_csv: ParsedCSV object
            n_results_per_machine: Results to return per machine

        Returns:
            Dictionary mapping machine names to retrieval results
        """
        results = {}

        for machine in parsed_csv.machines:
            similar = self.retrieve_similar(
                machine=machine,
                n_results=n_results_per_machine
            )
            results[machine.name] = similar

        return results

    def retrieve_by_filters(
        self,
        state_count: Optional[int] = None,
        min_interlocks: Optional[int] = None,
        max_interlocks: Optional[int] = None,
        tags: Optional[List[str]] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve machines by metadata filters (without similarity search)

        Args:
            state_count: Filter by exact state count
            min_interlocks: Minimum number of interlocks
            max_interlocks: Maximum number of interlocks
            tags: List of tags to filter by
            n_results: Number of results

        Returns:
            List of metadata dictionaries
        """
        # Build where clause for ChromaDB
        where = {}

        if state_count is not None:
            where["state_count"] = state_count

        if min_interlocks is not None or max_interlocks is not None:
            # Note: ChromaDB has limited support for range queries
            # This is a simplified implementation
            pass

        # For now, get all and filter in Python
        # (ChromaDB's where clause is limited)
        logger.info(f"Filtering machines with criteria: state_count={state_count}")

        # Get sample embeddings to query
        # We need a dummy query, so we'll just get all
        # This is not ideal but works for small datasets
        # TODO: Improve filtering with better ChromaDB queries

        results = []
        logger.warning("Filter-based retrieval is simplified - returning partial results")

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database

        Returns:
            Dictionary with statistics
        """
        total_count = self.vector_store.count()

        stats = {
            "total_machines_indexed": total_count,
            "collection_name": self.vector_store.collection_name,
            "embedding_dimension": 1536 if self.embedder.model == "text-embedding-3-small" else "unknown"
        }

        return stats


def get_retriever() -> LogicRetriever:
    """
    Get a logic retriever instance

    Returns:
        Initialized LogicRetriever
    """
    return LogicRetriever()
