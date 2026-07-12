"""User endpoints: self-service profile and admin management."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from backend.api.deps import CurrentAdmin, CurrentUser, DbSession
from backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


class UserOut(BaseModel):
    """Public user representation."""

    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UpdateMeRequest(BaseModel):
    """Editable self-profile fields."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)


class UpdateRoleRequest(BaseModel):
    """Admin role-change payload."""

    role: str


def _to_out(user) -> UserOut:  # type: ignore[no-untyped-def]
    """Map an ORM user to its public representation."""
    return UserOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUser) -> UserOut:
    """Return the authenticated user's profile."""
    return _to_out(user)


@router.put("/me", response_model=UserOut)
async def update_me(
    payload: UpdateMeRequest, user: CurrentUser, session: DbSession
) -> UserOut:
    """Update the authenticated user's profile."""
    updated = await UserService(session).update_user(user, full_name=payload.full_name)
    await session.commit()
    return _to_out(updated)


@router.get("", response_model=list[UserOut])
async def list_users(
    _admin: CurrentAdmin, session: DbSession, limit: int = 50, offset: int = 0
) -> list[UserOut]:
    """List all users (admin only)."""
    users = await UserService(session).list_users(limit=limit, offset=offset)
    return [_to_out(u) for u in users]


@router.put("/{user_id}/role", response_model=UserOut)
async def update_role(
    user_id: uuid.UUID, payload: UpdateRoleRequest, _admin: CurrentAdmin, session: DbSession
) -> UserOut:
    """Change a user's role (admin only)."""
    updated = await UserService(session).update_role(user_id, payload.role)
    await session.commit()
    return _to_out(updated)
