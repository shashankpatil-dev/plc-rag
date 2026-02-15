"""
Vector Database Interface using ChromaDB

Provides a simple interface to store and retrieve PLC logic embeddings.
Supports both ChromaDB (local) and Pinecone (cloud) backends.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from pathlib import Path
from src.config.settings import get_settings
from src.utils.logger import logger

settings = get_settings()


class VectorStore:
    """
    Vector database for storing and retrieving PLC logic embeddings

    Supports:
    - ChromaDB (local, default)
    - Pinecone (cloud, requires API key)
    """

    def __init__(self, collection_name: str = "plc_embeddings"):
        """
        Initialize vector store

        Args:
            collection_name: Name of the collection to use
        """
        self.collection_name = collection_name
        self.client = None
        self.collection = None

        if settings.vector_db_provider == "chromadb":
            self._init_chromadb()
        elif settings.vector_db_provider == "pinecone":
            self._init_pinecone()
        else:
            raise ValueError(f"Unsupported vector DB provider: {settings.vector_db_provider}")

    def _init_chromadb(self):
        """Initialize ChromaDB client"""
        # Create persistent directory
        db_path = Path("data/embeddings/chromadb")
        db_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at {db_path}")

        # Create client with persistence
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection '{self.collection_name}'")
        except ValueError:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PLC logic patterns and embeddings"}
            )
            logger.info(f"Created new collection '{self.collection_name}'")

    def _init_pinecone(self):
        """Initialize Pinecone client"""
        # TODO: Implement Pinecone support
        raise NotImplementedError("Pinecone support coming soon")

    def add(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Add embeddings to the vector store

        Args:
            embeddings: List of embedding vectors
            documents: List of text documents (for reference)
            metadatas: List of metadata dicts
            ids: List of unique IDs
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        logger.info(f"Adding {len(embeddings)} embeddings to collection")

        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Successfully added {len(embeddings)} embeddings")

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the vector store for similar embeddings

        Args:
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dict with keys: ids, distances, documents, metadatas
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        logger.debug(f"Querying collection for {n_results} results")

        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

        return results

    def get_by_id(self, ids: List[str]) -> Dict:
        """
        Get specific embeddings by ID

        Args:
            ids: List of IDs to retrieve

        Returns:
            Dict with embeddings, documents, metadatas
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        return self.collection.get(ids=ids)

    def delete(self, ids: List[str]) -> None:
        """
        Delete embeddings by ID

        Args:
            ids: List of IDs to delete
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        logger.info(f"Deleting {len(ids)} embeddings")
        self.collection.delete(ids=ids)

    def count(self) -> int:
        """Get total number of embeddings in collection"""
        if not self.collection:
            return 0

        return self.collection.count()

    def reset(self) -> None:
        """Delete all embeddings (use with caution!)"""
        if not self.collection:
            return

        logger.warning(f"Resetting collection '{self.collection_name}'")
        self.client.delete_collection(name=self.collection_name)

        # Recreate empty collection
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "PLC logic patterns and embeddings"}
        )
        logger.info("Collection reset complete")


def get_vector_store(collection_name: str = "plc_embeddings") -> VectorStore:
    """
    Get a vector store instance

    Args:
        collection_name: Name of collection to use

    Returns:
        Initialized VectorStore
    """
    return VectorStore(collection_name=collection_name)
