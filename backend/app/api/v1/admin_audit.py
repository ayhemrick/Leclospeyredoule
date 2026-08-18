"""Read-only view of the audit log."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import AdminDep, SessionDep
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogOut
from app.schemas.common import Page

router = APIRouter(prefix="/admin/audit", tags=["admin:audit"])


@router.get("", response_model=Page[AuditLogOut])
async def list_entries(
    session: SessionDep,
    _admin: AdminDep,
    action: Annotated[str | None, Query(max_length=60)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[AuditLogOut]:
    """Recent administrator activity, newest first."""
    filters = [AuditLog.action.startswith(action)] if action else []

    total = (
        await session.execute(select(func.count()).select_from(AuditLog).where(*filters))
    ).scalar_one()
    rows = (
        (
            await session.execute(
                select(AuditLog)
                .where(*filters)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return Page[AuditLogOut](
        items=[AuditLogOut.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
