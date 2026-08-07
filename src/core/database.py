from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings


# Создаем асинхронный движок
# При debug=True выводит команды в консоль
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo = settings.DEBUG,
    future = True,
    pool_pre_ping = True # Проверяет активность соединений перед использованием
)

# Фабрика для создания асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind = engine,
    class_ = AsyncSession,
    expire_on_commit = False, # Предотвращает нежелательные повторные запросы к БД после commit
    autoflush = False,
    autocommit = False,
)

# Базовый класс для всех будущих ORM-моделей
class Base(DeclarativeBase):
    pass

# FastAPI Dependency для получения асинхронной сессии БД в эндпоинтах
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    # Генератор асинхронной сессии с автоматическим закрытием после завершения запроса
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
