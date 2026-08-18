"""Administrator account management and the last-owner guard."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminRole, AdminUser
from tests.conftest import AdminClient

USERS = "/api/v1/admin/users"
NEW_ADMIN = {
    "email": "new-admin@example.com",
    "full_name": "Nouvelle Administratrice",
    "password": "AnotherStrongPass!2026",
    "role": "editor",
}


async def test_editor_cannot_list_admins(editor_client: AdminClient) -> None:
    assert (await editor_client.get(USERS)).status_code == 403


async def test_owner_can_invite_an_admin(owner_client: AdminClient) -> None:
    created = await owner_client.post(USERS, json=NEW_ADMIN)
    assert created.status_code == 201
    assert created.json()["role"] == "editor"
    assert "password" not in created.json()

    listed = await owner_client.get(USERS)
    assert NEW_ADMIN["email"] in {admin["email"] for admin in listed.json()}


async def test_duplicate_email_is_a_conflict(owner_client: AdminClient) -> None:
    assert (await owner_client.post(USERS, json=NEW_ADMIN)).status_code == 201
    assert (await owner_client.post(USERS, json=NEW_ADMIN)).status_code == 409


async def test_weak_password_is_rejected(owner_client: AdminClient) -> None:
    response = await owner_client.post(USERS, json={**NEW_ADMIN, "password": "short"})
    assert response.status_code == 422


async def test_deactivating_signs_the_account_out(
    owner_client: AdminClient, session: AsyncSession, editor: AdminUser
) -> None:
    before = editor.token_epoch
    response = await owner_client.patch(f"{USERS}/{editor.id}", json={"is_active": False})

    assert response.status_code == 200
    await session.refresh(editor)
    assert editor.is_active is False
    assert editor.token_epoch != before


async def test_last_owner_cannot_be_demoted(owner_client: AdminClient, owner: AdminUser) -> None:
    response = await owner_client.patch(f"{USERS}/{owner.id}", json={"role": "editor"})
    assert response.status_code == 409


async def test_last_owner_cannot_be_deactivated(
    owner_client: AdminClient, owner: AdminUser
) -> None:
    response = await owner_client.patch(f"{USERS}/{owner.id}", json={"is_active": False})
    assert response.status_code == 409


async def test_owner_can_be_demoted_once_another_owner_exists(
    owner_client: AdminClient, session: AsyncSession, owner: AdminUser
) -> None:
    second = await owner_client.post(USERS, json={**NEW_ADMIN, "role": "owner"})
    assert second.status_code == 201

    response = await owner_client.patch(f"{USERS}/{owner.id}", json={"role": "editor"})
    assert response.status_code == 200
    await session.refresh(owner)
    assert owner.role is AdminRole.EDITOR


async def test_owner_cannot_delete_themselves(owner_client: AdminClient, owner: AdminUser) -> None:
    assert (await owner_client.delete(f"{USERS}/{owner.id}")).status_code == 409


async def test_owner_can_delete_another_admin(owner_client: AdminClient, editor: AdminUser) -> None:
    assert (await owner_client.delete(f"{USERS}/{editor.id}")).status_code == 200
    assert (await owner_client.delete(f"{USERS}/{editor.id}")).status_code == 404
