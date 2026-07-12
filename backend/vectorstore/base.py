"""Abstract vector-store interface."""

from __future__ import annotations

import abc
import uuid


class VectorStore(abc.ABC):
    """Persists and queries embedding vectors keyed by entity id."""

    @abc.abstractmethod
    async def upsert_resume(self, resume_id: uuid.UUID, embedding: list[float]) -> None:
        """Store or replace the embedding for a resume."""

    @abc.abstractmethod
    async def query_similar_resumes(
        self, embedding: list[float], job_id: uuid.UUID, top_k: int
    ) -> list[tuple[uuid.UUID, float]]:
        """Return (resume_id, distance) pairs for a job, nearest first."""
