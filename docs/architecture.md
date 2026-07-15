# Architecture

## Goals

- Answer only from official uploaded documents
- Cite sources (filename + page)
- Keep retrieval and generation separate for safety and scalability
- Remain modular for future SaaS / multi-channel expansion

## High-level flow

```text
Student UI ──JWT──▶ FastAPI /chat
                      │
                      ├─ embed question (bge-m3)
                      ├─ vector search (pgvector)
                      ├─ build context blocks
                      ├─ stream answer (Ollama Qwen3)
                      └─ persist chat_history + citations
```

```text
Admin UI ──JWT──▶ FastAPI /documents/upload
                      │
                      ├─ validate PDF
                      ├─ store file
                      └─ background index:
                           extract → clean → chunk → embed → upsert vectors
```

## Modules

| Package | Responsibility |
| --- | --- |
| `api/` | HTTP adapters (auth, documents, chat, health) |
| `services/` | Application use-cases |
| `rag/` | Chunking, retrieval, LLM prompting |
| `embeddings/` | Embedding model lifecycle |
| `loaders/` | Document extraction |
| `models/` / `schemas/` | Persistence + API contracts |
| `security/` | Passwords, JWT, dependencies |

## Data model

- `users` — email, password hash, role
- `documents` — upload metadata + indexing status
- `document_chunks` — text, page, embedding vector
- `chat_history` — question/answer/citations JSON

## Why this shape scales later

- Document ownership can gain a `tenant_id` / `university_id` without changing the chat UI contract
- New loaders (DOCX, HTML crawl) plug into `loaders/`
- Channels (Telegram, WhatsApp, mobile) reuse `services/chat.py`
- Analytics can read `chat_history` and document index metrics independently

## Prompt policy

The system prompt forces grounded answers and a fixed fallback sentence when context is insufficient, reducing hallucinations.
