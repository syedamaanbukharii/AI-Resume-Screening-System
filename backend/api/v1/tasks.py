"""Background-task status polling endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.deps import CurrentUser, DbSession
from backend.core.exceptions import NotFoundException
from backend.database.repositories.task_repo import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatus(BaseModel):
    """Public representation of a background task's state."""

    id: str
    task_type: str
    reference_id: str
    status: str
    error_message: str | None

    model_config = {"from_attributes": True}


@router.get("/{task_id}", response_model=TaskStatus)
async def get_task(
    task_id: uuid.UUID, _user: CurrentUser, session: DbSession
) -> TaskStatus:
    """Return the current status of a background task."""
    task = await TaskRepository(session).get(task_id)
    if task is None:
        raise NotFoundException("Task not found")
    return TaskStatus(
        id=str(task.id),
        task_type=task.task_type,
        reference_id=str(task.reference_id),
        status=task.status,
        error_message=task.error_message,
    )
