"""Admin control of the rotating code, the policy and live visitor sessions."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminDep, CsrfDep, IpHashDep, OwnerDep, SessionDep
from app.models.access import AccessCode, RotationReason
from app.schemas.access import (
    AccessCodeOut,
    AccessPolicyOut,
    AccessPolicyUpdate,
    AccessStats,
    GuestSessionOut,
)
from app.schemas.common import Message, Page
from app.services import access_service, qr_service

router = APIRouter(prefix="/admin/access", tags=["admin:access"])


def _code_out(code: AccessCode) -> AccessCodeOut:
    """Attach the poster URL and rendered QR to a stored code."""
    return AccessCodeOut(
        id=code.id,
        code=code.code,
        is_active=code.is_active,
        reason=code.reason,
        scan_count=code.scan_count,
        created_at=code.created_at,
        expires_at=code.expires_at,
        retired_at=code.retired_at,
        poster_url=qr_service.poster_url(code.code),
        qr_svg=qr_service.render_svg(code.code),
    )


@router.get("/policy", response_model=AccessPolicyOut)
async def read_policy(session: SessionDep, _admin: AdminDep) -> AccessPolicyOut:
    """Current rotation and session rules."""
    policy = await access_service.get_policy(session)
    return AccessPolicyOut.model_validate(policy)


@router.patch("/policy", response_model=AccessPolicyOut)
async def update_policy(
    payload: AccessPolicyUpdate,
    session: SessionDep,
    owner: OwnerDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AccessPolicyOut:
    """Change how often the code rotates and how long a scan lasts."""
    policy = await access_service.update_policy(session, payload, actor=owner, ip_hash=ip_hash)
    return AccessPolicyOut.model_validate(policy)


@router.get("/code", response_model=AccessCodeOut)
async def read_active_code(session: SessionDep, _admin: AdminDep) -> AccessCodeOut:
    """The code currently on the wall, with a printable QR."""
    code = await access_service.ensure_active_code(session)
    return _code_out(code)


@router.post("/code/rotate", response_model=AccessCodeOut, status_code=status.HTTP_201_CREATED)
async def rotate_code(
    session: SessionDep,
    owner: OwnerDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AccessCodeOut:
    """Retire the current code immediately and print a new one."""
    code = await access_service.rotate_code(
        session, reason=RotationReason.MANUAL, actor=owner, ip_hash=ip_hash
    )
    return _code_out(code)


@router.get("/stats", response_model=AccessStats)
async def read_stats(session: SessionDep, _admin: AdminDep) -> AccessStats:
    """Headline numbers for the dashboard."""
    return AccessStats.model_validate(await access_service.collect_stats(session))


@router.get("/sessions", response_model=Page[GuestSessionOut])
async def list_sessions(
    session: SessionDep,
    _admin: AdminDep,
    include_ended: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[GuestSessionOut]:
    """Visitor sessions, newest first."""
    rows, total = await access_service.list_sessions(
        session, include_ended=include_ended, limit=limit, offset=offset
    )
    return Page[GuestSessionOut](
        items=[GuestSessionOut.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/sessions/{session_id}", response_model=Message)
async def revoke_session(
    session_id: uuid.UUID,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> Message:
    """Kick one device out of the guest guide."""
    ended = await access_service.revoke_session(session, session_id, actor=admin, ip_hash=ip_hash)
    if not ended:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No live session with that id")
    return Message(detail="Session ended")


@router.post("/sessions/revoke-all", response_model=Message)
async def revoke_all_sessions(
    session: SessionDep,
    owner: OwnerDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> Message:
    """Kick every device out of the guest guide."""
    count = await access_service.revoke_all_sessions(session, actor=owner, ip_hash=ip_hash)
    return Message(detail=f"{count} session(s) ended")
