"""User repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User
from backend.database.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for User records."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the User model."""
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email, or None."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
