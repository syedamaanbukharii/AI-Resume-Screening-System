"""Declarative base, portable column-type helpers, and model registry.

Column types are written portably so the ORM runs against PostgreSQL in
production/tests while degrading gracefully elsewhere:

* ``uuid_pk`` / UUIDs use SQLAlchemy core ``Uuid`` — no dialect-specific import.
* ``json_variant`` maps to ``jsonb`` on PostgreSQL and plain JSON elsewhere.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeEngine


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def json_variant() -> TypeEngine:
    """Return a JSON type that resolves to jsonb on PostgreSQL."""
    return JSON().with_variant(JSONB, "postgresql")


def embedding_column(dimension: int) -> Mapped[list[float] | None]:
    """Return a nullable embedding column.

    Uses pgvector's ``Vector`` type on PostgreSQL when the ``pgvector`` package
    is installed; otherwise falls back to a JSON-encoded float list so the ORM
    and portable (e.g. SQLite) test paths still function. Vector similarity
    queries require the pgvector backend.
    """
    try:
        from pgvector.sqlalchemy import Vector

        col_type: TypeEngine = Vector(dimension)
    except ImportError:
        col_type = JSON().with_variant(JSONB, "postgresql")
    return mapped_column(col_type, nullable=True)


def uuid_pk() -> Mapped[uuid.UUID]:
    """Return a UUID primary-key column with a client-side default."""
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


def created_at_col() -> Mapped[datetime]:
    """Return a created_at column defaulting to now()."""
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def updated_at_col() -> Mapped[datetime]:
    """Return an updated_at column.

    ``onupdate`` fires on ORM flushes only, not on raw SQL UPDATE statements.
    """
    return mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# Import models so they register on Base.metadata.
from backend.database.models.user import User  # noqa: E402
from backend.database.models.candidate import Candidate  # noqa: E402
from backend.database.models.job import Job  # noqa: E402
from backend.database.models.resume import Resume  # noqa: E402
from backend.database.models.candidate_job import CandidateJob  # noqa: E402
from backend.database.models.job_task import JobProcessingTask  # noqa: E402
from backend.database.models.interview_question import InterviewQuestion  # noqa: E402
from backend.database.models.report import Report  # noqa: E402
from backend.database.models.refresh_token import RefreshToken  # noqa: E402
from backend.database.models.audit_log import AuditLog  # noqa: E402

__all__ = [
    "Base",
    "json_variant",
    "embedding_column",
    "uuid_pk",
    "created_at_col",
    "updated_at_col",
    "User",
    "Candidate",
    "Job",
    "Resume",
    "CandidateJob",
    "JobProcessingTask",
    "InterviewQuestion",
    "Report",
    "RefreshToken",
    "AuditLog",
]
