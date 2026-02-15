"""
Ask Assistant Route
NLP query endpoint for personalized code assistance
Like Copilot, but ONLY trained on your codebase
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.core.knowledge.embedder import EmbeddingGenerator
from src.core.knowledge.vector_store import get_vector_store
from src.core.rag.generator import LLMGenerator
from src.utils.logger import logger

router = APIRouter()


class AskRequest(BaseModel):
    """Request model for code assistance query"""
    query: str
    n_examples: int = 3  # Number of code examples to retrieve
    include_code: bool = True  # Include full code examples in response


class CodeExample(BaseModel):
    """Code example from knowledge base"""
    routine_name: str
    similarity_score: float
    rung_count: int
    source_file: str
    code_preview: Optional[str] = None


class AskResponse(BaseModel):
    """Response model for code assistance"""
    query: str
    answer: str  # Markdown formatted
    code_examples: List[CodeExample]
    examples_used: int


@router.post("/ask", response_model=AskResponse)
async def ask_assistant(request: AskRequest) -> AskResponse:
    """
    Ask your personalized coding assistant about PLC patterns

    Uses RAG with ChromaDB to retrieve relevant examples from your knowledge base.

    Args:
        request: Query and options

    Returns:
        Markdown-formatted answer with code examples
    """
    logger.info(f"Assistant query: {request.query}")

    try:
        # Step 1: Create query embedding
        embedder = EmbeddingGenerator()
        query_embedding = embedder.embed_text(request.query)

        # Step 2: Retrieve similar routines from ChromaDB
        vector_store = get_vector_store()
        collection = vector_store.client.get_collection("plc_client_routines")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.n_examples
        )

        documents = results['documents'][0] if results['documents'] else []
        distances = results['distances'][0] if results['distances'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []

        logger.info(f"Retrieved {len(documents)} relevant routines")

        if not documents:
            return AskResponse(
                query=request.query,
                answer="No relevant examples found in the knowledge base. Try asking about PLC patterns, timers, or ladder logic.",
                code_examples=[],
                examples_used=0
            )

        # Step 3: Build context from retrieved routines
        context_parts = []
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
            routine_name = meta.get('routine_name', 'Unknown')
            source = meta.get('source_file', 'Unknown')
            rung_count = meta.get('rung_count', 0)

            context_parts.append(f"\n## Example {i}: {routine_name}")
            context_parts.append(f"- Source: {source}")
            context_parts.append(f"- Rungs: {rung_count}")
            context_parts.append(f"- Match Quality: {(1 - dist / 2) * 100:.1f}%")  # Distance to similarity

            if request.include_code:
                # Show first 1500 chars of routine code
                preview = doc[:1500]
                if len(doc) > 1500:
                    preview += "\n... (truncated)"
                context_parts.append(f"\n```\n{preview}\n```")

        context = "\n".join(context_parts)

        # Step 4: Generate markdown-formatted answer
        llm = LLMGenerator()

        prompt = f"""You are a PLC coding assistant trained on real client code. Answer questions using ONLY the examples below.

**IMPORTANT RULES:**
1. Format response in **well-structured Markdown**
2. Use code blocks with ```xml for L5X code
3. Reference specific routines from the examples
4. Match the exact coding style from the examples
5. If something isn't in the examples, say so clearly

**User Question:** {request.query}

**Retrieved Examples from Knowledge Base:**
{context}

**Instructions:**
- Answer in clear, structured Markdown
- Use headings, bullet points, and code blocks
- Show specific code snippets from the examples
- Explain which routine/pattern you're referencing
- Be concise but thorough

**Answer:**"""

        answer = llm.generate(
            prompt=prompt,
            temperature=0.3,  # Slightly creative for explanations
            max_tokens=2000
        )

        # Step 5: Format code examples for UI
        examples = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            examples.append(CodeExample(
                routine_name=meta.get('routine_name', 'Unknown'),
                similarity_score=1 - (dist / 2),  # Convert distance to similarity
                rung_count=int(meta.get('rung_count', 0)),
                source_file=meta.get('source_file', 'Unknown'),
                code_preview=doc[:800] if request.include_code else None
            ))

        logger.info(f"Generated markdown answer using {len(examples)} examples")

        return AskResponse(
            query=request.query,
            answer=answer,
            code_examples=examples,
            examples_used=len(examples)
        )

    except Exception as e:
        logger.error(f"Assistant error: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/ask/suggestions")
async def get_query_suggestions() -> Dict[str, List[str]]:
    """
    Get suggested queries to try

    Returns:
        Dictionary of query categories with example queries
    """
    return {
        "structure": [
            "How do I structure UDT_Sequencer?",
            "Show me the UDT_Machine structure",
            "What data types do you use?",
        ],
        "ladder_logic": [
            "How do I write timer rungs?",
            "Show me interlock logic examples",
            "How to implement state transitions?",
        ],
        "patterns": [
            "How do you handle Hold/Continue?",
            "Show me the Reset pattern",
            "How to structure conveyor logic?",
        ],
        "specific": [
            "How many timers in UDT_Sequencer?",
            "What's the bit packing pattern?",
            "Show me Input/Output array usage",
        ]
    }
