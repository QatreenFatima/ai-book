"""FastAPI application: health check, chat, ingest endpoints."""

import json
import subprocess
import sys
from pathlib import Path

import asyncpg
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from qdrant_client import QdrantClient

import db
import rag
from config import settings


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    selected_text: str | None = None


# Shared clients (initialized lazily for serverless compatibility)
_openai_client: OpenAI | None = None
_qdrant_client: QdrantClient | None = None
_db_pool: asyncpg.Pool | None = None


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
    return _openai_client


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return _qdrant_client


async def get_db_pool() -> asyncpg.Pool:
    global _db_pool
    if _db_pool is None:
        _db_pool = await db.create_pool()
        await db.init_db(_db_pool)
    return _db_pool


app = FastAPI(
    title="Physical AI Book RAG Chatbot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ],
    allow_origin_regex=r"https://.*\.(vercel\.app|github\.io)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-Id"],
)


@app.get("/api/health")
async def health_check():
    """Check status of all dependent services."""
    services = {"backend": "up", "postgres": "down", "vector_db": "down", "llm": "down"}

    # Check Postgres
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["postgres"] = "up"
    except Exception:
        pass

    # Check Qdrant
    try:
        get_qdrant_client().get_collections()
        services["vector_db"] = "up"
    except Exception:
        pass

    # Check OpenRouter
    try:
        get_openai_client().models.list()
        services["llm"] = "up"
    except Exception:
        pass

    all_up = all(v == "up" for v in services.values())
    any_down = any(v == "down" for v in services.values())

    if all_up:
        status = "healthy"
    elif any_down and services["backend"] == "up":
        status = "degraded"
    else:
        status = "unhealthy"

    return {"status": status, "services": services}


@app.post("/api/chat")
async def chat(request: Request, body: ChatRequest):
    """Send a chat message and receive a streamed SSE response."""
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(body.message) > 2000:
        raise HTTPException(status_code=400, detail="Message exceeds 2000 character limit")

    pool = await get_db_pool()
    openai_client = get_openai_client()
    qdrant_client = get_qdrant_client()

    # Create or validate session
    if body.session_id:
        session = await db.get_session(pool, body.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = body.session_id
    else:
        session_id = await db.create_session(pool)

    # Save user message
    await db.create_message(pool, session_id, "user", body.message)

    # Load conversation history
    history_rows = await db.get_messages_by_session(pool, session_id)
    history = [{"role": m["role"], "content": m["content"]} for m in history_rows[:-1]]

    # Build prompt based on mode
    sources = None
    if body.selected_text and body.selected_text.strip():
        messages = rag.build_selected_text_prompt(body.message, body.selected_text, history)
    else:
        try:
            query_embedding = rag.embed_query(openai_client, body.message)
            chunks = rag.retrieve_chunks(qdrant_client, query_embedding, top_k=5)
            sources = chunks
        except Exception:
            raise HTTPException(status_code=503, detail="Retrieval service unavailable")
        messages = rag.build_prompt(body.message, chunks, history)

    collected_content = []

    async def stream_and_collect():
        try:
            async for event in rag.generate_response_stream(openai_client, messages, sources):
                if event.startswith("data: ") and event.strip() != "data: [DONE]":
                    try:
                        data = json.loads(event[6:].strip())
                        if "content" in data:
                            collected_content.append(data["content"])
                    except (json.JSONDecodeError, KeyError):
                        pass
                yield event
        except Exception:
            yield 'data: {"error": "Stream interrupted. Please try again."}\n\n'
            yield "data: [DONE]\n\n"

        full_response = "".join(collected_content)
        if full_response:
            source_refs = None
            if sources:
                source_refs = [
                    {"source": s["source"], "section_title": s["section_title"], "score": round(s["score"], 3)}
                    for s in sources
                ]
            await db.create_message(pool, session_id, "assistant", full_response, source_refs)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "X-Session-Id": session_id,
    }

    return StreamingResponse(
        stream_and_collect(),
        media_type="text/event-stream",
        headers=headers,
    )


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Retrieve chat history for a session."""
    pool = await get_db_pool()
    session = await db.get_session(pool, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await db.get_messages_by_session(pool, session_id)
    return {"session_id": session_id, "messages": messages}


@app.post("/api/ingest")
async def ingest_docs(
    x_admin_key: str = Header(None, alias="X-Admin-Key"),
):
    """Re-index book content into Qdrant. Requires admin API key."""
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")

    ingest_script = Path(__file__).parent / "ingest.py"
    docs_path = Path(__file__).parent.parent / "docs"

    if not docs_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Docs directory not found: {docs_path}")

    try:
        result = subprocess.run(
            [sys.executable, str(ingest_script), "--docs-path", str(docs_path), "--reset"],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Ingestion timed out after 5 minutes")

    output_lines = result.stdout.strip().split("\n") if result.stdout else []
    files_processed = 0
    chunks_created = 0
    errors = []

    for line in output_lines:
        if "Files processed:" in line:
            files_processed = int(line.split(":")[-1].strip())
        elif "Chunks created:" in line:
            chunks_created = int(line.split(":")[-1].strip())
        elif line.strip().startswith("- "):
            errors.append(line.strip()[2:])

    if result.returncode != 0:
        errors.append(result.stderr.strip() if result.stderr else "Unknown error")

    return {
        "status": "completed" if result.returncode == 0 else "failed",
        "files_processed": files_processed,
        "chunks_created": chunks_created,
        "errors": errors,
    }
