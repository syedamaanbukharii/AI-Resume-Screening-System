"""Candidate service: ranked retrieval and recruiter status/notes updates."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundException, ValidationException
from backend.database.models import Candidate, CandidateJob
from backend.database.repositories.candidate_job_repo import CandidateJobRepository
from backend.database.repositories.candidate_repo import CandidateRepository

_VALID_STATUSES = {"new", "screened", "shortlisted", "interview", "rejected", "hired"}


class CandidateService:
    """Business logic for candidate retrieval and recruiter actions."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repositories to the session."""
        self.session = session
        self.candidates = CandidateRepository(session)
        self.candidate_jobs = CandidateJobRepository(session)

    async def list_ranked_for_job(self, job_id: uuid.UUID) -> list[CandidateJob]:
        """Return candidate-job rows for a job, ranked by composite score."""
        return await self.candidate_jobs.get_by_job_id_ranked(job_id)

    async def get_candidate(self, candidate_id: uuid.UUID) -> Candidate:
        """Return a candidate by id or raise NotFound."""
        candidate = await self.candidates.get(candidate_id)
        if candidate is None:
            raise NotFoundException("Candidate not found")
        return candidate

    async def get_for_job(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID
    ) -> CandidateJob:
        """Return the candidate-job row for a pair or raise NotFound."""
        cj = await self.candidate_jobs.get_by_candidate_and_job(candidate_id, job_id)
        if cj is None:
            raise NotFoundException("Candidate is not associated with this job")
        return cj

    async def update_status(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID, status: str
    ) -> CandidateJob:
        """Update a candidate's status on a job (recruiter action)."""
        if status not in _VALID_STATUSES:
            raise ValidationException(f"Invalid status: {status}")
        cj = await self.get_for_job(candidate_id, job_id)
        cj.status = status
        cj.status_updated_at = datetime.now(UTC)
        self.session.add(cj)
        await self.session.commit()
        await self.session.refresh(cj)
        return cj

    async def update_notes(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID, notes: str
    ) -> CandidateJob:
        """Set recruiter notes on a candidate-job row."""
        cj = await self.get_for_job(candidate_id, job_id)
        cj.recruiter_notes = notes
        self.session.add(cj)
        await self.session.commit()
        await self.session.refresh(cj)
        return cj
