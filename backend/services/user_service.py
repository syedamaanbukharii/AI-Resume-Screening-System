"""User service: profile and admin operations."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundException, ValidationException
from backend.database.models import User
from backend.database.repositories.user_repo import UserRepository

_VALID_ROLES = {"admin", "recruiter"}


class UserService:
    """Business logic for user profile and role management."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the user repository to the session."""
        self.session = session
        self.users = UserRepository(session)

    async def get_user(self, user_id: uuid.UUID) -> User:
        """Return a user by id or raise NotFound."""
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundException("User not found")
        return user

    async def update_user(self, user: User, *, full_name: str | None = None) -> User:
        """Update mutable profile fields on a user."""
        if full_name is not None:
            user.full_name = full_name
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def list_users(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        """Return a page of users (admin only)."""
        return await self.users.list(limit=limit, offset=offset)

    async def update_role(self, user_id: uuid.UUID, role: str) -> User:
        """Set a user's role (admin only)."""
        if role not in _VALID_ROLES:
            raise ValidationException(f"Invalid role: {role}")
        user = await self.get_user(user_id)
        user.role = role
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
