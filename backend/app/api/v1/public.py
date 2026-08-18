"""Public site content, plus the guest guide gated behind a scanned code."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import GuestDep, SessionDep
from app.models.content import Attraction, AttractionCategory, GuideSection, Visibility
from app.schemas.content import AttractionOut, GuideSectionOut

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/attractions", response_model=list[AttractionOut])
async def list_attractions(
    session: SessionDep,
    category: Annotated[AttractionCategory | None, Query()] = None,
) -> list[AttractionOut]:
    """List published places to visit around the property."""
    statement = (
        select(Attraction)
        .where(Attraction.is_published.is_(True))
        .order_by(Attraction.position, Attraction.name_fr)
    )
    if category is not None:
        statement = statement.where(Attraction.category == category)
    rows = (await session.execute(statement)).scalars().all()
    return [AttractionOut.from_model(row) for row in rows]


@router.get("/guide", response_model=list[GuideSectionOut])
async def list_public_sections(session: SessionDep) -> list[GuideSectionOut]:
    """Guide sections anyone may read, used by the public flyer."""
    statement = (
        select(GuideSection)
        .where(
            GuideSection.is_published.is_(True),
            GuideSection.visibility == Visibility.PUBLIC,
        )
        .order_by(GuideSection.position, GuideSection.slug)
    )
    rows = (await session.execute(statement)).scalars().all()
    return [GuideSectionOut.from_model(row) for row in rows]


@router.get("/guide/guest", response_model=list[GuideSectionOut])
async def list_guest_sections(session: SessionDep, _guest: GuestDep) -> list[GuideSectionOut]:
    """The full guest guide.

    Requires a live session issued by scanning the property QR code; without
    one the endpoint answers 403 and the SPA sends the visitor to the scan page.
    """
    statement = (
        select(GuideSection)
        .where(GuideSection.is_published.is_(True))
        .order_by(GuideSection.position, GuideSection.slug)
    )
    rows = (await session.execute(statement)).scalars().all()
    return [GuideSectionOut.from_model(row) for row in rows]
