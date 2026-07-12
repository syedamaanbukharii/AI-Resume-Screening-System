"""Database session dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and ensure it is closed after use."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
