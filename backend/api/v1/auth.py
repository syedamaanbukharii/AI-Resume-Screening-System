"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from backend.api.deps import CurrentUser, DbSession
from backend.services.audit_service import AuditService
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Refresh-token payload."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Access/refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user representation."""

    id: str
    email: EmailStr
    full_name: str
    role: str

    model_config = {"from_attributes": True}


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, session: DbSession, request: Request) -> UserResponse:
    """Register a new recruiter account."""
    service = AuthService(session)
    user = await service.signup(payload.email, payload.password, payload.full_name)
    await AuditService(session).log_action(
        user_id=user.id,
        action="signup",
        entity_type="user",
        entity_id=user.id,
        ip=request.client.host if request.client else None,
    )
    await session.commit()
    return UserResponse(
        id=str(user.id), email=user.email, full_name=user.full_name, role=user.role
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: DbSession) -> TokenResponse:
    """Authenticate and return a token pair."""
    access, refresh, _user = await AuthService(session).login(payload.email, payload.password)
    await session.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, session: DbSession) -> TokenResponse:
    """Rotate a refresh token for a new token pair."""
    access, new_refresh = await AuthService(session).refresh_token(payload.refresh_token)
    await session.commit()
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: CurrentUser, session: DbSession) -> Response:
    """Revoke all refresh tokens for the current user."""
    await AuthService(session).logout(user.id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
