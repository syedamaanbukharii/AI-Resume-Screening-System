# AI Resume Screening System

An explainable, agentic resume screening platform. Upload resumes against a job,
get deterministic evidence-backed rankings, and generate tailored interview
questions and hiring reports with an LLM — with every score traceable to why.

## What it does

- **Parse** resumes (PDF/DOCX/TXT) into structured profiles in a single LLM call.
- **Rank** candidates against a job with a deterministic, five-factor weighted
  score — skills (blended lexical + semantic), experience, education, full-document
  semantic similarity, and certifications — where every sub-score carries evidence.
- **Screen** each candidate with a LangGraph interview agent (conditional
  follow-up probes for unmet required skills) and a single-call hiring report,
  both streamed live over SSE, with PDF export.

## Architecture at a glance

```
Next.js frontend ──REST + SSE──▶ FastAPI (JWT + RBAC)
                                   ├─ Resume pipeline (async: extract → LLM parse → embed)
                                   ├─ Matching engine (deterministic, evidence-backed)
                                   ├─ Interview agent (LangGraph state machine)
                                   ├─ Report agent (single structured call)
                                   ├─ Model router (Groq online ↔ Gemma/Ollama offline)
                                   ├─ Embeddings (sentence-transformers | Ollama)
                                   └─ PostgreSQL + pgvector
```

See `docs/ARCHITECTURE.md` for the decisions behind each of these — including
which "agents" are deliberately *not* agents, and why.

## Quick start (Docker)

```bash
cp .env.example .env          # set GROQ_API_KEY for online LLM parsing (optional)
docker compose -f docker/docker-compose.yml up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

The default stack needs **no local model server** — embeddings run in-process via
sentence-transformers, and LLM parsing uses Groq when `GROQ_API_KEY` is set.

For a fully-offline path (Gemma + nomic-embed via Ollama):

```bash
docker compose -f docker/docker-compose.yml --profile offline up --build
# then set EMBEDDING_PROVIDER=ollama and EMBEDDING_DIMENSION=768 in the backend env
```

## Local development

See `docs/SETUP.md`. In short:

```bash
# Backend
pip install -r backend/requirements.txt
cd backend && alembic upgrade head && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Tech stack

FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL + pgvector · LangGraph · Groq ·
Ollama · sentence-transformers · Next.js 14 · Tailwind · shadcn/ui patterns.

## Documentation

- `docs/ARCHITECTURE.md` — design decisions and trade-offs.
- `docs/SETUP.md` — local and container setup.
- `docs/API.md` — endpoint reference.
