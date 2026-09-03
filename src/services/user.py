from typing import Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate


# Сервис для управления пользователями и бизнес логикой авторизации
class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        
    # Получение пользователя по id
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        return await self.session.scalar(query)
    
    # Получение пользователя по email
    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        return await self.session.scalar(query)

    # Получение пользователя по номеру телефона
    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        query = select(User).where(User.phone_number == phone_number)
        return await self.session.scalar(query)

    # Создание нового пользователя
    async def create(self, user_in: UserCreate) -> User:
        # Проверка email
        if await self.get_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует",
            )
            
        # Проверка телефона
        if user_in.phone_number and await self.get_by_phone(user_in.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким номером уже существует",
            )
            
        # Создание записи
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
        
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user
    
    # Аутентификация пользователя по email и паролю
    async def authenticate(
        self, email: str, password: str
    ) -> User:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Учетная запись пользователя деактивирована",
            )
        
        return user
    
    # Обновление профиля пользователя
    async def update(self, user: User, user_in: UserUpdate) -> User:
        # Исключаем непереданные поля
        update_data = user_in.model_dump(exclude_unset=True)
        
        if not update_data:
            return user
        
        # Проверка уникальности нового Email
        if (
            "email" in update_data
            and update_data["email"] != user.email
        ):
            if await self.get_by_email(update_data["email"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже существует",
                )
                
        # Проверка уникальности нового телефона
        if (
            "phone_number" in update_data
            and update_data["phone_number"] is not None
            and update_data["phone_number"] != user.phone_number
        ):
            if await self.get_by_phone(update_data["phone_number"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким номером телефона уже существует",
                )
                
        # Хеширование нового пароля
        if "password" in update_data:
            raw_password = update_data.pop("password")
            if raw_password:
                user.hashed_password = get_password_hash(raw_password)
                
        # Обновление остальных полей модели
        for field, value in update_data.items():
            setattr(user, field, value)
            
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
        