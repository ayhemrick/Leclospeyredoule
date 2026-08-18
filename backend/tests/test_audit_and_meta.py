"""Audit trail, health endpoint and response hardening."""

from __future__ import annotations

from httpx import AsyncClient

from app.main import SECURITY_HEADERS
from tests.conftest import AdminClient

AUDIT = "/api/v1/admin/audit"


async def test_health_reports_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_security_headers_are_present(client: AsyncClient) -> None:
    response = await client.get("/health")
    for header, value in SECURITY_HEADERS.items():
        assert response.headers[header] == value


async def test_login_is_recorded(owner_client: AdminClient) -> None:
    entries = (await owner_client.get(AUDIT)).json()
    actions = [entry["action"] for entry in entries["items"]]
    assert "auth.login_succeeded" in actions


async def test_rotation_is_recorded_with_context(owner_client: AdminClient) -> None:
    await owner_client.post("/api/v1/admin/access/code/rotate")

    entries = (await owner_client.get(AUDIT, params={"action": "access."})).json()
    rotation = next(e for e in entries["items"] if e["action"] == "access.code_rotated")
    assert rotation["context"]["reason"] == "manual"
    assert rotation["entity_type"] == "access_code"


async def test_content_changes_are_recorded(owner_client: AdminClient) -> None:
    created = await owner_client.post(
        "/api/v1/admin/content/attractions",
        json={
            "slug": "bourg",
            "category": "heritage",
            "name_fr": "Bourg",
            "name_en": "Bourg",
            "summary_fr": "Cité médiévale.",
            "summary_en": "Medieval town.",
        },
    )
    assert created.status_code == 201

    entries = (await owner_client.get(AUDIT, params={"action": "content."})).json()
    assert entries["total"] >= 1
    assert entries["items"][0]["context"]["slug"] == "bourg"


async def test_audit_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(AUDIT)).status_code == 401


async def test_audit_paginates(owner_client: AdminClient) -> None:
    page = (await owner_client.get(AUDIT, params={"limit": 1})).json()
    assert page["limit"] == 1
    assert len(page["items"]) <= 1
    assert page["total"] >= len(page["items"])


async def test_audit_never_stores_raw_ip(owner_client: AdminClient) -> None:
    entries = (await owner_client.get(AUDIT)).json()
    for entry in entries["items"]:
        assert "ip" not in entry
