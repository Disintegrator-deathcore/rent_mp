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
    
    credenitials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Декодируем и проверяем подпись токена
    payload = decode_token(token)
    if not payload:
        raise credenitials_exception

    # Проверяем, что это именно Access Token, а не Refresh
    token_type = payload.get("type")
    if token_type != "access":
        raise credenitials_exception
    
    # Извлекаем ID ползователя
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credenitials_exception
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credenitials_exception
    
    # Ищем пользователя в бд
    query = select(User).where(User.id == user_id)
    user = await session.scalar(query)
    
    if user is None:
        raise credenitials_exception
    
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
        if current_user.role.value not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции",
            )
        return current_user
    
# Инжектит сервис работы с пользователем
async def get_user_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserService:
    return UserService(session)
