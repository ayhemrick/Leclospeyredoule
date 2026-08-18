"""Admin CRUD for guide sections and nearby attractions."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminDep, CsrfDep, IpHashDep, SessionDep
from app.models.content import Attraction, GuideSection
from app.schemas.common import Message
from app.schemas.content import (
    AdminAttractionOut,
    AdminGuideSectionOut,
    AttractionPatch,
    AttractionWrite,
    GuideSectionPatch,
    GuideSectionWrite,
)
from app.services import audit_service

router = APIRouter(prefix="/admin/content", tags=["admin:content"])


async def _get_or_404[ModelT: (GuideSection, Attraction)](
    session: AsyncSession, model: type[ModelT], entity_id: uuid.UUID
) -> ModelT:
    """Fetch a row by id or raise 404."""
    row = await session.get(model, entity_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return row


def _conflict(exc: IntegrityError) -> HTTPException:
    """Translate a unique-violation into a readable 409."""
    return HTTPException(status.HTTP_409_CONFLICT, "That slug is already used")


# ---------------------------------------------------------------------------
# Guide sections
# ---------------------------------------------------------------------------
@router.get("/guide-sections", response_model=list[AdminGuideSectionOut])
async def list_sections(
    session: SessionDep,
    _admin: AdminDep,
    include_unpublished: Annotated[bool, Query()] = True,
) -> list[AdminGuideSectionOut]:
    """Every guide section, published or not."""
    statement = select(GuideSection).order_by(GuideSection.position, GuideSection.slug)
    if not include_unpublished:
        statement = statement.where(GuideSection.is_published.is_(True))
    rows = (await session.execute(statement)).scalars().all()
    return [AdminGuideSectionOut.from_model(row) for row in rows]


@router.post(
    "/guide-sections",
    response_model=AdminGuideSectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_section(
    payload: GuideSectionWrite,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AdminGuideSectionOut:
    """Add a guide section."""
    section = GuideSection(**payload.model_dump(), updated_by_admin_id=admin.id)
    session.add(section)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise _conflict(exc) from exc
    await audit_service.record(
        session,
        action="content.section_created",
        actor=admin,
        entity_type="guide_section",
        entity_id=section.id,
        context={"slug": section.slug},
        ip_hash=ip_hash,
    )
    return AdminGuideSectionOut.from_model(section)


@router.patch("/guide-sections/{section_id}", response_model=AdminGuideSectionOut)
async def update_section(
    section_id: uuid.UUID,
    payload: GuideSectionPatch,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AdminGuideSectionOut:
    """Edit a guide section."""
    section = await _get_or_404(session, GuideSection, section_id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(section, field, value)
    section.updated_by_admin_id = admin.id
    await session.flush()
    await audit_service.record(
        session,
        action="content.section_updated",
        actor=admin,
        entity_type="guide_section",
        entity_id=section.id,
        context={"fields": sorted(changes)},
        ip_hash=ip_hash,
    )
    return AdminGuideSectionOut.from_model(section)


@router.delete("/guide-sections/{section_id}", response_model=Message)
async def delete_section(
    section_id: uuid.UUID,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> Message:
    """Remove a guide section."""
    section = await _get_or_404(session, GuideSection, section_id)
    slug = section.slug
    await session.delete(section)
    await audit_service.record(
        session,
        action="content.section_deleted",
        actor=admin,
        entity_type="guide_section",
        entity_id=section_id,
        context={"slug": slug},
        ip_hash=ip_hash,
    )
    return Message(detail="Section deleted")


# ---------------------------------------------------------------------------
# Attractions
# ---------------------------------------------------------------------------
@router.get("/attractions", response_model=list[AdminAttractionOut])
async def list_attractions(session: SessionDep, _admin: AdminDep) -> list[AdminAttractionOut]:
    """Every attraction, published or not."""
    statement = select(Attraction).order_by(Attraction.position, Attraction.name_fr)
    rows = (await session.execute(statement)).scalars().all()
    return [AdminAttractionOut.from_model(row) for row in rows]


@router.post(
    "/attractions",
    response_model=AdminAttractionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_attraction(
    payload: AttractionWrite,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AdminAttractionOut:
    """Add a place to visit."""
    data = payload.model_dump()
    data["website_url"] = str(data["website_url"]) if data["website_url"] else None
    attraction = Attraction(**data, updated_by_admin_id=admin.id)
    session.add(attraction)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise _conflict(exc) from exc
    await audit_service.record(
        session,
        action="content.attraction_created",
        actor=admin,
        entity_type="attraction",
        entity_id=attraction.id,
        context={"slug": attraction.slug},
        ip_hash=ip_hash,
    )
    return AdminAttractionOut.from_model(attraction)


@router.patch("/attractions/{attraction_id}", response_model=AdminAttractionOut)
async def update_attraction(
    attraction_id: uuid.UUID,
    payload: AttractionPatch,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> AdminAttractionOut:
    """Edit a place to visit."""
    attraction = await _get_or_404(session, Attraction, attraction_id)
    changes = payload.model_dump(exclude_unset=True)
    if "website_url" in changes and changes["website_url"] is not None:
        changes["website_url"] = str(changes["website_url"])
    for field, value in changes.items():
        setattr(attraction, field, value)
    attraction.updated_by_admin_id = admin.id
    await session.flush()
    await audit_service.record(
        session,
        action="content.attraction_updated",
        actor=admin,
        entity_type="attraction",
        entity_id=attraction.id,
        context={"fields": sorted(changes)},
        ip_hash=ip_hash,
    )
    return AdminAttractionOut.from_model(attraction)


@router.delete("/attractions/{attraction_id}", response_model=Message)
async def delete_attraction(
    attraction_id: uuid.UUID,
    session: SessionDep,
    admin: AdminDep,
    ip_hash: IpHashDep,
    _csrf: CsrfDep,
) -> Message:
    """Remove a place to visit."""
    attraction = await _get_or_404(session, Attraction, attraction_id)
    slug = attraction.slug
    await session.delete(attraction)
    await audit_service.record(
        session,
        action="content.attraction_deleted",
        actor=admin,
        entity_type="attraction",
        entity_id=attraction_id,
        context={"slug": slug},
        ip_hash=ip_hash,
    )
    return Message(detail="Attraction deleted")
