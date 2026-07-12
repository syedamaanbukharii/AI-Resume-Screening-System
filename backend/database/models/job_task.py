"""Background job-processing task ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import Base, uuid_pk


class JobProcessingTask(Base):
    """Tracks the status of an async background task."""

    __tablename__ = "job_processing_tasks"
    __table_args__ = (
        CheckConstraint(
            "task_type IN ('resume_parse', 'batch_rank', 'generate_questions', 'generate_report')",
            name="ck_tasks_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')", name="ck_tasks_status"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    task_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
