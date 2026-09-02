from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.models.listing import ListingStatus


# Базовые поля объявления
class ListingBase(BaseModel):
    title: str = Field(
        ...,
        min_length = 5,
        max_length = 255,
        description = "Название объявления",
    )
    
    description: str = Field(
        ...,
        min_length = 10,
        description = "Подробное описание",
    )
    
    price_per_day: Decimal = Field(
        ...,
        gt = 0,
        max_digits = 10,
        decimal_places = 2,
        description = "Цена за день аренды",
    )
    
    address: str = Field(
        ...,
        min_length = 5,
        max_length = 512,
        description = "Физический адрес объекта",
    )
    
# Схема для создания нового объявления
class ListingCreate(ListingBase):
    pass

class ListingUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length = 5,
        max_length = 255,
    )
    
    description: Optional[str] = Field(
        None,
        min_length = 10,
    )
    
    price_per_day: Optional[Decimal] = Field(
        None,
        gt = 0,
        max_digits = 10,
        decimal_places = 2,
    )
    
    address: Optional[str] = Field(
        None,
        min_length = 5,
        max_length = 512,
    )
    
    status: Optional[ListingStatus] = None
    
# Схема для ответа API
class ListingResponse(ListingBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    status: ListingStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes = True)
    
# Схема фильтрации и пагинации для эндпоинта списка
class ListingFilter(BaseModel):
    min_price: Optional[Decimal] = Field(None, gt = 0)
    max_price: Optional[Decimal] = Field(None, gt = 0)
    status: Optional[ListingStatus] = ListingStatus.ACTIVE
    owner_id: Optional[uuid.UUID] = None
    limit: int = Field(20, ge = 1, le = 100)
    offset: int = Field(0, ge = 0)
    