"""FAISS-backed vector store for local dev without pgvector.

This keeps a per-process in-memory index. It is intended only for local
development; it is not shared across workers and is not persistent unless
explicitly saved. Production uses PgVectorStore.
"""

from __future__ import annotations

import threading
import uuid

from backend.vectorstore.base import VectorStore


class FaissStore(VectorStore):
    """A minimal in-memory nearest-neighbor store using numpy cosine.

    Uses numpy rather than a hard faiss dependency so local dev needs no
    native build. The interface matches PgVectorStore for drop-in swapping.
    """

    def __init__(self, dimension: int) -> None:
        """Initialize empty per-job vector maps."""
        self._dimension = dimension
        self._lock = threading.Lock()
        # job_id -> {resume_id: vector}
        self._vectors: dict[uuid.UUID, dict[uuid.UUID, list[float]]] = {}
        # resume_id -> job_id, for upsert routing
        self._resume_job: dict[uuid.UUID, uuid.UUID] = {}

    def register_resume_job(self, resume_id: uuid.UUID, job_id: uuid.UUID) -> None:
        """Associate a resume with its job so upsert can route it."""
        with self._lock:
            self._resume_job[resume_id] = job_id

    async def upsert_resume(self, resume_id: uuid.UUID, embedding: list[float]) -> None:
        """Store an embedding under its registered job."""
        if len(embedding) != self._dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self._dimension}, got {len(embedding)}"
            )
        with self._lock:
            job_id = self._resume_job.get(resume_id)
            if job_id is None:
                raise ValueError(f"Resume {resume_id} has no registered job")
            self._vectors.setdefault(job_id, {})[resume_id] = embedding

    async def query_similar_resumes(
        self, embedding: list[float], job_id: uuid.UUID, top_k: int
    ) -> list[tuple[uuid.UUID, float]]:
        """Return nearest resumes for a job by cosine distance."""
        import numpy as np

        with self._lock:
            candidates = self._vectors.get(job_id, {})
            if not candidates:
                return []
            query = np.asarray(embedding, dtype=np.float32)
            q_norm = np.linalg.norm(query) or 1.0
            scored: list[tuple[uuid.UUID, float]] = []
            for rid, vec in candidates.items():
                v = np.asarray(vec, dtype=np.float32)
                v_norm = np.linalg.norm(v) or 1.0
                cosine_sim = float(np.dot(query, v) / (q_norm * v_norm))
                scored.append((rid, 1.0 - cosine_sim))  # distance
            scored.sort(key=lambda pair: pair[1])
            return scored[:top_k]
