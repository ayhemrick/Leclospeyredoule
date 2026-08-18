"""Administrator accounts."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdminRole(enum.StrEnum):
    """What an administrator is allowed to do.

    ``OWNER`` may manage other administrators and access policy; ``EDITOR``
    may only edit site content.
    """

    OWNER = "owner"
    EDITOR = "editor"


class AdminUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A person who can sign in to the admin section."""

    __tablename__ = "admin_user"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AdminRole] = mapped_column(
        Enum(AdminRole, name="admin_role", native_enum=False, length=16, validate_strings=True),
        default=AdminRole.EDITOR,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Brute-force protection, reset on every successful login.
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Bumped on password change and on forced logout, which invalidates every
    # token minted earlier for this account.
    token_epoch: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), nullable=False
    )

    def __repr__(self) -> str:
        """Readable representation for logs and test failures."""
        return f"<AdminUser {self.email} role={self.role}>"
