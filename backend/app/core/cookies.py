"""Cookie names and the rules for setting them.

All session material is ``HttpOnly`` and ``SameSite=Lax``: the SPA is served
from the same site, and Lax still allows the QR deep link to work, since a
camera app opening the scan URL is a top-level navigation.
"""

from __future__ import annotations

from typing import Final

from fastapi import Response

from app.core.config import get_settings

ADMIN_ACCESS_COOKIE: Final = "cp_admin"
ADMIN_REFRESH_COOKIE: Final = "cp_refresh"
GUEST_COOKIE: Final = "cp_guest"
#: Readable by JavaScript on purpose: the SPA mirrors it into a request header
#: so the server can check that a mutating call came from its own page.
CSRF_COOKIE: Final = "cp_csrf"
CSRF_HEADER: Final = "X-CSRF-Token"

#: The refresh cookie is only ever sent to the token endpoints.
REFRESH_COOKIE_PATH: Final = "/api/v1/auth"


def set_session_cookie(
    response: Response,
    name: str,
    value: str,
    *,
    max_age_seconds: int,
    http_only: bool = True,
    path: str = "/",
) -> None:
    """Set one cookie using the environment's security settings."""
    settings = get_settings()
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age_seconds,
        httponly=http_only,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path=path,
    )


def clear_cookie(response: Response, name: str, *, path: str = "/") -> None:
    """Remove a cookie, matching the attributes it was set with."""
    settings = get_settings()
    response.delete_cookie(
        key=name,
        domain=settings.cookie_domain,
        path=path,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
