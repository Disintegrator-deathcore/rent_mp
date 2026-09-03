from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.core.database import get_async_session
from main import app
from src.models.base import BaseModel

# Тестовые данные
USER_DATA = {
    "email": "testuser@example.com",
    "first_name": "Тест",
    "last_name": "Тестов",
    "patronymic_name": "Тестович",
    "password": "StrongPassword123!",
    "role": "landlord"
}

VALID_LISTING_DATA = {
    "title": "Уютная квартира в центре",
    "description": "Просторная светлая квартира со всеми удобствами на длительный срок.",
    "price_per_day": "2500.00",
    "address": "г. Москва, ул. Тверская, д. 10",
}

# Используем тестовую базу данных или стандартный URL
TEST_DATABASE_URL = str(settings.DATABASE_URL)

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

async_session_maker = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True, scope="function")
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    # raise_app_exceptions=True пробрасывает внутренние ошибки сервера прямо в pytest
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=True),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Фикстура получения валидного заголовока с авторизацией."""
    reg_response = await client.post("/api/v1/auth/register", json=USER_DATA)
    assert reg_response.status_code == 201, f"Registration failed: {reg_response.text}"

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": USER_DATA["email"], "password": USER_DATA["password"]},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}