"""Administrator authentication.

Failed logins are counted per account and lock it for a cool-off window, which
blunts online password guessing without needing shared state between workers.
The response is deliberately identical for "no such account", "wrong password"
and "locked", so the endpoint cannot be used to enumerate administrators.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.models.admin_user import AdminRole, AdminUser
from app.services import audit_service

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Raised when credentials are rejected."""


class AccountLockedError(AuthenticationError):
    """Raised when too many failed attempts have locked the account."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("account temporarily locked")
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True, slots=True)
class Credentials:
    """A login attempt."""

    email: str
    password: str


def normalise_email(email: str) -> str:
    """Return the storage form of an e-mail address."""
    return email.strip().lower()


async def get_by_email(session: AsyncSession, email: str) -> AdminUser | None:
    """Look an administrator up by e-mail, case-insensitively."""
    statement = select(AdminUser).where(AdminUser.email == normalise_email(email))
    return (await session.execute(statement)).scalar_one_or_none()


async def get_by_id(session: AsyncSession, admin_id: uuid.UUID) -> AdminUser | None:
    """Look an administrator up by id."""
    return await session.get(AdminUser, admin_id)


async def count_admins(session: AsyncSession) -> int:
    """How many administrator accounts exist."""
    return (await session.execute(select(func.count()).select_from(AdminUser))).scalar_one()


async def authenticate(
    session: AsyncSession,
    credentials: Credentials,
    *,
    ip_hash: str | None = None,
) -> AdminUser:
    """Verify credentials and return the administrator.

    Raises:
        AccountLockedError: while the account is in its cool-off window.
        AuthenticationError: for unknown accounts, wrong passwords and
            deactivated accounts alike.
    """
    now = utcnow()
    admin = await get_by_email(session, credentials.email)

    if admin is None:
        # Spend roughly the same time as a real verification would, so response
        # timing does not reveal whether the address exists.
        verify_password(credentials.password, _DUMMY_HASH)
        raise AuthenticationError("invalid credentials")

    if admin.locked_until is not None and admin.locked_until > now:
        raise AccountLockedError(int((admin.locked_until - now).total_seconds()))

    if not verify_password(credentials.password, admin.password_hash):
        await _register_failure(session, admin, now=now, ip_hash=ip_hash)
        raise AuthenticationError("invalid credentials")

    if not admin.is_active:
        raise AuthenticationError("invalid credentials")

    if password_needs_rehash(admin.password_hash):
        admin.password_hash = hash_password(credentials.password)

    admin.failed_login_count = 0
    admin.locked_until = None
    admin.last_login_at = now
    await audit_service.record(
        session,
        action="auth.login_succeeded",
        actor=admin,
        entity_type="admin_user",
        entity_id=admin.id,
        ip_hash=ip_hash,
    )
    return admin


async def _register_failure(
    session: AsyncSession,
    admin: AdminUser,
    *,
    now: datetime,
    ip_hash: str | None,
) -> None:
    """Count a failed attempt and lock the account once the limit is reached."""
    settings = get_settings()
    admin.failed_login_count += 1
    locked = admin.failed_login_count >= settings.login_max_attempts
    if locked:
        admin.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
        admin.failed_login_count = 0

    await audit_service.record(
        session,
        action="auth.login_failed",
        actor=admin,
        entity_type="admin_user",
        entity_id=admin.id,
        context={"locked": locked},
        ip_hash=ip_hash,
    )
    logger.warning("failed admin login", extra={"admin_id": str(admin.id), "locked": locked})


async def create_admin(
    session: AsyncSession,
    *,
    email: str,
    full_name: str,
    password: str,
    role: AdminRole,
    created_by: AdminUser | None = None,
    ip_hash: str | None = None,
) -> AdminUser:
    """Create an administrator account."""
    admin = AdminUser(
        email=normalise_email(email),
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
    )
    session.add(admin)
    await session.flush()
    await audit_service.record(
        session,
        action="admin.created",
        actor=created_by,
        entity_type="admin_user",
        entity_id=admin.id,
        context={"email": admin.email, "role": role.value},
        ip_hash=ip_hash,
    )
    return admin


async def change_password(
    session: AsyncSession,
    admin: AdminUser,
    *,
    current_password: str,
    new_password: str,
    ip_hash: str | None = None,
) -> None:
    """Rotate an administrator's own password.

    Raises:
        AuthenticationError: if the current password does not match.
    """
    if not verify_password(current_password, admin.password_hash):
        raise AuthenticationError("invalid credentials")
    admin.password_hash = hash_password(new_password)
    # Invalidate every token minted before this change.
    admin.token_epoch = str(uuid.uuid4())
    await audit_service.record(
        session,
        action="admin.password_changed",
        actor=admin,
        entity_type="admin_user",
        entity_id=admin.id,
        ip_hash=ip_hash,
    )


#: Argon2 hash of a random string, used to equalise timing for unknown accounts.
_DUMMY_HASH = hash_password("unused-placeholder-for-constant-time-login")
