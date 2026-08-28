from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.database import get_async_session
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from src.models.user import User
from src.schemas.user import RefreshTokenRequest, UserCreate, UserRead, UserUpdate


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
            
    # Хэшируем пароль и создаем запись в бд
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

# Принимает валидный Refresh-токен и выдает новую пару токенов
@router.post(
    "/refresh",
    summary="Обновление JWT Access и Refresh токенов",
)
async def refresh_tokens(
    body: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный или просроченный refresh-токен.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Декодируем и проверяем токен
    payload = decode_token(body.refresh_token)
    if not payload:
        raise credentials_exception
    
    # Проверяем, что передали именно Refresh, а не Access токен
    if payload.get("type") != "refresh":
        raise credentials_exception
    
    # Достаем id пользователя
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Проверяем существование и активность пользователя в бд
    query = select(User).where(User.id == user_id)
    user = await session.scalar(query)
    
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
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    # Исключаем непереданные поля
    update_data = user_in.model_dump(exclude_unset=True)
    
    if not update_data:
        return current_user
    
    # Проверка уникальности нового Email
    if (
        "email" in update_data
        and update_data["email"] != current_user.email
    ):
        email_query = select(User).where(User.email == update_data["email"])
        existing_email = await session.scalar(email_query)
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует",
            )
            
    # Проверка уникальности нового телефона
    if (
        "phone_number" in update_data
        and update_data["phone_number"] is not None
        and update_data["phone_number"] != current_user.phone_number
    ):
        phone_query = select(User).where(User.phone_number == update_data["phone_number"])
        existing_phone = await session.scalar(phone_query)
        
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким номером телефона уже существует",
            )
            
    # Хеширование нового пароля
    if "password" in update_data:
        raw_password = update_data.pop("password")
        if raw_password:
            current_user.hashed_password = get_password_hash(raw_password)
            
    # Обновление остальных полей модели
    for field, value in update_data.items():
        setattr(current_user, field, value)
        
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    
    return current_user
