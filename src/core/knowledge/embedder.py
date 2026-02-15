"""
Embedding Generator

Creates embeddings for L5X routines and rungs using OpenRouter.
Uses text-embedding-3-small (1536 dimensions).
"""

from typing import List, Dict, Any
from openai import OpenAI
from src.config.settings import get_settings
from src.utils.logger import logger

settings = get_settings()


class EmbeddingGenerator:
    """
    Generates embeddings for text using OpenRouter

    Uses text-embedding-3-small for cost-effective, high-quality embeddings.
    """

    def __init__(self):
        """Initialize embedding generator"""
        if settings.embedding_provider == "openrouter":
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url
            )
            self.model = settings.openrouter_embedding_model
        elif settings.embedding_provider == "openai":
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_embedding_model
        else:
            raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")

        logger.info(f"Embedding generator initialized: {self.model}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions)
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding

            return embedding

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            List of embedding vectors
        """
        embeddings = []
        total = len(texts)

        logger.info(f"Embedding {total} texts in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(f"  Batch {batch_num}/{total_batches} ({len(batch)} texts)")

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                for data in response.data:
                    embeddings.append(data.embedding)

            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")
                # Add empty embeddings for failed batch
                embeddings.extend([[0.0] * 1536] * len(batch))

        logger.info(f"✅ Generated {len(embeddings)} embeddings")

        return embeddings


def create_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Convenience function to create embeddings

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    generator = EmbeddingGenerator()
    return generator.embed_batch(texts)
