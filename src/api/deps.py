from uuid import UUID
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_async_session
from src.core.security import decode_token
from src.models.user import User
from src.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Декодируем и проверяем подпись токена
    payload = decode_token(token)
    if not payload:
        raise credentials_exception

    # Проверяем, что это именно Access Token, а не Refresh
    if payload.get("type") != "access":
        raise credentials_exception
    
    # Извлекаем ID пользователя
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exception
    
    # Поддерживаем как UUID, так и integer ID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Ищем пользователя в БД
    query = select(User).where(User.id == user_id)
    user = await session.scalar(query)
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )

    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles
        
    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        # Безопасное получение строкового значения роли (для StrEnum и обычной строки)
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции",
            )
        return current_user


async def get_user_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserService:
    return UserService(session)