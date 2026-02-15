"""
Training Data Indexer

Indexes CSV+L5X pairs from the training data directory into the vector database.
Each machine gets its own embedding based on its logic pattern.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import re
from src.core.parser.csv_parser import parse_csv_file
from src.core.rag.embedder import get_embedder
from src.core.knowledge.vector_store import get_vector_store
from src.api.models.csv_models import MachineLogic
from src.utils.logger import logger


class TrainingDataIndexer:
    """
    Index training data (CSV + L5X pairs) into vector database

    Workflow:
    1. Find all training examples in data/training/
    2. Parse CSV files to extract machine logic
    3. Read corresponding L5X files
    4. Generate embeddings for each machine
    5. Store in vector database with metadata
    """

    def __init__(self, training_dir: str = "data/training"):
        """
        Initialize indexer

        Args:
            training_dir: Path to training data directory
        """
        self.training_dir = Path(training_dir)
        self.embedder = get_embedder()
        self.vector_store = get_vector_store()

        logger.info(f"Initialized indexer for {self.training_dir}")

    def _extract_udt_sections(self, l5x_content: str) -> str:
        """
        Extract UDT (User Defined Type) sections from L5X XML

        Args:
            l5x_content: Full L5X XML content

        Returns:
            Extracted UDT sections as string
        """
        try:
            # Extract DataTypes section which contains UDTs
            # Account for tabs and whitespace
            udt_match = re.search(
                r'<DataTypes>\s*(.*?)\s*</DataTypes>',
                l5x_content,
                re.DOTALL
            )

            if udt_match:
                datatypes_section = udt_match.group(1)

                # Truncate if too long (keep first 13000 chars to include full DataTypes section)
                if len(datatypes_section) > 13000:
                    datatypes_section = datatypes_section[:13000] + "\n...(truncated)"

                logger.info(f"Extracted DataTypes section ({len(datatypes_section)} chars)")
                return f"<DataTypes>\n{datatypes_section}\n</DataTypes>"

            # Fallback to first 2000 chars if no DataTypes found
            logger.warning("No DataTypes section found, using first 2000 chars")
            return l5x_content[:2000]

        except Exception as e:
            logger.warning(f"Failed to extract UDT sections: {e}")
            return l5x_content[:2000]

    def _generate_id(self, machine_name: str, source_file: str) -> str:
        """
        Generate unique ID for a machine embedding

        Args:
            machine_name: Name of the machine
            source_file: Source CSV filename

        Returns:
            Unique ID string
        """
        # Create hash from machine name + source file
        content = f"{machine_name}:{source_file}"
        return hashlib.md5(content.encode()).hexdigest()

    def _create_metadata(
        self,
        machine: MachineLogic,
        source_csv: str,
        l5x_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create metadata for a machine embedding

        Args:
            machine: MachineLogic object
            source_csv: Path to source CSV file
            l5x_path: Optional path to L5X file

        Returns:
            Metadata dictionary
        """
        metadata = {
            "machine_name": machine.name,
            "state_count": machine.state_count,
            "interlock_count": machine.total_interlock_count,
            "source_csv": source_csv,
            "interlocks": ",".join(machine.all_interlocks),  # Comma-separated for filtering
            "cycle_length": len(machine.cycle_path),
        }

        if l5x_path:
            metadata["l5x_file"] = l5x_path

        # Add pattern tags for easier filtering
        tags = []
        if machine.state_count >= 10:
            tags.append("multi-step")
        if machine.total_interlock_count > 5:
            tags.append("complex-interlocks")
        if machine.state_count == 12:
            tags.append("12-state-machine")

        if tags:
            metadata["tags"] = ",".join(tags)

        return metadata

    def index_example(self, example_dir: Path) -> int:
        """
        Index a single training example (CSV + L5X pair)

        Args:
            example_dir: Path to example directory

        Returns:
            Number of machines indexed
        """
        logger.info(f"Indexing example: {example_dir.name}")

        # Find CSV file
        csv_files = list(example_dir.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV file found in {example_dir}")
            return 0

        csv_path = csv_files[0]

        # Find L5X file
        l5x_files = list(example_dir.glob("*.l5x")) + list(example_dir.glob("*.L5X"))
        l5x_path = l5x_files[0] if l5x_files else None

        # Parse CSV
        with open(csv_path, 'r') as f:
            csv_content = f.read()

        try:
            parsed = parse_csv_file(csv_content)
        except Exception as e:
            logger.error(f"Failed to parse {csv_path}: {e}")
            return 0

        # Read L5X content if available
        l5x_content = None
        if l5x_path:
            try:
                with open(l5x_path, 'r') as f:
                    l5x_content = f.read()
                logger.info(f"Loaded L5X file: {l5x_path.name}")
            except Exception as e:
                logger.warning(f"Could not read L5X file: {e}")

        # Generate embeddings for each machine
        embeddings_data = self.embedder.embed_machines(parsed.machines)

        # Prepare data for vector store
        embeddings = []
        documents = []
        metadatas = []
        ids = []

        for machine, (description, embedding) in zip(parsed.machines, embeddings_data):
            # Generate unique ID
            machine_id = self._generate_id(machine.name, csv_path.name)

            # Create metadata
            metadata = self._create_metadata(
                machine,
                str(csv_path.relative_to(self.training_dir)),
                str(l5x_path.relative_to(self.training_dir)) if l5x_path else None
            )

            # Add L5X content to metadata if available
            if l5x_content:
                # Extract and store UDT sections (more useful than just first 1000 chars)
                metadata["l5x_preview"] = self._extract_udt_sections(l5x_content)

                # Also store controller info (first 500 chars for context)
                metadata["l5x_header"] = l5x_content[:500]

            embeddings.append(embedding)
            documents.append(description)
            metadatas.append(metadata)
            ids.append(machine_id)

        # Add to vector store
        self.vector_store.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Indexed {len(embeddings)} machines from {example_dir.name}")
        return len(embeddings)

    def index_all(self) -> int:
        """
        Index all training examples in the training directory

        Returns:
            Total number of machines indexed
        """
        if not self.training_dir.exists():
            logger.error(f"Training directory not found: {self.training_dir}")
            return 0

        # Find all example subdirectories
        example_dirs = [
            d for d in self.training_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

        if not example_dirs:
            logger.warning(f"No training examples found in {self.training_dir}")
            return 0

        total_indexed = 0

        logger.info(f"Found {len(example_dirs)} training example(s)")

        for example_dir in example_dirs:
            try:
                count = self.index_example(example_dir)
                total_indexed += count
            except Exception as e:
                logger.error(f"Error indexing {example_dir}: {e}")
                continue

        logger.info(f"Indexing complete: {total_indexed} total machines indexed")
        return total_indexed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about indexed data

        Returns:
            Dictionary with statistics
        """
        total_count = self.vector_store.count()

        return {
            "total_embeddings": total_count,
            "collection_name": self.vector_store.collection_name,
            "provider": self.vector_store.client.__class__.__name__
        }


def get_indexer(training_dir: str = "data/training") -> TrainingDataIndexer:
    """
    Get a training data indexer instance

    Args:
        training_dir: Path to training directory

    Returns:
        Initialized TrainingDataIndexer
    """
    return TrainingDataIndexer(training_dir=training_dir)
