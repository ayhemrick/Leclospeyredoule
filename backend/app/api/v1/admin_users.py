"""Managing administrator accounts. Owner role only."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CsrfDep, IpHashDep, OwnerDep, SessionDep
from app.models.admin_user import AdminRole, AdminUser
from app.schemas.auth import AdminCreate, AdminOut, AdminUpdate
from app.schemas.common import Message
from app.services import audit_service, auth_service

router = APIRouter(prefix="/admin/users", tags=["admin:users"])


@router.get("", response_model=list[AdminOut])
async def list_admins(session: SessionDep, _owner: OwnerDep) -> list[AdminUser]:
    """Every administrator account."""
    statement = select(AdminUser).order_by(AdminUser.created_at)
    return list((await session.execute(statement)).scalars().all())


@router.post("", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: AdminCreate,
    session: SessionDep,
    owner: OwnerDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AdminUser:
    """Invite another administrator with an initial password."""
    try:
        return await auth_service.create_admin(
            session,
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role=payload.role,
            created_by=owner,
            ip_hash=ip_hash,
        )
    except IntegrityError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with that e-mail already exists"
        ) from exc


@router.patch("/{admin_id}", response_model=AdminOut)
async def update_admin(
    admin_id: uuid.UUID,
    payload: AdminUpdate,
    session: SessionDep,
    owner: OwnerDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AdminUser:
    """Change another administrator's name, role or active status.

    Guards against an owner locking everyone out: the last active owner can
    neither be demoted nor deactivated.
    """
    target = await session.get(AdminUser, admin_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    changes = payload.model_dump(exclude_unset=True)
    losing_owner = (changes.get("role") not in (None, AdminRole.OWNER)) or (
        changes.get("is_active") is False
    )
    if target.role is AdminRole.OWNER and losing_owner and await _active_owner_count(session) <= 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "The last active owner cannot be demoted or deactivated"
        )

    for field, value in changes.items():
        setattr(target, field, value)
    if changes.get("is_active") is False:
        # Force every device of the deactivated account to sign out.
        target.token_epoch = str(uuid.uuid4())
    await session.flush()
    await audit_service.record(
        session,
        action="admin.updated",
        actor=owner,
        entity_type="admin_user",
        entity_id=target.id,
        context={"fields": sorted(changes)},
        ip_hash=ip_hash,
    )
    return target


@router.delete("/{admin_id}", response_model=Message)
async def delete_admin(
    admin_id: uuid.UUID,
    session: SessionDep,
    owner: OwnerDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> Message:
    """Delete an administrator account."""
    if admin_id == owner.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "You cannot delete your own account")
    target = await session.get(AdminUser, admin_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if target.role is AdminRole.OWNER and await _active_owner_count(session) <= 1:
        raise HTTPException(status.HTTP_409_CONFLICT, "The last active owner cannot be deleted")

    email = target.email
    await session.delete(target)
    await audit_service.record(
        session,
        action="admin.deleted",
        actor=owner,
        entity_type="admin_user",
        entity_id=admin_id,
        context={"email": email},
        ip_hash=ip_hash,
    )
    return Message(detail="Administrator deleted")


async def _active_owner_count(session: AsyncSession) -> int:
    """How many active owners remain."""
    statement = (
        select(func.count())
        .select_from(AdminUser)
        .where(AdminUser.role == AdminRole.OWNER, AdminUser.is_active.is_(True))
    )
    return (await session.execute(statement)).scalar_one()
