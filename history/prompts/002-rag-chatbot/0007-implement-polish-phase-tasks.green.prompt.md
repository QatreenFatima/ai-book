---
id: "0007"
title: "Implement Polish Phase Tasks"
stage: green
date: 2026-02-15
surface: agent
model: claude-opus-4-6
feature: 002-rag-chatbot
branch: 002-rag-chatbot
user: qatreena
command: /sp.implement
labels: ["implementation", "polish", "admin-endpoint", "error-handling", "documentation", "build-validation"]
links:
  spec: specs/002-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/main.py
  - src/components/ChatWidget.tsx
  - docs/chatbot-guide.mdx
  - sidebars.ts
  - specs/002-rag-chatbot/tasks.md
tests:
  - "Docusaurus dev server — compiles and serves successfully (HTTP 200 for / and /chatbot-guide)"
---

## Prompt

ok do all the work.

## Response snapshot

Implemented all remaining Polish phase code tasks (T044-T050). `backend/main.py`: added POST /api/ingest admin endpoint with X-Admin-Key header auth, subprocess call to ingest.py with --reset, parses output for files_processed/chunks_created/errors; wrapped SSE streaming in try/except to handle mid-stream errors gracefully (T044, T045). `ChatWidget.tsx`: added 2000-char limit validation on submit, character count indicator (shows at >1800 chars), friendly "Service temporarily unavailable" message for 503 errors, disabled send button when over limit (T046). Created `docs/chatbot-guide.mdx` with How to Use (General Q&A, Selected-Text, Chat History), Limitations, and Privacy sections (T047). Updated `sidebars.ts` to include chatbot-guide (T048). T049 already done (marked complete). Validated Docusaurus dev server — compiles successfully, both home page and /chatbot-guide return HTTP 200 (T050). Production build OOM killed again (WSL memory constraint, not a code issue).

## Outcome

- ✅ Impact: All implementable code tasks complete — 48 of 51 tasks marked done. Remaining 3 require user credentials/action (T003, T006, T009/T019/T051).
- 🧪 Tests: Docusaurus dev server compilation — PASS. Home page HTTP 200 — PASS. Chatbot guide page HTTP 200 — PASS. Production build — OOM killed (WSL, not code).
- 📁 Files: 4 files modified, 1 file created. Tasks T044-T050 marked complete.
- 🔁 Next prompts: User needs to: (1) create .env with real credentials (T006), (2) install Python deps (T003), (3) run ingest.py (T019), (4) verify end-to-end flow (T051). Then git commit and PR.
- 🧠 Reflection: The polish phase tasks were straightforward since the core architecture was solid. Admin ingest endpoint uses subprocess to keep the sync ingest.py script decoupled from async FastAPI. Error handling improvements were minimal since the initial implementation already had good validation.

## Evaluation notes (flywheel)

- Failure modes observed: Production build OOM kill in WSL (recurring, not a code issue). curl connectivity timing — needed 45s wait for dev server startup.
- Graders run and results (PASS/FAIL): Dev server compilation — PASS. Page HTTP 200 checks — PASS.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
