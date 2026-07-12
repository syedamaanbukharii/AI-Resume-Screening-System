"""Authentication service: signup, login, refresh, logout."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from backend.database.models import RefreshToken, User
from backend.database.repositories.refresh_token_repo import RefreshTokenRepository
from backend.database.repositories.user_repo import UserRepository
from backend.core.exceptions import (
    ConflictException,
    UnauthorizedException,
)


def _hash_token(token: str) -> str:
    """Return a SHA-256 hash of a refresh token for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    """Coordinates credential verification and token lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repositories to the current session."""
        self.session = session
        self.users = UserRepository(session)
        self.tokens = RefreshTokenRepository(session)

    async def signup(self, email: str, password: str, full_name: str) -> User:
        """Create a new user, rejecting duplicate emails."""
        if await self.users.get_by_email(email):
            raise ConflictException("Email already registered")
        return await self.users.create(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role="recruiter",
        )

    async def login(self, email: str, password: str) -> tuple[str, str, User]:
        """Verify credentials and issue access + refresh tokens."""
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException("Account is disabled")
        access, refresh = await self._issue_tokens(user.id)
        return access, refresh, user

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Rotate a valid refresh token, returning fresh access + refresh."""
        payload = decode_token(refresh_token, expected_type="refresh")
        stored = await self.tokens.get_by_token_hash(_hash_token(refresh_token))
        if stored is None or stored.revoked:
            raise UnauthorizedException("Refresh token is invalid or revoked")
        stored.revoked = True
        self.session.add(stored)
        user_id = uuid.UUID(payload["sub"])
        return await self._issue_tokens(user_id)

    async def logout(self, user_id: uuid.UUID) -> None:
        """Revoke all refresh tokens for a user."""
        await self.tokens.revoke_all_for_user(user_id)

    async def _issue_tokens(self, user_id: uuid.UUID) -> tuple[str, str]:
        """Create and persist a new access/refresh token pair."""
        access = create_access_token(str(user_id))
        refresh, _, expires_at = create_refresh_token(str(user_id))
        self.session.add(
            RefreshToken(
                user_id=user_id,
                token_hash=_hash_token(refresh),
                expires_at=expires_at,
                revoked=False,
            )
        )
        await self.session.flush()
        return access, refresh
