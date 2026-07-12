"""Pytest fixtures backed by a real PostgreSQL container.

SQLite is deliberately avoided: models use jsonb variants and Phase 2 adds
pgvector, neither of which SQLite can represent. A throwaway SQLite suite would
not exercise the production schema.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.api.deps import get_current_user
from backend.core.security import get_password_hash
from backend.database.models import Base, User
from backend.database.session import get_db
from backend.main import create_app


@pytest.fixture(scope="session")
def postgres_url() -> AsyncGenerator[str, None]:
    """Start a Postgres 16 container for the whole test session.

    Imported lazily so unit tests that don't request a DB fixture can run
    without testcontainers/Docker installed.
    """
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest_asyncio.fixture(scope="session")
async def engine(postgres_url: str):
    """Create the async engine and schema once per session."""
    eng = create_async_engine(postgres_url, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session wrapped in a transaction that rolls back per test."""
    connection = await engine.connect()
    trans = await connection.begin()
    factory = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx client with the DB dependency overridden."""
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _make_user(session: AsyncSession, role: str) -> User:
    """Insert a user with a known password and return it."""
    user = User(
        email=f"{role}-{uuid.uuid4().hex[:8]}@test.io",
        hashed_password=get_password_hash("password123"),
        full_name=f"Test {role}",
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def recruiter(db_session: AsyncSession) -> User:
    """Create and return a recruiter user."""
    return await _make_user(db_session, "recruiter")


@pytest_asyncio.fixture
async def admin(db_session: AsyncSession) -> User:
    """Create and return an admin user."""
    return await _make_user(db_session, "admin")


@pytest_asyncio.fixture
async def auth_client(
    db_session: AsyncSession, recruiter: User
) -> AsyncGenerator[AsyncClient, None]:
    """Yield a client authenticated as a recruiter via dependency override."""
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return recruiter

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(
    db_session: AsyncSession, admin: User
) -> AsyncGenerator[AsyncClient, None]:
    """Yield a client authenticated as an admin via dependency override."""
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_user() -> User:
        return admin

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
