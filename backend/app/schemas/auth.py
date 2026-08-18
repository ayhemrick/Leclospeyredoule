"""Administrator authentication schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.models.admin_user import AdminRole
from app.schemas.common import ApiModel

#: Long enough to resist offline guessing, short enough to stay typable.
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


class LoginRequest(ApiModel):
    """Credentials posted by the admin login form."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class AdminOut(ApiModel):
    """An administrator as returned to the admin UI."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: AdminRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class AdminCreate(ApiModel):
    """Payload to invite a new administrator."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    role: AdminRole = AdminRole.EDITOR


class AdminUpdate(ApiModel):
    """Payload to change another administrator's role or status."""

    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: AdminRole | None = None
    is_active: bool | None = None


class PasswordChange(ApiModel):
    """Payload for an administrator rotating their own password."""

    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class LoginResponse(ApiModel):
    """Returned after a successful login.

    Tokens themselves travel in ``HttpOnly`` cookies and never appear here;
    the CSRF token is echoed so the SPA can mirror it back in a header.
    """

    admin: AdminOut
    csrf_token: str
    access_token_expires_at: datetime
