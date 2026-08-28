from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.models.user import UserRole


# Базовые поля пользователя
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100, examples=["Иван"])
    last_name: str = Field(min_length=1, max_length=100, examples=["Иванов"])
    patronymic_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        examples=["Иванович"],
    )
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
    patronymic_name: Optional[str] = Field(
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
    
@field_validator("phone_number", "patronymic_name", mode="before")
@classmethod
def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
    if isinstance(v, str) and not v.strip():
        return None
    return v

# Схема для запроса обновления токенов
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        description="Refresh-токен, полученный при логине",
        examples=["kjNKJANKejkwjnkeN8798719kaksdnk..."],
    )
