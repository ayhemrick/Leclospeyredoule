"""Editable site content: guide sections and things to visit nearby.

Every user-facing string is stored twice, once per locale, so the admin can
keep the French and English versions of the site in step.
"""

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GuideCategory(enum.StrEnum):
    """Where a guide section appears in the guest guide."""

    ARRIVAL = "arrival"
    HOUSE = "house"
    PRACTICAL = "practical"
    RULES = "rules"
    LOCAL_TIPS = "local_tips"


class Visibility(enum.StrEnum):
    """Who may read a section."""

    #: Shown on the public flyer to anyone.
    PUBLIC = "public"
    #: Requires a valid QR-issued guest session.
    GUEST = "guest"


class AttractionCategory(enum.StrEnum):
    """Classification used by the filter chips on the public site."""

    HERITAGE = "heritage"
    WINE = "wine"
    NATURE = "nature"
    GASTRONOMY = "gastronomy"
    FAMILY = "family"


class GuideSection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A titled block of Markdown shown in the house guide."""

    __tablename__ = "guide_section"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    category: Mapped[GuideCategory] = mapped_column(
        Enum(
            GuideCategory,
            name="guide_category",
            native_enum=False,
            length=16,
            validate_strings=True,
        ),
        nullable=False,
    )
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, name="visibility", native_enum=False, length=16, validate_strings=True),
        default=Visibility.GUEST,
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(40))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    title_fr: Mapped[str] = mapped_column(String(160), nullable=False)
    title_en: Mapped[str] = mapped_column(String(160), nullable=False)
    body_fr: Mapped[str] = mapped_column(Text, nullable=False)
    body_en: Mapped[str] = mapped_column(Text, nullable=False)

    updated_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("admin_user.id", ondelete="SET NULL")
    )


class Attraction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Something to see or do around Blaye, listed on the public flyer."""

    __tablename__ = "attraction"

    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    category: Mapped[AttractionCategory] = mapped_column(
        Enum(
            AttractionCategory,
            name="attraction_category",
            native_enum=False,
            length=16,
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    name_fr: Mapped[str] = mapped_column(String(160), nullable=False)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    summary_fr: Mapped[str] = mapped_column(String(400), nullable=False)
    summary_en: Mapped[str] = mapped_column(String(400), nullable=False)
    description_fr: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description_en: Mapped[str] = mapped_column(Text, default="", nullable=False)

    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    travel_time_min: Mapped[int | None] = mapped_column(Integer)
    website_url: Mapped[str | None] = mapped_column(String(400))
    image_path: Mapped[str | None] = mapped_column(String(200))
    image_credit: Mapped[str | None] = mapped_column(String(300))

    updated_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("admin_user.id", ondelete="SET NULL")
    )
