"""Schemas for the rotating QR access system."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.models.access import RotationReason
from app.schemas.common import ApiModel

CODE_MIN_LENGTH = 8
CODE_MAX_LENGTH = 64


class RedeemRequest(ApiModel):
    """The code read from the QR poster, posted by the scan landing page."""

    code: str = Field(min_length=CODE_MIN_LENGTH, max_length=CODE_MAX_LENGTH)


class AccessStatus(ApiModel):
    """Whether the calling device currently holds guest access."""

    granted: bool
    expires_at: datetime | None = None
    #: Seconds left, so the UI can show a countdown without clock skew issues.
    seconds_remaining: int | None = None


class AccessPolicyOut(ApiModel):
    """Current access rules, as shown in the admin settings form."""

    auto_rotate: bool
    rotation_interval_minutes: int
    guest_session_minutes: int
    revoke_sessions_on_rotation: bool
    max_active_sessions: int
    updated_at: datetime


class AccessPolicyUpdate(ApiModel):
    """Partial update of the access rules.

    Bounds mirror the database check constraints: between five minutes and one
    year of rotation cadence, five minutes and thirty days of guest session.
    """

    auto_rotate: bool | None = None
    rotation_interval_minutes: int | None = Field(default=None, ge=5, le=525_600)
    guest_session_minutes: int | None = Field(default=None, ge=5, le=43_200)
    revoke_sessions_on_rotation: bool | None = None
    max_active_sessions: int | None = Field(default=None, ge=0, le=10_000)


class AccessCodeOut(ApiModel):
    """The active code and everything the admin needs to print it."""

    id: uuid.UUID
    code: str
    is_active: bool
    reason: RotationReason
    scan_count: int
    created_at: datetime
    expires_at: datetime | None
    retired_at: datetime | None
    #: Deep link encoded in the QR image.
    poster_url: str
    #: Inline SVG of the QR code, ready to render or print.
    qr_svg: str


class GuestSessionOut(ApiModel):
    """A live visitor session in the admin sessions table."""

    id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None
    user_agent: str | None
    access_code_id: uuid.UUID


class AccessStats(ApiModel):
    """Headline numbers for the admin dashboard."""

    active_sessions: int
    sessions_last_24h: int
    scans_current_code: int
    total_scans: int
    code_expires_at: datetime | None
    auto_rotate: bool
