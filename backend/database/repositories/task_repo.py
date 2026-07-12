"""Job-processing-task repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import JobProcessingTask
from backend.database.repositories.base_repo import BaseRepository


class TaskRepository(BaseRepository[JobProcessingTask]):
    """Data access for background task records."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the JobProcessingTask model."""
        super().__init__(JobProcessingTask, session)

    async def get_pending_tasks(self) -> list[JobProcessingTask]:
        """Return all tasks in the 'pending' state."""
        result = await self.session.execute(
            select(JobProcessingTask).where(JobProcessingTask.status == "pending")
        )
        return list(result.scalars().all())

    async def update_status(
        self, task: JobProcessingTask, status: str, error_message: str | None = None
    ) -> JobProcessingTask:
        """Transition a task to a new status, stamping timestamps."""
        task.status = status
        now = datetime.now(UTC)
        if status == "running" and task.started_at is None:
            task.started_at = now
        if status in {"completed", "failed"}:
            task.completed_at = now
        if error_message is not None:
            task.error_message = error_message
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task
