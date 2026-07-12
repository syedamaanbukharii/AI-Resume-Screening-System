"""PostgreSQL + pgvector-backed vector store."""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.vectorstore.base import VectorStore


def _to_pgvector_literal(embedding: list[float]) -> str:
    """Render a float list as a pgvector text literal: '[1,2,3]'."""
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


class PgVectorStore(VectorStore):
    """Reads and writes embeddings on the resumes table via pgvector.

    The embedding lives on ``resumes.embedding`` (a VECTOR column). This store
    operates on the caller's session so writes participate in the caller's
    transaction.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the caller's session."""
        self.session = session

    async def upsert_resume(self, resume_id: uuid.UUID, embedding: list[float]) -> None:
        """Write the embedding onto an existing resume row."""
        await self.session.execute(
            text(
                "UPDATE resumes SET embedding = CAST(:emb AS vector) WHERE id = :rid"
            ),
            {"emb": _to_pgvector_literal(embedding), "rid": str(resume_id)},
        )

    async def query_similar_resumes(
        self, embedding: list[float], job_id: uuid.UUID, top_k: int
    ) -> list[tuple[uuid.UUID, float]]:
        """Return the nearest resumes for a job by cosine distance."""
        result = await self.session.execute(
            text(
                """
                SELECT id, embedding <=> CAST(:emb AS vector) AS distance
                FROM resumes
                WHERE job_id = :jid AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT :k
                """
            ),
            {"emb": _to_pgvector_literal(embedding), "jid": str(job_id), "k": top_k},
        )
        return [(uuid.UUID(str(row[0])), float(row[1])) for row in result.all()]
