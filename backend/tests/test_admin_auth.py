"""Administrator sign-in, lockout, CSRF and token lifecycle."""

from __future__ import annotations

from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.cookies import ADMIN_ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER
from app.models import AdminUser
from tests.conftest import OWNER_PASSWORD, AdminClient

LOGIN = "/api/v1/auth/login"


async def test_login_sets_session_cookies(client: AsyncClient, owner: AdminUser) -> None:
    response = await client.post(LOGIN, json={"email": owner.email, "password": OWNER_PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["admin"]["email"] == owner.email
    assert body["admin"]["role"] == "owner"
    assert body["csrf_token"]
    assert ADMIN_ACCESS_COOKIE in response.cookies
    assert CSRF_COOKIE in response.cookies


async def test_login_is_case_insensitive_on_email(client: AsyncClient, owner: AdminUser) -> None:
    response = await client.post(
        LOGIN, json={"email": owner.email.upper(), "password": OWNER_PASSWORD}
    )
    assert response.status_code == 200


async def test_wrong_password_is_rejected(client: AsyncClient, owner: AdminUser) -> None:
    response = await client.post(LOGIN, json={"email": owner.email, "password": "wrong-password"})
    assert response.status_code == 401
    assert ADMIN_ACCESS_COOKIE not in response.cookies


async def test_unknown_account_looks_like_a_wrong_password(client: AsyncClient) -> None:
    response = await client.post(
        LOGIN, json={"email": "nobody@example.com", "password": "whatever-it-is"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid e-mail or password"


async def test_repeated_failures_lock_the_account(
    client: AsyncClient, session: AsyncSession, owner: AdminUser
) -> None:
    settings = get_settings()
    for _ in range(settings.login_max_attempts):
        await client.post(LOGIN, json={"email": owner.email, "password": "wrong-password"})

    locked = await client.post(LOGIN, json={"email": owner.email, "password": OWNER_PASSWORD})
    assert locked.status_code == 429
    assert "Retry-After" in locked.headers

    await session.refresh(owner)
    assert owner.locked_until is not None
    assert owner.locked_until > utcnow()


async def test_lockout_expires(
    client: AsyncClient, session: AsyncSession, owner: AdminUser
) -> None:
    owner.locked_until = utcnow() - timedelta(seconds=1)
    await session.flush()

    response = await client.post(LOGIN, json={"email": owner.email, "password": OWNER_PASSWORD})
    assert response.status_code == 200


async def test_deactivated_account_cannot_sign_in(
    client: AsyncClient, session: AsyncSession, owner: AdminUser
) -> None:
    owner.is_active = False
    await session.flush()

    response = await client.post(LOGIN, json={"email": owner.email, "password": OWNER_PASSWORD})
    assert response.status_code == 401


async def test_me_requires_a_session(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_me_returns_the_signed_in_admin(owner_client: AdminClient, owner: AdminUser) -> None:
    response = await owner_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == owner.email


async def test_mutation_without_csrf_header_is_refused(
    client: AsyncClient, owner: AdminUser
) -> None:
    await client.post(LOGIN, json={"email": owner.email, "password": OWNER_PASSWORD})
    response = await client.post("/api/v1/admin/access/code/rotate")
    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]


async def test_mutation_with_wrong_csrf_header_is_refused(
    client: AsyncClient, owner: AdminUser
) -> None:
    await client.post(LOGIN, json={"email": owner.email, "password": OWNER_PASSWORD})
    response = await client.post(
        "/api/v1/admin/access/code/rotate", headers={CSRF_HEADER: "not-the-cookie-value"}
    )
    assert response.status_code == 403


async def test_refresh_issues_a_new_access_cookie(client: AsyncClient, owner: AdminUser) -> None:
    await client.post(LOGIN, json={"email": owner.email, "password": OWNER_PASSWORD})
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert ADMIN_ACCESS_COOKIE in response.cookies


async def test_refresh_without_cookie_is_unauthorised(client: AsyncClient) -> None:
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401


async def test_logout_clears_the_session(owner_client: AdminClient) -> None:
    assert (await owner_client.post("/api/v1/auth/logout")).status_code == 200
    assert (await owner_client.get("/api/v1/auth/me")).status_code == 401


async def test_password_change_invalidates_older_tokens(
    client: AsyncClient, session: AsyncSession, owner: AdminUser, owner_client: AdminClient
) -> None:
    stale_token = client.cookies.get(ADMIN_ACCESS_COOKIE)
    assert stale_token is not None

    changed = await owner_client.post(
        "/api/v1/auth/password",
        json={"current_password": OWNER_PASSWORD, "new_password": "BrandNewPassword!2026"},
    )
    assert changed.status_code == 200

    # A client still presenting the pre-change token is signed out.
    stale_client = AsyncClient(
        transport=client._transport,
        base_url="http://testserver",
        cookies={ADMIN_ACCESS_COOKIE: stale_token},
    )
    async with stale_client:
        assert (await stale_client.get("/api/v1/auth/me")).status_code == 401


async def test_password_change_requires_the_current_one(owner_client: AdminClient) -> None:
    response = await owner_client.post(
        "/api/v1/auth/password",
        json={"current_password": "not-the-password", "new_password": "BrandNewPassword!2026"},
    )
    assert response.status_code == 400


async def test_short_passwords_are_rejected(owner_client: AdminClient) -> None:
    response = await owner_client.post(
        "/api/v1/auth/password",
        json={"current_password": OWNER_PASSWORD, "new_password": "short"},
    )
    assert response.status_code == 422
