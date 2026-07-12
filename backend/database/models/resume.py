"""Resume ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import Base, json_variant, uuid_pk, embedding_column
from sqlalchemy import DateTime, func
from backend.core.config import settings


class Resume(Base):
    """A resume file uploaded for a candidate against a specific job."""

    __tablename__ = "resumes"
    __table_args__ = (
        CheckConstraint("file_type IN ('pdf', 'docx', 'txt')", name="ck_resumes_file_type"),
        CheckConstraint(
            "parsing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_resumes_parsing_status",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_profile: Mapped[dict[str, Any] | None] = mapped_column(json_variant(), nullable=True)
    parsing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    parsing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # embedding: nomic-embed-text is 768-dim (see EMBEDDING_DIMENSION).
    embedding: Mapped[list[float] | None] = embedding_column(settings.EMBEDDING_DIMENSION)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
