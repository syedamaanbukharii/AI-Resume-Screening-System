"""Refresh-token repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import RefreshToken
from backend.database.repositories.base_repo import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Data access for refresh-token records."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the RefreshToken model."""
        super().__init__(RefreshToken, session)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Return a refresh token by its hash, or None."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoke every active refresh token for a user."""
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
