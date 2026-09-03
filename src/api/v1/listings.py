from typing import List
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.auth import get_current_user
from src.core.database import get_async_session
from src.models.user import User
from src.schemas.listing import(
    ListingCreate,
    ListingFilter,
    ListingResponse,
    ListingUpdate,
)
from src.services.listing import ListingService


router = APIRouter(prefix = "/listings", tags = ["Listings"])

def get_listing_service(
    session: AsyncSession = Depends(get_async_session),
) -> ListingService:
    return ListingService(session)

# Создание нового объявления (требуется авторизация)
@router.post("/", response_model = ListingResponse, status_code = status.HTTP_201_CREATED)
async def create_listing(
    dto: ListingCreate,
    current_user: User = Depends(get_current_user),
    service: ListingService = Depends(get_listing_service),
):
    return await service.create_listing(dto = dto, owner = current_user)

# Получение списка объявлений с фильтрацией и пагинацией
@router.get("/", response_model=List[ListingResponse])
async def get_listings(
    filters: ListingFilter = Depends(),
    service: ListingService = Depends(get_listing_service),
):
    return await service.get_listing(filters = filters)

# Получение конкретного объявления по ID
@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: uuid.UUID,
    service: ListingService = Depends(get_listing_service),
):
    return await service.get_listing_by_id(listing_id = listing_id)

# Обновление объявления
@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: uuid.UUID,
    dto: ListingUpdate,
    current_user: User = Depends(get_current_user),
    service: ListingService = Depends(get_listing_service),
):
    return await service.update_listing(
        listing_id = listing_id,
        dto = dto,
        current_user = current_user
    )
    
# Удаление объявления
@router.delete("/{listing_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ListingService = Depends(get_listing_service),
):
    await service.delete_listing(listing_id = listing_id, current_user = current_user)
    