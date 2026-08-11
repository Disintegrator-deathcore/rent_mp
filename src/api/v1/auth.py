from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from src.models.user import User
from src.schemas.user import UserCreate, UserRead


router = APIRouter(prefix="/auth", tags=["Auth"])

# Регистрирует нового пользователя с проверкой уникальности email и телефона
@router.post(
    "register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
async def register(
    user_in: UserCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    
    # Проверяем существует ли пользователь с таким email
    email_query = select(User).where(User.email == user_in.email)
    existing_user = await session.scalar(email_query)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )
        
    # Проверяем уникальность телефона, если он указан
    if user_in.phone_number:
        phone_query = select(User).where(User.phone_number == user_in.phone_number)
        existing_phone = await session.scalar(phone_query)
        
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким номером уже существует",
            )
            
    # Хешируем пароль и создаем запись в бд
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        email = user_in.email,
        hashed_password = hashed_pwd,
        first_name = user_in.first_name,
        last_name = user_in.last_name,
        patronymic_name = user_in.patronymic_name,
        phone_number = user_in.phone_number,
        role = user_in.role,
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user

# Выполняет вход пользователя
@router.post(
    "/login",
    summary="Аутентификация и получение JWT-токенов",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    # Ищем пользователя по email
    query = select(User).where(User.email == form_data.username)
    user = await session.scalar(query)
    
    # Проверяем существование пользователя и совпадение пароля
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Проверяем статус активности
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учетная запись деактивирована",
        )
        
    # Генерируем токены
    access_token = create_access_token(
        subject = user.id,
        extra_claims={"role": user.role.value},
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
