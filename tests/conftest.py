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


engine_test = create_async_engine(
    str(settings.DATABASE_URL),
    poolclass = NullPool,
    echo=False,
)
async_session_maker = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False
)
    
# Создает таблицы перед каждым тестом и очищает после
@pytest.fixture(autouse=True, scope="function")
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)
    yield
    
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        
# Асинхронный клиент для отправки http запросов к fastapi
@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session
            
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(
        transport = ASGITransport(app = app),
        base_url = "http://test",
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()
