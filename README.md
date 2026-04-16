# RagAPI — Document Q&A with RAG

A FastAPI-based REST API that implements **Retrieval-Augmented Generation (RAG)** — upload PDF documents and ask questions about them using an LLM with semantic search.

---

## What is RAG?

Instead of sending an entire document to an LLM (expensive, slow, hits token limits), RAG works in two phases:

**Upload phase:**
1. Extract text from PDF
2. Split text into overlapping chunks (~500 words)
3. Generate embeddings for each chunk using `all-MiniLM-L6-v2`
4. Store chunks + vectors in PostgreSQL via `pgvector`

**Query phase:**
1. Generate embedding for the user's question
2. Find the top-5 most similar chunks via vector similarity search
3. Pass relevant chunks as context to the LLM
4. Return the LLM's answer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL + pgvector |
| Async ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Groq API (llama-3.1-8b-instant) |
| Task Queue | Celery + Redis |
| Auth | JWT (python-jose) |
| Password Hashing | passlib + bcrypt |
| Containerization | Docker + docker-compose |

---

## Project Structure

```
ragapi/
├── app/
│   ├── api/
│   │   ├── auth.py           # register, login, /me
│   │   ├── documents.py      # upload, list, delete documents
│   │   ├── chat.py           # ask questions, get history
│   │   └── deps.py           # FastAPI dependencies (get_current_user)
│   ├── core/
│   │   ├── config.py         # settings via pydantic-settings
│   │   ├── security.py       # JWT, password hashing
│   │   ├── embeddings.py     # sentence-transformers model
│   │   ├── exceptions.py     # custom exceptions
│   │   └── logging_config.py
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/
│   │   ├── document_service.py   # upload, list, delete logic
│   │   ├── chat_service.py       # RAG pipeline + chat history
│   │   └── vector_service.py     # pgvector similarity search
│   ├── tasks/
│   │   └── process_document.py   # Celery task: PDF → chunks → embeddings
│   ├── database.py
│   ├── celery_app.py
│   └── main.py
├── alembic/                  # database migrations
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Docker + docker-compose
- Python 3.11+
- A [Groq API key](https://console.groq.com/)

### 1. Clone and configure

```bash
git clone <repo-url>
cd ragapi
```

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://vlad:1234@postgres:5432/ragapi
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GROQ_API_KEY=your-groq-api-key-here
```

### 2. Run with Docker

```bash
docker-compose up --build
```

This starts:
- `ragapi_api` — FastAPI app on port `8001`
- `ragapi_celery` — Celery worker for document processing
- `ragapi_db` — PostgreSQL with pgvector on port `5433`
- `ragapi_redis` — Redis on port `6380`

### 3. Run locally (faster development)

Start only infrastructure:

```bash
docker-compose up postgres redis
```

Run the app and worker locally:

```bash
# .env should use localhost ports:
# DATABASE_URL=postgresql+asyncpg://vlad:1234@localhost:5433/ragapi
# REDIS_URL=redis://localhost:6380

uvicorn app.main:app --reload --port 8001
celery -A app.celery_app worker --loglevel=info
```

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, returns JWT token |
| GET | `/auth/me` | Get current user info |
| POST | `/auth/confirm-dev/{email}` | Confirm email (dev only) |

### Documents

| Method | Endpoint | Description |
|---|---|---|
| POST | `/documents` | Upload a PDF document |
| GET | `/documents` | List all user's documents |
| DELETE | `/documents/{id}` | Delete a document |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat/{document_id}` | Ask a question about a document |
| GET | `/chat/{document_id}/history` | Get chat history for a document |

---

## Chat Pipeline (RAG + History)

Each question goes through this pipeline:

```
1. Load last 6 messages from DB (chat history)
2. If history exists → rephrase question to be standalone
   "Where did she go?" + history → "Where did Lena go on vacation?"
3. Search pgvector for top-5 relevant chunks using rephrased question
4. Build LLM prompt: system + history + context + original question
5. Get answer from Groq LLM
6. Save user message + assistant answer to DB
```

The rephrase step significantly improves retrieval quality for follow-up questions.

---

## Document Processing (Async)

Document processing runs as a **Celery background task** so it doesn't block the API:

```
Upload PDF → Save to disk → Create DB record (status: pending)
    → Celery task →
        Extract text (pypdf)
        Split into chunks (500 words, 50 word overlap)
        Generate embeddings (sentence-transformers)
        Save chunks + vectors to PostgreSQL
        Update status: done
```

Document statuses: `pending` → `processing` → `done` / `failed`

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use SQLite in-memory database and mock all external services (Groq API, embeddings).

---

## Architecture Decisions

**Why Celery for document processing?**
PDF processing + embedding generation is CPU-heavy and can take 30–60 seconds for large documents. Running it in a Celery worker keeps the API responsive.

**Why pgvector instead of a dedicated vector DB?**
For this scale, keeping vectors in PostgreSQL avoids managing a separate service (Pinecone, Weaviate, etc.) while still providing efficient similarity search.

**Why asyncio.to_thread for embeddings in FastAPI?**
`sentence-transformers` is synchronous and CPU-bound. Calling it directly in an async route would block the event loop. `asyncio.to_thread` runs it in a thread pool without blocking other requests.

**Why rephrase before RAG?**
Follow-up questions like "Where did he go?" lack context for vector search. Rephrasing to "Where did Arthur go on vacation?" dramatically improves retrieval quality.