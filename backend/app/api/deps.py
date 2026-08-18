"""Reusable FastAPI dependencies: identity, CSRF and client metadata."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import ADMIN_ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER, GUEST_COOKIE
from app.core.security import TokenError, constant_time_equals, decode_token, pseudonymise_ip
from app.db.session import get_session
from app.models.access import GuestSession
from app.models.admin_user import AdminRole, AdminUser
from app.services import access_service, auth_service

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required",
)
_FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Insufficient permissions",
)
#: Deliberately distinct from 401 so the SPA can send visitors to the scan page
#: instead of the admin login form.
_NO_GUEST_ACCESS = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Scan the property QR code to unlock the guest guide",
)


def client_ip(request: Request) -> str | None:
    """Best-effort client address.

    ``X-Forwarded-For`` is trusted only because the app is expected to sit
    behind a reverse proxy that sets it; the value is never stored raw.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def client_ip_hash(request: Request) -> str | None:
    """Pseudonymised client address, safe to persist."""
    return pseudonymise_ip(client_ip(request))


IpHashDep = Annotated[str | None, Depends(client_ip_hash)]


async def current_admin(request: Request, session: SessionDep) -> AdminUser:
    """Resolve the signed-in administrator from the access cookie.

    Raises:
        HTTPException: 401 if the cookie is missing, invalid, expired, minted
            before a password change, or belongs to a deactivated account.
    """
    token = request.cookies.get(ADMIN_ACCESS_COOKIE)
    if not token:
        raise _UNAUTHENTICATED
    try:
        decoded = decode_token(token, "access")
    except TokenError as exc:
        raise _UNAUTHENTICATED from exc

    admin = await auth_service.get_by_id(session, decoded.subject)
    if admin is None or not admin.is_active or admin.token_epoch != decoded.epoch:
        raise _UNAUTHENTICATED
    return admin


AdminDep = Annotated[AdminUser, Depends(current_admin)]


async def current_owner(admin: AdminDep) -> AdminUser:
    """Require the ``owner`` role, which gates policy and account management."""
    if admin.role is not AdminRole.OWNER:
        raise _FORBIDDEN
    return admin


OwnerDep = Annotated[AdminUser, Depends(current_owner)]


def verify_csrf(request: Request) -> None:
    """Enforce the double-submit CSRF token on state-changing requests.

    Safe methods are exempt; everything else must echo the ``cp_csrf`` cookie
    in the ``X-CSRF-Token`` header, which a cross-site page cannot read.
    """
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header or not constant_time_equals(cookie, header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid CSRF token",
        )


CsrfDep = Annotated[None, Depends(verify_csrf)]


async def optional_guest_session(request: Request, session: SessionDep) -> GuestSession | None:
    """Return the visitor's live session, or ``None`` if they have not scanned."""
    token = request.cookies.get(GUEST_COOKIE)
    if not token:
        return None
    return await access_service.resolve_session(session, token)


OptionalGuestDep = Annotated[GuestSession | None, Depends(optional_guest_session)]


async def require_guest_session(guest: OptionalGuestDep) -> GuestSession:
    """Gate an endpoint behind a valid QR-issued visitor session.

    Raises:
        HTTPException: 403 when the device has not scanned, or its window has
            elapsed or been revoked.
    """
    if guest is None:
        raise _NO_GUEST_ACCESS
    return guest


GuestDep = Annotated[GuestSession, Depends(require_guest_session)]
