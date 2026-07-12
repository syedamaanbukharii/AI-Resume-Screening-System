"""Vector-store factory selecting pgvector or FAISS per configuration."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.vectorstore.base import VectorStore
from backend.vectorstore.faiss_store import FaissStore
from backend.vectorstore.pgvector_store import PgVectorStore

# A single FAISS instance is shared across the process for local dev.
_faiss_singleton: FaissStore | None = None


def _get_faiss() -> FaissStore:
    """Return the process-wide FAISS store."""
    global _faiss_singleton
    if _faiss_singleton is None:
        _faiss_singleton = FaissStore(dimension=settings.EMBEDDING_DIMENSION)
    return _faiss_singleton


def _use_pgvector() -> bool:
    """Decide whether pgvector is the active backend."""
    mode = settings.VECTOR_STORE.lower()
    if mode == "pgvector":
        return True
    if mode == "faiss":
        return False
    # auto: use pgvector when the app DB is Postgres.
    return settings.DATABASE_URL.startswith("postgresql")


def get_vector_store(session: AsyncSession) -> VectorStore:
    """Return the configured vector store bound to the given session.

    pgvector uses the session directly; FAISS ignores it (in-memory).
    """
    if _use_pgvector():
        return PgVectorStore(session)
    return _get_faiss()
