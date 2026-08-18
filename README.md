# University Knowledge AI

Production-ready MVP for a **Retrieval-Augmented Generation (RAG)** university chatbot.

Students ask questions; the system answers **only** from uploaded official PDFs and returns citations (document name + page).

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js (App Router), TypeScript, Tailwind, React Query |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database | PostgreSQL + pgvector |
| LLM | NVIDIA Inference API (OpenAI-compatible) |
| Embeddings | BAAI/bge-m3 via sentence-transformers |
| Docs | PyMuPDF (+ built-in OCR fallback) |
| Deploy | Docker Compose |

## Quick start

```bash
cp .env.example .env
# add your NVIDIA_API_KEY in .env
docker compose up --build
```

First boot will:

1. Start Postgres with pgvector
2. Start backend and frontend services
3. Run migrations + seed users
4. Download the embedding model on first index/chat
5. Serve API on `:8000` and UI on `:3000`

Open **http://localhost:3000**

### Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Student | `student@university.edu` | `Student123!` |
| Admin | `admin@university.edu` | `Admin123!` |

### Seed a handbook PDF

```bash
# with backend deps installed locally
cd backend && python scripts/generate_sample_pdf.py
```

Then sign in as admin → **Admin** → upload `docs/samples/student_handbook.pdf`.

## API

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /documents/upload`
- `GET /documents`
- `DELETE /documents/{id}`
- `POST /documents/reindex`
- `POST /chat` (SSE streaming when `stream: true`)
- `GET /chat/history`
- `GET /health`

## RAG pipeline

1. Admin uploads a PDF
2. Text is extracted and cleaned
3. Semantic chunks are created with overlap
4. Embeddings are generated with **BAAI/bge-m3**
5. Chunks + vectors are stored in PostgreSQL (`pgvector`)
6. Chat queries retrieve top-k similar chunks
7. Only retrieved context is sent to the configured **NVIDIA model**
8. Answer + citations are returned (document + page)

If retrieval finds nothing reliable, the assistant replies:

> I couldn't find reliable information in the university's official documents.

## Local development (without full Compose)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# start postgres and set NVIDIA_API_KEY in your env/.env, then:
alembic upgrade head
python -m app.bootstrap
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Project layout

```text
university-ai/
  frontend/     Next.js UI
  backend/      FastAPI + RAG
  docker/       Dockerfiles + Postgres init
  docs/         Architecture notes + samples
```

## Security highlights

- JWT auth + bcrypt password hashing
- Role-based admin routes
- PDF type/size validation and magic-header check
- Parameterized SQL / SQLAlchemy ORM
- Input validation with Pydantic
- CORS allow-list

## Future-ready (not in MVP)

Multi-tenant universities, crawling, DOCX, voice, Telegram/WhatsApp, mobile apps, analytics, and multi-language can plug into the current service boundaries without a rewrite.

See `docs/architecture.md` for details.
