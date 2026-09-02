from typing import Sequence
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.listing import Listing, ListingStatus
from src.models.user import User, UserRole
from src.schemas.listing import ListingCreate, ListingFilter, ListingUpdate


class ListingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        
    # Создание нового объявления пользователем
    async def create_listing(self, dto: ListingCreate, owner: User) -> Listing:
        listing = Listing(
            title = dto.title,
            description = dto.description,
            price_per_day = dto.price_per_day,
            address = dto.address,
            owner_id = owner.id,
            status = ListingStatus.ACTIVE,
        )

        self.session.add(listing)
        await self.session.commit()
        await self.session.refresh(list)
        
        return listing
    
    # Получения объявления по id
    async def get_listing_by_id(self, listing_id: uuid.UUID) -> Listing:
        stmt = select(Listing).where(Listing.id == listing_id)
        result = await self.session.execute(stmt)
        listing = result.scalar_one_or_none()
        
        if not listing:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Объявление не найдено",
            )
        
        return listing

    # Получение списка объявлений с пагинацией и фильтрами
    async def get_listing(self, filters: ListingFilter) -> Sequence[Listing]:
        stmt = select(Listing)
        
        if filters.status:
            stmt = stmt.where(Listing.status == filters.status)
        if filters.owner_id:
            stmt = stmt.where(Listing.owner_id == filters.owner_id)
        if filters.min_price is not None:
            stmt = stmt.where(Listing.price_per_day == filters.min_price)
        if filters.max_price is not None:
            stmt = stmt.where(Listing.price_per_day == filters.max_price)
            
        stmt = stmt.offset(filters.offset).limit(filters.limit)
        result = await self.session.execute(stmt)
        
        return result.scalars().all()
    
    # Обновление объявления с проверкой прав доступа
    async def update_listing(
        self, listing_id: uuid.UUID, dto: ListingUpdate, current_user: User
    ) -> Listing:
        listing = await self.get_listing_by_id(listing_id)
        
        # Проверка прав
        if listing.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "У вас недостаточно прав для редактирования этого объявления",
            )
        
        update_data = dto.model_dump(exclude_unset = True)
        
        for field, value in update_data.items():
            setattr(listing, field, value)
        
        await self.session.commit()
        await self.session.refresh(listing)
        return listing
    
    # Удаление объявления с проверкой прав доступа
    async def delete_listing(self, listing_id: uuid.UUID, current_user: User) -> None:
        listing = await self.get_listing_by_id(listing_id)
        
        # Проверка прав
        if listing.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "У вас недостаточно прав для удаления этого объявления",
            )
        
        await self.session.delete(listing)
        await self.session.commit()
    