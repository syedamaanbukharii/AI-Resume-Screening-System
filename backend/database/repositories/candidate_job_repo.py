"""CandidateJob repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CandidateJob
from backend.database.repositories.base_repo import BaseRepository


class CandidateJobRepository(BaseRepository[CandidateJob]):
    """Data access for CandidateJob junction records."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the CandidateJob model."""
        super().__init__(CandidateJob, session)

    async def get_by_job_id_ranked(self, job_id: uuid.UUID) -> list[CandidateJob]:
        """Return candidate-job rows for a job, ranked by overall score desc."""
        result = await self.session.execute(
            select(CandidateJob)
            .where(CandidateJob.job_id == job_id)
            .order_by(CandidateJob.overall_score.desc().nullslast())
        )
        return list(result.scalars().all())

    async def get_by_candidate_and_job(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID
    ) -> CandidateJob | None:
        """Return the junction row for a (candidate, job) pair, or None."""
        result = await self.session.execute(
            select(CandidateJob).where(
                CandidateJob.candidate_id == candidate_id,
                CandidateJob.job_id == job_id,
            )
        )
        return result.scalar_one_or_none()
