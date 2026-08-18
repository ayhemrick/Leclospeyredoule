"""Shared fixtures.

The suite runs against a real PostgreSQL database rather than SQLite: the
schema relies on JSONB, ``gen_random_uuid()`` and row locking, so an in-memory
substitute would test something other than what ships.

Each test runs inside a transaction that is rolled back afterwards, with the
session joined to it through a savepoint so that request handlers can commit
normally.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

# Settings are read at import time, so the environment must be prepared first.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-not-used-anywhere-else-0123456789")
os.environ.setdefault("PUBLIC_BASE_URL", "http://testserver")
os.environ.setdefault("SEED_DEMO_CONTENT", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.cookies import CSRF_COOKIE, CSRF_HEADER
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models import AccessCode, AdminRole, AdminUser, GuestSession
from app.services import access_service, auth_service

DEFAULT_TEST_DB_URL = "postgresql+asyncpg://peyredoule:peyredoule@localhost:5433/peyredoule_test"
OWNER_PASSWORD = "OwnerPassword!2026"
EDITOR_PASSWORD = "EditorPassword!2026"


def _test_database_url() -> str:
    """URL of the scratch database, overridable for CI."""
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB_URL)


async def _ensure_database_exists(url: str) -> None:
    """Create the scratch database if the server does not have it yet."""
    admin_url, _, database = url.rpartition("/")
    engine = create_async_engine(f"{admin_url}/postgres", isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database}
            )
            if not exists:
                await connection.execute(text(f'CREATE DATABASE "{database}"'))
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
async def engine():
    """Session-wide engine against a freshly created schema."""
    url = _test_database_url()
    await _ensure_database_exists(url)
    engine = create_async_engine(url, poolclass=None)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncGenerator[AsyncSession]:
    """A session inside a transaction that is rolled back after the test."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        db_session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield db_session
        finally:
            await db_session.close()
            if transaction.is_active:
                await transaction.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """HTTP client bound to the app, sharing the test's transaction."""
    get_settings.cache_clear()
    app = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Domain fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
async def owner(session: AsyncSession) -> AdminUser:
    """A seeded owner account."""
    admin = await auth_service.create_admin(
        session,
        email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Owner",
        password=OWNER_PASSWORD,
        role=AdminRole.OWNER,
    )
    await session.flush()
    return admin


@pytest.fixture
async def editor(session: AsyncSession) -> AdminUser:
    """A seeded editor account."""
    admin = await auth_service.create_admin(
        session,
        email=f"editor-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Editor",
        password=EDITOR_PASSWORD,
        role=AdminRole.EDITOR,
    )
    await session.flush()
    return admin


@pytest.fixture
async def active_code(session: AsyncSession) -> AccessCode:
    """The active property code."""
    code = await access_service.ensure_active_code(session)
    await session.flush()
    return code


class AdminClient:
    """A signed-in admin HTTP client that carries the CSRF header."""

    def __init__(self, http: AsyncClient) -> None:
        self.http = http

    @property
    def _headers(self) -> dict[str, str]:
        token = self.http.cookies.get(CSRF_COOKIE)
        return {CSRF_HEADER: token} if token else {}

    async def get(self, url: str, **kwargs: object):
        """GET as the signed-in admin."""
        return await self.http.get(url, **kwargs)  # type: ignore[arg-type]

    async def post(self, url: str, **kwargs: object):
        """POST with the CSRF header attached."""
        return await self.http.post(url, headers=self._headers, **kwargs)  # type: ignore[arg-type]

    async def patch(self, url: str, **kwargs: object):
        """PATCH with the CSRF header attached."""
        return await self.http.patch(url, headers=self._headers, **kwargs)  # type: ignore[arg-type]

    async def delete(self, url: str, **kwargs: object):
        """DELETE with the CSRF header attached."""
        return await self.http.delete(url, headers=self._headers, **kwargs)  # type: ignore[arg-type]


async def sign_in(http: AsyncClient, email: str, password: str) -> AdminClient:
    """Log in and return a client that carries the session and CSRF token."""
    response = await http.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return AdminClient(http)


@pytest.fixture
async def owner_client(client: AsyncClient, owner: AdminUser) -> AdminClient:
    """Client signed in as the owner."""
    return await sign_in(client, owner.email, OWNER_PASSWORD)


@pytest.fixture
async def editor_client(client: AsyncClient, editor: AdminUser) -> AdminClient:
    """Client signed in as the editor."""
    return await sign_in(client, editor.email, EDITOR_PASSWORD)


@pytest.fixture
async def guest_session(session: AsyncSession, active_code: AccessCode) -> tuple[str, GuestSession]:
    """A redeemed visitor session and its raw token."""
    granted = await access_service.redeem(session, active_code.code, user_agent="pytest")
    await session.flush()
    guest = await session.get(GuestSession, granted.session_id)
    assert guest is not None
    return granted.token, guest


def expire(moment_delta_minutes: int) -> object:
    """Return a timestamp offset from now, for building expiries in tests."""
    return utcnow() + timedelta(minutes=moment_delta_minutes)
