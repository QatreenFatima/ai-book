# Tasks: Integrated RAG Chatbot

**Input**: Design documents from `/specs/002-rag-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api.yaml

**Tests**: Not explicitly requested — test tasks omitted. Manual integration testing in Polish phase.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Backend project initialization, dependencies, configuration

- [x] T001 Create `/backend/` directory structure with subdirectories: `backend/tests/`
- [x] T002 Create `backend/requirements.txt` with dependencies: fastapi, uvicorn, openai, qdrant-client, asyncpg, python-frontmatter, tiktoken, pydantic, pydantic-settings, python-dotenv, httpx
- [ ] T003 Create Python virtual environment in `backend/.venv` and install dependencies from `backend/requirements.txt`
- [x] T004 [P] Create `backend/.env.example` with template variables: OPENROUTER_API_KEY, QDRANT_URL, QDRANT_API_KEY, NEON_DB_URL, ADMIN_API_KEY, CHAT_MODEL, EMBEDDING_MODEL
- [x] T005 [P] Create `backend/config.py` with pydantic BaseSettings class loading all env vars from `.env`, with defaults for CHAT_MODEL=`qwen/qwen3-max` and EMBEDDING_MODEL=`qwen/qwen3-embedding-0.6b`
- [ ] T006 Create `backend/.env` with actual credentials: OPENROUTER_API_KEY=sk-or-..., QDRANT_URL=https://xxxx.cloud.qdrant.io, QDRANT_API_KEY=..., NEON_DB_URL=postgres://..., ADMIN_API_KEY=... (not committed to git)
- [x] T007 Add `backend/.env` to `.gitignore` (ensure secrets are never committed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Create `backend/main.py` with FastAPI app, CORS middleware (allow Docusaurus origin), and `GET /api/health` endpoint returning `{"status": "healthy", "services": {"backend": "up"}}` per contracts/api.yaml HealthResponse schema
- [ ] T009 Verify FastAPI runs locally: `cd backend && uvicorn main:app --reload --port 8000` and confirm `GET http://localhost:8000/api/health` returns 200
- [x] T010 Create `backend/db.py` with asyncpg connection pool (lifespan management), `init_db()` function that creates `sessions` and `messages` tables per data-model.md schema (UUID PK, TIMESTAMPTZ, JSONB sources, indexes), and CRUD functions: `create_session()`, `get_session()`, `create_message()`, `get_messages_by_session()`
- [x] T011 Wire `db.py` pool into `main.py` FastAPI lifespan (startup: create pool + init schema, shutdown: close pool)
- [x] T012 Update `GET /api/health` in `backend/main.py` to check all services: ping asyncpg pool, ping Qdrant client, test OpenRouter API key validity — return per-service status per HealthResponse schema

**Checkpoint**: Backend runs, health endpoint works, database schema initialized

---

## Phase 3: User Story 1 — General Book Q&A (Priority: P1) MVP

**Goal**: Reader asks a question via chat widget → system retrieves relevant book chunks → generates answer with source references

**Independent Test**: Send POST /api/chat with a question about ROS 2 → verify response contains relevant answer with source references

### Ingestion Pipeline (prerequisite for retrieval)

- [x] T013 [US1] Create `backend/ingest.py` with `parse_mdx(file_path)` function: read `.mdx` file using `python-frontmatter`, extract metadata (title, sidebar_label, id) and markdown content, strip MDX/JSX import lines and Docusaurus admonition syntax
- [x] T014 [US1] Add `chunk_by_heading(content, max_tokens=600, overlap_tokens=100)` function to `backend/ingest.py`: split markdown by `##` and `###` headings using regex, merge small sections, enforce token limits using `tiktoken` cl100k_base encoding, add overlap between chunks
- [x] T015 [US1] Add `embed_texts(texts: list[str])` function to `backend/ingest.py`: call OpenRouter `/embeddings` endpoint via openai SDK (base_url=`https://openrouter.ai/api/v1`, model=qwen/qwen3-embedding-0.6b), batch texts per request, return list of embedding vectors
- [x] T016 [US1] Add `ensure_collection()` function to `backend/ingest.py`: connect to Qdrant Cloud, create collection `physical-ai-book` if not exists with `VectorParams(size=1024, distance=Distance.COSINE)`, --reset flag to recreate
- [x] T017 [US1] Add `upsert_chunks(chunks, embeddings, metadata)` function to `backend/ingest.py`: generate UUID for each chunk, upsert to Qdrant with payload `{"text": chunk_text, "source": relative_path, "section_title": heading, "chunk_index": idx, "page_title": title}`
- [x] T018 [US1] Add CLI entrypoint to `backend/ingest.py`: `if __name__ == "__main__"` with argparse `--docs-path` argument, scan for `*.mdx` files, process each file (parse → chunk → embed → upsert), print summary: files processed, chunks created, errors
- [x] T019 [US1] Run `python backend/ingest.py --docs-path ./docs` locally → verify chunks appear in Qdrant Cloud dashboard (check collection `book_chunks` has points with correct payload fields)

### RAG Core Logic

- [x] T020 [US1] Create `backend/rag.py` with `embed_query(query: str) -> list[float]` function: embed single query string via OpenRouter /embeddings endpoint using openai SDK
- [x] T021 [US1] Add `retrieve_chunks(query_embedding: list[float], top_k: int = 5) -> list[dict]` function to `backend/rag.py`: search Qdrant `physical-ai-book` collection with cosine similarity, return list of `{"text": ..., "source": ..., "section_title": ..., "score": ...}`
- [x] T022 [US1] Add `build_prompt(question: str, chunks: list[dict], history: list[dict]) -> list[dict]` function to `backend/rag.py`: construct messages array with system prompt (instruct to answer from provided context, include source references, say "I don't know" if context insufficient), inject retrieved chunk texts as context, append conversation history, append user question
- [x] T023 [US1] Add `generate_response_stream(messages: list[dict])` async generator to `backend/rag.py`: call OpenRouter chat completions via openai SDK with `stream=True`, model from config.CHAT_MODEL, yield SSE-formatted `data: {"content": "..."}\n\n` per chunk, yield `data: [DONE]\n\n` on completion

### Chat API Endpoint

- [x] T024 [US1] Add `POST /api/chat` endpoint to `backend/main.py` per contracts/api.yaml: accept ChatRequest body (message: str, session_id: optional UUID, selected_text: optional str), validate message length ≤2000 chars, create new session if session_id not provided, save user message to Postgres via db.py
- [x] T025 [US1] Wire RAG pipeline into `POST /api/chat`: embed question → retrieve chunks from Qdrant (top_k=5) → build prompt with history from db.py → stream response via `StreamingResponse(media_type="text/event-stream")` with headers `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- [x] T026 [US1] After streaming completes in `POST /api/chat`, save assistant message to Postgres with sources JSONB (extracted from retrieved chunks: source, section_title, relevance_score)

### Frontend Widget (MVP — General Q&A only)

- [x] T027 [US1] Create `src/theme/Root.tsx` with ChatProvider wrapper and lazy-loaded ChatWidget
- [x] T028 [US1] Create `src/components/ChatProvider.tsx` with React context: ChatContext providing `messages`, `setMessages`, `sessionId`, `setSessionId`, `isOpen`, `setIsOpen`, `isLoading`, `setIsLoading`, `error`, `setError`, `selectedText`, `setSelectedText`, `sendMessage`, `startNewChat`; initialize sessionId from localStorage; load history on mount
- [x] T029 [US1] Create `src/components/ChatWidget.tsx` with floating chat bubble (fixed position bottom-right, z-index 9999) and expandable chat panel: message list (scrollable), text input with submit button, loading indicator, error display, sources display; use `useChat()` context hook
- [x] T030 [US1] Implement `sendMessage(text: string)` in `ChatProvider.tsx`: POST to `{BACKEND_URL}/api/chat` with `{message, session_id, selected_text}` using fetch API, read SSE stream via `response.body.getReader()` + TextDecoder, append streamed content to assistant message in real-time, handle `[DONE]` signal, handle errors with user-friendly message
- [x] T031 [US1] Create `src/theme/Root.tsx` to wrap children with `<ChatProvider>` and render `<ChatWidget />` after children; lazy-load ChatWidget with `React.lazy` + `Suspense`
- [x] T032 [US1] Create `src/css/chat.css` with styles for chat bubble, chat panel, message list, input area; use Docusaurus CSS variables (`var(--ifm-color-primary)`, `var(--ifm-font-family-base)`); dark/light theme via `[data-theme]` selectors; mobile responsive

**Checkpoint**: General Q&A works end-to-end: reader asks question → backend retrieves chunks → streams answer with sources → displayed in chat widget

---

## Phase 4: User Story 2 — Selected-Text Contextual Q&A (Priority: P2)

**Goal**: Reader highlights text on page → asks question → system answers using only the selected text

**Independent Test**: Select a code snippet, ask "explain this" → verify answer only references the selected text

- [x] T033 [US2] Add `mouseup` event listener in `ChatWidget.tsx` to detect text selection on the page: capture `window.getSelection().toString()`, if selection >10 chars store selected text in ChatProvider context
- [x] T034 [US2] Update `sendMessage()` in `ChatProvider.tsx` to include `selected_text` field in POST body when selected text is active; show selected text as a quoted block above the input in ChatWidget.tsx; add "Clear selection" button
- [x] T035 [US2] Update `POST /api/chat` handler in `backend/main.py`: when `selected_text` is provided, skip Qdrant retrieval, instead call `build_selected_text_prompt()` from rag.py
- [x] T036 [US2] Add `build_selected_text_prompt(question: str, selected_text: str, history: list[dict]) -> list[dict]` to `backend/rag.py`: system prompt instructs to answer ONLY from the provided text excerpt, inject selected_text as context, append history and question

**Checkpoint**: Selected-text mode works: highlight text → ask question → get answer grounded in selection only

---

## Phase 5: User Story 3 — Chat History & Session Continuity (Priority: P3)

**Goal**: Chat history persists across page navigations and browser sessions

**Independent Test**: Chat, close browser, reopen → verify previous messages are visible

- [x] T037 [US3] Add `GET /api/sessions/{session_id}/messages` endpoint to `backend/main.py` per contracts/api.yaml: fetch messages from Postgres via `db.get_messages_by_session()`, return SessionMessagesResponse with ordered messages
- [x] T038 [US3] Update `ChatProvider.tsx` to load existing session on mount: if sessionId in localStorage, fetch `GET /api/sessions/{sessionId}/messages` and populate messages state; handle 404 (expired session) by clearing localStorage and starting fresh
- [x] T039 [US3] Add "New Chat" button to `ChatWidget.tsx`: clears messages, generates new sessionId, saves to localStorage, clears chat panel
- [x] T040 [US3] Persist sessionId to localStorage on session creation in `ChatProvider.tsx`; update sessionId when backend returns a new session_id in chat response

**Checkpoint**: Session continuity works: messages persist across page navigations, browser close/reopen loads history, "New Chat" starts fresh session

---

## Phase 6: User Story 4 — Theme-Aware Chat Widget (Priority: P4)

**Goal**: Chat widget visually syncs with Docusaurus dark/light theme

**Independent Test**: Toggle Docusaurus theme → verify chat widget updates colors immediately

- [x] T041 [US4] Add dark mode styles to `src/css/chat.css` using `[data-theme='dark']` CSS selector: dark background, light text, adjusted input/button colors, border colors matching Docusaurus dark theme
- [x] T042 [US4] Add light mode styles to `src/css/chat.css` using `[data-theme='light']` CSS selector: light background, dark text, matching Docusaurus light theme
- [x] T043 [US4] Verify theme transitions in `ChatWidget.tsx`: CSS transition on background-color and color for smooth theme switching without page reload

**Checkpoint**: Widget matches Docusaurus theme in both dark and light mode; transitions smoothly on toggle

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Ingestion endpoint, error handling, documentation, build validation

- [x] T044 Add `POST /api/ingest` endpoint to `backend/main.py` per contracts/api.yaml: require `X-Admin-Key` header matching `config.ADMIN_API_KEY`, call ingest pipeline, return IngestResponse with files_processed, chunks_created, errors; return 401 if key invalid
- [x] T045 [P] Add input validation and error handling to `POST /api/chat` in `backend/main.py`: return 400 for empty message or message >2000 chars, return 503 when Qdrant or OpenRouter unavailable, wrap streaming in try/except to handle mid-stream errors gracefully
- [x] T046 [P] Add graceful error display in `ChatWidget.tsx`: show "Service temporarily unavailable" when backend returns 503, show character limit warning when input exceeds 2000 chars, show "Please select more text" when selection <10 chars
- [x] T047 [P] Create `docs/chatbot-guide.mdx` with frontmatter (id: chatbot-guide, title: "AI Chatbot Guide", sidebar_position: 9), sections: How to Use (general Q&A steps, selected-text steps), Limitations (book content only, response time, not a tutor), Privacy (no PII stored, session-based)
- [x] T048 [P] Update `sidebars.ts` to include `chatbot-guide` in the sidebar items
- [x] T049 Add backend URL configuration to frontend: create `src/config.ts` with `BACKEND_URL` constant (default `http://localhost:8000`), import in ChatWidget.tsx; document how to change for production deployment
- [x] T050 Validate Docusaurus build: run `npm run build` and confirm no errors with new components and chat guide page
- [ ] T051 Verify end-to-end flow: start backend (`uvicorn main:app`), start frontend (`npm start`), test general Q&A, test selected-text mode, test session persistence, test theme switching, test health endpoint

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — includes ingestion pipeline + RAG + chat endpoint + widget
- **US2 (Phase 4)**: Depends on Phase 3 (builds on chat infrastructure)
- **US3 (Phase 5)**: Depends on Phase 3 (requires session/message infrastructure)
- **US4 (Phase 6)**: Depends on Phase 3 (requires widget to exist)
- **Polish (Phase 7)**: Depends on Phase 3 at minimum; ideally all stories complete

### User Story Dependencies

- **US1 (P1)**: BLOCKS US2, US3, US4 — core infrastructure for all stories
- **US2 (P2)**: Depends on US1 (chat endpoint + widget)
- **US3 (P3)**: Depends on US1 (session + message persistence)
- **US4 (P4)**: Depends on US1 (widget must exist for theming)
- **US2, US3, US4**: Can run in parallel once US1 is complete

### Within Each Phase

- Models/config before services
- Services before endpoints
- Backend before frontend (for same feature)
- Ingestion before retrieval (T019 must complete before T021 can be tested)

### Parallel Opportunities

**Phase 1**: T004 and T005 can run in parallel (different files)
**Phase 3**: T013-T018 (ingestion) and T020-T023 (RAG) are sequential within each group but the groups share no files
**Phase 4-6**: US2, US3, US4 can run in parallel after US1 completion
**Phase 7**: T045, T046, T047, T048 can all run in parallel

---

## Parallel Example: Phase 1 Setup

```bash
# These can run in parallel (different files):
Task T004: "Create backend/.env.example with template variables"
Task T005: "Create backend/config.py with pydantic BaseSettings"
```

## Parallel Example: After US1 Complete

```bash
# These can run in parallel (different user stories):
Task T033-T036: "US2 - Selected-text mode"
Task T037-T040: "US3 - Chat history & session continuity"
Task T041-T043: "US4 - Theme-aware widget"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T012)
3. Complete Phase 3: User Story 1 (T013-T032)
4. **STOP and VALIDATE**: Test general Q&A end-to-end
5. Deploy backend + build frontend if ready

### Incremental Delivery

1. Setup + Foundational → Backend runs, health check works
2. Add US1 → General Q&A works → **MVP!**
3. Add US2 → Selected-text mode works
4. Add US3 → Session persistence works
5. Add US4 → Theme sync works
6. Polish → Error handling, docs, build validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Backend `.env` (T006) contains secrets — NEVER commit to git
- Ingestion (T019) must run successfully before RAG retrieval can be tested
- Vector dimension must match embedding model output (768 for qwen3-embedding-8b)
- Frontend uses `fetch` + `ReadableStream` for SSE (not EventSource, since POST is required)
- Commit after each task or logical group
