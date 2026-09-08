# from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Enum as SQLEnum, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.user import User
    

class ListingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    
class Listing(BaseModel):
    __tablename__ = "listings"
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable = False,
        index = True,
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable = False,
    )
    
    price_per_day: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable = False,
    )
    
    address: Mapped[str] = mapped_column(
        String(512),
        nullable = False,
    )
    
    status: Mapped[ListingStatus] = mapped_column(
        SQLEnum(
            ListingStatus,
            name = "listing_status_enum",
            native_enum = True,
        ),
        default = ListingStatus.ACTIVE,
        nullable = False,
        index = True,
    )
    
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid = True),
        ForeignKey("users.id", ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    
    owner: Mapped["User"] = relationship("User", back_populates = "listings")