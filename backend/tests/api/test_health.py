"""Health and readiness endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    """Liveness returns ok."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness(client: AsyncClient) -> None:
    """Readiness reports a connected database."""
    resp = await client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    assert resp.json()["database"] == "connected"
