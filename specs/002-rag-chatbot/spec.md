# Feature Specification: Integrated RAG Chatbot

**Feature Branch**: `002-rag-chatbot`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Add Integrated RAG Chatbot to the Docusaurus book — floating chat widget with general Q&A from book content and selected-text mode for contextual answers"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - General Book Q&A (Priority: P1)

A reader studying the Physical AI & Humanoid Robotics book has a question about a concept spread across multiple chapters. They click the floating chat bubble in the bottom-right corner, type their question (e.g., "How does sim-to-real transfer work with Isaac Gym?"), and receive a concise answer synthesized from relevant book sections with source references.

**Why this priority**: This is the core value proposition — turning static book content into an interactive learning assistant. Without this, there is no chatbot.

**Independent Test**: Can be fully tested by sending a question about book content and verifying the response references relevant sections. Delivers immediate value as a standalone feature.

**Acceptance Scenarios**:

1. **Given** the chat widget is visible on any book page, **When** a reader types a question and submits it, **Then** the system retrieves relevant book content and returns an answer within 10 seconds.
2. **Given** a reader asks a question about ROS 2 topics, **When** the answer is generated, **Then** the response includes references to the specific book sections used (page path and section title).
3. **Given** a reader asks a question unrelated to book content, **When** the system cannot find relevant chunks, **Then** it responds with a helpful message indicating the question is outside the book's scope.

---

### User Story 2 - Selected-Text Contextual Q&A (Priority: P2)

A reader is studying a specific code example or paragraph and wants deeper explanation. They highlight text on the page, which triggers a "Ask about this" option. They type a follow-up question (e.g., "Why does this use rclpy.spin() instead of a loop?"), and the system answers using only the selected text as context.

**Why this priority**: This differentiates the chatbot from a generic Q&A bot by enabling contextual, in-page assistance. It builds on P1 infrastructure.

**Independent Test**: Can be tested by selecting text on a page, asking a question, and verifying the answer is grounded only in the selected passage.

**Acceptance Scenarios**:

1. **Given** a reader highlights text on a book page, **When** they submit a question about the selection, **Then** the system answers using only the selected text as primary context.
2. **Given** a reader selects a short code snippet and asks "explain this", **When** the answer is generated, **Then** it explains the code without pulling in unrelated book content.
3. **Given** a reader selects text and asks a question unrelated to the selection, **Then** the system indicates the question does not relate to the selected passage.

---

### User Story 3 - Chat History and Session Continuity (Priority: P3)

A reader returns to the book after a break and wants to continue a previous conversation. Their chat history is preserved and visible in the chat widget, allowing them to pick up where they left off or reference previous answers.

**Why this priority**: Enhances user experience by supporting multi-session learning workflows. Not essential for MVP but significantly improves retention and usability.

**Independent Test**: Can be tested by starting a chat session, closing the browser, returning, and verifying previous messages are still visible.

**Acceptance Scenarios**:

1. **Given** a reader has an active chat session, **When** they navigate between book pages, **Then** the chat history persists within the same session.
2. **Given** a reader closes the browser and returns later, **When** they open the chat widget, **Then** their previous conversation history is displayed.
3. **Given** a reader wants to start fresh, **When** they click "New Chat", **Then** a new empty session begins while previous sessions remain accessible.

---

### User Story 4 - Theme-Aware Chat Widget (Priority: P4)

A reader using dark mode on the Docusaurus site opens the chat widget. The widget automatically matches the current site theme (dark or light), providing a visually consistent experience.

**Why this priority**: Polish feature that ensures the chatbot feels native to the book rather than a bolted-on external tool.

**Independent Test**: Can be tested by toggling the Docusaurus theme and verifying the chat widget updates its colors accordingly.

**Acceptance Scenarios**:

1. **Given** the site is in dark mode, **When** the reader opens the chat widget, **Then** the widget renders with dark mode styling.
2. **Given** the reader toggles the theme while the chat is open, **When** the theme changes, **Then** the widget styling updates immediately without page reload.

---

### Edge Cases

- What happens when the backend service is unavailable? The chat widget displays a friendly "Service temporarily unavailable" message and retries periodically.
- What happens when a reader sends an extremely long message (>2000 characters)? The system truncates the input to a reasonable limit and notifies the reader.
- What happens when the selected text is too short (<10 characters) for meaningful Q&A? The system prompts the reader to select more text or use general Q&A instead.
- What happens when multiple readers send requests simultaneously? The backend handles concurrent requests without degradation for at least 50 simultaneous users.
- What happens when the vector database has not been ingested yet? The system returns a clear error indicating content indexing is required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a floating chat bubble on all book pages that opens a chat panel when clicked.
- **FR-002**: System MUST accept free-text questions from readers and return answers generated from book content.
- **FR-003**: System MUST retrieve relevant content chunks from the book's vector index to augment answer generation.
- **FR-004**: System MUST include source references (page path and section title) in every generated answer.
- **FR-005**: System MUST support a selected-text mode where the reader highlights text and asks questions answered using only that text.
- **FR-006**: System MUST persist chat sessions and message history so readers can resume conversations.
- **FR-007**: System MUST provide a health-check endpoint that reports system status (backend, vector database, LLM service).
- **FR-008**: System MUST provide an ingestion mechanism to chunk, embed, and index all book `.mdx` content files.
- **FR-009**: System MUST store metadata with each content chunk (source page path, section title) for attribution.
- **FR-010**: System MUST sync the chat widget's visual theme with the Docusaurus site theme (dark/light mode).
- **FR-011**: System MUST handle backend unavailability gracefully with user-facing error messages.
- **FR-012**: System MUST enforce input length limits and inform readers when their input exceeds the limit.
- **FR-013**: System MUST protect all API keys and credentials via environment variables — no secrets in client-side code.
- **FR-014**: System MUST provide an admin-only ingestion trigger (not exposed to readers).

### Key Entities

- **ChatSession**: Represents a conversation between a reader and the chatbot. Attributes: unique session identifier, creation timestamp, last activity timestamp.
- **ChatMessage**: A single message within a session. Attributes: role (reader or assistant), content text, timestamp, source references (if assistant message).
- **ContentChunk**: A segment of book content stored in the vector index. Attributes: text content, embedding vector, source page path, section title, chunk position.
- **SelectedTextContext**: Temporary context for selected-text mode. Attributes: selected text, source page URL, reader's question.

## Assumptions

- The book content in `/docs/*.mdx` is the sole knowledge base — no external data sources.
- Readers do not need authentication; the chatbot is publicly accessible.
- Chat session persistence uses browser-based session identification (no user accounts).
- The ingestion process is run manually by the book maintainer, not triggered by readers.
- The backend is deployed as a single service instance (no horizontal scaling required for MVP).
- Chunk size of 500-800 tokens with 100-200 token overlap provides adequate retrieval granularity.
- Top-k retrieval of 5-8 chunks provides sufficient context without excessive noise.

## Constraints

- All external service usage must fit within free-tier limits (vector database: 1 GB, relational database: free tier, LLM API: pay-per-use).
- The chat widget must not degrade Docusaurus page load performance (lazy-loaded, <50KB initial bundle).
- Backend response time target: <10 seconds end-to-end for general Q&A.
- No user-identifiable information is collected or stored beyond session-scoped chat history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Readers receive relevant, book-grounded answers to 80% of on-topic questions (measured by source references matching the question topic).
- **SC-002**: End-to-end response time for general Q&A is under 10 seconds for 95% of requests.
- **SC-003**: The chat widget loads without adding more than 1 second to initial page load time.
- **SC-004**: Selected-text mode answers are grounded exclusively in the selected passage (no unrelated book content leaks in).
- **SC-005**: Chat history persists across page navigations within a session with 100% reliability.
- **SC-006**: The system handles at least 50 concurrent readers without response degradation.
- **SC-007**: The health-check endpoint accurately reports the status of all dependent services.
- **SC-008**: All book `.mdx` files are successfully chunked, embedded, and indexed by the ingestion pipeline.
