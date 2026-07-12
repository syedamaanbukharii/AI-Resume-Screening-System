"""Candidate-report ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import Base, json_variant, uuid_pk


class Report(Base):
    """A generated hiring report for a candidate-job pairing."""

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "recommendation IN "
            "('strongly_recommend', 'recommend', 'neutral', 'not_recommend')",
            name="ck_report_recommendation",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list[Any]] = mapped_column(json_variant(), default=list, nullable=False)
    weaknesses: Mapped[list[Any]] = mapped_column(json_variant(), default=list, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    risk_factors: Mapped[list[Any]] = mapped_column(json_variant(), default=list, nullable=False)
    interview_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
