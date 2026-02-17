# Implementation Plan: Integrated RAG Chatbot

**Branch**: `002-rag-chatbot` | **Date**: 2026-02-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-rag-chatbot/spec.md`

## Summary

Add an interactive RAG (Retrieval-Augmented Generation) chatbot to the Physical AI & Humanoid Robotics Docusaurus book. The chatbot provides two modes: (1) general Q&A that retrieves relevant book content chunks via vector search and generates answers using an LLM, and (2) selected-text mode where readers highlight text and ask questions answered using only that context. The system uses a FastAPI backend with OpenRouter for LLM/embeddings, Qdrant Cloud for vector storage, and Neon Postgres for chat history persistence.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/React (frontend widget)
**Primary Dependencies**: FastAPI, uvicorn, openai (OpenRouter-compatible), qdrant-client, asyncpg, python-frontmatter, tiktoken, pydantic
**Storage**: Qdrant Cloud (vectors, 1GB free tier), Neon Serverless Postgres (chat history, free tier)
**Testing**: pytest + pytest-asyncio (backend), manual integration testing (frontend)
**Target Platform**: Linux server (backend), browser (frontend via Docusaurus)
**Project Type**: Web application (backend API + frontend widget)
**Performance Goals**: <10s end-to-end response, <1s widget load overhead, 50 concurrent users
**Constraints**: Free-tier service limits, <50KB initial widget bundle, no user PII
**Scale/Scope**: Single backend instance, ~7 MDX files ingested, ~500-1000 chunks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Educational Clarity | PASS | Chatbot answers reference book sections; enhances learning |
| II. Docusaurus Compatibility | PASS | Widget integrated via Root swizzling; uses Docusaurus theme system |
| III. Practical Code Examples | PASS | All backend code is runnable with documented dependencies |
| IV. Visual Learning | N/A | Chatbot is an interactive feature, not content requiring diagrams |
| V. Module-Based Structure | PASS | Chatbot is additive; does not alter existing module structure |
| VI. Technical Accuracy | PASS | Uses current LTS versions; all APIs documented |

**Post-design re-check**: PASS — no constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-rag-chatbot/
├── plan.md              # This file
├── research.md          # Technology research findings
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Integration scenarios and setup guide
├── contracts/
│   └── api.yaml         # OpenAPI 3.1 specification
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Task breakdown (created by /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── main.py              # FastAPI application entry point
├── rag.py               # RAG core: embed, retrieve, generate
├── ingest.py            # MDX chunking + embedding + Qdrant upsert
├── db.py                # Neon Postgres: sessions, messages CRUD
├── config.py            # Settings via environment variables
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── tests/
    ├── test_rag.py      # RAG pipeline unit tests
    ├── test_ingest.py   # Ingestion pipeline tests
    └── test_api.py      # API endpoint tests

src/
├── components/
│   ├── ChatWidget.tsx   # Floating chat bubble + panel UI
│   └── ChatProvider.tsx # React context for chat state
├── theme/
│   └── Root.tsx         # Swizzled Root for global widget injection
└── css/
    └── chat.css         # Chat widget styles (dark/light theme)
```

**Structure Decision**: Web application pattern — Python backend in `/backend/` directory, React frontend components integrated into existing Docusaurus `/src/` directory. Backend is a separate deployable service; frontend is embedded in the Docusaurus build.

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Backend Framework | FastAPI | 0.110+ | REST API + SSE streaming |
| ASGI Server | uvicorn | 0.27+ | Production server |
| LLM API | OpenRouter | v1 | Chat completions + embeddings |
| LLM Client | openai (Python) | 1.x | OpenAI-compatible SDK |
| Vector DB | Qdrant Cloud | Free tier | Chunk storage + cosine search |
| Vector Client | qdrant-client | 1.x | Python Qdrant SDK |
| Relational DB | Neon Postgres | Free tier | Session + message persistence |
| DB Driver | asyncpg | 0.29+ | Async Postgres for FastAPI |
| MDX Parsing | python-frontmatter | 1.x | Frontmatter extraction |
| Tokenization | tiktoken | 0.5+ | Token counting for chunking |
| Validation | pydantic | 2.x | Request/response models |
| Frontend | React (Docusaurus) | 18.x | Chat widget UI |
| Streaming | SSE (text/event-stream) | — | Real-time LLM response delivery |

## Architecture

### Request Flow (General Q&A)

```
Reader → ChatWidget (React)
  → POST /api/chat { message, session_id }
  → FastAPI handler
    → Embed question via OpenRouter /embeddings
    → Search Qdrant (cosine, top-k=5)
    → Build prompt: system + history + chunks + question
    → Stream response via OpenRouter /chat/completions (stream=true)
    → Save messages to Neon Postgres
  → SSE stream back to ChatWidget
  → Render answer with source references
```

### Request Flow (Selected-Text Mode)

```
Reader → Highlights text → ChatWidget
  → POST /api/chat { message, session_id, selected_text }
  → FastAPI handler
    → Skip Qdrant retrieval
    → Build prompt: system + selected_text + question
    → Stream response via OpenRouter
    → Save messages to Neon Postgres
  → SSE stream back to ChatWidget
```

### Ingestion Pipeline

```
Admin runs: python ingest.py --docs-path ../docs
  → Scan all .mdx files in docs/
  → For each file:
    → Parse frontmatter (title, sidebar_label)
    → Strip MDX components/imports
    → Split by ## and ### headings
    → Chunk to ~512 tokens with 100-token overlap
    → Embed chunks via OpenRouter /embeddings (batch)
    → Upsert to Qdrant with metadata payload
  → Report: files processed, chunks created, errors
```

## Implementation Phases

### Phase 1: Backend Setup
- Initialize `/backend/` directory with virtual environment
- Create `config.py` with pydantic Settings (env vars)
- Create `requirements.txt` with all dependencies
- Create `.env.example` template
- Create `main.py` with FastAPI app, CORS, health check endpoint
- Create `db.py` with asyncpg pool, schema init, session/message CRUD

### Phase 2: Ingestion Pipeline
- Create `ingest.py` with MDX parsing, chunking, embedding, Qdrant upsert
- Implement heading-based chunking with token-aware sizing
- Batch embedding via OpenRouter
- Qdrant collection creation and upsert

### Phase 3: RAG Core Logic
- Create `rag.py` with embed_query, retrieve_chunks, generate_response
- Implement selected-text mode (bypass retrieval)
- Build prompt construction with system prompt, history, chunks
- Implement SSE streaming from OpenRouter

### Phase 4: Chat API Endpoints
- Wire `POST /api/chat` endpoint with streaming response
- Wire `GET /api/sessions/{id}/messages` for history retrieval
- Wire `POST /api/ingest` with admin key protection
- Add input validation (message length, session ID format)

### Phase 5: Frontend Widget
- Swizzle Docusaurus Root component
- Create `ChatProvider.tsx` with React context (messages, session state)
- Create `ChatWidget.tsx` with floating bubble, chat panel, message list
- Implement SSE consumption via `fetch` + `ReadableStream`
- Add selected-text detection (mouseup listener, context menu)
- Add theme sync via CSS `[data-theme]` selectors
- Add `chat.css` with dark/light mode styles

### Phase 6: Testing & Documentation
- Write backend tests (pytest): health, chat, ingest, RAG logic
- Manual integration testing: general Q&A, selected-text, history
- Create `docs/chatbot-guide.mdx` explaining usage and limitations
- Validate build (`npm run build`)

## Complexity Tracking

No constitution violations to justify. The feature is additive and does not alter existing book content or module structure.
