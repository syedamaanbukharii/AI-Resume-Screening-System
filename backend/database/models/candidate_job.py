"""CandidateJob junction ORM model — one row per (candidate, job)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import Base, uuid_pk


class CandidateJob(Base):
    """Screening state and scores for a candidate on a specific job."""

    __tablename__ = "candidate_jobs"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),
        CheckConstraint(
            "status IN ('new', 'screened', 'shortlisted', 'interview', 'rejected', 'hired')",
            name="ck_candidate_jobs_status",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    skill_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    experience_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    education_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    certification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")
    recruiter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
