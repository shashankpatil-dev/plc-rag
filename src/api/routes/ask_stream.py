"""
Streaming Ask Assistant Route
Real-time streaming responses for better UX
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator
import json
import asyncio
from src.core.knowledge.embedder import EmbeddingGenerator
from src.core.knowledge.vector_store import get_vector_store
from src.core.rag.generator import LLMGenerator
from src.utils.logger import logger

router = APIRouter()


class StreamAskRequest(BaseModel):
    """Request for streaming assistant"""
    query: str
    n_examples: int = 3


async def stream_response(query: str, n_examples: int = 3) -> AsyncGenerator[str, None]:
    """
    Stream response in chunks for better UX

    Yields JSON chunks:
    - {"type": "status", "message": "Searching knowledge base..."}
    - {"type": "example", "data": {...}}
    - {"type": "content", "text": "chunk of answer"}
    - {"type": "done"}
    """
    try:
        # Status: Starting
        yield f"data: {json.dumps({'type': 'status', 'message': 'Thinking...'})}\n\n"
        await asyncio.sleep(0.1)

        # Step 1: Search knowledge base
        yield f"data: {json.dumps({'type': 'status', 'message': 'Searching knowledge base...'})}\n\n"

        embedder = EmbeddingGenerator()
        query_embedding = embedder.embed_text(query)

        vector_store = get_vector_store()
        collection = vector_store.client.get_collection("plc_client_routines")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_examples
        )

        documents = results['documents'][0] if results['documents'] else []
        distances = results['distances'][0] if results['distances'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []

        logger.info(f"Stream: Retrieved {len(documents)} examples")

        # Step 2: Send examples
        yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(documents)} relevant examples...'})}\n\n"
        await asyncio.sleep(0.2)

        for doc, meta, dist in zip(documents, metadatas, distances):
            example_data = {
                "routine_name": meta.get('routine_name', 'Unknown'),
                "similarity_score": 1 - (dist / 2),
                "rung_count": int(meta.get('rung_count', 0)),
                "source_file": meta.get('source_file', 'Unknown'),
                "code_preview": doc[:600]  # Shorter preview for better UX
            }
            yield f"data: {json.dumps({'type': 'example', 'data': example_data})}\n\n"
            await asyncio.sleep(0.1)

        # Step 3: Generate answer
        yield f"data: {json.dumps({'type': 'status', 'message': 'Generating answer...'})}\n\n"

        # Build context
        context_parts = []
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
            routine_name = meta.get('routine_name', 'Unknown')
            source = meta.get('source_file', 'Unknown')

            context_parts.append(f"\n## Example {i}: {routine_name}")
            context_parts.append(f"Source: {source}")
            preview = doc[:1200]
            context_parts.append(f"\n```\n{preview}\n```")

        context = "\n".join(context_parts)

        # Generate with LLM
        llm = LLMGenerator()

        prompt = f"""You are a helpful PLC coding assistant. Answer questions using the examples below.

**IMPORTANT**:
- Keep response SIMPLE and READABLE
- Use clear headings and short paragraphs
- Show code examples in simple blocks
- Be conversational and friendly
- Focus on practical explanation

**Question**: {query}

**Examples from Knowledge Base**:
{context}

**Instructions**:
- Answer in markdown format
- Keep it concise but complete
- Use simple language
- Show specific code snippets
- Be helpful and clear

**Answer**:"""

        # Get full response (in production, you'd stream from LLM)
        full_answer = llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1500
        )

        # Stream answer in chunks for typing effect (preserve newlines!)
        # Split by spaces but keep newlines
        import re

        # Split content into chunks while preserving line breaks
        lines = full_answer.split('\n')
        newline_char = '\n'

        for line in lines:
            if line.strip():  # If line has content
                # Split line into words
                words = line.split()
                chunk_size = 8  # Words per chunk

                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i + chunk_size]) + ' '
                    yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"
                    await asyncio.sleep(0.03)  # Typing effect delay

            # Send newline to preserve formatting
            yield f"data: {json.dumps({'type': 'content', 'text': newline_char})}\n\n"
            await asyncio.sleep(0.02)

        # Done
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        logger.info("Stream: Complete")

    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.get("/ask-stream")
async def ask_assistant_stream(query: str, n_examples: int = 3):
    """
    Streaming assistant endpoint (GET for EventSource compatibility)

    Returns Server-Sent Events (SSE) stream with:
    - Status updates
    - Code examples
    - Streamed answer text
    """
    return StreamingResponse(
        stream_response(query, n_examples),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
