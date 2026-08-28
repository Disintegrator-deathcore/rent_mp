import pytest
from httpx import AsyncClient


# Данные для тестового пользователя
USER_DATA = {
    "email": "testuser@example.com",
    "first_name": "Тест",
    "last_name": "Тестов",
    "patronymic_name": "Тестович",
    "password": "StrongPassword123!",
    "role": "client"
}

# Тест успешной регистрации пользователя
@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json=USER_DATA)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == USER_DATA["email"]
    assert data["first_name"] == USER_DATA["first_name"]
    assert data["patronymic_name"] == USER_DATA["patronymic_name"]
    assert "id" in data
    assert "password" not in data
    
# Тест успешного входа и получения пары токенов
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Регистрируем
    await client.post("/api/v1/auth/register", json=USER_DATA)
    
    # Логинимся через form-data
    login_data = {
        "username": USER_DATA["email"],
        "password": USER_DATA["password"],
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    
# Тест получения профиля текущего пользователя
@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=USER_DATA)
    
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        }
    )
    access_token = login_res.json()["access_token"]
    
    # Отправляем запрос с заголовком для авторизации
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == USER_DATA["email"]
    
# Тест успешного обновления профиля
@pytest.mark.asyncio
async def test_patch_me_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=USER_DATA)
    
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        }
    )
    access_token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}
    update_data = {"first_name": "НовоеИмя", "phone_number": "+79990001122"}
    
    response = await client.patch("/api/v1/auth/me", json=update_data, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["first_name"] == "НовоеИмя"
    assert response.json()["phone_number"] == "+79990001122"
    
# Тест успешного обновления пары токенов по refresh токену
@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=USER_DATA)
    
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        }
    )
    refresh_token = login_res.json()["refresh_token"]
    
    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        }
    )
    
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
