"""Visitor-facing access endpoints: redeem a scanned code, check status."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import IpHashDep, OptionalGuestDep, SessionDep
from app.core.clock import utcnow
from app.core.cookies import GUEST_COOKIE, clear_cookie, set_session_cookie
from app.schemas.access import AccessStatus, RedeemRequest
from app.schemas.common import Message
from app.services import access_service
from app.services.access_service import AccessDeniedError, DenialReason

router = APIRouter(prefix="/access", tags=["access"])

_DENIAL_MESSAGES = {
    DenialReason.UNKNOWN_CODE: "This code is not recognised.",
    DenialReason.EXPIRED_CODE: "This code has been replaced. Please scan the poster again.",
    DenialReason.AT_CAPACITY: "The guest guide is at capacity. Please try again shortly.",
}


def _status_from(expires_at: datetime) -> AccessStatus:
    """Build an :class:`AccessStatus` from an expiry timestamp."""
    remaining = int((expires_at - utcnow()).total_seconds())
    return AccessStatus(granted=True, expires_at=expires_at, seconds_remaining=max(remaining, 0))


@router.post("/redeem", response_model=AccessStatus)
async def redeem(
    payload: RedeemRequest,
    request: Request,
    response: Response,
    session: SessionDep,
    ip_hash: IpHashDep,
) -> AccessStatus:
    """Exchange a scanned property code for a time-limited guest session."""
    try:
        granted = await access_service.redeem(
            session,
            payload.code,
            user_agent=request.headers.get("user-agent"),
            ip_hash=ip_hash,
        )
    except AccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_DENIAL_MESSAGES[exc.reason],
            headers={"X-Access-Denied-Reason": exc.reason.value},
        ) from exc

    max_age = max(int((granted.expires_at - utcnow()).total_seconds()), 0)
    set_session_cookie(response, GUEST_COOKIE, granted.token, max_age_seconds=max_age)
    return _status_from(granted.expires_at)


@router.get("/status", response_model=AccessStatus)
async def read_status(guest: OptionalGuestDep) -> AccessStatus:
    """Report whether this device currently holds guest access."""
    if guest is None:
        return AccessStatus(granted=False)
    return _status_from(guest.expires_at)


@router.post("/leave", response_model=Message)
async def leave(response: Response, session: SessionDep, guest: OptionalGuestDep) -> Message:
    """End this device's guest session, for a visitor who is checking out."""
    if guest is not None:
        await access_service.revoke_session(session, guest.id)
    clear_cookie(response, GUEST_COOKIE)
    return Message(detail="Guest access ended")
