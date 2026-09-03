import uuid
import pytest
from httpx import AsyncClient

# Валидные тестовые данные для создания объявления
VALID_LISTING_DATA = {
    "title": "Уютная квартира в центре",
    "description": "Просторная светлая квартира со всеми удобствами на длительный срок.",
    "price_per_day": "2500.00",
    "address": "г. Москва, ул. Тверская, д. 10",
}

@pytest.mark.asyncio
async def test_create_listing_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Успешное создание объявления авторизованным пользователем."""
    response = await client.post(
        "/api/v1/listings/",
        json=VALID_LISTING_DATA,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == VALID_LISTING_DATA["title"]
    assert data["address"] == VALID_LISTING_DATA["address"]
    assert "id" in data
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_create_listing_unauthorized(client: AsyncClient):
    """Попытка создания объявления без авторизации (ожидаем 401)."""
    response = await client.post(
        "/api/v1/listings/",
        json=VALID_LISTING_DATA,
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_listings_list(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Получение списка объявлений."""
    # Создаем тестовое объявление
    await client.post(
        "/api/v1/listings/",
        json=VALID_LISTING_DATA,
        headers=auth_headers,
    )

    response = await client.get("/api/v1/listings/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_listing_by_id_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Получение объявления по его UUID."""
    create_res = await client.post(
        "/api/v1/listings/",
        json=VALID_LISTING_DATA,
        headers=auth_headers,
    )
    listing_id = create_res.json()["id"]

    response = await client.get(f"/api/v1/listings/{listing_id}")
    assert response.status_code == 200
    assert response.json()["id"] == listing_id


@pytest.mark.asyncio
async def test_get_listing_by_id_not_found(client: AsyncClient):
    """Запрос несуществующего объявления по случайно сгенерированному UUID."""
    random_uuid = uuid.uuid4()
    response = await client.get(f"/api/v1/listings/{random_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_listing_owner_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Обновление объявления его владельцем."""
    create_res = await client.post(
        "/api/v1/listings/",
        json=VALID_LISTING_DATA,
        headers=auth_headers,
    )
    listing_id = create_res.json()["id"]

    update_payload = {"title": "Новое название квартиры"}
    response = await client.patch(
        f"/api/v1/listings/{listing_id}",
        json=update_payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == update_payload["title"]


@pytest.mark.asyncio
async def test_delete_listing_owner_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Успешное удаление объявления его владельцем."""
    create_res = await client.post(
        "/api/v1/listings/",
        json=VALID_LISTING_DATA,
        headers=auth_headers,
    )
    listing_id = create_res.json()["id"]

    delete_res = await client.delete(
        f"/api/v1/listings/{listing_id}",
        headers=auth_headers,
    )
    assert delete_res.status_code == 204

    # Проверяем, что объявление действительно удалено
    get_res = await client.get(f"/api/v1/listings/{listing_id}")
    assert get_res.status_code == 404