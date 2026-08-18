"""Recording administrator actions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog

SYSTEM_ACTOR = "system"


async def record(
    session: AsyncSession,
    *,
    action: str,
    actor: AdminUser | None = None,
    entity_type: str | None = None,
    entity_id: str | UUID | int | None = None,
    context: dict[str, Any] | None = None,
    ip_hash: str | None = None,
) -> AuditLog:
    """Append one entry to the audit log.

    Args:
        session: the active database session; the caller commits.
        action: dotted action name, e.g. ``access.code_rotated``.
        actor: the administrator responsible, or ``None`` for automatic events.
        entity_type: the kind of object touched, e.g. ``attraction``.
        entity_id: identifier of the object touched.
        context: extra JSON-serialisable detail worth keeping.
        ip_hash: pseudonymised client address.

    Returns:
        The persisted log entry (not yet committed).
    """
    entry = AuditLog(
        action=action,
        actor_admin_id=actor.id if actor else None,
        actor_label=actor.email if actor else SYSTEM_ACTOR,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        context=context or {},
        ip_hash=ip_hash,
    )
    session.add(entry)
    await session.flush()
    return entry
