"""RAG core: embed queries, retrieve chunks from Qdrant, build prompts, stream responses."""

import json
from collections.abc import AsyncGenerator

from openai import OpenAI
from qdrant_client import QdrantClient

from config import settings

COLLECTION_NAME = "physical-ai-book"

SYSTEM_PROMPT = """You are a helpful teaching assistant for the "Physical AI & Humanoid Robotics" textbook.
Answer questions using ONLY the provided context from the book.
If the context does not contain enough information to answer, say "I don't have enough information from the book to answer that."

Rules:
- Be concise and educational.
- Reference which book section your answer comes from (page path and section title).
- Format source references at the end as: **Sources:** followed by a bulleted list.
- Use code examples from the book when relevant.
- Do not make up information not present in the context."""

SELECTED_TEXT_SYSTEM_PROMPT = """You are a helpful teaching assistant for the "Physical AI & Humanoid Robotics" textbook.
Answer the question using ONLY the provided text excerpt. Do not use any other knowledge.
If the question cannot be answered from the excerpt alone, say so clearly.

Rules:
- Be concise and educational.
- Only reference the provided excerpt — do not bring in outside information.
- If the excerpt is code, explain what it does step by step."""


def embed_query(client: OpenAI, query: str) -> list[float]:
    """Embed a single query string via OpenRouter embeddings endpoint."""
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=[query],
    )
    return response.data[0].embedding


def retrieve_chunks(qdrant: QdrantClient, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """Search Qdrant for the most relevant book chunks."""
    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
    )
    return [
        {
            "text": hit.payload["text"],
            "source": hit.payload.get("source", ""),
            "section_title": hit.payload.get("section_title", ""),
            "page_title": hit.payload.get("page_title", ""),
            "score": hit.score,
        }
        for hit in results.points
    ]


def build_prompt(
    question: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> list[dict]:
    """Build messages array for general Q&A with retrieved context."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"[{chunk['source']} > {chunk['section_title']}]"
        context_parts.append(f"--- Context {i} {source_info} ---\n{chunk['text']}")

    context_block = "\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Book context:\n\n{context_block}"},
        {"role": "assistant", "content": "I've read the provided book context. What would you like to know?"},
    ]

    # Append conversation history
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Append current question
    messages.append({"role": "user", "content": question})

    return messages


def build_selected_text_prompt(
    question: str,
    selected_text: str,
    history: list[dict] | None = None,
) -> list[dict]:
    """Build messages array for selected-text mode (no retrieval)."""
    messages = [
        {"role": "system", "content": SELECTED_TEXT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Text excerpt:\n\n{selected_text}"},
        {"role": "assistant", "content": "I've read the excerpt. What would you like to know about it?"},
    ]

    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    return messages


async def generate_response_stream(
    client: OpenAI,
    messages: list[dict],
    sources: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream chat completion from OpenRouter as SSE-formatted events."""
    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=messages,
        stream=True,
        max_tokens=1024,
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            yield f"data: {json.dumps({'content': content})}\n\n"

    # Send sources with the final event
    if sources:
        source_data = [
            {
                "source": s.get("source", ""),
                "section_title": s.get("section_title", ""),
                "score": round(s.get("score", 0), 3),
            }
            for s in sources
        ]
        yield f"data: {json.dumps({'sources': source_data})}\n\n"

    yield "data: [DONE]\n\n"
