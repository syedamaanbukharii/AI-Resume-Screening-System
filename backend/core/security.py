"""Security primitives: bcrypt password hashing and PyJWT token handling.

Uses the ``bcrypt`` library directly (no passlib) and ``PyJWT`` (no python-jose).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from backend.core.config import settings
from backend.core.exceptions import UnauthorizedException

# bcrypt rejects passwords longer than 72 bytes; we truncate defensively.
_BCRYPT_MAX_BYTES = 72


def get_password_hash(password: str) -> str:
    """Hash a plaintext password with bcrypt and return a UTF-8 string."""
    pwd_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plaintext password matches the bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    """Create a signed JWT and return (token, jti, expiry)."""
    now = datetime.now(UTC)
    expire = now + expires_delta
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def create_access_token(subject: str) -> str:
    """Create a short-lived access token for the given subject (user id)."""
    token, _, _ = _create_token(
        subject, "access", timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return token


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Create a long-lived refresh token; return (token, jti, expiry)."""
    return _create_token(
        subject, "refresh", timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and validate a JWT, optionally asserting its ``type`` claim."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedException("Invalid token") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise UnauthorizedException("Invalid token type")
    return payload
