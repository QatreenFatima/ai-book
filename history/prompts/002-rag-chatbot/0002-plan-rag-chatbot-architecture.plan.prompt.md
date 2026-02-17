---
id: "0002"
title: "Plan RAG Chatbot Architecture"
stage: plan
date: 2026-02-14
surface: agent
model: claude-opus-4-6
feature: 002-rag-chatbot
branch: 002-rag-chatbot
user: qatreena
command: /sp.plan
labels: ["architecture", "rag", "chatbot", "fastapi", "docusaurus"]
links:
  spec: specs/002-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-rag-chatbot/plan.md
  - specs/002-rag-chatbot/research.md
  - specs/002-rag-chatbot/data-model.md
  - specs/002-rag-chatbot/quickstart.md
  - specs/002-rag-chatbot/contracts/api.yaml
tests:
  - "Constitution check — all 6 principles PASS"
---

## Prompt

/sp.plan Detailed plan for adding RAG Chatbot feature to the book.

Phase order:
1. Setup external services (Qdrant Cloud, Neon Postgres, OpenRouter)
2. Backend project structure (/backend/ with main.py, rag.py, ingest.py, db.py)
3. Ingestion pipeline (chunk MDX, embed with Qwen, upsert to Qdrant)
4. Chat logic (retrieve top-k, selected_text mode, prompt building, OpenRouter streaming)
5. Frontend integration (ChatWidget.tsx, Root swizzling, theme sync)
6. Testing & docs

Dependencies: fastapi, uvicorn, qdrant-client, openai, asyncpg, python-dotenv, pydantic
Output order: 1→2→3→4→5→6

## Response snapshot

Created complete architectural plan with 5 artifacts: plan.md (6-phase implementation plan with tech stack, architecture flows, project structure), research.md (6 technology decisions with rationale and alternatives), data-model.md (Postgres schema for sessions/messages + Qdrant collection schema), contracts/api.yaml (OpenAPI 3.1 spec with 4 endpoints), quickstart.md (setup guide with 3 integration scenarios). Constitution check passed all 6 principles. Agent context (CLAUDE.md) updated with new tech stack.

## Outcome

- ✅ Impact: Complete architectural plan ready for task breakdown. All technology decisions documented with rationale.
- 🧪 Tests: Constitution check — PASS (6/6 principles).
- 📁 Files: 5 artifacts created (plan.md, research.md, data-model.md, quickstart.md, contracts/api.yaml).
- 🔁 Next prompts: /sp.tasks to generate task breakdown, then /sp.implement.
- 🧠 Reflection: User provided detailed phase ordering which aligned well with the plan structure. Research confirmed all technology choices are viable within free-tier constraints.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): Constitution check — PASS.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
