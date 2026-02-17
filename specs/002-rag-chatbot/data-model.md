# Data Model: RAG Chatbot

**Feature**: 002-rag-chatbot
**Date**: 2026-02-14

## Relational Database (Neon Postgres)

### Entity: Session

Represents a chat conversation between a reader and the chatbot.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique session identifier |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Session creation time |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last activity time |
| metadata | JSONB | NULLABLE | Optional session metadata (source page, etc.) |

**Indexes**: PK on `id`

---

### Entity: Message

A single message within a chat session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PK | Auto-incrementing message ID |
| session_id | UUID | FK → sessions(id) ON DELETE CASCADE, NOT NULL | Parent session |
| role | VARCHAR(20) | NOT NULL, CHECK IN ('user', 'assistant') | Message author role |
| content | TEXT | NOT NULL | Message text content |
| sources | JSONB | NULLABLE | Source references for assistant messages |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Message timestamp |

**Indexes**:
- PK on `id`
- `idx_messages_session_id` on `session_id`
- `idx_messages_created_at` on `created_at DESC`

**Sources JSONB structure** (for assistant messages):
```json
[
  {
    "page_path": "module1-ros2",
    "section_title": "Creating a Publisher Node",
    "relevance_score": 0.87
  }
]
```

---

## Vector Database (Qdrant)

### Collection: book_chunks

Stores embedded book content chunks for similarity search.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique chunk identifier |
| vector | float[768] | Embedding vector (qwen3-embedding-8b output) |
| text | string (payload) | Raw chunk text content |
| page_path | string (payload) | Source MDX file path (e.g., "module1-ros2") |
| section_title | string (payload) | Heading of the section containing this chunk |
| chunk_index | integer (payload) | Position of chunk within the page |
| page_title | string (payload) | Frontmatter title of the source page |

**Config**:
- Distance: COSINE
- Vector size: 768 (matches qwen3-embedding-8b output dimension)

**Payload indexes**:
- `page_path` — for filtering search to specific pages

---

## Relationships

```
sessions 1 ──── * messages
  (UUID)          (session_id FK)

book_chunks (standalone — no FK relationships)
```

## State Transitions

### Session Lifecycle
```
Created → Active → Idle (no activity for 30 min) → Archived (after 30 days)
```

### Message Flow
```
User sends message → Message saved (role=user)
  → Retrieve chunks from Qdrant (or use selected_text)
  → Generate response via OpenRouter
  → Message saved (role=assistant, sources populated)
```

## Validation Rules

- `session_id` in messages must reference an existing session
- `role` must be either `user` or `assistant`
- `content` must be non-empty and ≤10,000 characters
- `sources` JSONB (when present) must be a valid array of objects with `page_path` and `section_title`
- Vector dimension must be exactly 768
