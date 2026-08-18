"""Seeding, the rotation worker and production configuration guards."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import utcnow
from app.core.config import Settings
from app.models import (
    AccessCode,
    AccessPolicy,
    AdminRole,
    AdminUser,
    Attraction,
    AuditLog,
    GuideSection,
    RotationReason,
)
from app.services import access_service, rotation_worker, seed


async def test_seed_admin_creates_a_single_owner(session: AsyncSession) -> None:
    await seed.seed_admin(session)
    await session.flush()

    admins = (await session.execute(select(AdminUser))).scalars().all()
    assert len(admins) == 1
    assert admins[0].role is AdminRole.OWNER


async def test_seed_admin_is_idempotent(session: AsyncSession, owner: AdminUser) -> None:
    await seed.seed_admin(session)
    await session.flush()

    count = (await session.execute(select(func.count()).select_from(AdminUser))).scalar_one()
    assert count == 1


async def test_seed_content_inserts_demo_rows(session: AsyncSession) -> None:
    await seed.seed_content(session)
    await session.flush()

    attractions = (await session.execute(select(Attraction))).scalars().all()
    sections = (await session.execute(select(GuideSection))).scalars().all()
    assert len(attractions) >= 10
    assert len(sections) >= 10
    assert {s.visibility.value for s in sections} == {"public", "guest"}


async def test_seed_content_does_not_duplicate_or_overwrite(session: AsyncSession) -> None:
    await seed.seed_content(session)
    await session.flush()

    edited = (
        await session.execute(select(GuideSection).where(GuideSection.slug == "nos-adresses"))
    ).scalar_one()
    edited.body_fr = "Texte modifié par le propriétaire."
    await session.flush()

    await seed.seed_content(session)
    await session.flush()

    count = (await session.execute(select(func.count()).select_from(GuideSection))).scalar_one()
    assert count == len(seed.GUIDE_SECTIONS)
    await session.refresh(edited)
    assert edited.body_fr == "Texte modifié par le propriétaire."


async def test_seed_all_publishes_a_code(session: AsyncSession) -> None:
    await seed.seed_all(session)
    await session.flush()

    code = await access_service.get_active_code(session)
    assert code is not None


async def test_worker_rotates_an_overdue_code(engine, monkeypatch: pytest.MonkeyPatch) -> None:
    """The worker commits for real, so it avoids the rolled-back fixture.

    Sharing that session would have the worker block on the row locks the
    fixture's open transaction holds.
    """
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(rotation_worker, "get_sessionmaker", lambda: factory)

    async with factory() as setup:
        code = await access_service.ensure_active_code(setup)
        original = code.code
        code.expires_at = utcnow() - timedelta(minutes=5)
        await setup.commit()

    try:
        stop = asyncio.Event()
        task = asyncio.create_task(rotation_worker.run_rotation_worker(stop))
        await asyncio.sleep(0.3)
        stop.set()
        await asyncio.wait_for(task, timeout=10)

        async with factory() as check:
            active = (
                await check.execute(select(AccessCode).where(AccessCode.is_active.is_(True)))
            ).scalar_one()
            assert active.code != original
            assert active.reason is RotationReason.SCHEDULED
    finally:
        async with factory() as cleanup:
            await cleanup.execute(delete(AuditLog))
            await cleanup.execute(delete(AccessCode))
            await cleanup.execute(delete(AccessPolicy))
            await cleanup.commit()


def test_production_config_rejects_development_defaults() -> None:
    settings = Settings(
        app_env="production",
        app_secret_key="dev-only-secret-change-me-0000000000000000000000000000000000",
        cookie_secure=False,
        admin_password="ChangeMe!2026",
    )
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_ready()

    message = str(error.value)
    assert "APP_SECRET_KEY" in message
    assert "COOKIE_SECURE" in message
    assert "ADMIN_PASSWORD" in message


def test_production_config_accepts_hardened_values() -> None:
    settings = Settings(
        app_env="production",
        app_secret_key="a-real-secret-that-is-long-enough-to-be-safe-0123456789",
        cookie_secure=True,
        admin_password="a-real-admin-password",
    )
    settings.assert_production_ready()


def test_cors_origins_are_parsed() -> None:
    settings = Settings(
        app_secret_key="a-real-secret-that-is-long-enough-to-be-safe-0123456789",
        cors_origins="https://a.example, https://b.example ,",
    )
    assert settings.cors_origin_list == ["https://a.example", "https://b.example"]


def test_blank_cookie_domain_becomes_none() -> None:
    settings = Settings(
        app_secret_key="a-real-secret-that-is-long-enough-to-be-safe-0123456789",
        cookie_domain="   ",
    )
    assert settings.cookie_domain is None
