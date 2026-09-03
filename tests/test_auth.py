from uuid import uuid4
import pytest
from fastapi import status
from httpx import AsyncClient

from src.models.user import User


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
        },
    )
    
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    
# Тест успешного удаления пользователем своего аккаунта
@pytest.mark.asyncio
async def test_user_can_delete_self_success(client: AsyncClient):
    reg_res = await client.post("/api/v1/auth/register", json=USER_DATA)
    user_id = reg_res.json()["id"]
    
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        },
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Удаляем свой аккаунт
    delete_res = await client.delete(f"/api/v1/auth/{user_id}", headers=headers)
    assert delete_res.status_code == status.HTTP_204_NO_CONTENT
    
    # Проверяем, что повторный запрос /me возвращает 401
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == status.HTTP_401_UNAUTHORIZED

# Тест отказа удаления чужого аккаунта обычным пользователем
@pytest.mark.asyncio
async def test_delete_other_user_forbidden(client: AsyncClient):
    # Регистрируем первого пользователя
    reg_res = await client.post("/api/v1/auth/register", json=USER_DATA)
    victim_user_id = reg_res.json()["id"]
    
    # Регистрируем второго пользователя
    other_user_data = USER_DATA.copy()
    other_user_data["email"] = "otheruser@example.com"
    await client.post("/api/v1/auth/register", json=other_user_data)
    
    # Логинимся под вторым пользователем
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
                "username": other_user_data["email"],
                "password": other_user_data["password"],
        },
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Вторым пользователем пытаемся удалить первого
    delete_res = await client.delete(f"/api/v1/auth/{victim_user_id}", headers=headers)
    assert delete_res.status_code == status.HTTP_403_FORBIDDEN
    
# Тст возврата 404 при попытке администратором удалить несуществующий UUID
@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient):
    # Регистрируем админа
    admin_data = USER_DATA.copy()
    admin_data["email"] = "admin@example.com"
    admin_data["role"] = "admin"
    await client.post("/api/v1/auth/register", json=admin_data)

    # Логинимся под админом
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_data["email"],
            "password": admin_data["password"],
        },
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Пытаемся удалить несуществующий UUID
    non_existent_id = str(uuid4())
    delete_res = await client.delete(f"/api/v1/auth/{non_existent_id}", headers=headers)
    assert delete_res.status_code == status.HTTP_404_NOT_FOUND
