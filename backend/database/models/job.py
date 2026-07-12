"""Job posting ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import (
    Base,
    created_at_col,
    embedding_column,
    json_variant,
    updated_at_col,
    uuid_pk,
)
from backend.core.config import settings


def _default_scoring_weights() -> dict[str, float]:
    """Return a fresh default scoring-weights dict (callable to avoid aliasing)."""
    return {
        "skill": 0.35,
        "experience": 0.25,
        "education": 0.15,
        "semantic": 0.15,
        "certification": 0.10,
    }


class Job(Base):
    """A job posting against which candidates are screened."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'closed', 'archived')", name="ck_jobs_status"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_parsed: Mapped[dict[str, Any] | None] = mapped_column(json_variant(), nullable=True)
    required_skills: Mapped[list[Any]] = mapped_column(json_variant(), default=list, nullable=False)
    preferred_skills: Mapped[list[Any]] = mapped_column(json_variant(), default=list, nullable=False)
    min_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scoring_weights: Mapped[dict[str, float]] = mapped_column(
        json_variant(), default=_default_scoring_weights, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # embedding: JD embedding for semantic matching (768-dim).
    embedding: Mapped[list[float] | None] = embedding_column(settings.EMBEDDING_DIMENSION)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()
