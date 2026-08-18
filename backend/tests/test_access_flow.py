"""The visitor journey: scan, unlock, expire, revoke."""

from __future__ import annotations

from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.core.cookies import GUEST_COOKIE
from app.models import AccessCode, GuestSession
from app.models.content import GuideCategory, GuideSection, Visibility
from app.services import access_service
from app.services.access_service import AccessDeniedError, DenialReason

GUEST_GUIDE = "/api/v1/public/guide/guest"
REDEEM = "/api/v1/access/redeem"


async def _add_sections(session: AsyncSession) -> None:
    """Add one public and one guest-only section."""
    session.add_all(
        [
            GuideSection(
                slug="public-section",
                category=GuideCategory.HOUSE,
                visibility=Visibility.PUBLIC,
                title_fr="Publique",
                title_en="Public",
                body_fr="Texte",
                body_en="Text",
            ),
            GuideSection(
                slug="guest-section",
                category=GuideCategory.PRACTICAL,
                visibility=Visibility.GUEST,
                title_fr="Privée",
                title_en="Private",
                body_fr="Code du portail",
                body_en="Gate code",
            ),
        ]
    )
    await session.flush()


async def test_guest_guide_requires_a_scan(client: AsyncClient, session: AsyncSession) -> None:
    await _add_sections(session)
    response = await client.get(GUEST_GUIDE)
    assert response.status_code == 403


async def test_public_guide_never_leaks_guest_sections(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _add_sections(session)
    response = await client.get("/api/v1/public/guide")
    assert response.status_code == 200
    slugs = {section["slug"] for section in response.json()}
    assert slugs == {"public-section"}


async def test_scanning_the_code_unlocks_the_guide(
    client: AsyncClient, session: AsyncSession, active_code: AccessCode
) -> None:
    await _add_sections(session)

    redeemed = await client.post(REDEEM, json={"code": active_code.code})
    assert redeemed.status_code == 200
    body = redeemed.json()
    assert body["granted"] is True
    assert body["seconds_remaining"] > 0
    assert GUEST_COOKIE in redeemed.cookies

    unlocked = await client.get(GUEST_GUIDE)
    assert unlocked.status_code == 200
    slugs = {section["slug"] for section in unlocked.json()}
    assert slugs == {"public-section", "guest-section"}


async def test_scan_is_counted_on_the_code(
    client: AsyncClient, session: AsyncSession, active_code: AccessCode
) -> None:
    await client.post(REDEEM, json={"code": active_code.code})
    await session.refresh(active_code)
    assert active_code.scan_count == 1


async def test_unknown_code_is_refused(client: AsyncClient) -> None:
    response = await client.post(REDEEM, json={"code": "definitely-not-a-code"})
    assert response.status_code == 403
    assert response.headers["X-Access-Denied-Reason"] == DenialReason.UNKNOWN_CODE.value


async def test_retired_code_is_refused(
    client: AsyncClient, session: AsyncSession, active_code: AccessCode
) -> None:
    stale = active_code.code
    await access_service.rotate_code(session, reason=access_service.RotationReason.MANUAL)
    await session.flush()

    response = await client.post(REDEEM, json={"code": stale})
    assert response.status_code == 403
    assert response.headers["X-Access-Denied-Reason"] == DenialReason.EXPIRED_CODE.value


async def test_expired_session_stops_granting_access(
    client: AsyncClient, session: AsyncSession, active_code: AccessCode
) -> None:
    await _add_sections(session)
    await client.post(REDEEM, json={"code": active_code.code})
    assert (await client.get(GUEST_GUIDE)).status_code == 200

    guest = (await session.execute(GuestSession.__table__.select())).first()
    assert guest is not None
    await session.execute(
        GuestSession.__table__.update().values(expires_at=utcnow() - timedelta(minutes=1))
    )
    await session.flush()

    assert (await client.get(GUEST_GUIDE)).status_code == 403
    status = (await client.get("/api/v1/access/status")).json()
    assert status["granted"] is False


async def test_revoked_session_stops_granting_access(
    client: AsyncClient, session: AsyncSession, active_code: AccessCode
) -> None:
    await _add_sections(session)
    await client.post(REDEEM, json={"code": active_code.code})

    guest = (await session.execute(GuestSession.__table__.select())).first()
    assert guest is not None
    await access_service.revoke_session(session, guest.id)
    await session.flush()

    assert (await client.get(GUEST_GUIDE)).status_code == 403


async def test_leaving_ends_the_session(
    client: AsyncClient, session: AsyncSession, active_code: AccessCode
) -> None:
    await _add_sections(session)
    await client.post(REDEEM, json={"code": active_code.code})

    left = await client.post("/api/v1/access/leave")
    assert left.status_code == 200
    assert (await client.get(GUEST_GUIDE)).status_code == 403


async def test_capacity_limit_refuses_further_scans(
    session: AsyncSession, active_code: AccessCode
) -> None:
    policy = await access_service.get_policy(session)
    policy.max_active_sessions = 1
    await session.flush()

    await access_service.redeem(session, active_code.code)
    await session.flush()

    try:
        await access_service.redeem(session, active_code.code)
    except AccessDeniedError as exc:
        assert exc.reason is DenialReason.AT_CAPACITY
    else:  # pragma: no cover - only reached if the cap stops working
        raise AssertionError("expected the second scan to be refused")


async def test_session_token_is_never_stored_in_clear(
    session: AsyncSession, guest_session: tuple[str, GuestSession]
) -> None:
    token, guest = guest_session
    assert guest.token_hash != token
    assert len(guest.token_hash) == 64


async def test_forged_cookie_does_not_grant_access(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _add_sections(session)
    client.cookies.set(GUEST_COOKIE, "a-token-that-was-never-issued")
    assert (await client.get(GUEST_GUIDE)).status_code == 403
