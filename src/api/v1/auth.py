from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.deps import get_current_user, get_user_service
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.models.user import User
from src.schemas.user import (
    RefreshTokenRequest,
    UserCreate,
    UserRead,
    UserUpdate,
)
from src.services.user import UserService


router = APIRouter(prefix="/auth", tags=["Auth"])

# Регистрирует нового пользователя с проверкой уникальности email и телефона
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
async def register(
    user_in: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    
    return await user_service.create(user_in)

# Выполняет вход пользователя
@router.post(
    "/login",
    summary="Аутентификация и получение JWT-токенов",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> dict[str, str]:
    
    user = await user_service.authenticate(
        email = form_data.username,
        password = form_data.password,
    )
    
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value},
    )
    refresh_token = create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

# Возвращает информацию о текущем авторизованном пользователе на основе JWT-токена
@router.get(
    "/me",
    response_model=UserRead,
    summary="Получить профиль текущего пользователя",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
    
# Частично обновляет профиль авторизованного пользователя
# обновляются только те поля, которые были переданы в теле запроса
@router.patch(
    "/me",
    response_model=UserRead,
    summary="Обновить профиль текущего пользователя",
)
async def update_me(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    
    return await user_service.update(user = current_user, user_in = user_in)

# Принимает валидный Refresh-токен и выдает новую пару токенов
@router.post(
    "/refresh",
    summary="Обновление JWT Access и Refresh токенов",
)
async def refresh_tokens(
    body: RefreshTokenRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> dict[str, str]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный или просроченный refresh-токен.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Декодируем и проверяем токен
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise credentials_exception
    
    # Достаем id пользователя
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Проверяем существование и активность пользователя в бд
    user = await user_service.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учетная запись деактивирована",
        )
        
    # Генерируем новую пару токенов
    new_access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value},
    )
    new_refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
    