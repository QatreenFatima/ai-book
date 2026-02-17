"""Neon Postgres: connection pool, schema init, session/message CRUD."""

import json
import uuid
from datetime import datetime, timezone

import asyncpg

from config import settings


async def create_pool() -> asyncpg.Pool:
    """Create and return an asyncpg connection pool."""
    return await asyncpg.create_pool(
        settings.neon_db_url,
        min_size=2,
        max_size=10,
    )


async def init_db(pool: asyncpg.Pool) -> None:
    """Create sessions and messages tables if they don't exist."""
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata JSONB
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                sources JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id
            ON messages(session_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_created_at
            ON messages(created_at DESC)
        """)


async def create_session(pool: asyncpg.Pool, metadata: dict | None = None) -> str:
    """Create a new chat session and return its UUID."""
    session_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (id, metadata) VALUES ($1, $2)",
            uuid.UUID(session_id),
            json.dumps(metadata) if metadata else None,
        )
    return session_id


async def get_session(pool: asyncpg.Pool, session_id: str) -> dict | None:
    """Fetch a session by ID. Returns None if not found."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, created_at, updated_at, metadata FROM sessions WHERE id = $1",
            uuid.UUID(session_id),
        )
    if row is None:
        return None
    return {
        "id": str(row["id"]),
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "metadata": row["metadata"],
    }


async def create_message(
    pool: asyncpg.Pool,
    session_id: str,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> int:
    """Insert a message into a session. Returns the message ID."""
    async with pool.acquire() as conn:
        msg_id = await conn.fetchval(
            """INSERT INTO messages (session_id, role, content, sources)
               VALUES ($1, $2, $3, $4)
               RETURNING id""",
            uuid.UUID(session_id),
            role,
            content,
            json.dumps(sources) if sources else None,
        )
        # Update session's updated_at timestamp
        await conn.execute(
            "UPDATE sessions SET updated_at = $1 WHERE id = $2",
            datetime.now(timezone.utc),
            uuid.UUID(session_id),
        )
    return msg_id


async def get_messages_by_session(pool: asyncpg.Pool, session_id: str) -> list[dict]:
    """Fetch all messages for a session, ordered by creation time."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, role, content, sources, created_at
               FROM messages
               WHERE session_id = $1
               ORDER BY created_at ASC""",
            uuid.UUID(session_id),
        )
    return [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "sources": json.loads(row["sources"]) if row["sources"] else None,
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]
