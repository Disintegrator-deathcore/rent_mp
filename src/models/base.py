from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


pk_index = Annotated[
    int,
    mapped_column(
        primary_key=True,
        autoincrement=True,
        index = True,
    ),
]

timestamp_created = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
]

timestamp_updated = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
]

class BaseModel(Base):
    __abstract__ = True
    
    id: Mapped[pk_index]
    created_at: Mapped[timestamp_created]
    updated_at: Mapped[timestamp_updated]
    
    def __repr__(self) -> str:
        attrs = [f"id={self.id}"]
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"
