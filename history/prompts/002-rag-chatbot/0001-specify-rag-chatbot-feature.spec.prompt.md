---
id: "0001"
title: "Specify RAG Chatbot Feature"
stage: spec
date: 2026-02-14
surface: agent
model: claude-opus-4-6
feature: 002-rag-chatbot
branch: 002-rag-chatbot
user: qatreena
command: /sp.specify
labels: ["rag", "chatbot", "specification", "docusaurus"]
links:
  spec: specs/002-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-rag-chatbot/spec.md
  - specs/002-rag-chatbot/checklists/requirements.md
tests:
  - "Specification quality checklist — all items PASS"
---

## Prompt

/sp.specify Specification update — Add Integrated RAG Chatbot to the Docusaurus book:

Project name: physical-ai-humanoid-robotics-rag-chatbot

Overall architecture:
- Frontend: Docusaurus (React) → floating chat bubble/widget (bottom-right) or dedicated /chat page
- Backend: FastAPI (Python 3.11+) → REST API endpoints (/chat, /ingest if needed)
- LLM: OpenRouter API (use models like qwen/qwen3-max or deepseek/deepseek-chat for generation)
- Embeddings: OpenRouter-compatible Qwen embeddings (e.g. qwen/qwen3-embedding-8b or 0.6b for free tier efficiency)
- Vector DB: Qdrant Cloud Free Tier (1 GB cluster) — store book chunks + metadata (page path, section title)
- Relational DB: Neon Serverless Postgres (free tier) — store chat sessions, history, user-selected text snippets
- Ingestion: One-time script — chunk all .mdx files from /docs/, embed with Qwen, upsert to Qdrant
- Features:
  1. General Q&A: Retrieve relevant chunks from whole book → augment prompt → generate answer via OpenRouter
  2. Selected-text mode: User highlights text in page → send selected text + question → answer ONLY using that text (no retrieval, or hybrid)
- Security: Use environment variables for OPENROUTER_API_KEY, QDRANT_URL, QDRANT_API_KEY, NEON_DB_URL
- Deployment:
  - Backend: Render.com / Railway / Fly.io (free tier possible)
  - Frontend integration: React component in Docusaurus (custom global component or plugin)
- Performance: Chunk size ~500-800 tokens, overlap 100-200, top-k=5-8 retrieval

Required endpoints (FastAPI):
- POST /api/chat → { "messages": [...], "selected_text": optional str } → stream or return response
- POST /api/ingest → (admin only, or run offline) re-index book content
- GET /api/health → status check

Docusaurus integration rules:
- Add chat widget via custom React component in src/components/ChatWidget.tsx
- Use iframe fallback option if widget complex (but prefer native React for better UX)
- Add sidebar link to full /chat page if widget not enough
- Respect Docusaurus theme (dark/light mode sync)

Use LangChain or LlamaIndex optional — but prefer lightweight (direct OpenRouter + qdrant-client + sentence-transformers style if needed)

Apply all previous clarity, constitution rules to code comments and docs.

## Response snapshot

Created feature specification for the Integrated RAG Chatbot at `specs/002-rag-chatbot/spec.md`. The spec defines 4 user stories (General Book Q&A as P1, Selected-Text Contextual Q&A as P2, Chat History/Session Continuity as P3, Theme-Aware Widget as P4), 14 functional requirements, 4 key entities (ChatSession, ChatMessage, ContentChunk, SelectedTextContext), 8 success criteria, and 5 edge cases. All implementation details from the user input were intentionally excluded from the spec (reserved for plan.md). Quality checklist passed all validation items.

## Outcome

- ✅ Impact: Complete feature specification created; ready for planning phase.
- 🧪 Tests: Specification quality checklist — all 16 items PASS.
- 📁 Files: spec.md (specification), checklists/requirements.md (quality validation).
- 🔁 Next prompts: /sp.clarify or /sp.plan to proceed with architecture planning.
- 🧠 Reflection: User provided extensive implementation details which were properly separated — spec captures WHAT/WHY, plan.md will capture HOW. No clarification markers needed since the user input was comprehensive.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): Quality checklist — PASS (16/16 items).
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
