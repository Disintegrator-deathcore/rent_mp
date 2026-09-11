from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.models.user import UserRole, Gender


# Базовые поля пользователя
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(
        min_length=1,
        max_length=100,
        examples=["Иван"],
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        examples=["Иванов"],
    )
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
        examples=["+79991112233"],
    )
    gender: Optional[Gender] = Field(
        default=None,
        description="Пол пользователя",
    )
    birth_day: Optional[date] = Field(
        default=None,
        description="Дата рождения пользователя",
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        examples=["Москва"],
        description="Местонахождение пользователя на текущий момент",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        examples=["https://example.com/avatars/user.jpg"],
        description="Аватар пользователя",
    )
    
    @field_validator("phone_number", "patronymic_name", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str) and not v.strip():
            return None
        return v
    
# Схема регистрации нового пользователя
class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Пароль должен содержать минимум 8 символов",
        examples=["StrongPassword123!"],
    )
    role: UserRole = Field(
        default=UserRole.CLIENT,
        description="Роль пользователя"
    )
    
    @field_validator("role")
    @classmethod
    def prevent_admin_registration(cls, role: UserRole) -> UserRole:
        if role == UserRole.ADMIN:
            raise ValueError("Регистрация с ролью ADMIN запрещена")
        return role
    
# Схема входа в систему
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

# Ответ при успешном логине/обновлении токена
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

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
    gender: Optional[Gender] = Field(
        default=None,
    )
    birth_day: Optional[date] = Field(
        default=None,
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
    )
    avatar_url: Optional[str] = Field(
        default=None,
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
    )
    
    @field_validator(
        "phone_number",
        "patronymic_name",
        "city",
        "avatar_url",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str) and not v.strip():
            return None
        return v
    
# Схема для возврата данных из API
class UserRead(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    
    # Только для чтения
    balance: Decimal = Field(
        default=Decimal("0.00"),
    )
    tenant_rating: Decimal = Field(
        default=Decimal("0.00"),
        description="Рейтинг пользователя как арендатора"
    )
    landlord_rating: Decimal = Field(
        default=Decimal("0.00"),
        description="Рейтинг пользователя как арендодателя"
    )
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Схема для запроса обновления токенов
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        description="Refresh-токен, полученный при логине",
        examples=["kjNKJANKejkwjnkeN8798719kaksdnk..."],
    )

# Верификация
class UserVerificationRequest(BaseModel):
    document_type: str = Field(
        ...,
        description="Тип документа (паспорт, права и т.д.)",
    )
    document_number: str = Field(
        ...,
        description = "Номер документа",
    )
    document_image_url: str = Field(
        ...,
        description = "Ссылка на фото документа",
    )

# Двухфакторка
class TwoFactorEnableRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-значный TOTP код или SMS код",
    )

class TwoFactoryVerifyRequest(BaseModel):
    user_id: UUID
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
    )

# Альтернативный вход через соцсети (OAuth2)
class SocialAuthRequest(BaseModel):
    provider: str = Field(
        ...,
        examples=["vk", "ok", "max", "telegram"],
        description="Провайдер авторизации",
    )

# Удаление аккаунта (подтверждение удаления)
class UserDeleteRequest(BaseModel):
    password: str = Field(
        ...,
        description="Текущий пароль для подтверждения удаления",
    )
