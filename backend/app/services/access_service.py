"""The rotating-code access system.

Lifecycle of a visit:

1. A single :class:`~app.models.access.AccessCode` is active and printed as a
   QR poster at the property.
2. A visitor scans it; :func:`redeem` exchanges the code for an opaque session
   token, stored hashed, and returns it to be set as an ``HttpOnly`` cookie.
3. Gated endpoints call :func:`resolve_session` on every request.
4. The code rotates on the cadence in :class:`~app.models.access.AccessPolicy`,
   either from the background worker or lazily on the next request that needs
   the code, whichever happens first.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import Executable, delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.core.logging import get_logger
from app.core.security import generate_access_code, generate_opaque_token, hash_secret
from app.models.access import (
    POLICY_SINGLETON_ID,
    AccessCode,
    AccessPolicy,
    GuestSession,
    RotationReason,
)
from app.models.admin_user import AdminUser
from app.schemas.access import AccessPolicyUpdate
from app.services import audit_service

logger = get_logger(__name__)

#: Do not write ``last_seen_at`` more often than this, to keep reads cheap.
LAST_SEEN_THROTTLE = timedelta(minutes=1)


async def _affected_rows(session: AsyncSession, statement: Executable) -> int:
    """Run an UPDATE or DELETE and return how many rows it touched."""
    result = cast("CursorResult[Any]", await session.execute(statement))
    return result.rowcount


class DenialReason(enum.StrEnum):
    """Why a scan was refused."""

    UNKNOWN_CODE = "unknown_code"
    EXPIRED_CODE = "expired_code"
    AT_CAPACITY = "at_capacity"


class AccessDeniedError(Exception):
    """Raised when a scanned code cannot be exchanged for a session."""

    def __init__(self, reason: DenialReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class RedeemedAccess:
    """The result of a successful scan."""

    token: str
    session_id: uuid.UUID
    expires_at: datetime


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------
async def get_policy(session: AsyncSession, *, for_update: bool = False) -> AccessPolicy:
    """Return the singleton policy row, creating it with defaults if missing.

    Args:
        session: active database session.
        for_update: take a row lock, which serialises concurrent rotations.
    """
    statement = select(AccessPolicy).where(AccessPolicy.id == POLICY_SINGLETON_ID)
    if for_update:
        statement = statement.with_for_update()
    policy = (await session.execute(statement)).scalar_one_or_none()
    if policy is None:
        policy = AccessPolicy(id=POLICY_SINGLETON_ID)
        session.add(policy)
        await session.flush()
    return policy


async def update_policy(
    session: AsyncSession,
    patch: AccessPolicyUpdate,
    *,
    actor: AdminUser,
    ip_hash: str | None = None,
) -> AccessPolicy:
    """Apply an admin change to the access rules.

    Changing the rotation cadence also re-dates the active code, so the admin
    sees the new expiry immediately instead of after the next rotation.
    """
    policy = await get_policy(session, for_update=True)
    changes = patch.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(policy, field, value)
    await session.flush()

    code = await get_active_code(session)
    if code is not None:
        code.expires_at = _expiry_for(code.created_at, policy)
    await audit_service.record(
        session,
        action="access.policy_updated",
        actor=actor,
        entity_type="access_policy",
        entity_id=POLICY_SINGLETON_ID,
        context=changes,
        ip_hash=ip_hash,
    )
    return policy


def _expiry_for(minted_at: datetime, policy: AccessPolicy) -> datetime | None:
    """Return when a code minted at ``minted_at`` should rotate."""
    if not policy.auto_rotate:
        return None
    return minted_at + timedelta(minutes=policy.rotation_interval_minutes)


# ---------------------------------------------------------------------------
# Codes
# ---------------------------------------------------------------------------
async def get_active_code(session: AsyncSession) -> AccessCode | None:
    """Return the currently printed code, if one exists."""
    statement = (
        select(AccessCode)
        .where(AccessCode.is_active.is_(True))
        .order_by(AccessCode.created_at.desc())
        .limit(1)
    )
    return (await session.execute(statement)).scalar_one_or_none()


async def ensure_active_code(session: AsyncSession) -> AccessCode:
    """Return the active code, minting or rotating it as the policy requires.

    This is the entry point used by request handlers: it means a fresh install
    has a working poster on first load, and an overdue rotation is applied even
    if the background worker is not running.
    """
    policy = await get_policy(session)
    code = await get_active_code(session)
    now = utcnow()

    if code is None:
        return await _mint_code(session, policy=policy, reason=RotationReason.INITIAL)
    if policy.auto_rotate and code.expires_at is not None and code.expires_at <= now:
        return await rotate_code(session, reason=RotationReason.SCHEDULED)
    return code


async def rotate_code(
    session: AsyncSession,
    *,
    reason: RotationReason,
    actor: AdminUser | None = None,
    ip_hash: str | None = None,
) -> AccessCode:
    """Retire the active code and publish a new one.

    Existing visitor sessions survive by default: someone already inside the
    house should not be logged out because the poster was reprinted. Owners who
    want the opposite can turn on ``revoke_sessions_on_rotation``.
    """
    policy = await get_policy(session, for_update=True)
    now = utcnow()
    previous = await get_active_code(session)

    if previous is not None:
        previous.is_active = False
        previous.retired_at = now

    revoked = 0
    if previous is not None and policy.revoke_sessions_on_rotation:
        revoked = await revoke_sessions_for_code(session, previous.id, at=now)

    code = await _mint_code(session, policy=policy, reason=reason, actor=actor, now=now)
    await audit_service.record(
        session,
        action="access.code_rotated",
        actor=actor,
        entity_type="access_code",
        entity_id=code.id,
        context={
            "reason": reason.value,
            "previous_code_id": str(previous.id) if previous else None,
            "revoked_sessions": revoked,
        },
        ip_hash=ip_hash,
    )
    logger.info(
        "access code rotated",
        extra={"reason": reason.value, "revoked_sessions": revoked, "code_id": str(code.id)},
    )
    return code


async def _mint_code(
    session: AsyncSession,
    *,
    policy: AccessPolicy,
    reason: RotationReason,
    actor: AdminUser | None = None,
    now: datetime | None = None,
) -> AccessCode:
    """Insert a fresh active code."""
    minted_at = now or utcnow()
    code = AccessCode(
        code=generate_access_code(),
        is_active=True,
        reason=reason,
        expires_at=_expiry_for(minted_at, policy),
        rotated_by_admin_id=actor.id if actor else None,
    )
    session.add(code)
    await session.flush()
    return code


# ---------------------------------------------------------------------------
# Visitor sessions
# ---------------------------------------------------------------------------
async def redeem(
    session: AsyncSession,
    code_value: str,
    *,
    user_agent: str | None = None,
    ip_hash: str | None = None,
) -> RedeemedAccess:
    """Exchange a scanned code for a visitor session.

    Raises:
        AccessDeniedError: if the code is unknown, no longer active, past its
            rotation date, or the property is at its session cap.
    """
    policy = await get_policy(session)
    now = utcnow()

    statement = select(AccessCode).where(AccessCode.code == code_value)
    code = (await session.execute(statement)).scalar_one_or_none()
    if code is None:
        raise AccessDeniedError(DenialReason.UNKNOWN_CODE)
    if not code.is_active:
        raise AccessDeniedError(DenialReason.EXPIRED_CODE)
    if code.expires_at is not None and code.expires_at <= now:
        # The worker has not caught up yet; rotate now and refuse this scan so
        # the visitor re-scans the poster that is actually on the wall.
        await rotate_code(session, reason=RotationReason.SCHEDULED)
        raise AccessDeniedError(DenialReason.EXPIRED_CODE)

    if policy.max_active_sessions > 0:
        live = await count_active_sessions(session, at=now)
        if live >= policy.max_active_sessions:
            raise AccessDeniedError(DenialReason.AT_CAPACITY)

    token = generate_opaque_token(32)
    guest = GuestSession(
        token_hash=hash_secret(token),
        access_code_id=code.id,
        expires_at=now + timedelta(minutes=policy.guest_session_minutes),
        last_seen_at=now,
        user_agent=(user_agent or "")[:255] or None,
        ip_hash=ip_hash,
    )
    session.add(guest)
    code.scan_count += 1
    await session.flush()

    logger.info("guest session issued", extra={"session_id": str(guest.id)})
    return RedeemedAccess(token=token, session_id=guest.id, expires_at=guest.expires_at)


async def resolve_session(session: AsyncSession, token: str) -> GuestSession | None:
    """Return the live visitor session for ``token``, or ``None``.

    Also refreshes ``last_seen_at``, throttled so that a page with several API
    calls does not turn every read into a write.
    """
    statement = select(GuestSession).where(GuestSession.token_hash == hash_secret(token))
    guest = (await session.execute(statement)).scalar_one_or_none()
    if guest is None:
        return None

    now = utcnow()
    if not guest.is_valid_at(now):
        return None
    if guest.last_seen_at is None or now - guest.last_seen_at > LAST_SEEN_THROTTLE:
        guest.last_seen_at = now
    return guest


async def revoke_session(
    session: AsyncSession,
    session_id: uuid.UUID,
    *,
    actor: AdminUser | None = None,
    ip_hash: str | None = None,
) -> bool:
    """End one visitor session. Returns whether a live session was ended."""
    now = utcnow()
    statement = (
        update(GuestSession)
        .where(GuestSession.id == session_id, GuestSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    if await _affected_rows(session, statement) == 0:
        return False
    await audit_service.record(
        session,
        action="access.session_revoked",
        actor=actor,
        entity_type="guest_session",
        entity_id=session_id,
        ip_hash=ip_hash,
    )
    return True


async def revoke_all_sessions(
    session: AsyncSession,
    *,
    actor: AdminUser | None = None,
    ip_hash: str | None = None,
) -> int:
    """End every live visitor session. Returns how many were ended."""
    now = utcnow()
    statement = (
        update(GuestSession)
        .where(GuestSession.revoked_at.is_(None), GuestSession.expires_at > now)
        .values(revoked_at=now)
    )
    count = await _affected_rows(session, statement)
    await audit_service.record(
        session,
        action="access.sessions_revoked_all",
        actor=actor,
        entity_type="guest_session",
        context={"count": count},
        ip_hash=ip_hash,
    )
    return count


async def revoke_sessions_for_code(
    session: AsyncSession, code_id: uuid.UUID, *, at: datetime | None = None
) -> int:
    """End every live session that was admitted by one code."""
    now = at or utcnow()
    statement = (
        update(GuestSession)
        .where(
            GuestSession.access_code_id == code_id,
            GuestSession.revoked_at.is_(None),
            GuestSession.expires_at > now,
        )
        .values(revoked_at=now)
    )
    return await _affected_rows(session, statement)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
async def count_active_sessions(session: AsyncSession, *, at: datetime | None = None) -> int:
    """Number of visitor sessions currently granting access."""
    now = at or utcnow()
    statement = (
        select(func.count())
        .select_from(GuestSession)
        .where(GuestSession.revoked_at.is_(None), GuestSession.expires_at > now)
    )
    return int((await session.execute(statement)).scalar_one())


async def list_sessions(
    session: AsyncSession,
    *,
    include_ended: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[GuestSession], int]:
    """Return a page of visitor sessions, newest first, plus the total count."""
    now = utcnow()
    filters = []
    if not include_ended:
        filters = [GuestSession.revoked_at.is_(None), GuestSession.expires_at > now]

    total = (
        await session.execute(select(func.count()).select_from(GuestSession).where(*filters))
    ).scalar_one()
    rows = (
        (
            await session.execute(
                select(GuestSession)
                .where(*filters)
                .order_by(GuestSession.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total


async def collect_stats(session: AsyncSession) -> dict[str, int | datetime | bool | None]:
    """Headline access numbers for the admin dashboard."""
    now = utcnow()
    policy = await get_policy(session)
    code = await get_active_code(session)

    recent = (
        await session.execute(
            select(func.count())
            .select_from(GuestSession)
            .where(GuestSession.created_at > now - timedelta(hours=24))
        )
    ).scalar_one()
    total_scans = (
        await session.execute(select(func.coalesce(func.sum(AccessCode.scan_count), 0)))
    ).scalar_one()

    return {
        "active_sessions": await count_active_sessions(session, at=now),
        "sessions_last_24h": recent,
        "scans_current_code": code.scan_count if code else 0,
        "total_scans": int(total_scans),
        "code_expires_at": code.expires_at if code else None,
        "auto_rotate": policy.auto_rotate,
    }


async def purge_expired_sessions(session: AsyncSession, *, older_than_days: int = 30) -> int:
    """Delete long-dead sessions so the table does not grow without bound."""
    cutoff = utcnow() - timedelta(days=older_than_days)
    return await _affected_rows(
        session, delete(GuestSession).where(GuestSession.expires_at < cutoff)
    )
