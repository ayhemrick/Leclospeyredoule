"""The visitor access-control domain: policy, rotating code, guest sessions.

Only one :class:`AccessCode` is active at a time. It is the value printed as a
QR poster at the property. Scanning it creates a :class:`GuestSession`, which
whitelists that device for the window configured in :class:`AccessPolicy`.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# The policy table holds exactly one row, pinned to this id.
POLICY_SINGLETON_ID = 1


class RotationReason(enum.StrEnum):
    """Why a code was issued."""

    INITIAL = "initial"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class AccessPolicy(TimestampMixin, Base):
    """Owner-configurable rules for the rotating property code.

    Stored as a single row so the admin UI can edit rotation cadence and
    visitor session length without a redeploy.
    """

    __tablename__ = "access_policy"
    __table_args__ = (
        CheckConstraint("id = 1", name="singleton"),
        CheckConstraint("rotation_interval_minutes BETWEEN 5 AND 525600", name="rotation_range"),
        CheckConstraint("guest_session_minutes BETWEEN 5 AND 43200", name="session_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=POLICY_SINGLETON_ID)

    #: When true a background worker replaces the active code on the cadence below.
    auto_rotate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    #: How long a code stays valid before it is rotated (default: one week).
    rotation_interval_minutes: Mapped[int] = mapped_column(Integer, default=10080, nullable=False)
    #: How long one scan whitelists a device (default: 24 hours).
    guest_session_minutes: Mapped[int] = mapped_column(Integer, default=1440, nullable=False)
    #: Whether rotating the code also kicks out visitors admitted by the old one.
    revoke_sessions_on_rotation: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    #: Safety valve: refuse new scans once this many sessions are live (0 = unlimited).
    max_active_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    updated_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("admin_user.id", ondelete="SET NULL")
    )


class AccessCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One generation of the printed property code."""

    __tablename__ = "access_code"
    __table_args__ = (UniqueConstraint("code", name="uq_access_code_code"),)

    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    #: Set from the rotation interval in force when the code was minted.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[RotationReason] = mapped_column(
        Enum(
            RotationReason,
            name="rotation_reason",
            native_enum=False,
            length=16,
            validate_strings=True,
        ),
        default=RotationReason.INITIAL,
        nullable=False,
    )
    scan_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rotated_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("admin_user.id", ondelete="SET NULL")
    )

    sessions: Mapped[list[GuestSession]] = relationship(back_populates="access_code")

    def __repr__(self) -> str:
        """Readable representation that never leaks the full code."""
        return f"<AccessCode {self.code[:4]}... active={self.is_active}>"


class GuestSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A device whitelisted by scanning the property code.

    The cookie value itself is never stored: only its HMAC, so the table is
    useless to an attacker who dumps the database.
    """

    __tablename__ = "guest_session"

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    access_code_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("access_code.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    #: Truncated keyed hash, never the raw address.
    ip_hash: Mapped[str | None] = mapped_column(String(32))

    access_code: Mapped[AccessCode] = relationship(back_populates="sessions")

    def is_valid_at(self, moment: datetime) -> bool:
        """Whether this session still grants access at ``moment``."""
        return self.revoked_at is None and self.expires_at > moment
