"""Admin CRUD over guide sections and attractions."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import AdminClient

SECTIONS = "/api/v1/admin/content/guide-sections"
ATTRACTIONS = "/api/v1/admin/content/attractions"

SECTION_PAYLOAD = {
    "slug": "le-chai",
    "category": "house",
    "visibility": "guest",
    "position": 5,
    "title_fr": "Le chai",
    "title_en": "The cellar",
    "body_fr": "Table, billard, bibliothèque.",
    "body_en": "Table, billiards, library.",
}
ATTRACTION_PAYLOAD = {
    "slug": "citadelle",
    "category": "heritage",
    "name_fr": "Citadelle",
    "name_en": "Citadel",
    "summary_fr": "Fortification de Vauban.",
    "summary_en": "Vauban fortification.",
    "distance_km": "1.5",
    "travel_time_min": 5,
}


async def test_content_endpoints_require_authentication(client: AsyncClient) -> None:
    assert (await client.get(SECTIONS)).status_code == 401
    assert (await client.get(ATTRACTIONS)).status_code == 401


async def test_editor_may_manage_content(editor_client: AdminClient) -> None:
    created = await editor_client.post(SECTIONS, json=SECTION_PAYLOAD)
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == {"fr": "Le chai", "en": "The cellar"}
    assert body["title_fr"] == "Le chai"


async def test_section_appears_in_the_guest_guide(
    owner_client: AdminClient, client: AsyncClient, active_code
) -> None:
    await owner_client.post(SECTIONS, json=SECTION_PAYLOAD)
    await client.post("/api/v1/access/redeem", json={"code": active_code.code})

    guide = await client.get("/api/v1/public/guide/guest")
    assert guide.status_code == 200
    assert "le-chai" in {section["slug"] for section in guide.json()}


async def test_unpublished_section_is_hidden_from_visitors(
    owner_client: AdminClient, client: AsyncClient, active_code
) -> None:
    created = await owner_client.post(SECTIONS, json={**SECTION_PAYLOAD, "is_published": False})
    assert created.status_code == 201
    await client.post("/api/v1/access/redeem", json={"code": active_code.code})

    guide = await client.get("/api/v1/public/guide/guest")
    assert "le-chai" not in {section["slug"] for section in guide.json()}


async def test_duplicate_slug_is_a_conflict(owner_client: AdminClient) -> None:
    assert (await owner_client.post(SECTIONS, json=SECTION_PAYLOAD)).status_code == 201
    duplicate = await owner_client.post(SECTIONS, json=SECTION_PAYLOAD)
    assert duplicate.status_code == 409


async def test_invalid_slug_is_rejected(owner_client: AdminClient) -> None:
    response = await owner_client.post(SECTIONS, json={**SECTION_PAYLOAD, "slug": "Le Chai!"})
    assert response.status_code == 422


async def test_section_can_be_edited_and_deleted(owner_client: AdminClient) -> None:
    created = (await owner_client.post(SECTIONS, json=SECTION_PAYLOAD)).json()

    edited = await owner_client.patch(
        f"{SECTIONS}/{created['id']}", json={"title_en": "The barrel cellar"}
    )
    assert edited.status_code == 200
    assert edited.json()["title"]["en"] == "The barrel cellar"
    assert edited.json()["title"]["fr"] == "Le chai"

    deleted = await owner_client.delete(f"{SECTIONS}/{created['id']}")
    assert deleted.status_code == 200
    assert (await owner_client.patch(f"{SECTIONS}/{created['id']}", json={})).status_code == 404


async def test_attraction_round_trip(owner_client: AdminClient, client: AsyncClient) -> None:
    created = await owner_client.post(ATTRACTIONS, json=ATTRACTION_PAYLOAD)
    assert created.status_code == 201

    public = await client.get("/api/v1/public/attractions")
    assert public.status_code == 200
    names = {item["name"]["en"] for item in public.json()}
    assert "Citadel" in names


async def test_attractions_can_be_filtered_by_category(
    owner_client: AdminClient, client: AsyncClient
) -> None:
    await owner_client.post(ATTRACTIONS, json=ATTRACTION_PAYLOAD)
    await owner_client.post(
        ATTRACTIONS,
        json={**ATTRACTION_PAYLOAD, "slug": "vignoble", "category": "wine"},
    )

    wine = await client.get("/api/v1/public/attractions", params={"category": "wine"})
    assert {item["slug"] for item in wine.json()} == {"vignoble"}


async def test_image_requires_a_credit_line(owner_client: AdminClient) -> None:
    response = await owner_client.post(
        ATTRACTIONS, json={**ATTRACTION_PAYLOAD, "image_path": "/images/x.jpg"}
    )
    assert response.status_code == 422
    assert "image_credit" in response.text


async def test_unpublished_attraction_is_hidden(
    owner_client: AdminClient, client: AsyncClient
) -> None:
    await owner_client.post(ATTRACTIONS, json={**ATTRACTION_PAYLOAD, "is_published": False})
    public = await client.get("/api/v1/public/attractions")
    assert public.json() == []
