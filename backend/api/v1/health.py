"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from backend.api.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — always returns ok if the process is up."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(session: DbSession) -> dict[str, str]:
    """Readiness probe — verifies the database is reachable."""
    await session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
