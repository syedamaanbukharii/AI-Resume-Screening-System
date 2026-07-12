"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings


def create_engine(url: str | None = None) -> AsyncEngine:
    """Create an async engine for the given URL (defaults to settings)."""
    return create_async_engine(
        url or settings.DATABASE_URL,
        echo=settings.APP_DEBUG,
        pool_pre_ping=True,
        future=True,
    )


engine: AsyncEngine = create_engine()

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
