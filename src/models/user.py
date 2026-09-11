from enum import Enum
from datetime import date
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Date, Enum as SQLEnum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.listing import Listing


# Роли пользователя
class UserRole(str, Enum):
    CLIENT = "client"
    LANDLORD = "landlord"
    ADMIN = "admin"
    
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

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
    
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(512),
        unique=True,
        nullable=True,
    )
    
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    
    birth_day: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    gender: Mapped[Optional[Gender]] = mapped_column(
        SQLEnum(
            Gender,
            name="gender_enum",
            native_enum=True,
        ),
        nullable=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        default=0.00,
    )

    # Денормализованные рейтинги
    landlord_rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    tenant_rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.00"),
        nullable=False,
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
    
    listings: Mapped[List["Listing"]] = relationship(
        "Listing",
        back_populates = "owner",
        cascade = "all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
