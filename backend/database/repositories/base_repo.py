"""Generic async CRUD repository."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Reusable async CRUD operations parameterized by an ORM model."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        """Bind the repository to a model type and session."""
        self.model = model
        self.session = session

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        """Return an entity by primary key, or None."""
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """Return a page of entities ordered by insertion."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return the total number of rows for the model."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, **kwargs: Any) -> ModelT:
        """Insert a new entity, flush to populate defaults, and return it."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelT, **kwargs: Any) -> ModelT:
        """Apply field updates to an entity and flush."""
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        """Hard-delete an entity by id; return True if a row was removed."""
        stmt = delete(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return bool(result.rowcount)
