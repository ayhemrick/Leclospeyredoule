"""Append-only record of everything an administrator changes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """One recorded action.

    Rows are never updated or deleted by the application: the admin UI only
    reads them, which is what makes the log worth trusting.
    """

    __tablename__ = "audit_log"

    action: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    actor_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("admin_user.id", ondelete="SET NULL"), index=True
    )
    #: Kept denormalised so the log stays readable after an account is deleted.
    actor_label: Mapped[str] = mapped_column(String(160), default="system", nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(60))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ip_hash: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
