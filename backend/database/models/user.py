"""User ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models import Base, created_at_col, updated_at_col, uuid_pk
import uuid


class User(Base):
    """A platform user with an admin or recruiter role."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'recruiter')", name="ck_users_role"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="recruiter")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()
