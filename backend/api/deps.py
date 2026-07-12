"""FastAPI dependencies for auth and database access."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ForbiddenException, UnauthorizedException
from backend.core.security import decode_token
from backend.database.models import User
from backend.database.repositories.user_repo import UserRepository
from backend.database.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    session: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    """Resolve and return the authenticated user from a bearer token."""
    if not token:
        raise UnauthorizedException("Not authenticated")
    payload = decode_token(token, expected_type="access")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedException("Invalid token subject") from exc

    user = await UserRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(user: CurrentUser) -> User:
    """Ensure the authenticated user has the admin role."""
    if user.role != "admin":
        raise ForbiddenException("Admin privileges required")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
