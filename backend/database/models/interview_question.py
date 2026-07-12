"""Interview-question ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import Base, uuid_pk


class InterviewQuestion(Base):
    """A generated interview question tied to a candidate-job pairing."""

    __tablename__ = "interview_questions"
    __table_args__ = (
        CheckConstraint(
            "category IN ('technical', 'behavioral', 'scenario', 'coding', 'followup')",
            name="ck_iq_category",
        ),
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')", name="ck_iq_difficulty"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
