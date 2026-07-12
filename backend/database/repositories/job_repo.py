"""Job repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Job
from backend.database.repositories.base_repo import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Data access for Job records."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the Job model."""
        super().__init__(Job, session)

    async def get_by_creator(self, user_id: uuid.UUID) -> list[Job]:
        """Return all jobs created by a given user."""
        result = await self.session.execute(select(Job).where(Job.created_by == user_id))
        return list(result.scalars().all())

    async def get_active_jobs(self) -> list[Job]:
        """Return all jobs with status 'active'."""
        result = await self.session.execute(select(Job).where(Job.status == "active"))
        return list(result.scalars().all())

    async def list_filtered(
        self, *, status: str | None, limit: int, offset: int
    ) -> list[Job]:
        """Return a page of jobs, optionally filtered by status."""
        stmt = select(Job)
        if status is not None:
            stmt = stmt.where(Job.status == status)
        stmt = stmt.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
