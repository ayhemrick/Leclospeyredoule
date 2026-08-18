"""Idempotent seeding of the first administrator and the demo content.

Runs on startup. Existing rows are left untouched, so an owner who edits the
guide in the admin section does not lose that work on the next deploy.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.admin_user import AdminRole
from app.models.content import Attraction, GuideSection
from app.services import access_service, auth_service
from app.services.seed_data import ATTRACTIONS, GUIDE_SECTIONS

logger = get_logger(__name__)


async def seed_admin(session: AsyncSession) -> None:
    """Create the configured owner account if no administrator exists yet."""
    if await auth_service.count_admins(session) > 0:
        return
    settings = get_settings()
    admin = await auth_service.create_admin(
        session,
        email=settings.admin_email,
        full_name=settings.admin_full_name,
        password=settings.admin_password,
        role=AdminRole.OWNER,
    )
    logger.info("seeded first administrator", extra={"email": admin.email})


async def seed_content(session: AsyncSession) -> None:
    """Insert demo attractions and guide sections that are not present yet."""
    existing_attractions = set((await session.execute(select(Attraction.slug))).scalars().all())
    added_attractions = 0
    for row in ATTRACTIONS:
        if row["slug"] in existing_attractions:
            continue
        session.add(Attraction(**row))
        added_attractions += 1

    existing_sections = set((await session.execute(select(GuideSection.slug))).scalars().all())
    added_sections = 0
    for section in GUIDE_SECTIONS:
        if section["slug"] in existing_sections:
            continue
        session.add(GuideSection(**section))
        added_sections += 1

    await session.flush()
    if added_attractions or added_sections:
        logger.info(
            "seeded demo content",
            extra={"attractions": added_attractions, "guide_sections": added_sections},
        )


async def seed_all(session: AsyncSession) -> None:
    """Seed the administrator, the access policy, the first code and content."""
    settings = get_settings()
    await seed_admin(session)
    await access_service.ensure_active_code(session)
    if settings.seed_demo_content:
        await seed_content(session)
