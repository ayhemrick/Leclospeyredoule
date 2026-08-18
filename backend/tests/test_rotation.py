"""Code rotation: automatic, manual, and what it does to live sessions."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.models import AccessCode, GuestSession, RotationReason
from app.schemas.access import AccessPolicyUpdate
from app.services import access_service
from tests.conftest import AdminClient


async def test_first_call_mints_a_code(session: AsyncSession) -> None:
    code = await access_service.ensure_active_code(session)
    assert code.is_active
    assert code.reason is RotationReason.INITIAL
    assert code.expires_at is not None


async def test_overdue_code_rotates_lazily(session: AsyncSession) -> None:
    code = await access_service.ensure_active_code(session)
    original = code.code
    code.expires_at = utcnow() - timedelta(minutes=1)
    await session.flush()

    rotated = await access_service.ensure_active_code(session)
    assert rotated.code != original
    assert rotated.reason is RotationReason.SCHEDULED

    await session.refresh(code)
    assert code.is_active is False
    assert code.retired_at is not None


async def test_no_rotation_before_the_interval_elapses(session: AsyncSession) -> None:
    code = await access_service.ensure_active_code(session)
    again = await access_service.ensure_active_code(session)
    assert again.id == code.id


async def test_auto_rotate_off_means_no_expiry(session: AsyncSession) -> None:
    policy = await access_service.get_policy(session)
    policy.auto_rotate = False
    await session.flush()

    code = await access_service.rotate_code(session, reason=RotationReason.MANUAL)
    assert code.expires_at is None

    unchanged = await access_service.ensure_active_code(session)
    assert unchanged.id == code.id


async def test_sessions_survive_rotation_by_default(
    session: AsyncSession, guest_session: tuple[str, GuestSession]
) -> None:
    token, _ = guest_session
    await access_service.rotate_code(session, reason=RotationReason.MANUAL)
    await session.flush()

    assert await access_service.resolve_session(session, token) is not None


async def test_sessions_can_be_cut_on_rotation(
    session: AsyncSession, guest_session: tuple[str, GuestSession]
) -> None:
    token, _ = guest_session
    policy = await access_service.get_policy(session)
    policy.revoke_sessions_on_rotation = True
    await session.flush()

    await access_service.rotate_code(session, reason=RotationReason.MANUAL)
    await session.flush()

    assert await access_service.resolve_session(session, token) is None


async def test_changing_the_interval_redates_the_active_code(session: AsyncSession, owner) -> None:
    code = await access_service.ensure_active_code(session)
    before = code.expires_at
    assert before is not None

    await access_service.update_policy(
        session, AccessPolicyUpdate(rotation_interval_minutes=60), actor=owner
    )
    await session.flush()
    await session.refresh(code)

    assert code.expires_at is not None
    assert code.expires_at < before
    assert code.expires_at == code.created_at + timedelta(minutes=60)


async def test_only_one_code_is_ever_active(session: AsyncSession) -> None:
    await access_service.ensure_active_code(session)
    for _ in range(3):
        await access_service.rotate_code(session, reason=RotationReason.MANUAL)
    await session.flush()

    active = (
        (await session.execute(select(AccessCode).where(AccessCode.is_active.is_(True))))
        .scalars()
        .all()
    )
    assert len(active) == 1


async def test_owner_can_rotate_over_http(owner_client: AdminClient) -> None:
    before = (await owner_client.get("/api/v1/admin/access/code")).json()
    rotated = await owner_client.post("/api/v1/admin/access/code/rotate")

    assert rotated.status_code == 201
    body = rotated.json()
    assert body["code"] != before["code"]
    assert body["reason"] == RotationReason.MANUAL.value
    assert body["poster_url"].endswith(f"/a/{body['code']}")
    assert body["qr_svg"].startswith("<svg")


async def test_editor_cannot_rotate(editor_client: AdminClient) -> None:
    response = await editor_client.post("/api/v1/admin/access/code/rotate")
    assert response.status_code == 403


async def test_owner_can_change_the_policy(owner_client: AdminClient) -> None:
    response = await owner_client.patch(
        "/api/v1/admin/access/policy",
        json={"rotation_interval_minutes": 120, "guest_session_minutes": 240},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rotation_interval_minutes"] == 120
    assert body["guest_session_minutes"] == 240


async def test_policy_bounds_are_enforced(owner_client: AdminClient) -> None:
    response = await owner_client.patch(
        "/api/v1/admin/access/policy", json={"guest_session_minutes": 1}
    )
    assert response.status_code == 422


async def test_revoke_all_ends_live_sessions(
    session: AsyncSession, owner_client: AdminClient, guest_session: tuple[str, GuestSession]
) -> None:
    token, _ = guest_session
    response = await owner_client.post("/api/v1/admin/access/sessions/revoke-all")
    assert response.status_code == 200
    assert await access_service.resolve_session(session, token) is None


async def test_stats_report_live_sessions(
    owner_client: AdminClient, guest_session: tuple[str, GuestSession]
) -> None:
    stats = (await owner_client.get("/api/v1/admin/access/stats")).json()
    assert stats["active_sessions"] == 1
    assert stats["sessions_last_24h"] == 1
    assert stats["total_scans"] >= 1
