"""Audit service: append-only action logging."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import AuditLog


class AuditService:
    """Writes immutable audit-log entries."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the session."""
        self.session = session

    async def log_action(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip: str | None = None,
    ) -> AuditLog:
        """Persist an audit-log entry and return it."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
