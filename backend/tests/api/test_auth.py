"""Authentication flow tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str = "new@test.io") -> dict:
    """Register a user and return the response JSON."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "full_name": "New User"},
    )
    return resp


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient) -> None:
    """A new email registers successfully."""
    resp = await _signup(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@test.io"
    assert body["role"] == "recruiter"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient) -> None:
    """Registering the same email twice conflicts."""
    await _signup(client, "dup@test.io")
    resp = await _signup(client, "dup@test.io")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


@pytest.mark.asyncio
async def test_login_and_refresh(client: AsyncClient) -> None:
    """Login returns tokens; refresh rotates them."""
    await _signup(client, "login@test.io")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@test.io", "password": "password123"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["token_type"] == "bearer"

    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"] != tokens["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Wrong password is rejected."""
    await _signup(client, "wrong@test.io")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@test.io", "password": "nope-nope-nope"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_is_single_use(client: AsyncClient) -> None:
    """A rotated refresh token cannot be reused."""
    await _signup(client, "rotate@test.io")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "rotate@test.io", "password": "password123"},
    )
    old_refresh = login.json()["refresh_token"]
    await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401
