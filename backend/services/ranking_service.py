"""Ranking service: JD embedding and orchestrated job ranking."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories.job_repo import JobRepository
from backend.embeddings.base import BaseEmbedder, EmbeddingError
from backend.embeddings.factory import get_embedder
from backend.matching.ranker import rank_job
from backend.matching.schemas import MatchResult

logger = structlog.get_logger(__name__)


class RankingService:
    """Coordinates JD embedding and the matching engine for a job."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the job repository to the session."""
        self.session = session
        self.jobs = JobRepository(session)

    async def embed_job_description(self, job_id: uuid.UUID) -> bool:
        """Embed a job's description text and store it on the job row.

        Runs synchronously (one short call, not a batch) so the semantic factor
        has both sides of the cosine. Returns True on success, False if the
        embedder is unreachable — a missing JD embedding degrades semantic
        scoring to neutral rather than failing the whole rank.
        """
        job = await self.jobs.get(job_id)
        if job is None:
            return False
        text = job.description_raw
        parsed = job.description_parsed or {}
        if isinstance(parsed, dict):
            extra = " ".join(
                str(x)
                for key in ("required_skills", "preferred_skills", "responsibilities")
                for x in (parsed.get(key) or [])
            )
            text = f"{text}\n{extra}".strip()
        try:
            embedder: BaseEmbedder = get_embedder()
            vector = await embedder.embed(text)
        except EmbeddingError as exc:
            logger.warning("jd_embed_failed", job_id=str(job_id), error=str(exc))
            return False
        job.embedding = vector
        self.session.add(job)
        await self.session.commit()
        return True

    async def rank(self, job_id: uuid.UUID) -> list[tuple[uuid.UUID, MatchResult]]:
        """Score and persist rankings for all completed candidates on a job."""
        try:
            embedder: BaseEmbedder | None = get_embedder()
        except EmbeddingError:
            embedder = None  # semantic skill fallback degrades gracefully
        return await rank_job(session=self.session, job_id=job_id, embedder=embedder)
