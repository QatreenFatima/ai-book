# RAG Chatbot Technologies Research

## Research Findings for Docusaurus-Integrated RAG Chatbot

---

### 1. OpenRouter API

**Decision**: Use OpenRouter as the unified API gateway for both LLM chat completions and embeddings.

**Rationale**: OpenRouter provides an OpenAI-compatible API supporting 300+ models. Single authentication, single SDK (`openai` Python package with custom `base_url`). Supports both chat completions (`qwen/qwen3-max`, `deepseek/deepseek-chat`) and embeddings (`qwen/qwen3-embedding-8b`) through one interface.

**Alternatives considered**:
- Direct OpenAI API — more expensive, limited to OpenAI models
- Multiple provider SDKs — increased complexity, separate auth per provider
- Self-hosted models — significant infrastructure costs, maintenance burden

**Key implementation notes**:
- Base URL: `https://openrouter.ai/api/v1`
- Auth: Bearer token in Authorization header
- Use OpenAI Python SDK with `base_url="https://openrouter.ai/api/v1"`
- Model IDs: `qwen/qwen3-max`, `deepseek/deepseek-chat`, `qwen/qwen3-embedding-8b`
- Embeddings endpoint is fully OpenAI-compatible (`/embeddings`)
- Batch embeddings supported (multiple texts per request)

---

### 2. Qdrant Cloud Free Tier

**Decision**: Use Qdrant Cloud free tier (1GB cluster) for vector storage and cosine similarity search.

**Rationale**: 1GB supports ~1M vectors at 768 dimensions. Built-in metadata filtering, excellent Python async support via `qdrant-client`. Cloud-managed, no infrastructure overhead.

**Alternatives considered**:
- Pinecone — no meaningful free tier
- Chroma — requires self-hosting for production
- pgvector — lower performance on similarity search

**Key implementation notes**:
- Client: `qdrant-client` PyPI package
- Distance metric: `Distance.COSINE`
- Collection config: `VectorParams(size=768, distance=Distance.COSINE)` (match embedding model output dim)
- Payload stores: `page_path`, `section_title`, `chunk_text`, `chunk_index`
- Metadata filtering available via `Filter` / `FieldCondition`
- Upsert in batches to avoid payload size limits

---

### 3. Neon Serverless Postgres

**Decision**: Use Neon free tier with `asyncpg` driver for chat session/message persistence.

**Rationale**: Free tier provides ~100 connections, unlimited storage, auto-pause on inactivity. `asyncpg` is 17.88% faster than `psycopg2` for async workloads — ideal for FastAPI.

**Alternatives considered**:
- Supabase — more complex for simple CRUD
- psycopg2 — synchronous driver, doesn't leverage FastAPI async

**Key implementation notes**:
- Driver: `asyncpg` with connection pool (`min_size=2, max_size=10`)
- Use FastAPI lifespan for pool creation/teardown
- Built-in PgBouncer in transaction mode
- Schema: `sessions` table (UUID PK, timestamps, metadata JSONB) + `messages` table (session FK, role, content, timestamps, metadata JSONB)

---

### 4. FastAPI Streaming (SSE)

**Decision**: Implement streaming LLM responses via FastAPI `StreamingResponse` with async generators using SSE protocol.

**Rationale**: SSE is the industry standard for LLM streaming. Simpler than WebSockets for unidirectional streaming. Works over standard HTTP, native browser support via `EventSource` API.

**Alternatives considered**:
- WebSockets — bidirectional overhead unnecessary
- Long polling — higher latency, poor UX
- Batch responses — no real-time feedback

**Key implementation notes**:
- Content-Type: `text/event-stream`
- Format: `data: {json}\n\n` per message, `data: [DONE]\n\n` for completion
- Headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no` (nginx)
- Client: `fetch` with `ReadableStream` or `EventSource` API
- For POST requests (chat), use `fetch` + streaming reader (EventSource only supports GET)

---

### 5. MDX Chunking Strategy

**Decision**: Parse MDX with `python-frontmatter`, chunk by heading boundaries, 512-token chunks with 100-token overlap.

**Rationale**: Heading-based chunking preserves semantic structure. 512 tokens balances context retention with retrieval precision (industry baseline with 85-90% recall). 100-token overlap (~19.5%) ensures continuity.

**Alternatives considered**:
- Fixed-size chunking — breaks semantic boundaries
- Sentence-based — too granular, loses context
- Page-level — exceeds context window, poor retrieval precision

**Key implementation notes**:
- Libraries: `python-frontmatter`, `tiktoken` (cl100k_base encoding)
- Split by `##` and `###` headings using regex
- Strip MDX/JSX components (admonitions, imports) before embedding
- Preserve frontmatter metadata (`title`, `sidebar_label`) as chunk payload
- Token counting with `tiktoken` for accurate sizing

---

### 6. Docusaurus React Integration

**Decision**: Swizzle Docusaurus `Root` component to inject global chat widget. Use CSS data-attribute selectors for theme sync.

**Rationale**: Root component renders at top of React tree, never unmounts. Swizzling is Docusaurus's official customization mechanism. CSS `[data-theme='dark']` selectors avoid hydration mismatches from `useColorMode` during SSR.

**Alternatives considered**:
- Custom Docusaurus plugin — overkill for single component
- Script injection — loses React benefits, no theme context
- Footer swizzling — inconsistent presence across pages

**Key implementation notes**:
- Swizzle: `npm run swizzle @docusaurus/theme-classic Root -- --eject` → creates `src/theme/Root.js`
- Root wraps children with `<ChatProvider>` context + renders `<ChatWidget />`
- Theme sync via CSS: `[data-theme='dark'] .chat-widget { ... }`
- Lazy-load chat UI for performance (`React.lazy` + `Suspense`)
- Use CSS variables from Docusaurus theme (`var(--ifm-color-primary)`)
- Persist session ID in `localStorage`
- Fixed position: `bottom: 20px; right: 20px; z-index: 9999`
