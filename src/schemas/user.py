from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole


# Базовые поля пользователя
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100, examples=["Иван"])
    last_name: str = Field(min_length=1, max_length=100, examples=["Иванов"])
    phone_number: Optional[str] = Field(
        default=None,
        max_length=30,
        pattern=r"^\+?[1-9]\d{1,14}$",
        examples=["+79991112233"]
    )
    
# Схема регистрации нового пользователя
class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Пароль должен содержать минимум 8 символов",
        examples=["StrongPassword123!"],
    )
    role: UserRole = Field(default=UserRole.CLIENT)
    
# Схема для обновления профиля
# Поля опциональные для возможности изменения пользователем
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    phone_number: Optional[str] = Field(
        default=None,
        max_length=30,
        pattern=r"^\+?[1-9]\d{1,14}$",
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
    )
    
# Схема для возврата данных из API
class UserRead(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)