"""Administrator sign-in, token refresh and password management."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import AdminDep, CsrfDep, IpHashDep, SessionDep
from app.core.config import get_settings
from app.core.cookies import (
    ADMIN_ACCESS_COOKIE,
    ADMIN_REFRESH_COOKIE,
    CSRF_COOKIE,
    REFRESH_COOKIE_PATH,
    clear_cookie,
    set_session_cookie,
)
from app.core.security import (
    TokenError,
    create_token,
    decode_token,
    generate_opaque_token,
)
from app.models.admin_user import AdminUser
from app.schemas.auth import AdminOut, LoginRequest, LoginResponse, PasswordChange
from app.schemas.common import Message
from app.services import audit_service, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_session(response: Response, admin: AdminUser) -> LoginResponse:
    """Mint the cookie trio for ``admin`` and describe the session."""
    settings = get_settings()
    access_token, _, access_expires = create_token(admin.id, "access", epoch=admin.token_epoch)
    refresh_token, _, _ = create_token(admin.id, "refresh", epoch=admin.token_epoch)
    csrf_token = generate_opaque_token(24)

    set_session_cookie(
        response,
        ADMIN_ACCESS_COOKIE,
        access_token,
        max_age_seconds=settings.access_token_ttl_minutes * 60,
    )
    set_session_cookie(
        response,
        ADMIN_REFRESH_COOKIE,
        refresh_token,
        max_age_seconds=settings.refresh_token_ttl_days * 86_400,
        path=REFRESH_COOKIE_PATH,
    )
    set_session_cookie(
        response,
        CSRF_COOKIE,
        csrf_token,
        max_age_seconds=settings.refresh_token_ttl_days * 86_400,
        http_only=False,
    )
    return LoginResponse(
        admin=AdminOut.model_validate(admin),
        csrf_token=csrf_token,
        access_token_expires_at=access_expires,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: SessionDep,
    ip_hash: IpHashDep,
) -> LoginResponse:
    """Exchange e-mail and password for a cookie-based admin session."""
    credentials = auth_service.Credentials(email=payload.email, password=payload.password)
    try:
        admin = await auth_service.authenticate(session, credentials, ip_hash=ip_hash)
    except auth_service.AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except auth_service.AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid e-mail or password",
        ) from exc
    return _issue_session(response, admin)


@router.post("/refresh", response_model=LoginResponse)
async def refresh(request: Request, response: Response, session: SessionDep) -> LoginResponse:
    """Swap a valid refresh cookie for a new access and refresh pair."""
    token = request.cookies.get(ADMIN_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    try:
        decoded = decode_token(token, "refresh")
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required") from exc

    admin = await auth_service.get_by_id(session, decoded.subject)
    if admin is None or not admin.is_active or admin.token_epoch != decoded.epoch:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return _issue_session(response, admin)


@router.get("/me", response_model=AdminOut)
async def me(admin: AdminDep) -> AdminUser:
    """Return the signed-in administrator."""
    return admin


@router.post("/logout", response_model=Message)
async def logout(response: Response, _csrf: CsrfDep) -> Message:
    """Clear the session cookies on this device."""
    clear_cookie(response, ADMIN_ACCESS_COOKIE)
    clear_cookie(response, ADMIN_REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
    clear_cookie(response, CSRF_COOKIE)
    return Message(detail="Signed out")


@router.post("/logout-everywhere", response_model=Message)
async def logout_everywhere(
    response: Response,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> Message:
    """Invalidate every token issued to this account, on all devices."""
    admin.token_epoch = str(uuid.uuid4())
    await audit_service.record(
        session,
        action="auth.logout_everywhere",
        actor=admin,
        entity_type="admin_user",
        entity_id=admin.id,
        ip_hash=ip_hash,
    )
    clear_cookie(response, ADMIN_ACCESS_COOKIE)
    clear_cookie(response, ADMIN_REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
    clear_cookie(response, CSRF_COOKIE)
    return Message(detail="Signed out on every device")


@router.post("/password", response_model=Message)
async def change_password(
    payload: PasswordChange,
    response: Response,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> Message:
    """Change the signed-in administrator's password and re-issue the session."""
    try:
        await auth_service.change_password(
            session,
            admin,
            current_password=payload.current_password,
            new_password=payload.new_password,
            ip_hash=ip_hash,
        )
    except auth_service.AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        ) from exc
    _issue_session(response, admin)
    return Message(detail="Password updated")
