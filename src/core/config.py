from enum import Enum
from typing import List, Union

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Настройки приложения
    PROJECT_NAME: str = "Rental Marketplace API"
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Подключение к postgres
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = Field(default=...)
    POSTGRES_PASSWORD: str = Field(default=...)
    POSTGRES_DB: str = Field(default=...)
    
    # Автоматически собираемый или явно передаваемый DSN
    DATABASE_URL: Union[PostgresDsn, str] = Field(default=...)
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Union[str, None], values) -> str:
        if isinstance(v, str) and v:
            return v
        # Собираем DSN автоматически, если он не задан строкой
        user = values.data.get("POSTGRES_USER")
        password = values.data.get("POSTGRES_PASSWORD")
        server = values.data.get("POSTGRES_SERVER")
        port = values.data.get("POSTGRES_PORT")
        db = values.data.get("POSTGRES_DB")
        return f"postgresql+asyncpg://{user}:{password}@{server}/{port}/{db}"
        
    # Безопасность и JWT
    SECRET_KEY: str = Field(default=...)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # REDIS
    REDIS_URL: Union[RedisDsn, str] = "redis://localhost:6379/0"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
# Создаем синглтон настроек для импорта в других модулях
settings = Settings()