"""Schemas for guide sections and nearby attractions.

Read models expose one ``LocalizedString`` per translatable field so the site
can switch language client-side; write models take the flat ``*_fr`` /
``*_en`` columns, which is what an editor form posts.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Self

from pydantic import Field, HttpUrl, field_validator, model_validator

from app.models.content import AttractionCategory, GuideCategory, Visibility
from app.schemas.common import ApiModel, LocalizedString

if TYPE_CHECKING:
    from app.models.content import Attraction, GuideSection

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _validate_slug(value: str) -> str:
    """Reject slugs that would not be URL-safe."""
    if not SLUG_PATTERN.match(value):
        raise ValueError("slug must be lowercase words separated by single hyphens")
    return value


# ---------------------------------------------------------------------------
# Guide sections
# ---------------------------------------------------------------------------
class GuideSectionOut(ApiModel):
    """A guide section rendered by the site, in both locales."""

    id: uuid.UUID
    slug: str
    category: GuideCategory
    visibility: Visibility
    position: int
    icon: str | None
    title: LocalizedString
    body: LocalizedString
    updated_at: datetime

    @classmethod
    def from_model(cls, section: GuideSection) -> Self:
        """Build the public representation of a stored section."""
        return cls(
            id=section.id,
            slug=section.slug,
            category=section.category,
            visibility=section.visibility,
            position=section.position,
            icon=section.icon,
            title=LocalizedString.of(section.title_fr, section.title_en),
            body=LocalizedString.of(section.body_fr, section.body_en),
            updated_at=section.updated_at,
        )


class AdminGuideSectionOut(GuideSectionOut):
    """Guide section including the raw editable fields."""

    is_published: bool
    title_fr: str
    title_en: str
    body_fr: str
    body_en: str

    @classmethod
    def from_model(cls, section: GuideSection) -> Self:
        """Build the admin representation of a stored section."""
        return cls(
            id=section.id,
            slug=section.slug,
            category=section.category,
            visibility=section.visibility,
            position=section.position,
            icon=section.icon,
            title=LocalizedString.of(section.title_fr, section.title_en),
            body=LocalizedString.of(section.body_fr, section.body_en),
            updated_at=section.updated_at,
            is_published=section.is_published,
            title_fr=section.title_fr,
            title_en=section.title_en,
            body_fr=section.body_fr,
            body_en=section.body_en,
        )


class GuideSectionWrite(ApiModel):
    """Create a guide section from the admin editor."""

    slug: str = Field(min_length=2, max_length=80)
    category: GuideCategory
    visibility: Visibility = Visibility.GUEST
    position: int = Field(default=0, ge=0, le=999)
    icon: str | None = Field(default=None, max_length=40)
    is_published: bool = True
    title_fr: str = Field(min_length=1, max_length=160)
    title_en: str = Field(min_length=1, max_length=160)
    body_fr: str = Field(min_length=1)
    body_en: str = Field(min_length=1)

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, value: str) -> str:
        return _validate_slug(value)


class GuideSectionPatch(ApiModel):
    """Partial update of a guide section."""

    category: GuideCategory | None = None
    visibility: Visibility | None = None
    position: int | None = Field(default=None, ge=0, le=999)
    icon: str | None = Field(default=None, max_length=40)
    is_published: bool | None = None
    title_fr: str | None = Field(default=None, min_length=1, max_length=160)
    title_en: str | None = Field(default=None, min_length=1, max_length=160)
    body_fr: str | None = Field(default=None, min_length=1)
    body_en: str | None = Field(default=None, min_length=1)


# ---------------------------------------------------------------------------
# Attractions
# ---------------------------------------------------------------------------
class AttractionOut(ApiModel):
    """A place to visit, as consumed by the public site."""

    id: uuid.UUID
    slug: str
    category: AttractionCategory
    position: int
    name: LocalizedString
    summary: LocalizedString
    description: LocalizedString
    distance_km: Decimal | None
    travel_time_min: int | None
    website_url: str | None
    image_path: str | None
    image_credit: str | None

    @classmethod
    def from_model(cls, attraction: Attraction) -> Self:
        """Build the public representation of a stored attraction."""
        return cls(
            id=attraction.id,
            slug=attraction.slug,
            category=attraction.category,
            position=attraction.position,
            name=LocalizedString.of(attraction.name_fr, attraction.name_en),
            summary=LocalizedString.of(attraction.summary_fr, attraction.summary_en),
            description=LocalizedString.of(attraction.description_fr, attraction.description_en),
            distance_km=attraction.distance_km,
            travel_time_min=attraction.travel_time_min,
            website_url=attraction.website_url,
            image_path=attraction.image_path,
            image_credit=attraction.image_credit,
        )


class AdminAttractionOut(AttractionOut):
    """Attraction including the raw editable fields."""

    is_published: bool
    name_fr: str
    name_en: str
    summary_fr: str
    summary_en: str
    description_fr: str
    description_en: str

    @classmethod
    def from_model(cls, attraction: Attraction) -> Self:
        """Build the admin representation of a stored attraction."""
        return cls(
            id=attraction.id,
            slug=attraction.slug,
            category=attraction.category,
            position=attraction.position,
            name=LocalizedString.of(attraction.name_fr, attraction.name_en),
            summary=LocalizedString.of(attraction.summary_fr, attraction.summary_en),
            description=LocalizedString.of(attraction.description_fr, attraction.description_en),
            distance_km=attraction.distance_km,
            travel_time_min=attraction.travel_time_min,
            website_url=attraction.website_url,
            image_path=attraction.image_path,
            image_credit=attraction.image_credit,
            is_published=attraction.is_published,
            name_fr=attraction.name_fr,
            name_en=attraction.name_en,
            summary_fr=attraction.summary_fr,
            summary_en=attraction.summary_en,
            description_fr=attraction.description_fr,
            description_en=attraction.description_en,
        )


class AttractionWrite(ApiModel):
    """Create an attraction from the admin editor."""

    slug: str = Field(min_length=2, max_length=80)
    category: AttractionCategory
    position: int = Field(default=0, ge=0, le=999)
    is_published: bool = True
    name_fr: str = Field(min_length=1, max_length=160)
    name_en: str = Field(min_length=1, max_length=160)
    summary_fr: str = Field(min_length=1, max_length=400)
    summary_en: str = Field(min_length=1, max_length=400)
    description_fr: str = ""
    description_en: str = ""
    distance_km: Decimal | None = Field(default=None, ge=0, le=9999)
    travel_time_min: int | None = Field(default=None, ge=0, le=1440)
    website_url: HttpUrl | None = None
    image_path: str | None = Field(default=None, max_length=200)
    image_credit: str | None = Field(default=None, max_length=300)

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, value: str) -> str:
        return _validate_slug(value)

    @model_validator(mode="after")
    def _credit_required_with_image(self) -> Self:
        """Refuse an image without a credit line, since every photo is licensed."""
        if self.image_path and not self.image_credit:
            raise ValueError("image_credit is required when image_path is set")
        return self


class AttractionPatch(ApiModel):
    """Partial update of an attraction."""

    category: AttractionCategory | None = None
    position: int | None = Field(default=None, ge=0, le=999)
    is_published: bool | None = None
    name_fr: str | None = Field(default=None, min_length=1, max_length=160)
    name_en: str | None = Field(default=None, min_length=1, max_length=160)
    summary_fr: str | None = Field(default=None, min_length=1, max_length=400)
    summary_en: str | None = Field(default=None, min_length=1, max_length=400)
    description_fr: str | None = None
    description_en: str | None = None
    distance_km: Decimal | None = Field(default=None, ge=0, le=9999)
    travel_time_min: int | None = Field(default=None, ge=0, le=1440)
    website_url: HttpUrl | None = None
    image_path: str | None = Field(default=None, max_length=200)
    image_credit: str | None = Field(default=None, max_length=300)
