"""Resume repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Resume
from backend.database.repositories.base_repo import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    """Data access for Resume records."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the Resume model."""
        super().__init__(Resume, session)

    async def get_by_job_id(self, job_id: uuid.UUID) -> list[Resume]:
        """Return all resumes uploaded for a job."""
        result = await self.session.execute(select(Resume).where(Resume.job_id == job_id))
        return list(result.scalars().all())

    async def get_by_candidate_id(self, candidate_id: uuid.UUID) -> list[Resume]:
        """Return all resumes for a candidate, newest first."""
        result = await self.session.execute(
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.uploaded_at.desc())
        )
        return list(result.scalars().all())
