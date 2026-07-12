# Setup

## Prerequisites
- Python 3.12+, Node 20+
- PostgreSQL 16 with the `pgvector` extension (or use the Docker stack)
- Optional: a Groq API key for online LLM parsing; Ollama for the offline path

## Option A — Docker (recommended)

```bash
cp .env.example .env      # set GROQ_API_KEY if you want online parsing
docker compose -f docker/docker-compose.yml up --build
```

Frontend at http://localhost:3000, API at http://localhost:8000/docs. The
backend container runs `alembic upgrade head` on start and pre-downloads the
embedding model at build time.

## Option B — Local

### Database
Use the Docker Postgres, or a local install with pgvector:

```sql
CREATE DATABASE resume_db;
\c resume_db
CREATE EXTENSION IF NOT EXISTS vector;
```

### Backend

```bash
pip install -r backend/requirements.txt
cp .env.example .env       # set DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY
cd backend
alembic upgrade head
uvicorn main:app --reload  # http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local  # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                 # http://localhost:3000
```

## Embedding provider

Default is in-process `sentence-transformers` (bge-small, 384-dim) — no external
service. For a fully-offline path with Ollama:

```bash
ollama pull nomic-embed-text
ollama pull gemma3:4b
# in .env:
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
```

Changing the dimension requires re-running the migration against an empty
embedding column (pgvector columns are dimension-typed).

## Tests

```bash
cd backend && pytest -q          # backend (uses testcontainers → needs Docker)
cd frontend && npm run build     # frontend type-check + build
```
