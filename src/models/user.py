from enum import Enum
from typing import Optional

from sqlalchemy import Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel


# Роли пользователя
class UserRole(str, Enum):
    CLIENT = "client"
    LANDLORD = "landlord"
    ADMIN = "admin"

# Модель пользователя    
class User(BaseModel):
    __tablename__ = "users"
    
    # Учетные данные
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # Персональные данные
    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    last_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    patronymic_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    phone_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=True,
    )
    
    # Статусы и доступ
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="user_role_enum",
            native_enum=True
            ),
        default=UserRole.CLIENT,
        nullable=False,
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
