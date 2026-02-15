#!/usr/bin/env python3
"""
Build Knowledge Base

Parse L5X files, create embeddings, and index to ChromaDB.
This builds the RAG knowledge base for better code generation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.knowledge.l5x_parser import parse_l5x_directory
from src.core.knowledge.embedder import EmbeddingGenerator
from src.core.knowledge.vector_store import get_vector_store
from src.utils.logger import logger


def parse_l5x_files():
    """Step 1: Parse all L5X files"""
    print("=" * 60)
    print("STEP 1: Parse L5X Files")
    print("=" * 60)

    l5x_dir = project_root / "assets" / "l5x"

    print(f"\n📁 Directory: {l5x_dir}")

    # Parse all L5X files
    routines = parse_l5x_directory(str(l5x_dir))

    print(f"\n✅ Parsed {len(routines)} routines")

    # Show statistics
    total_rungs = sum(r.rung_count for r in routines)
    all_instructions = set()
    all_tags = set()

    for routine in routines:
        all_instructions.update(routine.instructions_used)
        all_tags.update(routine.tags_used)

    print(f"\n📊 Statistics:")
    print(f"   Total routines: {len(routines)}")
    print(f"   Total rungs: {total_rungs}")
    print(f"   Unique instructions: {len(all_instructions)}")
    print(f"   Unique tags: {len(all_tags)}")

    # Show sample routines
    print(f"\n📋 Sample Routines (first 5):")
    for routine in routines[:5]:
        print(f"   - {routine.name} ({routine.rung_count} rungs) from {routine.source_file}")

    return routines


def create_embeddings_for_routines(routines):
    """Step 2: Create embeddings"""
    print("\n" + "=" * 60)
    print("STEP 2: Create Embeddings")
    print("=" * 60)

    print(f"\n🤖 Using: text-embedding-3-small (1536 dimensions)")
    print(f"   Items to embed: {len(routines)} routines")

    # Prepare texts for embedding
    routine_texts = []
    for routine in routines:
        text = routine.to_text()
        routine_texts.append(text)

    # Create embeddings
    embedder = EmbeddingGenerator()

    print(f"\n⏳ Generating embeddings...")
    embeddings = embedder.embed_batch(routine_texts, batch_size=50)

    print(f"\n✅ Created {len(embeddings)} embeddings")
    print(f"   Dimension: {len(embeddings[0])}")

    # Estimate cost
    total_tokens = sum(len(text.split()) for text in routine_texts)
    cost = (total_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens

    print(f"\n💰 Cost Estimate:")
    print(f"   Tokens: ~{total_tokens:,}")
    print(f"   Cost: ~${cost:.4f}")

    return embeddings


def index_to_chromadb(routines, embeddings):
    """Step 3: Index to ChromaDB"""
    print("\n" + "=" * 60)
    print("STEP 3: Index to ChromaDB")
    print("=" * 60)

    # Get vector store
    vector_store = get_vector_store()

    # Reset collection (fresh start)
    print(f"\n🗑️  Resetting collection...")
    try:
        vector_store.client.delete_collection(name="plc_client_routines")
        print(f"   Deleted old collection")
    except:
        print(f"   No old collection found")

    # Create fresh collection
    collection = vector_store.client.create_collection(
        name="plc_client_routines",
        metadata={"dimension": 1536, "description": "Client L5X routines"}
    )

    print(f"✅ Created collection: plc_client_routines")

    # Prepare documents and metadata
    documents = []
    metadatas = []
    ids = []

    for i, routine in enumerate(routines):
        # Document: searchable text
        documents.append(routine.to_text())

        # Metadata: structured data
        metadatas.append({
            "routine_name": routine.name,
            "routine_type": routine.type,
            "source_file": routine.source_file,
            "rung_count": routine.rung_count,
            "instructions": ",".join(routine.instructions_used[:10]),  # Limit size
            "description": routine.description[:200]  # Limit size
        })

        # ID: unique identifier
        ids.append(f"routine_{i}")

    # Add to collection
    print(f"\n⏳ Indexing {len(documents)} routines...")

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    print(f"✅ Indexed {len(documents)} routines to ChromaDB")

    return collection


def test_retrieval(collection):
    """Step 4: Test retrieval"""
    print("\n" + "=" * 60)
    print("STEP 4: Test Retrieval")
    print("=" * 60)

    test_queries = [
        "safety logic emergency stop",
        "conveyor start stop control",
        "timer delay sequence",
        "fault handling error",
    ]

    # Create embedder for queries
    embedder = EmbeddingGenerator()

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")

        # Create embedding for query
        query_embedding = embedder.embed_text(query)

        # Query with embedding (not text)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        print(f"   Top 3 results:")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"\n   {i}. {metadata['routine_name']}")
            print(f"      Source: {metadata['source_file']}")
            print(f"      Rungs: {metadata['rung_count']}")
            print(f"      Distance: {distance:.4f}")
            print(f"      Preview: {doc[:150]}...")


def main():
    """Build complete knowledge base"""
    print("\n🏗️  Building PLC-RAG Knowledge Base\n")

    try:
        # Step 1: Parse L5X files
        routines = parse_l5x_files()

        if not routines:
            print("\n❌ No routines found. Check L5X files.")
            return 1

        # Step 2: Create embeddings
        embeddings = create_embeddings_for_routines(routines)

        # Step 3: Index to ChromaDB
        collection = index_to_chromadb(routines, embeddings)

        # Step 4: Test retrieval
        test_retrieval(collection)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"\n✅ Knowledge base built successfully!")
        print(f"\n📊 Statistics:")
        print(f"   L5X files parsed: 9")
        print(f"   Routines indexed: {len(routines)}")
        print(f"   Total rungs: {sum(r.rung_count for r in routines)}")
        print(f"   ChromaDB collection: plc_client_routines")
        print(f"   Embedding dimensions: 1536")

        print(f"\n✨ Next steps:")
        print(f"   1. Test RAG-enhanced generation")
        print(f"   2. Compare quality with/without RAG")
        print(f"   3. Extract style profiles")

        return 0

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
