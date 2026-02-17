# Quickstart: RAG Chatbot

## Prerequisites

- Python 3.11+
- Node.js 18+ (for Docusaurus)
- Accounts: OpenRouter, Qdrant Cloud, Neon

## 1. External Services Setup

### OpenRouter
1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Create API key → save as `OPENROUTER_API_KEY`

### Qdrant Cloud
1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create free cluster (1GB)
3. Save cluster URL as `QDRANT_URL` and API key as `QDRANT_API_KEY`

### Neon Postgres
1. Sign up at [neon.tech](https://neon.tech)
2. Create free project → create database `rag_chatbot`
3. Save connection string as `NEON_DB_URL`

## 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Fill in: OPENROUTER_API_KEY, QDRANT_URL, QDRANT_API_KEY, NEON_DB_URL
```

## 3. Database Migration

```bash
cd backend
python -c "import asyncio; from db import init_db; asyncio.run(init_db())"
```

## 4. Ingest Book Content

```bash
cd backend
python ingest.py --docs-path ../docs
```

## 5. Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## 6. Start Frontend (Docusaurus)

```bash
npm start
```

## 7. Verify

- Open http://localhost:3000/ai-book/
- Click the chat bubble (bottom-right)
- Ask: "What is ROS 2?"
- Verify answer includes source references

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | `sk-or-v1-...` |
| `QDRANT_URL` | Qdrant Cloud cluster URL | `https://xxx.qdrant.io` |
| `QDRANT_API_KEY` | Qdrant API key | `...` |
| `NEON_DB_URL` | Neon Postgres connection string | `postgresql://user:pass@host/db` |
| `ADMIN_API_KEY` | Admin key for ingestion endpoint | Any secure string |
| `CHAT_MODEL` | OpenRouter chat model (default: `qwen/qwen3-max`) | `deepseek/deepseek-chat` |
| `EMBEDDING_MODEL` | OpenRouter embedding model | `qwen/qwen3-embedding-8b` |

## Integration Scenarios

### Scenario 1: General Q&A
1. Reader opens chat widget
2. Types question about book content
3. Backend embeds question → searches Qdrant (top-5) → builds prompt → streams response
4. Response includes source references

### Scenario 2: Selected-Text Q&A
1. Reader highlights text on a page
2. Clicks "Ask about this" → types question
3. Backend uses selected text as context (no Qdrant retrieval)
4. Response grounded only in selected text

### Scenario 3: Session Continuity
1. Reader chats, closes browser
2. Returns later → session ID in localStorage
3. Backend loads history from Neon → chat resumes
