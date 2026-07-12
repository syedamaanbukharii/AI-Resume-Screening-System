"""Candidate repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Candidate
from backend.database.repositories.base_repo import BaseRepository


class CandidateRepository(BaseRepository[Candidate]):
    """Data access for Candidate records."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the Candidate model."""
        super().__init__(Candidate, session)

    async def get_by_email(self, email: str) -> Candidate | None:
        """Return a candidate by email, or None."""
        result = await self.session.execute(
            select(Candidate).where(Candidate.email == email)
        )
        return result.scalar_one_or_none()
