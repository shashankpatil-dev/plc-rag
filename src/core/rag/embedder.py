"""
Embedding Generator for PLC Logic Patterns

Converts CSV logic structures into semantic text descriptions
and generates embeddings using OpenAI or Google Gemini embedding models.
"""
from typing import List
from openai import OpenAI
import google.generativeai as genai
from src.api.models.csv_models import MachineLogic, ParsedCSV
from src.config.settings import get_settings
from src.utils.logger import logger

settings = get_settings()


class EmbeddingGenerator:
    """
    Generate embeddings for PLC logic patterns

    Supports:
    - OpenAI text-embedding-3-small
    - Google Gemini text-embedding-004 (FREE!)
    - OpenRouter (uses OpenAI embeddings)
    """

    def __init__(self):
        """Initialize embedding generator"""
        # Use separate embedding provider (can be different from LLM provider)
        self.provider = settings.embedding_provider

        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_embedding_model
            self.embedding_dim = 1536  # OpenAI embedding dimension
            logger.info(f"Initialized OpenAI embeddings with model: {self.model}")

        elif self.provider == "gemini":
            if not settings.google_api_key:
                raise ValueError("GOOGLE_API_KEY not set in environment")
            genai.configure(api_key=settings.google_api_key)
            self.model = "models/text-embedding-004"  # Latest Gemini embedding model
            self.embedding_dim = 768  # Gemini embedding dimension
            logger.info(f"Initialized Gemini embeddings with model: {self.model}")

        elif self.provider == "openrouter":
            # OpenRouter uses OpenAI-compatible API for embeddings
            if not settings.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY not set in environment")
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url
            )
            # Use OpenAI's embedding model through OpenRouter
            self.model = "openai/text-embedding-3-small"
            self.embedding_dim = 1536
            logger.info(f"Initialized OpenRouter embeddings with model: {self.model}")

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def create_semantic_description(self, machine: MachineLogic) -> str:
        """
        Create a semantic text description of a machine's logic

        This description captures the essence of the state machine
        for similarity matching.

        Args:
            machine: MachineLogic object to describe

        Returns:
            Semantic text description
        """
        # Build description
        description_parts = [
            f"Machine: {machine.name}",
            f"Type: Conveyor state machine control system",
            f"Total States: {machine.state_count}",
            f"State Cycle: {' -> '.join(map(str, machine.cycle_path))}",
        ]

        # Add interlock information
        if machine.total_interlock_count > 0:
            description_parts.append(
                f"Interlocks: {machine.total_interlock_count} unique sensors"
            )
            description_parts.append(
                f"Interlock Tags: {', '.join(machine.all_interlocks[:10])}"  # First 10
            )

        # Add state descriptions (first few states for context)
        description_parts.append("Key States:")
        for state in machine.states[:5]:  # First 5 states
            interlock_desc = f"with interlocks {', '.join(state.interlocks)}" if state.interlocks else "no interlocks"
            description_parts.append(
                f"  Step {state.step}: {state.description} ({interlock_desc}, "
                f"condition: {state.condition}, next: {state.next_step})"
            )

        # Pattern identification
        patterns = []
        if machine.state_count >= 10:
            patterns.append("multi-step sequence")
        if machine.total_interlock_count > 5:
            patterns.append("complex interlock logic")
        if any(state.interlock_count > 2 for state in machine.states):
            patterns.append("multiple safety conditions")

        if patterns:
            description_parts.append(f"Patterns: {', '.join(patterns)}")

        return "\n".join(description_parts)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats)
        """
        if self.provider == "openai" or self.provider == "openrouter":
            # Both use OpenAI-compatible API
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding

        elif self.provider == "gemini":
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"  # For indexing documents
            )
            return result['embedding']

        raise NotImplementedError(f"Embedding generation not implemented for {self.provider}")

    def embed_machine(self, machine: MachineLogic) -> tuple[str, List[float]]:
        """
        Create semantic description and embedding for a machine

        Args:
            machine: MachineLogic to embed

        Returns:
            Tuple of (description, embedding)
        """
        description = self.create_semantic_description(machine)
        embedding = self.generate_embedding(description)

        logger.debug(f"Generated embedding for {machine.name}: {len(embedding)} dimensions")

        return description, embedding

    def embed_machines(self, machines: List[MachineLogic]) -> List[tuple[str, List[float]]]:
        """
        Embed multiple machines

        Args:
            machines: List of MachineLogic objects

        Returns:
            List of (description, embedding) tuples
        """
        results = []

        logger.info(f"Generating embeddings for {len(machines)} machines")

        for machine in machines:
            description, embedding = self.embed_machine(machine)
            results.append((description, embedding))

        logger.info(f"Successfully generated {len(results)} embeddings")

        return results

    def embed_csv(self, parsed_csv: ParsedCSV) -> List[tuple[str, List[float]]]:
        """
        Embed all machines in a parsed CSV

        Args:
            parsed_csv: ParsedCSV object

        Returns:
            List of (description, embedding) tuples
        """
        return self.embed_machines(parsed_csv.machines)

    def generate_query_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a query (used in retrieval)

        For Gemini, uses task_type="retrieval_query" instead of "retrieval_document"

        Args:
            text: Query text

        Returns:
            Embedding vector
        """
        if self.provider == "openai" or self.provider == "openrouter":
            # OpenAI/OpenRouter don't distinguish between document and query embeddings
            return self.generate_embedding(text)

        elif self.provider == "gemini":
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_query"  # For queries
            )
            return result['embedding']

        raise NotImplementedError(f"Query embedding not implemented for {self.provider}")


def get_embedder() -> EmbeddingGenerator:
    """
    Get an embedding generator instance

    Returns:
        Initialized EmbeddingGenerator
    """
    return EmbeddingGenerator()
