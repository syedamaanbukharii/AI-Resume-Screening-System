"""Job service: CRUD and lifecycle for job postings."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundException, ValidationException
from backend.database.models import Job
from backend.database.repositories.job_repo import JobRepository

_VALID_STATUSES = {"draft", "active", "closed", "archived"}


class JobService:
    """Business logic for creating and managing job postings."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the job repository to the session."""
        self.session = session
        self.jobs = JobRepository(session)

    async def create_job(self, *, created_by: uuid.UUID, **fields: Any) -> Job:
        """Create a job posting owned by the given user."""
        return await self.jobs.create(created_by=created_by, **fields)

    async def get_job(self, job_id: uuid.UUID) -> Job:
        """Return a job by id or raise NotFound."""
        job = await self.jobs.get(job_id)
        if job is None:
            raise NotFoundException("Job not found")
        return job

    async def list_jobs(
        self, *, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Job]:
        """Return a page of jobs, optionally filtered by status."""
        if status is not None and status not in _VALID_STATUSES:
            raise ValidationException(f"Invalid status filter: {status}")
        return await self.jobs.list_filtered(status=status, limit=limit, offset=offset)

    async def update_job(self, job_id: uuid.UUID, **fields: Any) -> Job:
        """Apply partial updates to a job."""
        job = await self.get_job(job_id)
        updatable = {k: v for k, v in fields.items() if v is not None}
        return await self.jobs.update(job, **updatable)

    async def change_status(self, job_id: uuid.UUID, status: str) -> Job:
        """Transition a job to a new lifecycle status."""
        if status not in _VALID_STATUSES:
            raise ValidationException(f"Invalid status: {status}")
        job = await self.get_job(job_id)
        return await self.jobs.update(job, status=status)

    async def delete_job(self, job_id: uuid.UUID) -> Job:
        """Soft-delete a job by archiving it."""
        return await self.change_status(job_id, "archived")
